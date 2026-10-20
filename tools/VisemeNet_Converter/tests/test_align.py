# -*- coding: utf-8 -*-
# VisemeNet Converter - Correct 모드 통합 시험 (실제 MFA + 모델, setup_mfa.bat 을 먼저 실행)
# 사용: .venv\Scripts\python tools\VisemeNet_Converter\tests\test_align.py <작업 폴더>
#       test_audio\ 의 wav 두 개 + 같은 이름 대본(.txt)을 쓴다.
import json
import os
import shutil
import sys
import warnings

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from tools.VisemeNet_Converter.app.core import aligner, converter, viseme_merge   # noqa: E402

warnings.simplefilter("ignore")
results = []


def check(name, cond):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def main(work):
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    intro = os.path.join(ROOT, "test_audio", "visemenet_intro.wav")
    coffee = os.path.join(ROOT, "test_audio", "coffee_xxxx.wav")
    logs = []
    log = lambda lv, m: logs.append((lv, m))   # noqa: E731

    inst = aligner.find_install(ROOT)
    check("MFA install found (mfa_path.local.txt)", inst is not None)
    if inst is None:
        print("RESULT 1 FAILED - run setup_mfa.bat first")
        return 1

    # 1) 사전 검사
    _, problems = converter.preflight([coffee], "", False, 120, True, converter.AlignConfig("English"), ROOT)
    check("no output folder: result txt would overwrite the transcript -> E34",
          [p[1] for p in problems] == ["E34"])
    _, problems = converter.preflight([coffee], "", False, 120, True, None, ROOT)
    check("E34 also in audio-only mode (transcript is protected)", [p[1] for p in problems] == ["E34"])
    _, problems = converter.preflight([coffee], os.path.join(work, "x"), False, 120, True,
                                      converter.AlignConfig("English", os.path.join(work, "nope")), ROOT)
    check("MFA folder given but wrong -> falls back to mfa_path.local.txt", problems == [])
    lonely = os.path.join(work, "lonely")
    os.makedirs(lonely)
    shutil.copy(coffee, os.path.join(lonely, "no_transcript.wav"))
    out_dir = os.path.join(work, "out")
    cfg = converter.AlignConfig("English")
    jobs, problems = converter.preflight([intro, coffee, os.path.join(lonely, "no_transcript.wav")],
                                         out_dir, False, 120, True, cfg, ROOT)
    check("preflight ok with output folder", problems == [] and len(jobs) == 3)
    check("transcripts found", [bool(j.transcript) for j in jobs] == [True, True, False])

    # 2) 변환 (정렬 한 번 + 보정)
    engine = converter.Engine(ROOT)
    written, stopped = converter.run_batch(engine, jobs, True, "test", log, align_cfg=cfg)
    for lv, m in logs:
        if lv in ("WARN", "ERROR"):
            print("   ", lv, m)
    check("3 files written", len(written) == 3 and stopped is None)
    check("one MFA run for the batch", sum(m.startswith("MFA align:") for _, m in logs) == 1)
    check("file without transcript -> audio only",
          any("no_transcript.wav" in m and "audio only" in m for lv, m in logs if lv == "OK"))

    meta = json.load(open(os.path.join(out_dir, "coffee_xxxx.visemenet.json"), encoding="utf-8"))
    corr = meta.get("correction", {})
    check("json: correction info", corr.get("language") == "English" and corr.get("transcript") == "This coffee sucks"
          and corr.get("phone_segments", 0) > 5)
    ph = json.load(open(os.path.join(out_dir, "coffee_xxxx.phones.json"), encoding="utf-8"))
    words = [w[2] for w in ph["words"] if w[2]]
    check("phones.json: words aligned", words == ["this", "coffee", "sucks"])
    check("no phones.json for audio-only file", not os.path.exists(os.path.join(out_dir, "no_transcript.phones.json")))
    check("no correction in audio-only json",
          "correction" not in json.load(open(os.path.join(out_dir, "no_transcript.visemenet.json"), encoding="utf-8")))

    # 3) 보정 결과: 입술 음소 구간에서 MBP / FV 가 floor 이상, Jaw / Lip 은 원래 값
    raw = engine.predict(intro)
    out = np.loadtxt(os.path.join(out_dir, "visemenet_intro.txt"))
    check("Jaw / Lip unchanged by the correction", np.abs(np.round(raw[:, :2], 4) - out[:, :2]).max() < 1e-6)
    ph = json.load(open(os.path.join(out_dir, "visemenet_intro.phones.json"), encoding="utf-8"))
    pmap = viseme_merge.load_default_map(ROOT, converter.COLUMNS)
    mbp, fv = converter.COLUMNS.index("MBP"), converter.COLUMNS.index("FV")
    lip_ok, lip_n, raw_ok = True, 0, 0
    for t0, t1, label in ph["phones"]:
        parts = pmap.lookup(label) or []
        if len(parts) != 1 or not set(parts[0]) & {"MBP", "FV"}:
            continue
        c = mbp if "MBP" in parts[0] else fv
        r0, r1 = int(round(t0 * 100)), int(round(t1 * 100))
        if r1 > out.shape[0] or r1 <= r0:
            continue
        lip_n += 1
        lip_ok = lip_ok and out[r0:r1, c].min() >= 0.8 * max(parts[0].values()) - 1e-4
        raw_ok += raw[r0:r1, c].min() >= 0.8
    check("lip phones found in the intro ({0})".format(lip_n), lip_n >= 5)
    check("every lip phone reaches the lip floor after correction", lip_ok)
    print("    (before correction {0} of {1} lip phones reached 0.8)".format(raw_ok, lip_n))

    print("RESULT", "OK" if all(results) else "{0} FAILED".format(results.count(False)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
