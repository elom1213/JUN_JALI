# -*- coding: utf-8 -*-
# VisemeNet Converter - 대본 보정(안 B) · TextGrid · 대본 찾기 시험 (MFA · TensorFlow 없이, 합성 데이터)
# 사용: .venv\Scripts\python tools\VisemeNet_Converter\tests\test_merge.py <작업 폴더>
import os
import shutil
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from tools.VisemeNet_Converter.app.core import aligner, viseme_merge                # noqa: E402
from tools.VisemeNet_Converter.app.core.converter import COLUMNS                    # noqa: E402

results = []


def check(name, cond):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def col(name):
    return COLUMNS.index(name)


LONG_TG = '''File type = "ooTextFile"
Object class = "TextGrid"

xmin = 0
xmax = 1.0
tiers? <exists>
size = 2
item []:
    item [1]:
        class = "IntervalTier"
        name = "words"
        xmin = 0
        xmax = 1.0
        intervals: size = 2
        intervals [1]:
            xmin = 0
            xmax = 0.2
            text = ""
        intervals [2]:
            xmin = 0.2
            xmax = 1.0
            text = "map"
    item [2]:
        class = "IntervalTier"
        name = "phones"
        xmin = 0
        xmax = 1.0
        intervals: size = 4
        intervals [1]:
            xmin = 0
            xmax = 0.2
            text = ""
        intervals [2]:
            xmin = 0.2
            xmax = 0.3
            text = "m"
        intervals [3]:
            xmin = 0.3
            xmax = 0.6
            text = "æ"
        intervals [4]:
            xmin = 0.6
            xmax = 1.0
            text = "pʰ"
'''

SHORT_TG = '''File type = "ooTextFile"
Object class = "TextGrid"

0
1.0
<exists>
1
"IntervalTier"
"phones"
0
1.0
2
0
0.5
"s"
0.5
1.0
"ɯ"
'''


