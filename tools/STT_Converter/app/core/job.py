# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 작업 단위 + 사전 검사 (docs/0130_stt_converter_plan.md D5 · D6 · D13 · §5-3 E40 ~ E44)
#
# 사전 검사는 VisemeNet Converter 와 같은 원칙 - 하나라도 실패면 아무것도 변환하지 않는다 (환경 · 경로 문제를 미리).
#   E40 엔진 패키지 없음 · E42 wav 를 못 읽음(손상 · 0 초) · E43 출력 폴더 쓰기 불가
# 기존 대본(<이름>.lab / .txt)이 있으면 existing 정책: skip(기본, W25) / overwrite / backup(<이름>.lab.bak).
# 출력 확장자 .lab 기본 - .txt 는 VisemeNet 결과 22열 txt 와 이름이 겹친다(E34). .txt 를 고르면 그 사실을 경고(W26).

import os

TRANSCRIPT_EXTS = (".lab", ".txt")
EXISTING_MODES = (("Skip (keep the existing transcript)", "skip"),
                  ("Overwrite", "overwrite"),
                  ("Overwrite with backup (.bak)", "backup"))
JSON_SUFFIX = ".stt.json"


class WavInfo(object):
    def __init__(self, path, sample_rate, channels, frames, subtype=""):
        self.path = path
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames = frames
        self.subtype = subtype

    @property
    def seconds(self):
        return self.frames / float(self.sample_rate) if self.sample_rate else 0.0

    def summary(self):
        return "{0} Hz, {1} ch, {2:.1f} s{3}".format(self.sample_rate, self.channels, self.seconds,
                                                     " " + self.subtype if self.subtype else "")


def read_wav_info(path):
    """soundfile 로 헤더만 읽는다 (없으면 wave 모듈). 실패면 ValueError."""
    try:
        import soundfile as sf
        i = sf.info(path)
        return WavInfo(path, i.samplerate, i.channels, i.frames, i.subtype)
    except ImportError:
        import wave
        with wave.open(path, "rb") as w:
            return WavInfo(path, w.getframerate(), w.getnchannels(), w.getnframes(), "PCM_{0}".format(w.getsampwidth() * 8))
    except Exception as e:
        raise ValueError(str(e) or repr(e))


class Job(object):
    def __init__(self, wav_path, language, out_path, json_path):
        self.wav_path = wav_path
        self.language = language
        self.out_path = out_path
        self.json_path = json_path
        self.info = None
        self.existing = os.path.isfile(out_path)
        self.skipped = False                    # existing = skip 이고 대본이 이미 있다
        self.warnings = []                      # [(code, message)] 사전 검사 경고

    @property
    def name(self):
        return os.path.basename(self.wav_path)


def output_paths(wav_path, out_dir, ext):
    stem = os.path.splitext(os.path.basename(wav_path))[0]
    folder = out_dir or os.path.dirname(os.path.abspath(wav_path))
    return os.path.join(folder, stem + ext), os.path.join(folder, stem + JSON_SUFFIX)


def _check_writable(folder):
    try:
        os.makedirs(folder, exist_ok=True)
        probe = os.path.join(folder, ".stt_write_test")
        with open(probe, "w") as f:
            f.write("x")
        os.remove(probe)
        return True
    except OSError:
        return False


def preflight(wav_paths, language, out_dir="", ext=".lab", existing="skip", engine_cls=None):
    """Returns (jobs, problems). problems = [(wav_or_"", code, message)] - 비어 있지 않으면 변환하지 않는다."""
    jobs, problems = [], []
    if engine_cls is not None and not engine_cls.available():
        problems.append(("", "E40", "engine package is not installed - run setup_stt.bat"))
    if ext not in TRANSCRIPT_EXTS:
        problems.append(("", "E43", "unknown transcript extension {0}".format(ext)))
    folders_checked = {}
    seen = set()
    for wav in wav_paths:
        wav = os.path.abspath(wav)
        if wav.lower() in seen:
            continue
        seen.add(wav.lower())
        out_path, json_path = output_paths(wav, out_dir, ext)
        job = Job(wav, language, out_path, json_path)
        try:
            job.info = read_wav_info(wav)
        except ValueError as e:
            problems.append((wav, "E42", "cannot read audio: {0}".format(e)))
            continue
        if job.info.frames <= 0 or job.info.seconds < 0.1:
            problems.append((wav, "E42", "audio is empty ({0:.2f} s)".format(job.info.seconds)))
            continue
        folder = os.path.dirname(out_path)
        if folder not in folders_checked:
            folders_checked[folder] = _check_writable(folder)
        if not folders_checked[folder]:
            problems.append((wav, "E43", "cannot write to the output folder: {0}".format(folder)))
            continue
        if ext == ".txt":
            job.warnings.append(("W26", "output is .txt - a VisemeNet 22-column result with the same name would be "
                                        "mistaken for a transcript; .lab is recommended"))
        if job.existing:
            if existing == "skip":
                job.skipped = True
                job.warnings.append(("W25", "transcript exists - skipped ({0})".format(os.path.basename(out_path))))
            elif existing == "backup":
                job.warnings.append(("W27", "transcript exists - will be backed up to {0}.bak".format(
                    os.path.basename(out_path))))
            else:
                job.warnings.append(("W27", "transcript exists - will be overwritten"))
        jobs.append(job)
    return jobs, problems
