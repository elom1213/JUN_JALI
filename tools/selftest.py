# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# [JUN_JALI] 추론 환경 자가 검사 - setup_env.bat 의 마지막 단계
#
# 1) 패키지 import  2) 모델 로드  3) test_audio/coffee_xxxx.wav 추론 -> (364, 22) · 유한값.
# 종료 코드 0 = 통과. 메시지는 영어(툴 UI 규칙).

import os
import sys
import warnings

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_WAV = os.path.join(ROOT, "test_audio", "coffee_xxxx.wav")
EXPECTED = (364, 22)


def main():
    try:
        import numpy as np
        import scipy                                    # noqa: F401
        import python_speech_features                   # noqa: F401
        import PySide6                                  # noqa: F401
        import tensorflow as tf
    except Exception as e:                              # DLL load failed 등
        print("[ERROR] import failed: {0}".format(e))
        if "DLL load failed" in str(e):
            print("        Install the Microsoft Visual C++ Redistributable (x64):")
            print("        https://aka.ms/vs/17/release/vc_redist.x64.exe")
        return 1
    print("[OK] packages  tensorflow {0}, numpy {1}".format(tf.__version__, np.__version__))

    sys.path.insert(0, ROOT)
    try:
        from tools.VisemeNet_Converter.app.core import converter
    except Exception as e:
        print("[ERROR] converter import failed: {0}".format(e))
        return 1

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            engine = converter.Engine(ROOT)
            engine.load()
            out = engine.predict(TEST_WAV)
    except Exception as e:
        print("[ERROR] model test failed: {0}".format(e))
        return 1

    if tuple(out.shape) != EXPECTED or not np.isfinite(out).all():
        print("[ERROR] unexpected model output {0} (expected {1})".format(out.shape, EXPECTED))
        return 1
    print("[OK] model     coffee_xxxx.wav -> {0}".format(out.shape))
    return 0


if __name__ == "__main__":
    sys.exit(main())
