# -*- coding: utf-8 -*-
# VisemeNet Converter - version info
#
# 01.00  wav -> VisemeNet txt standalone converter. WAV list (shared TSL) + output folder,
#        preflight check of every file (44.1 kHz / 16-bit / channels / length / silence /
#        output collisions) - one failure stops everything before anything is converted,
#        and an error while converting stops the batch. Writes <name>.txt (same as the
#        original README) and <name>.visemenet.json (columns, fps, source wav).

APP_NAME = "VisemeNet Converter"
VERSION = "01.00"
LAST_UPDATE = "2026-10-19"
