# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 일본어 대본 정규화 (docs/0130_stt_converter_plan.md §4)
#
# 숫자 -> 漢数字 (3時 -> 三時, 2026年 -> 二千二十六年, 1,000 -> 千, 3.5 -> 三点五, 50% -> 五十パーセント).
#   읽기(さんじ · にせんにじゅうろくねん)는 MFA 의 Sudachi 분절기가 漢数字 + 조수사를 보고 정한다 - 아라비아 숫자는 못 읽는다.
#   かな 전용 출력(Kana output 옵션)은 pykakasi 가 있을 때만 (to_kana) - 없으면 漢字 혼용 그대로.
# 공백 · 줄바꿈: 여기서는 **남긴다** (사람이 읽기 좋게). 제거는 VisemeNet Converter v01.04 가 MFA 직전에 한다.
# 영문 단어는 사용자 사전(カタカナ)으로 - 남으면 W23.

import re

from . import base

_KANJI_DIGITS = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
_SMALL = ["", "十", "百", "千"]
_BIG = ["", "万", "億", "兆", "京"]

_NUM_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(%|％)?")


def kanji(n):
    """정수 -> 漢数字. 십 · 백 · 천 앞의 一 은 생략(一十 -> 十), 만 · 억 앞은 생략하지 않는다(一万)."""
    if n == 0:
        return "零"
    parts = []
    big = 0
    while n > 0:
        chunk = n % 10000
        n //= 10000
        if chunk:
            s = _chunk(chunk)
            if big and chunk == 1:
                s = "一"
            parts.append(s + _BIG[big])
        big += 1
    return "".join(reversed(parts))


def _chunk(chunk):
    out = []
    for i, unit in ((3, "千"), (2, "百"), (1, "十"), (0, "")):
        d = (chunk // (10 ** i)) % 10
        if not d:
            continue
        out.append((unit if d == 1 and i > 0 else _KANJI_DIGITS[d] + unit))
    return "".join(out)


def read_number(num_text, percent=False):
    parsed = base.split_number(num_text)
    if parsed is None:
        return None, "unparsable number"
    whole, frac = parsed
    if frac is not None:
        return kanji(whole) + "点" + "".join("零" if c == "0" else _KANJI_DIGITS[int(c)] for c in frac), "decimal"
    if percent:
        return kanji(whole) + "パーセント", "percent"
    return kanji(whole), "kanji"


def to_kana(text):
    """漢字 혼용 -> ひらがな (pykakasi). 없으면 None 을 돌려준다 (호출자가 그대로 둔다)."""
    try:
        import pykakasi
    except ImportError:
        return None
    kks = pykakasi.kakasi()
    return "".join(item["hira"] for item in kks.convert(text))


def normalize(text, user_dict=None, kana=False):
    raw = text
    t = base.common_clean(text)
    t, replaced = base.apply_user_dict(t, user_dict)
    unresolved = []

    def _sub(m):
        word, rule = read_number(m.group(1), bool(m.group(2)))
        if word is None:
            unresolved.append((m.group(0), rule))
            return m.group(0)
        replaced.append((m.group(0), word, rule))
        return word

    t = _NUM_RE.sub(_sub, t)
    if kana:
        converted = to_kana(t)
        if converted is None:
            unresolved.append(("(kana output)", "pykakasi is not installed - kanji kept"))
        else:
            replaced.append(("(kanji)", "(kana)", "pykakasi"))
            t = converted
    t = base.finish(t)
    for tok in base.find_digits(t):
        unresolved.append((tok, "digits left"))
    for tok in base.find_latin(t):
        unresolved.append((tok, "latin letters - add to the Japanese user dictionary (katakana)"))
    return base.NormalizeResult(raw, t, replaced, unresolved)