def main(work):
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    pmap = viseme_merge.load_default_map(ROOT, COLUMNS)

    # 1) 매핑표
    check("map: p -> MBP", pmap.lookup("p") == [{"MBP": 1.0}])
    check("map: aspirated pʰ -> MBP (modifier stripped)", pmap.lookup("pʰ") == [{"MBP": 1.0}])
    check("map: Korean tense p͈ -> MBP", pmap.lookup("p͈") == [{"MBP": 1.0}])
    check("map: tɕʰ -> ShChZh", pmap.lookup("tɕʰ") == [{"ShChZh": 1.0}])
    check("map: diphthong aj -> Ah then JY", pmap.lookup("aj") == [{"Ah": 1.0}, {"JY": 1.0}])
    check("map: ɯ -> Ih + Eu (unrounded)", pmap.lookup("ɯ") == [{"Ih": 0.5, "Eu": 0.5}])
    check("map: h is neutral", pmap.lookup("h") == [])
    check("map: unknown symbol -> None", pmap.lookup("ʘ") is None)
    try:
        viseme_merge.PhoneMap({"phones": {"p": {"Nope": 1}}}, COLUMNS)
        check("map: bad viseme name rejected", False)
    except ValueError:
        check("map: bad viseme name rejected", True)

    # 2) TextGrid
    tg_long = os.path.join(work, "long.TextGrid")
    with open(tg_long, "w", encoding="utf-8") as f:
        f.write(LONG_TG)
    tiers = aligner.parse_textgrid(tg_long)
    check("textgrid long: tiers", set(tiers) == {"words", "phones"})
    check("textgrid long: phones", [p[2] for p in tiers["phones"]] == ["", "m", "æ", "pʰ"])
    check("textgrid long: times", tiers["phones"][1][:2] == (0.2, 0.3))
    tg_short = os.path.join(work, "short.TextGrid")
    with open(tg_short, "w", encoding="utf-8") as f:
        f.write(SHORT_TG)
    check("textgrid short", aligner.parse_textgrid(tg_short) == {"phones": [(0.0, 0.5, "s"), (0.5, 1.0, "ɯ")]})

    # 3) 보정 - 합성 VisemeNet 출력 (1초 = 100행, 모든 비짐 0.3, Jaw 0.5, Lip 0.4)
    values = np.full((100, 22), 0.3)
    values[:, 0], values[:, 1] = 0.5, 0.4
    phones = tiers["phones"]
    p = viseme_merge.Params()
    out, rep = viseme_merge.correct(values, phones, pmap, p)
    check("shape kept", out.shape == values.shape)
    check("Jaw / Lip untouched", np.array_equal(out[:, :2], values[:, :2]))
    check("m segment: MBP >= lip floor 0.8", out[20:30, col("MBP")].min() >= 0.8 - 1e-9)
    check("p segment: MBP >= lip floor 0.8", out[60:100, col("MBP")].min() >= 0.8 - 1e-9)
    check("æ segment: Aa >= floor 0.6", out[33:57, col("Aa")].min() >= 0.6 - 1e-9)
    check("æ segment: other visemes attenuated", abs(out[45, col("Ee")] - 0.3 * 0.5) < 1e-9)
    check("silence: visemes x0.2", abs(out[5, col("Aa")] - 0.3 * 0.2) < 1e-9)
    check("ramp: MBP rises before the m segment", 0.3 * 0.2 < out[18, col("MBP")] < 0.8)
    check("ramp: no step at silence -> m boundary", np.abs(np.diff(out[:, col("Ee")])).max() < 0.1)
    check("report: segments", rep["segments"] == 3 and rep["unmapped"] == [])

    # 값이 이미 floor 보다 크면 그대로 (최솟값만 보장)
    loud = values.copy()
    loud[:, col("MBP")] = 0.95
    out2, _ = viseme_merge.correct(loud, phones, pmap, p)
    check("floor keeps larger values", abs(out2[25, col("MBP")] - 0.95) < 1e-9)

    # spn · 중립 · 표에 없는 음소 -> 그대로 / 보고
    out3, rep3 = viseme_merge.correct(values, [(0.0, 0.5, "spn"), (0.5, 0.7, "h"), (0.7, 1.0, "ʘ")], pmap, p)
    check("spn / neutral / unknown keep VisemeNet values", np.allclose(out3, values))
    check("report: unknown phone listed", rep3["unmapped"] == ["ʘ"])

    # 모델 출력보다 긴 음소 (끝 0.32초) -> 무시, 개수만 보고
    out4, rep4 = viseme_merge.correct(values[:50], phones, pmap, p)
    check("phones beyond the model rows are ignored", out4.shape == (50, 22) and rep4["beyond_rows"] >= 1)

    # 일본어 ん: 뒤가 m 이면 MBP, 뒤가 없으면 GK
    out5, _ = viseme_merge.correct(values, [(0.0, 0.3, "ɴ"), (0.3, 0.6, "m")], pmap, p)
    check("ɴ before m -> MBP", out5[15, col("MBP")] >= 0.8 - 1e-9)
    out6, _ = viseme_merge.correct(values, [(0.0, 0.3, "ɴ")], pmap, p)
    check("ɴ at the end -> GK", out6[15, col("GK")] >= 0.6 - 1e-9)
    out7, _ = viseme_merge.correct(values, [(0.0, 0.3, "ɴː"), (0.3, 0.6, "b")], pmap, p)
    check("long ɴː before b -> MBP", out7[15, col("MBP")] >= 0.8 - 1e-9)

    # 실제 MFA 사전(english / korean / japanese _mfa)의 음소가 전부 표에 있다 (setup_mfa.bat 뒤에만)
    dict_dir = os.path.join(ROOT, ".mfa", "models", "pretrained_models", "dictionary")
    for lang in ("english_mfa", "korean_mfa", "japanese_mfa"):
        path = os.path.join(dict_dir, lang + ".dict")
        if not os.path.isfile(path):
            print("SKIP {0} phone coverage (no MFA dictionary at {1})".format(lang, dict_dir))
            continue
        phones_used = set()
        with open(path, encoding="utf-8") as f:
            for line in f:
                cells = line.rstrip("\n").split("\t")
                if len(cells) > 1:
                    phones_used.update(cells[-1].split())
        missing = sorted(ph for ph in phones_used if ph not in pmap.keep and not pmap.is_assimilating(ph)
                         and pmap.lookup(ph) is None)
        check("{0}: all {1} phones mapped {2}".format(lang, len(phones_used), missing or ""), not missing)

    # 4) 대본 찾기 - .lab 우선, VisemeNet 결과 txt 는 대본이 아니다
    wav = os.path.join(work, "a.wav")
    open(wav, "wb").close()
    with open(os.path.join(work, "a.txt"), "w", encoding="utf-8") as f:
        f.write("0.1000 0.2000 0.3000\n")
    check("viseme txt is not a transcript", aligner.transcript_path(wav) is None)
    with open(os.path.join(work, "a.txt"), "w", encoding="utf-8") as f:
        f.write("Hello there\n")
    check("txt transcript found", aligner.transcript_path(wav).endswith("a.txt"))
    with open(os.path.join(work, "a.lab"), "w", encoding="utf-8") as f:
        f.write("Hello lab\n")
    check(".lab preferred over .txt", aligner.transcript_path(wav).endswith("a.lab"))
    check("transcript text normalised", aligner.read_transcript(os.path.join(work, "a.lab")) == "Hello lab")
    with open(os.path.join(work, "empty.lab"), "w", encoding="utf-8") as f:
        f.write("  \n")
    try:
        aligner.read_transcript(os.path.join(work, "empty.lab"))
        check("empty transcript -> E32", False)
    except aligner.AlignError as e:
        check("empty transcript -> E32", e.code == "E32")
    with open(os.path.join(work, "cp949.lab"), "wb") as f:
        f.write("안녕".encode("cp949"))
    try:
        aligner.read_transcript(os.path.join(work, "cp949.lab"))
        check("non-UTF-8 transcript -> E32", False)
    except aligner.AlignError as e:
        check("non-UTF-8 transcript -> E32", e.code == "E32")

    print("RESULT", "OK" if all(results) else "{0} FAILED".format(results.count(False)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
