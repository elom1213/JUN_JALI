# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
#
# M0 실측 스크립트 (docs/0130_stt_converter_plan.md §6) - faster-whisper 로 wav 를 받아쓰고
# 옆의 손 대본(<이름>.txt / .lab)이 있으면 CER / WER 을 잰다. 결과는 §11 표에 적는다.
#
#   .venv_stt\Scripts\python.exe tools\STT_Converter\tests\m0_transcribe.py ^
#       --language Korean --compute float16 ^
#       ..\JUN_JALI_Voice\0060_Vivian_voice\src_kr\0010_vivian_kr.wav
#
# 옵션: --model large-v3-turbo | large-v3 | <HF repo> · --device cuda|cpu · --compute float16|int8_float16|int8
#       --beam 5 · --no-vad · --json <폴더> (세그먼트 json 저장)
# Windows: pip 로 받은 nvidia cuBLAS / cuDNN DLL 폴더를 ctranslate2 import 전에 등록한다 (아래 add_nvidia_dlls).
# 출력은 항상 UTF-8 로 쓴다 - `python -I` 는 PYTHONUTF8 환경 변수를 무시하므로 콘솔이 cp949 면 일본어 출력에서
#   UnicodeEncodeError 가 났다 (2026-10-23 M0-3 JP 결과 유실). 아래 _force_utf8_stdio 가 막는다.
# --device cpu 면 CUDA 를 전혀 건드리지 않는다 (DLL 등록 · 장치 수 조회 생략) - 개발 PC 가 CUDA 작업에서 강제 종료되는 문제 때문.
import argparse
import json
import os
import sys
import time


def _force_utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_force_utf8_stdio()

LANG_CODES = {"English": "en", "Korean": "ko", "Japanese": "ja"}


def add_nvidia_dlls():
    """pip 의 nvidia-cublas-cu12 / nvidia-cudnn-cu12 가 둔 DLL 폴더를 프로세스 DLL 탐색 경로에 더한다.
    Returns 등록한 폴더 목록 (없으면 빈 리스트 - 시스템 CUDA 가 PATH 에 있을 수도 있다)."""
    added = []
    if os.name != "nt":
        return added
    try:
        import nvidia  # pip 네임스페이스 패키지
    except ImportError:
        return added
    for base in list(getattr(nvidia, "__path__", [])):
        for sub in ("cublas", "cudnn"):
            d = os.path.join(base, sub, "bin")
            if os.path.isdir(d):
                os.add_dll_directory(d)
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                added.append(d)
    return added


def transcript_next_to(wav):
    base = os.path.splitext(wav)[0]
    for ext in (".lab", ".txt"):
        p = base + ext
        if os.path.isfile(p):
            with open(p, encoding="utf-8-sig") as f:
                return p, f.read()
    return None, None


def norm_for_metric(text, lang):
    """측정용 정규화 - 구두점 · 공백만 정리 (대본 정규화와 다르다, 비교 공정성용)."""
    import re
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[「」『』【】（）()\[\]\"'“”‘’…・、。，．,.!?！？:;：；\-—~～]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if lang in ("Japanese",):
        text = text.replace(" ", "")   # 일본어는 공백 없이 글자 단위
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wavs", nargs="+")
    ap.add_argument("--language", required=True, choices=sorted(LANG_CODES))
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--compute", default="float16")
    ap.add_argument("--beam", type=int, default=5)
    ap.add_argument("--no-vad", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    if a.device != "cpu":
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        try:
            from tools.STT_Converter.app.core import device as _dev
            forced = _dev.force_cpu_reason()
        except Exception:
            forced = ""
        if forced:
            print("[M0] CPU forced ({0}) - using --device cpu --compute int8".format(forced))
            a.device, a.compute = "cpu", "int8"

    import ctranslate2
    from faster_whisper import WhisperModel
    if a.device == "cpu":
        # CPU 전용 - CUDA 초기화 없음
        print("[M0] device cpu - CUDA not touched. ctranslate2", ctranslate2.__version__,
              "cpu compute types:", sorted(ctranslate2.get_supported_compute_types("cpu")),
              "threads:", os.cpu_count())
    else:
        dlls = add_nvidia_dlls()
        print("[M0] nvidia DLL dirs:", dlls or "(none)")
        print("[M0] ctranslate2", ctranslate2.__version__, "cuda devices:", ctranslate2.get_cuda_device_count(),
              "supported compute types:", sorted(ctranslate2.get_supported_compute_types(a.device)))

    t0 = time.perf_counter()
    model = WhisperModel(a.model, device=a.device, compute_type=a.compute)
    t_load = time.perf_counter() - t0
    print("[M0] model {0} loaded on {1}/{2} in {3:.1f} s".format(a.model, a.device, a.compute, t_load))

    try:
        import jiwer
    except ImportError:
        jiwer = None

    for wav in a.wavs:
        wav = os.path.abspath(wav)
        t1 = time.perf_counter()
        segments, info = model.transcribe(
            wav, language=LANG_CODES[a.language], beam_size=a.beam,
            vad_filter=not a.no_vad, vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=False, word_timestamps=True)
        segs = []
        for s in segments:
            segs.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text,
                         "avg_logprob": round(s.avg_logprob, 3), "no_speech_prob": round(s.no_speech_prob, 3),
                         "compression_ratio": round(s.compression_ratio, 3),
                         "words": [[round(w.start, 3), round(w.end, 3), w.word, round(w.probability, 3)]
                                   for w in (s.words or [])]})
        t_tr = time.perf_counter() - t1
        hyp = " ".join(s["text"].strip() for s in segs)
        print("\n[M0] {0}  ({1:.1f} s audio, {2:.1f} s transcribe, x{3:.1f} realtime) detected={4} p={5:.2f}"
              .format(os.path.basename(wav), info.duration, t_tr, info.duration / max(t_tr, 1e-6),
                      info.language, info.language_probability))
        print("[M0] HYP:", hyp)
        ref_path, ref = transcript_next_to(wav)
        if ref and jiwer:
            r, h = norm_for_metric(ref, a.language), norm_for_metric(hyp, a.language)
            cer = jiwer.cer(r, h)
            wer = jiwer.wer(r, h) if a.language != "Japanese" else float("nan")
            print("[M0] REF({0}): {1}".format(os.path.basename(ref_path), r))
            print("[M0] CER {0:.2%}  WER {1:.2%}".format(cer, wer))
        if a.json:
            os.makedirs(a.json, exist_ok=True)
            out = os.path.join(a.json, os.path.splitext(os.path.basename(wav))[0] + ".m0.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump({"wav": wav, "model": a.model, "device": a.device, "compute": a.compute,
                           "language": a.language, "detected": info.language, "detected_prob": info.language_probability,
                           "load_s": t_load, "transcribe_s": t_tr, "duration_s": info.duration,
                           "text": hyp, "segments": segs}, f, ensure_ascii=False, indent=1)
            print("[M0] json ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
