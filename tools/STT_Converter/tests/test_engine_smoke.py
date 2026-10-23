# -*- coding: utf-8 -*-
# STT Converter - 실제 모델 스모크 시험 (CPU int8, models/ 에 large-v3-turbo 가 있어야 한다 - setup_stt.bat 뒤).
# cli.py 를 그대로 불러 test_audio/coffee_xxxx.wav (3.99 s, "This coffee sucks") 를 받아쓴다 -> .lab 에 coffee.
# 개발 PC 의 CUDA 금지(§6) 를 지키기 위해 --device cpu:int8 고정. 사용: .venv_stt\Scripts\python.exe ... <작업 폴더>
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CLI = os.path.join(ROOT, "tools", "STT_Converter", "cli.py")
WAV = os.path.join(ROOT, "test_audio", "coffee_xxxx.wav")
results = []


def check(name, cond):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def run_cli(args):
    env = dict(os.environ, PYTHONUTF8="1", HF_HUB_OFFLINE="1", HF_HOME=os.path.join(ROOT, "models"))
    p = subprocess.run([sys.executable, CLI] + args, capture_output=True, text=True, encoding="utf-8", env=env)
    print("      $ cli.py " + " ".join(args))
    for line in (p.stdout or "").splitlines():
        print("      " + line)
    return p.returncode, p.stdout or ""


def main(work):
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    wav = os.path.join(work, "coffee_xxxx.wav")
    shutil.copy2(WAV, wav)

    rc, out = run_cli([wav, "--language", "English", "--device", "cpu:int8"])
    lab = os.path.join(work, "coffee_xxxx.lab")
    check("cli exit 0", rc == 0)
    check("lab written with 'coffee'", os.path.isfile(lab) and "coffee" in open(lab, encoding="utf-8").read().lower())
    check("stt.json written", os.path.isfile(os.path.join(work, "coffee_xxxx.stt.json")))
    check("VAD auto turned off for the 4 s clip", "VAD off" in out)
    check("DONE line", "[DONE] 1 transcript(s) written" in out)

    rc, out = run_cli([work, "--language", "English", "--device", "cpu:int8", "--quiet"])
    check("second run: existing skipped (W25), exit 0", rc == 0 and "W25" in out and "0 transcript(s) written" in out)

    rc, out = run_cli([os.path.join(work, "nothing_here"), "--language", "English"])
    check("no wav -> exit 1", rc == 1)
    rc, out = run_cli([wav, "--language", "Klingon"])
    check("bad language -> exit 2", rc == 2)

    n_fail = results.count(False)
    print("\n{0} checks, {1} failed".format(len(results), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("TEMP", "."), "stt_test_smoke")))
