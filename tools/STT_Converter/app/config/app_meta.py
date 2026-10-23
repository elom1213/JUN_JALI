# -*- coding: utf-8 -*-
# STT Converter - 작업표시줄 아이콘용 메타 (Maya_Python/JUN_All/docs/taskbar_icon_guide.md)

import os
import sys

APP_USER_MODEL_ID = "JUN.JALI.STTConverter"

_TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def icon_path(ext=".ico"):
    """icon/STT_Converter<ext>. 없으면 빈 문자열 (기본 아이콘)."""
    base = getattr(sys, "_MEIPASS", _TOOL_ROOT)
    path = os.path.join(base, "icon", "STT_Converter" + ext)
    return path if os.path.isfile(path) else ""
