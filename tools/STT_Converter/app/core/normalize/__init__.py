# -*- coding: utf-8 -*-
# STT Converter - 언어별 대본 정규화 진입점. normalize(text, language, user_dict=None, kana=False) -> NormalizeResult
from . import base, english, japanese, korean  # noqa: F401
from .base import NormalizeResult  # noqa: F401

LANGUAGES = ("English", "Korean", "Japanese")
_MODULES = {"English": english, "Korean": korean, "Japanese": japanese}


def normalize(text, language, user_dict=None, kana=False):
    if language not in _MODULES:
        raise ValueError("unknown language: {0!r} (expected one of {1})".format(language, ", ".join(LANGUAGES)))
    if language == "Japanese":
        return japanese.normalize(text, user_dict, kana=kana)
    return _MODULES[language].normalize(text, user_dict)
