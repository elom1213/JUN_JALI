# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# [JUN_JALI] STT Converter 환경 자가 검사 - setup_stt.bat 의 마지막 단계 (docs/0130_stt_converter_plan.md T1)
#
# 1) 패키지 import  2) 장치 요약(강제 CPU 면 CUDA 를 건드리지 않는다)  3) models/ 의 large-v3-turbo 를 CPU int8 로 올려
#    test_audio/coffee_xxxx.wav (3.99 s, "This coffee sucks") 를 받아쓴다 -> 'coffee' 가 들어 있어야 통과.
# 자가 검사는 **항상 CPU** 로 돈다 - 설치 단계에서 GPU 드라이버 문제로 멈추지 않게, 그리고 개발 PC 의 CUDA 강제 종료
# 문제(§11) 를 피하려고. GPU 는 변환기를 띄웠을 때 Device 콤보로 고른다.
# 종료 코드 0 = 통과. 메시지는 영어(툴 UI 규칙). 옵션: --wav <파일> --language <English|Korean|Japanese> --model <이름>

import argparse
import os
import sys
import time

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))
TEST_WAV = os.path.join(REPO_ROOT, "test_audio", "coffee_xxxx.wav")
EXPECT_WORD = "coffee"


def _utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main():
    _utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=TEST_WAV)
    ap.add_argument("--language", default="English")
    ap.add_argument("--model", default="large-v3-turbo")
    a = ap.parse_args()

    try:
        import ctranslate2
        import faster_whisper
        import PySide6                                   # noqa: F401
        import num2words                                 # noqa: F401
        import soundfile                                 # noqa: F401
    except Exception as e:                               # DLL load failed 등
        print("[ERROR] import failed: {0}".format(e))
        if "DLL load failed" in str(e):
            print("        Install the Microsoft Visual C++ Redistributable (x64):")
            print("        https://aka.ms/vs/17/release/vc_redist.x64.exe")
        return 1
    print("[OK] packages  faster-whisper {0}, ctranslate2 {1}, python {2}.{3}".format(
        faster_whisper.__version__, ctranslate2.__version__, *sys.version_info[:2]))

    sys.path.insert(0, REPO_ROOT)
    try:
        from tools.STT_Converter.app.core import device, settings
        from tools.STT_Converter.app.core.engines import FasterWhisperEngine, TranscribeOptions
        from tools.STT_Converter.app.core.normalize import normalize
    except Exception as e:
        print("[ERROR] converter import failed: {0}".format(e))
        return 1

    info = device.detect()
    print("[OK] device    {0}".format(info.summary()))

    cache = os.path.join(REPO_ROOT, "models")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")        # 설치 단계에서 받았어야 한다 - 없으면 E41 로 알린다
    engine = FasterWhisperEngine(a.model, "cpu", "int8", cache)
    try:
        t0 = time.perf_counter()
        engine.load()
        print("[OK] model     {0} loaded on cpu/int8 in {1:.1f} s".format(a.model, time.perf_counter() - t0))
        if not os.path.isfile(a.wav):
            print("[ERROR] test wav not found: {0}".format(a.wav))
            return 1
        t1 = time.perf_counter()
        result = engine.transcribe(a.wav, a.language, TranscribeOptions(vad=False))
    except Exception as e:
        print("[ERROR] model test failed: {0}".format(e))
        if "E41" in str(e):
            print("        The model is not in models\\ - run setup_stt.bat again with an internet connection.")
        return 1
    text = normalize(result.text, a.language).text
    print("[OK] transcribe {0} ({1:.1f} s audio) -> \"{2}\"  in {3:.1f} s".format(
        os.path.basename(a.wav), result.duration or 0.0, text, time.perf_counter() - t1))
    if a.wav == TEST_WAV and EXPECT_WORD not in text.lower():
        print("[ERROR] unexpected transcript (expected the word '{0}')".format(EXPECT_WORD))
        return 1
    settings.load()                                      # data/ 폴더 · 설정 파일이 읽히는지
    return 0


if __name__ == "__main__":
    sys.exit(main())
