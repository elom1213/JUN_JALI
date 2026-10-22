# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# VisemeNet Converter - 추론 엔진 + 일괄 변환 (UI 비의존, docs/0030_tool_plan.md §4.3 ~ §4.5)
#
# 흐름: preflight(전부 검사) -> 하나라도 실패면 아무것도 변환하지 않음 -> run_batch(하나씩 추론 · 쓰기)
#       -> 변환 중 오류가 나면 남은 파일은 건너뛰고 멈춘다. (사용자 요청: 문제가 생기면 중단 + 이유를 로그로)
#
# Correct 모드 (docs/0060_transcript_mfa_plan.md 안 B): wav 옆의 대본(<이름>.lab / .txt)을 MFA 로 정렬해
#   음소 구간으로 비짐을 보정한다. 대본이 없는 파일은 오디오만으로 변환한다(대본은 선택 입력).
#   정렬은 run_batch 시작 때 대본 있는 파일을 묶어 **한 번에** 한다. 정렬에 실패한 파일은 W10 경고 후 오디오만.
#
# 원본 inference.py · postprocess.py 는 수정하지 않는다. 다만 predict_outputs 의 기본 경로가 현재 폴더 기준
# 상대경로("./saved_params/...")라 절대경로를 넘긴다. TensorFlow import 는 느리므로(~5초) load() 에서만.

import contextlib
import io
import logging
import math
import os
import sys
import time

import numpy as np

from . import aligner, output_writer, viseme_merge
from .wav_check import WavError, check_wav


COLUMNS = ["Jaw", "Lip", "Ah", "Aa", "Eh", "Ee", "Ih", "Oh", "Uh", "U", "Eu", "Schwa", "R", "S",
           "ShChZh", "Th", "JY", "LNTD", "GK", "MBP", "FV", "W"]
MODEL_FPS = 100
MODEL_FILE = "visemenet_frozen.pb"
PARAM_FILES = ("saved_params/wav_mean_std.csv", "saved_params/maya_close_face.txt")
ROW_TOLERANCE = 2               # expected_rows() 와의 허용 차
NET2_HALF_WINDOW = 32           # 모델 net2 가 앞에 0 을 32줄 채우고 64줄 창으로 훑는다 -> 끝 32줄(0.32 s)이 빠진다


class ConvertError(Exception):
    """변환 중 멈춰야 하는 문제. code 는 E09 ~ E11 (출력 계획), E20 ~ E24 (추론 · 쓰기)."""

    def __init__(self, code, message, detail=None):
        super().__init__("{0} {1}".format(code, message))
        self.code = code
        self.message = message
        self.detail = detail


class _WarningCatcher(logging.Handler):
    """python_speech_features 의 'frame will be truncated' 경고를 모은다 (44.1kHz 에서는 정상)."""

    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


DROPOUT_KEEP_SUFFIX = "dropout/keep_prob"


def _load_graph_deterministic(pb_filepath):
    """frozen 그래프를 불러오며 net2 의 dropout 을 끈다 (keep_prob 0.5 -> 1.0).

    원본 model.py 는 net2 LSTM 7개에 DropoutWrapper(output_keep_prob=0.5) 를 **상수로** 박아 두어
    (feed 하는 dropout placeholder 는 net1 에만 걸린다) 추론 때도 dropout 이 돈다 -> 같은 wav 도 돌릴 때마다
    결과가 다르다(실측 최대 차 0.64). inverted dropout 이라 keep_prob=1 이 곧 '기댓값' 추론이다.
    """
    import numpy as np_
    import tensorflow as tf

    with tf.io.gfile.GFile(pb_filepath, "rb") as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())
    patched = 0
    for node in graph_def.node:
        if node.op == "Const" and node.name.endswith(DROPOUT_KEEP_SUFFIX):
            node.attr["value"].tensor.CopyFrom(tf.make_tensor_proto(np_.float32(1.0)))
            patched += 1
    graph = tf.Graph()
    with graph.as_default():
        tf.import_graph_def(graph_def, name="")
    return graph, patched


