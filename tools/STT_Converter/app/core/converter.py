# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 일괄 변환 (UI 비의존, docs/0130_stt_converter_plan.md §5)
#
# 흐름: job.preflight(전부 검사, 하나라도 실패면 변환 0) -> run_batch: 엔진 로드(한 번) -> 파일마다
#       transcribe -> W20(감지 언어 ≠ 선택) · W22(빈 결과: .lab 안 씀) · 정규화 -> W23(남은 토큰) · W24(환각 의심)
#       -> .lab(+.bak) · .stt.json 쓰기. 파일 하나의 실패는 그 파일만 W 로 넘기고 계속한다(D13 - 결과가 서로 독립).
# 엔진 로드가 CUDA 때문에 실패(E44)하면 CPU int8 엔진으로 다시 만들어 계속한다(W21) - fallback_factory 가 있을 때.
# log(level, message) · progress(done, total, name) · should_stop() 콜백만으로 UI 에 알린다.

import os

from . import output_writer
from .engines import EngineError, TranscribeOptions
from .normalize import normalize as normalize_text


class NormalizeConfig(object):
    def __init__(self, enabled=True, user_dict=None, kana=False):
        self.enabled = enabled
        self.user_dict = dict(user_dict or {})
        self.kana = kana


def _noop(*args, **kwargs):
    return None


def run_batch(engine, jobs, options=None, norm_cfg=None, write_json=True, existing="skip",
              converter_name="STT Converter", log=_noop, progress=_noop, should_stop=lambda: False,
              fallback_factory=None):
    """Returns (written_paths, stop_reason) - stop_reason "" 이면 정상 종료. engine 은 로드돼 있지 않아도 된다."""
    options = options or TranscribeOptions()
    norm_cfg = norm_cfg or NormalizeConfig()
    written = []
    todo = [j for j in jobs if not j.skipped]
    for j in jobs:
        for code, message in j.warnings:
            log("WARN", "{0}  {1} {2}".format(j.name, code, message))
    if not todo:
        return written, ""

    if not engine.loaded:
        log("INFO", "Loading model {0} (first run downloads it)...".format(engine.describe()))
        try:
            engine.load(log)
        except EngineError as e:
            if e.code == "E44" and engine.device == "cuda" and fallback_factory is not None:
                log("WARN", "W21 CUDA failed ({0}) - falling back to CPU int8, this is slow".format(
                    (e.detail or e.message)[:200]))
                engine = fallback_factory()
                engine.load(log)
            else:
                log("ERROR", "{0} {1}".format(e.code, e.message))
                if e.detail:
                    log("INFO", "detail: {0}".format(e.detail[:500]))
                return written, "Stopped: {0} {1}".format(e.code, e.message)

    total = len(todo)
    for i, j in enumerate(todo):
        if should_stop():
            return written, "stopped by user"
        progress(i, total, j.name)
        warnings = []
        try:
            result = engine.transcribe(j.wav_path, j.language, options)
        except EngineError as e:
            log("WARN", "{0}  {1} {2} - skipped".format(j.name, e.code, e.message))
            if e.detail:
                log("INFO", "detail: {0}".format(e.detail[:300]))
            continue

        if result.language and result.language != engine_lang_code(j.language) and (result.language_prob or 0) >= 0.5:
            warnings.append(("W20", "detected language '{0}' (p={1:.2f}) differs from the selected {2}".format(
                result.language, result.language_prob or 0, j.language)))
        norm = None
        if result.empty:
            warnings.append(("W22", "no speech recognized - transcript not written"))
        else:
            if norm_cfg.enabled:
                norm = normalize_text(result.text, j.language, norm_cfg.user_dict, kana=norm_cfg.kana)
                for tok, why in norm.unresolved:
                    warnings.append(("W23", "unresolved token '{0}' ({1})".format(tok, why)))
            for a, b, why in result.suspects():
                warnings.append(("W24", "possible hallucination at {0:.1f}-{1:.1f} s ({2})".format(a, b, why)))
        for code, message in warnings:
            log("WARN", "{0}  {1} {2}".format(j.name, code, message))

        try:
            if not result.empty:
                output_writer.write_transcript(j.out_path, norm.text if norm is not None else result.text,
                                               backup=(existing == "backup" and j.existing))
                written.append(j.out_path)
            if write_json:
                output_writer.write_json(j.json_path, output_writer.build_json(
                    j, result, norm, engine, options, converter_name, warnings))
        except OSError as e:
            log("WARN", "{0}  E43 cannot write output: {1} - skipped".format(j.name, e))
            continue

        text = (norm.text if norm is not None else result.text)
        preview = text if len(text) <= 80 else text[:77] + "..."
        log("OK", "{0} -> {1}  ({2} segment(s), {3:.1f} s audio, {4:.1f} s){5}".format(
            j.name, os.path.basename(j.out_path) if not result.empty else "(no transcript)",
            len(result.segments), result.duration or j.info.seconds, result.seconds or 0.0,
            "" if result.empty else "  " + preview))
        progress(i + 1, total, j.name)
    return written, ""


def engine_lang_code(language):
    from .engines import LANG_CODES
    return LANG_CODES.get(language, language)
