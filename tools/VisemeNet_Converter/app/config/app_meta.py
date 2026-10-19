# -*- coding: utf-8 -*-
# VisemeNet Converter - 작업표시줄 아이콘용 메타 (Maya_Python/JUN_All/docs/taskbar_icon_guide.md)

import os
import sys

APP_USER_MODEL_ID = "JUN.JALI.VisemeNetConverter"

_TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def icon_path(ext=".ico"):
    """icon/VisemeNet_Converter<ext>. PyInstaller(_MEIPASS) 대비."""
    base = getattr(sys, "_MEIPASS", _TOOL_ROOT)
    path = os.path.join(base, "icon", "VisemeNet_Converter" + ext)
    return path if os.path.isfile(path) else ""
