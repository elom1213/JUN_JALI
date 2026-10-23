# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 영어 대본 정규화 (docs/0130_stt_converter_plan.md §4, 0080 §③ "읽는 대로")
#
# 숫자 -> 단어 (num2words). 연도(1100 ~ 2099, 4자리 단독) 는 twenty eighteen 처럼 두 자리씩, 2000 ~ 2009 는 two thousand (and) N.
# 서수 1st 2nd 3rd 4th -> first second third fourth. % -> percent. $5 -> five dollars (£ € 도). 시각 3:30 -> three thirty.
# 소수 3.5 -> three point five. 콤마 1,000 -> one thousand. 약어 · 고유명사는 사용자 사전(남은 로마자 약어는 W23 이 아니다 -
# 영어 사전은 G2P 폴백이 있다 - 다만 전부 대문자인 2 ~ 5 글자 토큰(UE · KWI)은 W23 으로 알려 준다).

import re

from . import base

try:
    from num2words import num2words
except ImportError:           # 테스트 환경에 없을 때 - 아주 작은 폴백
    num2words = None

_ORDINAL_RE = re.compile(r"\b(\d+)(st|nd|rd|th)\b", re.IGNORECASE)
_TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_CURRENCY_RE = re.compile(r"([$£€])\s?(\d[\d,]*(?:\.\d+)?)")
_PERCENT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s?%")
_NUMBER_RE = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?![\w])")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,5}\b")

_CURRENCY_WORDS = {"$": ("dollar", "cent"), "£": ("pound", "penny"), "€": ("euro", "cent")}


def _n2w(n, to="cardinal"):
    if num2words is not None:
        # num2words 는 영국식 "two thousand and eighteen" - 미국식으로 and 를 뺀다 (MFA 사전엔 둘 다 있다)
        return num2words(n, to=to, lang="en").replace("-", " ").replace(",", "").replace(" and ", " ")
    # 폴백 (num2words 가 없을 때 테스트가 통째로 죽지 않게) - 천 · 백만 · 십억까지 재귀
    ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
            "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    if to == "ordinal":
        special = {1: "first", 2: "second", 3: "third", 5: "fifth", 8: "eighth", 9: "ninth", 12: "twelfth"}
        if n in special:
            return special[n]
        w = _n2w(n)
        return w[:-1] + "ieth" if w.endswith("y") else w + "th"
    if n < 20:
        return ones[n]
    if n < 100:
        return tens[n // 10] + ("" if n % 10 == 0 else " " + ones[n % 10])
    if n < 1000:
        return ones[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + _n2w(n % 100))
    for value, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= value:
            head, rest = divmod(n, value)
            return _n2w(head) + " " + name + ("" if rest == 0 else " " + _n2w(rest))
    return str(n)


def read_year(n):
    """1100 ~ 2099 -> 두 자리씩. 2000 -> two thousand, 2005 -> two thousand five, 2018 -> twenty eighteen."""
    if 2000 <= n <= 2009:
        return "two thousand" + ("" if n == 2000 else " " + _n2w(n - 2000))
    hi, lo = divmod(n, 100)
    if lo == 0:
        return _n2w(hi) + " hundred"
    if lo < 10:
        return _n2w(hi) + " oh " + _n2w(lo)
    return _n2w(hi) + " " + _n2w(lo)


def read_number(num_text, year_ok=True):
    parsed = base.split_number(num_text)
    if parsed is None:
        return None, "unparsable number"
    whole, frac = parsed
    if frac is not None:
        return _n2w(whole) + " point " + " ".join(_n2w(int(c)) for c in frac), "decimal"
    if year_ok and 1100 <= whole <= 2099 and "," not in num_text and len(num_text) == 4:
        return read_year(whole), "year"
    return _n2w(whole), "cardinal"


def normalize(text, user_dict=None):
    raw = text
    t = base.common_clean(text)
    t, replaced = base.apply_user_dict(t, user_dict)
    unresolved = []

    def rec(m, word, rule):
        replaced.append((m.group(0), word, rule))
        return word

    t = _TIME_RE.sub(lambda m: rec(m, _n2w(int(m.group(1))) + (" o'clock" if m.group(2) == "00" else
                                       (" oh " if m.group(2)[0] == "0" else " ") + _n2w(int(m.group(2)))), "time"), t)
    t = _ORDINAL_RE.sub(lambda m: rec(m, _n2w(int(m.group(1)), "ordinal"), "ordinal"), t)
    t = _PERCENT_RE.sub(lambda m: rec(m, read_number(m.group(1), year_ok=False)[0] + " percent", "percent"), t)

    def cur(m):
        unit, cent = _CURRENCY_WORDS[m.group(1)]
        parsed = base.split_number(m.group(2))
        if parsed is None:
            unresolved.append((m.group(0), "unparsable currency"))
            return m.group(0)
        whole, frac = parsed
        word = _n2w(whole) + " " + (unit if whole == 1 else unit + "s")
        if frac:
            c = int(frac[:2].ljust(2, "0"))
            word += " " + _n2w(c) + " " + (cent if c == 1 else ("pence" if cent == "penny" else cent + "s"))
        return rec(m, word, "currency")

    t = _CURRENCY_RE.sub(cur, t)

    def num(m):
        word, rule = read_number(m.group(1))
        if word is None:
            unresolved.append((m.group(0), rule))
            return m.group(0)
        return rec(m, word, rule)

    t = _NUMBER_RE.sub(num, t)
    t = base.finish(t)
    for tok in base.find_digits(t):
        unresolved.append((tok, "digits left"))
    for tok in _ACRONYM_RE.findall(t):
        if tok not in ("I", "A", "OK"):
            unresolved.append((tok, "acronym - spell it (U E) or add to the English user dictionary"))
    return base.NormalizeResult(raw, t, replaced, unresolved)
