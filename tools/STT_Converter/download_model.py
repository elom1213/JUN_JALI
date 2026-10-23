# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# [JUN_JALI] STT Converter - 모델 선다운로드 (setup_stt.bat 4단계). 사용: download_model.py <모델 이름 | HF repo> <캐시 폴더>
# faster-whisper 의 크기 이름(large-v3-turbo · large-v3 · distil-large-v3.5 ...) 은 Systran / mobiuslabsgmbh repo 로,
# "kotoba-tech/..." 같은 repo 이름은 그대로 받는다. 캐시는 models\hub (= HF_HOME=models 일 때 hub 폴더와 같다).
# 종료 코드 0 = 받음(이미 있으면 그대로). 메시지는 영어.

import os
import sys
import time


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if len(sys.argv) < 3:
        print("usage: download_model.py <model> <cache_dir>")
        return 2
    name, cache = sys.argv[1], os.path.abspath(sys.argv[2])
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.pop("HF_HUB_OFFLINE", None)
    try:
        from faster_whisper.utils import download_model
    except ImportError as e:
        print("[ERROR] faster-whisper is not installed: {0}".format(e))
        return 1
    t0 = time.perf_counter()
    try:
        path = download_model(name, cache_dir=cache)
    except Exception as e:
        print("[ERROR] download failed for '{0}': {1}".format(name, str(e)[:300]))
        return 1
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    print("[OK] model '{0}' -> {1}  ({2:.2f} GB, {3:.0f} s)".format(name, path, total / 1e9, time.perf_counter() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
