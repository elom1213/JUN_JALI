# -*- coding: utf-8 -*-
# VisemeNet Converter - 코어 일괄 변환 시험 (헤드리스)
# 사용: .venv\Scripts\python tools\VisemeNet_Converter\tests\test_core.py <작업 폴더>
#       (make_bad_wavs.py 를 먼저 같은 폴더로 실행)
import json
import os
import shutil
import sys
import warnings

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from tools.VisemeNet_Converter.app.core import converter   # noqa: E402

warnings.simplefilter("ignore")
results = []


def check(name, cond):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name)


def main(work):
    intro = os.path.join(ROOT, "test_audio", "visemenet_intro.wav")
    coffee = os.path.join(ROOT, "test_audio", "coffee_xxxx.wav")
    out_dir = os.path.join(work, "out")
    shutil.rmtree(out_dir, ignore_errors=True)
    logs = []
    log = lambda lv, m: logs.append((lv, m))   # noqa: E731

    # 1) 나쁜 파일이 섞이면 아무것도 변환하지 않는다
    jobs, problems = converter.preflight([intro, os.path.join(work, "rate_48k.wav"), coffee], out_dir, False, 120)
    check("preflight finds the 48k file", [p[1] for p in problems] == ["E03"])
    check("nothing written after failed preflight", not os.listdir(out_dir))

    # 2) 같은 이름 충돌
    os.makedirs(os.path.join(work, "dup"), exist_ok=True)
    shutil.copy(coffee, os.path.join(work, "dup", "coffee_xxxx.wav"))
    _, problems = converter.preflight([coffee, os.path.join(work, "dup", "coffee_xxxx.wav")], out_dir, False, 120)
    check("same output name -> E11", [p[1] for p in problems] == ["E11"])

    # 3) 정상 변환 + 원본 결과와 같은 값
    engine = converter.Engine(ROOT)
    jobs, problems = converter.preflight([intro, coffee], out_dir, False, 120)
    written, stopped = converter.run_batch(engine, jobs, True, "test", log)
    check("2 files converted", len(written) == 2 and stopped is None)
    first = np.loadtxt(os.path.join(out_dir, "visemenet_intro.txt"))
    again = engine.predict(intro)
    check("deterministic: same wav -> same values", np.abs(np.round(again, 4) - first).max() < 1e-6)
    check("deterministic: 7 dropout constants turned off", engine.patched_dropouts == 7)
    original = converter.Engine(ROOT, deterministic=False)
    a, b = original.predict(coffee), original.predict(coffee)
    check("original mode: differs run to run (published behaviour)", np.abs(a - b).max() > 0.01)
    check("rows = expected_rows()", first.shape[0] == converter.expected_rows(655488) == 1452)
    meta = json.load(open(os.path.join(out_dir, "coffee_xxxx.visemenet.json"), encoding="utf-8"))
    check("json rows/fps/columns", meta["rows"] == 364 and meta["fps"] == 100 and len(meta["columns"]) == 22)
    check("no .tmp left", not [f for f in os.listdir(out_dir) if f.endswith(".tmp")])
    check("truncation note once", sum("truncated" in m for _, m in logs) == 1)

    # 4) 이미 있으면 E09, Overwrite 면 통과
    _, problems = converter.preflight([coffee], out_dir, False, 120)
    check("exists -> E09", [p[1] for p in problems] == ["E09"])
    jobs, problems = converter.preflight([coffee], out_dir, True, 120)
    check("overwrite -> ok", not problems and len(jobs) == 1)

    # 5) 변환 중 오류 -> 남은 파일 처리 안 함
    jobs, _ = converter.preflight([coffee, intro], os.path.join(work, "out2"), True, 120)
    real = engine.predict
    def broken(path, notes=None):
        raise converter.ConvertError("E21", "inference failed: simulated")
    engine.predict = broken
    logs.clear()
    written, stopped = converter.run_batch(engine, jobs, True, "test", log)
    engine.predict = real
    check("stops at first error", written == [] and stopped and "E21" in stopped)
    check("second file not written", not os.path.exists(os.path.join(work, "out2", "visemenet_intro.txt")))

    # 6) Stop 요청
    jobs, _ = converter.preflight([coffee, intro], os.path.join(work, "out3"), True, 120)
    calls = {"n": 0}
    def stop_after_first():
        calls["n"] += 1
        return calls["n"] > 1
    written, stopped = converter.run_batch(engine, jobs, True, "test", log, should_stop=stop_after_first)
    check("stop after first file", len(written) == 1 and "stopped by user" in stopped)

    # 7) 모델 파일 없음 -> E20
    try:
        converter.Engine(work).load()
        check("missing model -> E20", False)
    except converter.ConvertError as e:
        check("missing model -> E20", e.code == "E20")

    print("RESULT", "OK" if all(results) else "{0} FAILED".format(results.count(False)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
