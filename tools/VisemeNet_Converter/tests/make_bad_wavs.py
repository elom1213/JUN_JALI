# -*- coding: utf-8 -*-
# VisemeNet Converter - 검사 규칙 시험용 wav 만들기 + check_wav / preflight 결과 확인
# 사용: .venv\Scripts\python tools\VisemeNet_Converter\tests\make_bad_wavs.py <출력 폴더>
import os
import sys

import numpy as np
import scipy.io.wavfile as wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from tools.VisemeNet_Converter.app.core.wav_check import check_wav, WavError   # noqa: E402

SR = 44100


def tone(sec, sr=SR, amp=8000):
    t = np.arange(int(sec * sr)) / float(sr)
    # 큰 amp 는 int16 로 바로 바꾸면 넘쳐서 감긴다 - 먼저 잘라서 클리핑을 만든다.
    return np.clip(np.sin(2 * np.pi * 220 * t) * amp, -32768, 32767).astype(np.int16)


def make(folder):
    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(folder, "한글 폴더"), exist_ok=True)
    cases = {
        "ok_mono.wav": (SR, tone(2.0), None),
        "ok_stereo.wav": (SR, np.stack([tone(2.0), tone(2.0)], axis=1), "W01"),
        "rate_48k.wav": (48000, tone(2.0, 48000), "E03"),
        "float32.wav": (SR, tone(2.0).astype(np.float32) / 32768.0, "E04"),
        "int32_24bit.wav": (SR, tone(2.0).astype(np.int32) << 16, "E04"),
        "three_ch.wav": (SR, np.stack([tone(2.0)] * 3, axis=1), "E05"),
        "short.wav": (SR, tone(0.2), "E06"),
        "silent.wav": (SR, np.zeros(SR * 2, np.int16), "E08"),
        "clipping.wav": (SR, tone(2.0, amp=60000), "W02"),
        os.path.join("한글 폴더", "한글_ok.wav"): (SR, tone(2.0), None),
    }
    for name, (sr, data, _) in cases.items():
        wavfile.write(os.path.join(folder, name), sr, data)
    with open(os.path.join(folder, "broken.wav"), "wb") as f:
        f.write(b"RIFF\x00\x00\x00\x00WAVEjunkjunkjunk")
    cases["broken.wav"] = (None, None, "E02")
    cases["missing.wav"] = (None, None, "E01")
    return cases


def main(folder):
    cases = make(folder)
    bad = 0
    for name, (_, _, want) in sorted(cases.items()):
        path = os.path.join(folder, name)
        try:
            info = check_wav(path, max_seconds=120)
            got = info.warnings[0][0] if info.warnings else None
            msg = info.summary()
        except WavError as e:
            got, msg = e.code, e.message
        ok = got == want
        bad += not ok
        print("{0}  {1:28s} want {2:5s} got {3:5s} {4}".format("PASS" if ok else "FAIL", name, str(want), str(got), msg))
    try:
        check_wav(os.path.join(folder, "ok_mono.wav"), max_seconds=1.0)
        print("FAIL  max length")
        bad += 1
    except WavError as e:
        print("{0}  max length -> {1} {2}".format("PASS" if e.code == "E07" else "FAIL", e.code, e.message))
        bad += e.code != "E07"
    print("RESULT", "OK" if not bad else "{0} FAILED".format(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
