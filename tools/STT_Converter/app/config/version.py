# -*- coding: utf-8 -*-
# STT Converter - version info
#
# 01.00  Speech (wav) -> transcript (.lab) for the VisemeNet Converter Correct mode. faster-whisper
#        large-v3-turbo (CTranslate2), English / Korean / Japanese, language forced per batch (D4).
#        WAV list (shared TSL) + Language / Engine / Model / Device / Beam / VAD / Kana + output folder,
#        extension (.lab / .txt), existing-file policy (Skip / Overwrite / Backup), .stt.json side file.
#        Preflight of every file (E40 - E43) - one failure stops everything before anything is written;
#        a failure while converting skips that file only (D13). Text normalization per language (numbers
#        -> words, user dictionary, W23 for leftover tokens), W20 language mismatch, W22 empty result,
#        W24 hallucination suspects, W25 skipped. Device: Auto / CUDA float16 / CUDA int8_float16 /
#        CPU int8 with automatic CPU fallback (W21); JUN_STT_FORCE_CPU=1 or data/force_cpu.flag never
#        touches CUDA (docs/0130 §6 - the development PC crashes on CUDA start-up). VAD: Auto = off for
#        clips shorter than 10 s (docs/0130 §11 M0-3: VAD cut the first word of 3.7 s / 4.9 s clips).
#        Headless cli.py with the same core (A00560 JaliBatch P4 calls it).

APP_NAME = "STT Converter"
VERSION = "01.00"
LAST_UPDATE = "2026-10-23"