class Engine(object):
    """VisemeRegressor 를 한 번 로드해 여러 파일에 쓴다.

    deterministic=True (기본) : net2 dropout 을 끈다 - 같은 입력 = 같은 결과.
    deterministic=False       : 원본 그대로 (돌릴 때마다 조금씩 다르다).
    """

    def __init__(self, root, deterministic=True):
        self.root = os.path.abspath(root)
        self.deterministic = deterministic
        self.patched_dropouts = 0
        self._regressor = None

    @property
    def mode_name(self):
        return "deterministic (net2 dropout off)" if self.deterministic else "original (random dropout)"

    @property
    def loaded(self):
        return self._regressor is not None

    def check_files(self):
        for rel in (MODEL_FILE,) + PARAM_FILES:
            if not os.path.isfile(os.path.join(self.root, rel)):
                raise ConvertError("E20", "model file missing: {0}".format(rel))

    def load(self):
        if self._regressor is not None:
            return
        self.check_files()
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        if self.root not in sys.path:
            sys.path.insert(0, self.root)
        try:
            # _load_graph 가 텐서 이름을 print 한다 - 화면(로그)에 내보내지 않는다.
            with contextlib.redirect_stdout(io.StringIO()):
                from inference import VisemeRegressor
                cls = VisemeRegressor
                if self.deterministic:
                    engine = self

                    class _DeterministicRegressor(VisemeRegressor):
                        # inference.py 는 고치지 않는다 - 그래프 불러오기만 바꿔 끼운다.
                        def _load_graph(self, pb_filepath):
                            graph, engine.patched_dropouts = _load_graph_deterministic(pb_filepath)
                            return graph
                    cls = _DeterministicRegressor
                regressor = cls(pb_filepath=os.path.join(self.root, MODEL_FILE))
            if self.deterministic and self.patched_dropouts == 0:
                raise ConvertError("E21", "model load failed: no dropout constant found to turn off")
            self._regressor = regressor
        except ConvertError:
            raise
        except Exception as e:
            raise ConvertError("E21", "model load failed: {0}".format(_first_line(e)), detail=repr(e))

    def predict(self, wav_path, notes=None):
        """wav -> (N, 22). notes 리스트를 주면 라이브러리 경고 문구를 담는다."""
        self.load()
        catcher = _WarningCatcher()
        logging.getLogger().addHandler(catcher)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                out = self._regressor.predict_outputs(
                    wav_file_path=wav_path,
                    mean_std_csv_path=os.path.join(self.root, PARAM_FILES[0]),
                    close_face_txt_path=os.path.join(self.root, PARAM_FILES[1]))
        except Exception as e:
            raise ConvertError("E21", "inference failed: {0}".format(_first_line(e)), detail=repr(e))
        finally:
            logging.getLogger().removeHandler(catcher)
        if notes is not None:
            notes.extend(catcher.messages)

        out = np.asarray(out, dtype=np.float64)
        if out.ndim != 2 or out.shape[1] != len(COLUMNS):
            raise ConvertError("E23", "unexpected output shape {0}".format(tuple(out.shape)))
        if not np.isfinite(out).all():
            raise ConvertError("E22", "model output has NaN / inf")
        return out


# ------------------------------------------------------------------ batch

class Job(object):
    def __init__(self, wav_path, info, txt_path, json_path):
        self.wav_path = wav_path
        self.info = info
        self.txt_path = txt_path
        self.json_path = json_path
        self.transcript_path = None
        self.transcript = ""


class AlignConfig(object):
    """Correct 모드 설정. preflight 가 install(MfaInstall) 을 채운다."""

    def __init__(self, language="English", mfa_folder="", params=None):
        self.language = language
        self.mfa_folder = mfa_folder
        self.params = params or viseme_merge.Params()
        self.install = None


