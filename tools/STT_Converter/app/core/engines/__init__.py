# -*- coding: utf-8 -*-
# STT Converter - 엔진 목록. UI 콤보는 ENGINES 순서, available() 가 False 면 비활성.
from .base import Engine, EngineError, TranscribeOptions, TranscribeResult, Segment, Word, LANGUAGES, LANG_CODES  # noqa: F401
from .faster_whisper_engine import FasterWhisperEngine, MODEL_CHOICES as FW_MODEL_CHOICES  # noqa: F401

ENGINES = {
    "faster-whisper": FasterWhisperEngine,
}

try:                                                    # 2차 엔진 - 선택 설치 (requirements_stt_qwen.txt)
    from .qwen3_asr_engine import Qwen3ASREngine  # noqa: F401
    ENGINES["qwen3-asr"] = Qwen3ASREngine
except ImportError:
    pass


def make_engine(name, model_name, device, compute_type, cache_dir=""):
    cls = ENGINES.get(name)
    if cls is None:
        raise EngineError("E40", "unknown engine: {0}".format(name))
    return cls(model_name, device, compute_type, cache_dir)
