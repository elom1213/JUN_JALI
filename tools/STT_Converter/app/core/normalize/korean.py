# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 한국어 대본 정규화 (docs/0130_stt_converter_plan.md §4)
#
# 숫자 -> 수사. 뒤에 붙은 단위명사(counter)로 고유어 / 한자어를 고른다.
#   한자어: 일 이 삼 ... (등 · 년 · 월 · 일 · 분 · 초 · 층 · 원 · 호 · 번지 · 학년 · 페이지 · 퍼센트 · 도 · 미터 ...) 과 기본값
#   고유어: 한 두 세 네 다섯 ... (개 · 명 · 시 · 살 · 번 · 마리 · 잔 · 병 · 권 · 장 · 대 · 시간 · 달 · 곳 · 가지 · 사람 ...) - 99 까지만, 100 이상은 한자어
#   소수: 3.5 -> 삼 점 오 · 콤마 1,000 -> 천
# 띄어쓰기는 유지한다 (korean_mfa 는 mecab 으로 다시 분절). 영문 약어는 사용자 사전으로(남으면 W23).
# 수사와 단위명사 사이 띄어쓰기: 숫자 표기 그대로 붙여 쓴다 (1등 -> 일등, 3개 -> 세개) - MFA 사전은 "세개" 보다
# "세 개" 를 더 잘 알지만 mecab 분절이 둘 다 처리한다. 표준 띄어쓰기(세 개)를 쓰려면 SPACE_COUNTER = True.

import re

from . import base

SPACE_COUNTER = False

_SINO_DIGITS = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
_SINO_SMALL_UNITS = ["", "십", "백", "천"]
_SINO_BIG_UNITS = ["", "만", "억", "조", "경"]

_NATIVE_ONES = ["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉"]
_NATIVE_TENS = ["", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"]
# 단독(단위 없이) 쓰는 고유어 꼴 - 1 ~ 4 와 20 이 다르다
_NATIVE_ALONE = {1: "하나", 2: "둘", 3: "셋", 4: "넷", 20: "스물"}

# 고유어 수사를 쓰는 단위명사 (긴 것부터 맞춘다). '시' 는 시각(3시 = 세 시), '시간' 도 고유어.
NATIVE_COUNTERS = (
    "시간", "사람", "가지", "그루", "켤레", "송이", "마리", "번째",
    "개", "명", "시", "살", "번", "잔", "병", "권", "장", "대", "달", "곳", "척", "채", "벌", "통", "줄", "칸",
    "컵", "판", "쌍", "알", "톨", "포기", "다발", "묶음", "차례", "군데", "방", "발", "타", "갑",
)
# 한자어 수사를 쓰는 단위명사 (없는 단위는 전부 한자어 - 기본값)
SINO_COUNTERS = (
    "퍼센트", "페이지", "킬로그램", "킬로미터", "센티미터", "밀리미터", "미터", "킬로", "그램", "리터", "학년",
    "번지", "년", "월", "일", "분", "초", "등", "층", "원", "호", "도", "회", "차", "점", "세", "주", "배",
    "인분", "인치", "달러", "엔", "위", "급", "단", "조", "항", "권", "부", "편", "탄", "기", "대대", "중대",
)
# 숫자 뒤에 올 수 있는 단위를 긴 것부터
_COUNTER_RE = "|".join(sorted(set(NATIVE_COUNTERS + SINO_COUNTERS), key=len, reverse=True))
_NUM_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(%|" + _COUNTER_RE + r")?")


def sino(n):
    """정수 -> 한자어 수사. 0 -> 영. 1만 이상에서 만 단위 앞의 '일' 은 생략한다(만, 억) - 단 '일만' 도 맞지만 구어는 '만'."""
    if n == 0:
        return "영"
    if n < 0:
        return "마이너스 " + sino(-n)
    parts = []
    big = 0
    while n > 0:
        chunk = n % 10000
        n //= 10000
        if chunk:
            s = _sino_chunk(chunk, first_big=(n == 0 and big > 0))
            parts.append(s + _SINO_BIG_UNITS[big])
        big += 1
    return "".join(reversed(parts))


def _sino_chunk(chunk, first_big=False):
    """0 < chunk < 10000 -> 한자어. 십 · 백 · 천 앞의 1 은 생략(일십 -> 십). 만 단위 앞의 1 도 생략(일만 -> 만)."""
    out = []
    for i, unit in ((3, "천"), (2, "백"), (1, "십"), (0, "")):
        d = (chunk // (10 ** i)) % 10
        if not d:
            continue
        if d == 1 and i > 0:
            out.append(unit)
        elif d == 1 and i == 0 and first_big and chunk == 1:
            out.append("")          # 만 · 억 앞의 1 -> 생략 ("만", "억")
        else:
            out.append(_SINO_DIGITS[d] + unit)
    return "".join(out)


def native(n, with_counter=True):
    """1 ~ 99 -> 고유어 수사. with_counter=True 면 관형형(한 · 두 · 세 · 네 · 스무), False 면 단독형(하나 · 둘 · 셋 · 넷 · 스물).
    범위 밖이면 None."""
    if not 1 <= n <= 99:
        return None
    tens, ones = divmod(n, 10)
    if ones == 0 and tens == 2:
        return "스무" if with_counter else "스물"
    if not with_counter and n in _NATIVE_ALONE:
        return _NATIVE_ALONE[n]
    one = _NATIVE_ONES[ones]
    if not with_counter and ones in (1, 2, 3, 4) and tens:
        one = {1: "하나", 2: "둘", 3: "셋", 4: "넷"}[ones]
    return _NATIVE_TENS[tens] + one


def read_number(num_text, counter=None):
    """숫자 문자열 + 단위 -> 읽기. Returns (읽기, 규칙 이름) 또는 (None, 이유)."""
    parsed = base.split_number(num_text)
    if parsed is None:
        return None, "unparsable number"
    whole, frac = parsed
    if frac is not None:
        word = sino(whole) + " 점 " + " ".join(_SINO_DIGITS[int(c)] if c != "0" else "영" for c in frac)
        if counter == "%":
            return word + " 퍼센트", "decimal percent"
        return (word + " " + counter if counter else word), "decimal"
    if counter == "%":
        return sino(whole) + "퍼센트", "percent"
    if counter in NATIVE_COUNTERS:
        word = native(whole, with_counter=True)
        if word is not None:
            return word + (" " if SPACE_COUNTER else "") + counter, "native counter"
        return sino(whole) + (" " if SPACE_COUNTER else "") + counter, "sino (native range exceeded)"
    if counter:
        return sino(whole) + (" " if SPACE_COUNTER else "") + counter, "sino counter"
    return sino(whole), "sino"


def normalize(text, user_dict=None):
    raw = text
    t = base.common_clean(text)
    t, replaced = base.apply_user_dict(t, user_dict)
    unresolved = []

    def _sub(m):
        word, rule = read_number(m.group(1), m.group(2))
        if word is None:
            unresolved.append((m.group(0), rule))
            return m.group(0)
        replaced.append((m.group(0), word, rule))
        return word

    t = _NUM_RE.sub(_sub, t)
    t = base.finish(t)
    for tok in base.find_digits(t):
        unresolved.append((tok, "digits left"))
    for tok in base.find_latin(t):
        unresolved.append((tok, "latin letters - add to the Korean user dictionary"))
    return base.NormalizeResult(raw, t, replaced, unresolved)