def preflight(wav_paths, out_dir, overwrite, max_seconds, write_json=True, align_cfg=None, repo_root=None):
    """전부 검사한다. Returns (jobs, problems). problems = [(wav, code, message)] - 비어야 변환 가능.

    align_cfg 가 있으면(Correct 모드) MFA 설치 · 언어 모델(E30 · E31) 과 대본(E32) 도 검사한다.
    """
    jobs, problems = [], []
    if align_cfg is not None:
        root = repo_root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))))
        align_cfg.install = aligner.find_install(root, align_cfg.mfa_folder)
        if align_cfg.install is None:
            return [], [("", "E30", "MFA not found - set the MFA folder or run setup_mfa.bat")]
        try:
            aligner.check_models(align_cfg.install, align_cfg.language)
        except aligner.AlignError as e:
            return [], [("", e.code, e.message)]

    if out_dir:
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as e:
            return [], [("", "E10", "cannot create output folder {0}: {1}".format(out_dir, e.strerror))]
        if not os.access(out_dir, os.W_OK):
            return [], [("", "E10", "cannot write to {0}".format(out_dir))]

    claimed = {}
    for wav in wav_paths:
        try:
            info = check_wav(wav, max_seconds)
        except WavError as e:
            problems.append((wav, e.code, e.message))
            continue

        txt, js = output_writer.output_paths(wav, out_dir)
        key = os.path.normcase(os.path.abspath(txt))
        if key in claimed:
            problems.append((wav, "E11", "two files would write the same output: {0} "
                                         "(also {1})".format(os.path.basename(txt), claimed[key])))
            continue
        claimed[key] = wav

        # 결과 txt 가 대본(같은 이름 .txt)을 덮어쓰면 안 된다 - 모드와 상관없이 막는다
        if os.path.isfile(txt) and not aligner.looks_like_viseme_txt(txt):
            problems.append((wav, "E34", "output would overwrite the transcript {0} - choose an output folder "
                                         "or rename the transcript to .lab".format(os.path.basename(txt))))
            continue

        transcript_path, transcript = None, ""
        if align_cfg is not None:
            transcript_path = aligner.transcript_path(wav)
            if transcript_path:
                try:
                    transcript = aligner.read_transcript(transcript_path)
                except aligner.AlignError as e:
                    problems.append((wav, e.code, e.message))
                    continue

        if not overwrite:
            exists = [p for p in ((txt, js) if write_json else (txt,)) if os.path.exists(p)]
            if exists:
                problems.append((wav, "E09", "output exists: {0} (turn on Overwrite)".format(exists[0])))
                continue
        if not out_dir and not os.access(os.path.dirname(txt), os.W_OK):
            problems.append((wav, "E10", "cannot write to {0}".format(os.path.dirname(txt))))
            continue

        job = Job(wav, info, txt, js)
        job.transcript_path, job.transcript = transcript_path, transcript
        jobs.append(job)
    return jobs, problems


def run_batch(engine, jobs, write_json, converter_name, log, progress=None, should_stop=None, align_cfg=None,
              stage=None):
    """jobs 를 차례로 변환한다. 오류가 나면 멈춘다.

    Args:
        log: log(level, message) - level 은 "OK" / "INFO" / "WARN" / "ERROR" / "DONE".
        progress: progress(done, total, name) 또는 None.
        should_stop: () -> bool. True 면 다음 파일 전에 멈춘다.
        align_cfg: AlignConfig (preflight 를 거친 것) 또는 None(오디오만).
        stage: stage(key) 또는 None - 단계가 바뀔 때 알린다: "align"(대본 있는 파일이 있을 때만) / "convert".

    Returns:
        (written_jobs, stopped_reason) - 다 끝나면 stopped_reason 은 None.
    """
    written = []
    total = len(jobs)
    truncation_noted = False
    t0 = time.time()

    log("INFO", "inference mode: {0}".format(engine.mode_name))
    aligned, phone_map, mfa_name = {}, None, ""
    if align_cfg is not None:
        if stage and any(job.transcript for job in jobs):
            stage("align")
        try:
            aligned, phone_map, mfa_name = _align_all(jobs, align_cfg, log, progress)
        except (aligner.AlignError, ValueError, OSError) as e:
            code = getattr(e, "code", "E33")
            log("ERROR", "{0} {1}".format(code, getattr(e, "message", str(e))))
            if getattr(e, "detail", None):
                log("INFO", "detail: {0}".format(e.detail))
            return written, "{0} {1}".format(code, getattr(e, "message", str(e)))
        if should_stop and should_stop():
            return written, "stopped by user after alignment"

    if stage:
        stage("convert")
    for i, job in enumerate(jobs):
        name = os.path.basename(job.wav_path)
        if should_stop and should_stop():
            return written, "stopped by user before {0}".format(name)
        if progress:
            progress(i, total, name)

        notes = []
        t = time.time()
        try:
            out = engine.predict(job.wav_path, notes)
            expected = expected_rows(job.info.n_samples, job.info.sample_rate)
            if out.shape[0] < 1 or abs(out.shape[0] - expected) > ROW_TOLERANCE:
                raise ConvertError("E23", "unexpected output length {0} rows (expected {1})"
                                   .format(out.shape[0], expected))
            result = aligned.get(job.wav_path)
            correction = None
            if result is not None and result.ok:
                out, report = viseme_merge.correct(out, result.phones, phone_map, align_cfg.params)
                correction = _correction_info(job, result, report, align_cfg, mfa_name)
                _log_correction(log, name, result, report)
            try:
                output_writer.write_txt(job.txt_path, out)
                if write_json:
                    output_writer.write_json(job.json_path, job.info, out, COLUMNS, MODEL_FPS,
                                             MODEL_FILE, converter_name, engine.mode_name, correction)
                if correction is not None:
                    output_writer.write_phones(output_writer.phones_path(job.txt_path), job.info,
                                               result.words, result.phones, correction)
            except OSError as e:
                raise ConvertError("E24", "cannot write {0}: {1}".format(job.txt_path, e.strerror or e))
        except ConvertError as e:
            log("ERROR", "{0}  {1} {2}".format(name, e.code, e.message))
            if e.detail:
                log("INFO", "detail: {0}".format(e.detail))
            return written, "{0} {1} ({2})".format(e.code, e.message, name)

        if notes and not truncation_noted and any("truncated" in n for n in notes):
            log("INFO", "'frame will be truncated' from python_speech_features is normal at 44.1 kHz "
                        "(the model was trained the same way)")
            truncation_noted = True

        written.append(job)
        log("OK", "{0}  -> {1}  ({2} rows, {3}, {4:.1f} s)".format(
            name, os.path.basename(job.txt_path), out.shape[0],
            "corrected" if correction is not None else "audio only", time.time() - t))

    if progress:
        progress(total, total, "")
    log("DONE", "{0} converted in {1:.1f} s".format(len(written), time.time() - t0))
    return written, None


