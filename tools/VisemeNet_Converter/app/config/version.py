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
# 01.02  Windows 10 / Python 3.14 PCs: MFA runs isolated from the PC's Python and conda variables
#        (PYTHONHOME / PYTHONPATH / user site-packages / CONDA_*) - a Python 3.14 PYTHONHOME or
#        PYTHONPATH made the tool's Python 3.11 load the 3.14 standard library and fail on its
#        first import (numpy -> warnings -> _py_warnings: AttributeError). setup_mfa.bat: install
#        folder at most 80 characters (260-character path limit), same isolation in all .bat files.
# 01.03  Convert progress popup: a modal gauge window opens when Convert is pressed and fills until the
#        batch ends (Checking files / Loading model / Aligning transcripts / Converting, weighted by the
#        expected time, per-file steps weighted by audio length, smooth fill between reports, elapsed
#        time, Stop button = stop after the current file). Closes at 100 %, or at once on stop / error.

APP_NAME = "VisemeNet Converter"
VERSION = "01.03"
LAST_UPDATE = "2026-10-22"
