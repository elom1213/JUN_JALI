# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-20
# VisemeNet Converter - 창 설정 저장 (목록 · 출력 폴더 · 옵션). data/settings.json, gitignore 대상.

import json
import os


_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "data", "settings.json")

DEFAULTS = {
    "wav_files": [],
    "output_dir": "",
    "write_json": True,
    "overwrite": False,
    "max_seconds": 120,
    "last_dir": "",
    "align_mode": "audio",          # "audio" | "correct" (대본 + MFA)
    "language": "English",
    "mfa_folder": "",               # 비면 mfa_path.local.txt (setup_mfa.bat 이 씀)
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
        os.makedirs(os.path.dirname(_PATH), exist_ok=True)
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