def _align_all(jobs, cfg, log, progress):
    """대본 있는 파일을 한 번에 MFA 로 정렬한다. Returns ({wav: AlignResult}, PhoneMap, 'MFA x.y.z')."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))))
    phone_map = viseme_merge.load_default_map(root, COLUMNS)
    items = [(job.wav_path, job.wav_path, job.transcript) for job in jobs if job.transcript]
    for job in jobs:
        if not job.transcript:
            log("INFO", "{0}  no transcript (.lab / .txt next to the WAV) - audio only"
                .format(os.path.basename(job.wav_path)))
    if not items:
        return {}, phone_map, ""
    if progress:
        progress(0, len(jobs), "aligning transcripts (MFA)")
    mfa_name = "MFA " + (aligner.version(cfg.install) or "?")
    results = aligner.align(cfg.install, cfg.language, items, log=log)
    for key, res in results.items():
        if not res.ok:
            log("WARN", "{0}  W10 alignment failed - audio only (check that the transcript matches the speech)"
                .format(os.path.basename(key)))
    return results, phone_map, mfa_name


def _correction_info(job, result, report, cfg, mfa_name):
    acoustic, dictionary, _g2p = aligner.LANGUAGES[cfg.language]
    return {
        "mode": "correct",
        "language": cfg.language,
        "transcript_file": os.path.abspath(job.transcript_path).replace("\\", "/"),
        "transcript": job.transcript,
        "aligner": "{0} ({1} / {2})".format(mfa_name, acoustic, dictionary),
        "phone_segments": report["segments"],
        "unmapped_phones": report["unmapped"],
        "oov_words": [w[2] for w in result.words if w[2] in ("<unk>", "spn")],
        "params": report["params"],
    }


def _log_correction(log, name, result, report):
    oov = sum(1 for p in result.phones if p[2] == "spn")
    if oov:
        log("WARN", "{0}  W11 {1} word(s) not in the dictionary - VisemeNet values kept there"
            .format(name, oov))
    if report["unmapped"]:
        log("WARN", "{0}  W13 phones not in ipa_to_jali.json: {1} - VisemeNet values kept there"
            .format(name, " ".join(report["unmapped"])))
    if report["beyond_rows"]:
        log("INFO", "{0}  {1} phone(s) in the last 0.32 s (beyond the model output) were skipped"
            .format(name, report["beyond_rows"]))


def expected_rows(n_samples, sample_rate=44100):
    """모델이 내놓을 줄 수. 줄 i = 음성 i * 10ms (시작은 맞고 **끝 0.32초가 빠진다**).

    python_speech_features 프레임 수(25ms 창 · 10ms 간격) -> inference.py 가 4의 배수로 자름
    -> 원본 model.py 의 net2 가 win_size_2(64) 창을 앞쪽 32줄 0 패딩 위에서 훑어 32줄이 준다.
    실측: coffee_xxxx 398 -> 396 -> 364, visemenet_intro 1485 -> 1484 -> 1452.
    """
    frame_len = int(math.floor(0.025 * sample_rate + 0.5))
    step = int(math.floor(0.01 * sample_rate + 0.5))
    frames = 1 if n_samples <= frame_len else 1 + int(math.ceil((n_samples - frame_len) / float(step)))
    return (frames // 4) * 4 - NET2_HALF_WINDOW


def _first_line(e):
    text = str(e).strip() or type(e).__name__
    return text.splitlines()[0]
