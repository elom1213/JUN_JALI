# -*- coding: utf-8 -*-
# VisemeNet Converter - version info
#
# 01.00  wav -> VisemeNet txt standalone converter. WAV list (shared TSL) + output folder,
#        preflight check of every file (44.1 kHz / 16-bit / channels / length / silence /
#        output collisions) - one failure stops everything before anything is converted,
#        and an error while converting stops the batch. Writes <name>.txt (same as the
#        original README) and <name>.visemenet.json (columns, fps, source wav).
# 01.01  Transcript mode "Correct with transcript (MFA)" (docs/0060 plan B): a transcript next to
#        each WAV (<name>.lab / .txt) is aligned with Montreal Forced Aligner (setup_mfa.bat) and
#        the 20 viseme columns are corrected phone by phone (lip floor on p/b/m/f/v, others
#        attenuated, silence x0.2, 30 ms ramps); Jaw / Lip untouched. Writes <name>.phones.json.
#        English / Korean / Japanese. New checks E30 - E34 (E34: never overwrite a transcript),
#        warnings W10 / W11 / W13.

APP_NAME = "VisemeNet Converter"
VERSION = "01.01"
LAST_UPDATE = "2026-10-20"
