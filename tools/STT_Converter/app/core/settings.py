# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 창 설정 저장 (목록 · 언어 · 엔진 · 모델 · 장치 · 출력 옵션). data/settings.json, gitignore 대상.
# 사용자 사전은 data/user_dict_{en,ko,ja}.json - 여기서 읽고 쓴다 (없으면 빈 사전).

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
_PATH = os.path.join(DATA_DIR, "settings.json")
_DICT_FILES = {"English": "user_dict_en.json", "Korean": "user_dict_ko.json", "Japanese": "user_dict_ja.json"}

DEFAULTS = {
    "wav_files": [],
    "language": "Korean",
    "engine": "faster-whisper",
    "model": "large-v3-turbo",
    "custom_model": "",
    "device": "auto",
    "beam_size": 5,
    "vad": "auto",
    "kana": False,
    "normalize": True,
    "output_dir": "",
    "ext": ".lab",
    "existing": "skip",
    "write_json": True,
    "last_dir": "",
}


def load():
    data = dict(DEFAULTS)
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            data.update({k: v for k, v in loaded.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    return data


def save(data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def user_dict_path(language):
    return os.path.join(DATA_DIR, _DICT_FILES.get(language, "user_dict_{0}.json".format(language.lower())))


def load_user_dict(language):
    try:
        with open(user_dict_path(language), "r", encoding="utf-8") as f:
            d = json.load(f)
        return {str(k): str(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_user_dict(language, mapping):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(user_dict_path(language), "w", encoding="utf-8") as f:
            json.dump(dict(mapping), f, ensure_ascii=False, indent=2, sort_keys=True)
        return True
    except OSError:
        return False
