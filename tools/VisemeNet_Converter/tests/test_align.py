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

# 합성 TextGrid (MFA 없이 W12 검사) - words: (무음) high <unk> f / phones: sil h aj(2.27 s) spn f
_FAKE_TG = '''File type = "ooTextFile"
Object class = "TextGrid"

xmin = 0
xmax = 4.1
tiers? <exists>
size = 2
item []:
    item [1]:
        class = "IntervalTier"
        name = "words"
        xmin = 0
        xmax = 4.1
        intervals: size = 4
        intervals [1]:
            xmin = 0
            xmax = 1.0
            text = ""
        intervals [2]:
            xmin = 1.0
            xmax = 3.3
            text = "high"
        intervals [3]:
            xmin = 3.3
            xmax = 4.0
            text = "<unk>"
        intervals [4]:
            xmin = 4.0
            xmax = 4.1
            text = "f"
    item [2]:
        class = "IntervalTier"
        name = "phones"
        xmin = 0
        xmax = 4.1
        intervals: size = 5
        intervals [1]:
            xmin = 0
            xmax = 1.0
            text = ""
        intervals [2]:
            xmin = 1.0
            xmax = 1.03
            text = "h"
        intervals [3]:
            xmin = 1.03
            xmax = 3.3
            text = "aj"
        intervals [4]:
            xmin = 3.3
            xmax = 4.0
            text = "spn"
        intervals [5]:
            xmin = 4.0
            xmax = 4.1
            text = "f"
'''


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

    # 0) 언어별 대본 정규화 (MFA 없이) - 일본어는 공백 · 줄바꿈 제거, 영어 · 한국어는 그대로
    ja = aligner.normalize_transcript(" ".join("パエトーン様、あなたが\n思い浮かべる そんな存在に。".split()), "Japanese")
    check("Japanese transcript: whitespace removed before MFA", ja == "パエトーン様、あなたが思い浮かべるそんな存在に。")
    check("English / Korean transcripts unchanged",
          aligner.normalize_transcript("This coffee sucks", "English") == "This coffee sucks"
          and aligner.normalize_transcript("파에톤 님이 어디로", "Korean") == "파에톤 님이 어디로")

    # 0b) 긴 음소 · W12 (MFA 없이) - 무음 1.0 s 와 spn 0.7 s 는 빼고, 2.27 s 의 aj 만 잡는다
    tg = os.path.join(work, "fake.TextGrid")
    with open(tg, "w", encoding="utf-8") as f:
        f.write(_FAKE_TG)
    fake = aligner.AlignResult("fake.wav", tg)
    check("AlignResult: parsed, wide_beam defaults to False", fake.ok and fake.wide_beam is False)
    check("long_phones: speech phones >= 0.5 s only (silence / spn skipped)",
          [(round(s, 2), round(e, 2), l) for s, e, l in fake.long_phones()] == [(1.03, 3.3, "aj")])
    check("short threshold catches h / f too", len(fake.long_phones(0.02)) == 3)
    msg = converter.w12_text(fake)
    check("W12 text: time range + phone, no wide-beam part",
          "phone(s) longer than 0.5 s at 1.0-3.3 s (aj)" in msg and "wide beam" not in msg)
    fake.wide_beam = True
    check("W12 text: wide beam first, then long phones",
          converter.w12_text(fake).startswith("aligned only with a wide beam (100 / 400); phone(s) longer"))

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
    check("matching transcripts: no wide-beam retry, no W12",
          not any(m.startswith("MFA found no alignment") for _, m in logs)
          and not any(" W12 " in m for lv, m in logs if lv == "WARN"))

    meta = json.load(open(os.path.join(out_dir, "coffee_xxxx.visemenet.json"), encoding="utf-8"))
    corr = meta.get("correction", {})
    check("json: correction info", corr.get("language") == "English" and corr.get("transcript") == "This coffee sucks"
          and corr.get("phone_segments", 0) > 5)
    check("json: wide_beam False, long_phones empty", corr.get("wide_beam") is False and corr.get("long_phones") == [])
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
