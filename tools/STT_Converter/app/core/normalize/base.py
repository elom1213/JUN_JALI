# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 대본 정규화 공통부 (docs/0130_stt_converter_plan.md §4)
#
# STT 결과(자막 표기: 숫자 · 기호 · 영문 약어)를 MFA 가 사전으로 읽을 수 있는 "발음대로 쓴 단어" 로 바꾼다.
# 정규화는 정렬용이다 - 원문은 .stt.json 의 raw_text 에 보존되고 여기 결과만 .lab 에 쓴다.
#
# 공통 규칙: NFKC(전각 -> 반각) · 따옴표 · 괄호 · 말줄임표 · 대시 제거 · 줄바꿈 -> 공백 · 연속 공백 1개.
#            문장부호 . , ? ! 는 남긴다 (MFA 가 무시한다, 사람이 읽기 좋다).
# 언어별 규칙(숫자 읽기 · 사용자 사전 · 남은 토큰 검사)은 english.py · korean.py · japanese.py.
# 사용자 사전: {"KWI": "케이더블유아이"} 꼴 - 토큰 단위로 치환(긴 키부터), 대소문자 구분 없음(영문).

import re
import unicodedata


class NormalizeResult(object):
    """정규화 결과. text = .lab 에 쓸 문장, raw = 입력 원문,
    replaced = [(원 토큰, 바뀐 토큰, 규칙)], unresolved = [(토큰, 이유)] (W23 로 보고)."""

    def __init__(self, raw, text, replaced=None, unresolved=None):
        self.raw = raw
        self.text = text
        self.replaced = list(replaced or [])
        self.unresolved = list(unresolved or [])

    @property
    def changed(self):
        return self.raw != self.text


# 지우는 기호 (전각은 NFKC 가 먼저 반각으로 바꾼다 - 「」『』【】 등 CJK 괄호는 NFKC 가 안 바꾸므로 직접 적는다)
_STRIP_CHARS = "\"“”「」『』【】〈〉《》()[]{}…・‥"
# 아포스트로피: 단어 안(I'll · don't · 's)은 남기고, 따옴표로 쓰인 것(앞뒤가 글자가 아님)만 지운다
_APOSTROPHE_QUOTE = re.compile(r"(?<!\w)'|'(?!\w)")
_DASHES = re.compile(r"[\-‐-―−~〜～]+")
_ELLIPSIS = re.compile(r"\.{2,}")
_SPACES = re.compile(r"[ \t\r\n　]+")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([.,?!、。，．？！])")


def common_clean(text):
    """언어 공통 전처리. 숫자 처리 전에 부른다 (NFKC 로 전각 숫자가 반각이 된 뒤 숫자 규칙이 돈다)."""
    t = unicodedata.normalize("NFKC", text or "")
    t = _ELLIPSIS.sub(" ", t)
    for ch in _STRIP_CHARS:
        t = t.replace(ch, " ")
    t = t.replace("‘", "'").replace("’", "'")
    t = _APOSTROPHE_QUOTE.sub(" ", t)
    t = _DASHES.sub(" ", t)
    t = _SPACES.sub(" ", t)
    t = _SPACE_BEFORE_PUNCT.sub(r"\1", t)
    return t.strip()


def apply_user_dict(text, user_dict, case_insensitive=True):
    """사용자 사전 치환 - 긴 키부터, 토큰 경계(공백 · 문장부호 · 문자열 끝) 기준. Returns (text, replaced)."""
    replaced = []
    if not user_dict:
        return text, replaced
    keys = sorted((k for k in user_dict if k and k.strip()), key=len, reverse=True)
    flags = re.IGNORECASE if case_insensitive else 0
    for key in keys:
        value = user_dict[key]
        # 영숫자 키는 \b 경계, 그 외(한글 · 가나)는 공백/문장부호 경계
        if re.fullmatch(r"[A-Za-z0-9_.&+-]+", key):
            pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(key) + r"(?![A-Za-z0-9])", flags)
        else:
            pattern = re.compile(r"(?<![^\s.,?!])" + re.escape(key) + r"(?![^\s.,?!])", flags)
        new, n = pattern.subn(value, text)
        if n:
            replaced.append((key, value, "user_dict x{0}".format(n)))
            text = new
    return text, replaced


def finish(text):
    """마지막 공백 정리 - 줄바꿈 없는 한 줄."""
    t = _SPACES.sub(" ", text)
    t = _SPACE_BEFORE_PUNCT.sub(r"\1", t)
    return t.strip()


def find_digits(text):
    """남은 숫자 토큰 (정규화 뒤에도 남았으면 W23)."""
    return re.findall(r"\d[\d,.]*", text)


def find_latin(text):
    """남은 로마자 단어 (한국어 · 일본어 대본에서 W23 후보)."""
    return re.findall(r"[A-Za-z][A-Za-z'.&+-]*", text)


def split_number(num_text):
    """'1,234.5' -> (1234, '5') / '12' -> (12, None). 콤마 제거. 실패면 None."""
    s = num_text.replace(",", "")
    if not s or not re.fullmatch(r"\d+(\.\d+)?", s):
        return None
    if "." in s:
        a, b = s.split(".", 1)
        return int(a), b
    return int(s), None
