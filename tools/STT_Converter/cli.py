# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 헤드리스 (docs/0130_stt_converter_plan.md D12 · T4). UI 와 같은 코어(app/core)를 쓴다.
#
#   .venv_stt\Scripts\python.exe tools\STT_Converter\cli.py <폴더 | wav ...> --language Korean
#       [--out DIR] [--ext .lab|.txt] [--existing skip|overwrite|backup] [--no-json]
#       [--engine faster-whisper] [--model large-v3-turbo] [--device auto|cuda:float16|cuda:int8_float16|cpu:int8]
#       [--beam 5] [--vad auto|on|off] [--kana] [--no-normalize] [--user-dict FILE.json] [--quiet]
#
# 종료 코드: 0 = 전부 끝남(건너뜀 · 경고 포함), 1 = 사전 검사 실패(아무것도 안 씀) 또는 엔진 로드 실패 · 중단,
#            2 = 인자 오류. 로그는 stdout 에 "[LEVEL] message" (UI 로그와 같은 줄) - A00560 JaliBatch P4 가 읽는다.
# 모델 캐시는 저장소 models/ (HF_HOME). 개발 PC 의 CUDA 금지(force_cpu.flag)는 device.choose 가 처리한다.

import argparse
import json
import os
import sys

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
os.environ.setdefault("HF_HOME", os.path.join(REPO_ROOT, "models"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from tools.STT_Converter.app.config.version import APP_NAME, VERSION            # noqa: E402
from tools.STT_Converter.app.core import converter, device, job, settings      # noqa: E402
from tools.STT_Converter.app.core.engines import ENGINES, LANGUAGES, TranscribeOptions, make_engine  # noqa: E402

DEVICE_KEYS = [k for _l, k in device.DEVICE_CHOICES]


def _utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def collect_wavs(paths):
    """폴더는 바로 아래 .wav 만(하위 폴더 X), 파일은 그대로. 중복 제거, 순서 유지."""
    out, seen = [], set()
    for p in paths:
        cands = []
        if os.path.isdir(p):
            cands = [os.path.join(p, n) for n in sorted(os.listdir(p)) if n.lower().endswith(".wav")]
        elif p.lower().endswith(".wav"):
            cands = [p]
        for c in cands:
            c = os.path.normpath(os.path.abspath(c))
            if c.lower() not in seen:
                seen.add(c.lower())
                out.append(c)
    return out


def build_parser():
    ap = argparse.ArgumentParser(prog="cli.py", description="{0} v{1} - wav -> transcript (.lab)".format(APP_NAME, VERSION))
    ap.add_argument("inputs", nargs="+", help="wav files and/or folders (folder = its .wav files, not recursive)")
    ap.add_argument("--language", required=True, choices=LANGUAGES)
    ap.add_argument("--out", default="", help="output folder (default: next to each wav)")
    ap.add_argument("--ext", default=".lab", choices=list(job.TRANSCRIPT_EXTS))
    ap.add_argument("--existing", default="skip", choices=[k for _l, k in job.EXISTING_MODES])
    ap.add_argument("--no-json", action="store_true", help="do not write <name>.stt.json")
    ap.add_argument("--engine", default="faster-whisper", choices=sorted(ENGINES))
    ap.add_argument("--model", default="large-v3-turbo", help="size name or Hugging Face repo")
    ap.add_argument("--device", default="auto", choices=DEVICE_KEYS)
    ap.add_argument("--beam", type=int, default=5)
    ap.add_argument("--vad", default="auto", choices=("auto", "on", "off"),
                    help="auto = off for clips shorter than {0:.0f} s".format(converter.VAD_AUTO_MIN_SECONDS))
    ap.add_argument("--kana", action="store_true", help="Japanese: write everything in kana")
    ap.add_argument("--no-normalize", action="store_true", help="write the raw recognized text")
    ap.add_argument("--user-dict", default="", help="json {token: replacement}; default data/user_dict_<lang>.json")
    ap.add_argument("--quiet", action="store_true", help="only WARN / ERROR / DONE lines")
    return ap


def main(argv=None):
    _utf8_stdio()
    ap = build_parser()
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0

    def log(level, message):
        if a.quiet and level in ("INFO", "OK"):
            return
        print("[{0}] {1}".format(level, message), flush=True)

    wavs = collect_wavs(a.inputs)
    if not wavs:
        log("ERROR", "no .wav files in: {0}".format(", ".join(a.inputs)))
        return 1
    log("INFO", "{0} v{1} - {2} file(s), language {3}".format(APP_NAME, VERSION, len(wavs), a.language))

    engine_cls = ENGINES[a.engine]
    jobs, problems = job.preflight(wavs, a.language, a.out, a.ext, a.existing, engine_cls)
    for wav, code, message in problems:
        log("ERROR", "{0}  {1} {2}".format(os.path.basename(wav) or "Output", code, message))
    if problems:
        log("ERROR", "{0} problem(s) found. Nothing was converted.".format(len(problems)))
        return 1

    dev, compute, note = device.choose(a.device)
    if note:
        log("WARN", "W21 {0}".format(note))
    log("INFO", "device: {0}".format(device.detect().summary()))
    cache = os.path.join(REPO_ROOT, "models")
    engine = make_engine(a.engine, a.model, dev, compute, cache)
    fallback = (lambda: make_engine(a.engine, a.model, "cpu", "int8", cache)) if dev == "cuda" else None

    if a.user_dict:
        try:
            with open(a.user_dict, "r", encoding="utf-8") as f:
                user_dict = {str(k): str(v) for k, v in json.load(f).items()}
        except (OSError, ValueError, AttributeError) as e:
            log("ERROR", "cannot read --user-dict {0}: {1}".format(a.user_dict, e))
            return 2
    else:
        user_dict = settings.load_user_dict(a.language)
    norm_cfg = converter.NormalizeConfig(enabled=not a.no_normalize, user_dict=user_dict, kana=a.kana)
    options = TranscribeOptions(beam_size=a.beam, vad={"auto": "auto", "on": True, "off": False}[a.vad])

    written, reason = converter.run_batch(
        engine, jobs, options, norm_cfg, write_json=not a.no_json, existing=a.existing,
        converter_name="{0} {1} (cli)".format(APP_NAME, VERSION), log=log, fallback_factory=fallback)
    skipped = sum(1 for j in jobs if j.skipped)
    if reason:
        log("ERROR", reason)
        return 1
    log("DONE", "{0} transcript(s) written, {1} skipped (existing), {2} file(s) total".format(
        len(written), skipped, len(jobs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
