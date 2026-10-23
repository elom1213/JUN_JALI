# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 엔진 인터페이스 (docs/0130_stt_converter_plan.md D2 · D3)
#
# 엔진 = 모델을 한 번 올려 여러 wav 를 받아쓰는 객체. UI · converter 는 이 인터페이스만 본다.
#   faster_whisper_engine.FasterWhisperEngine  (1차)
#   qwen3_asr_engine.Qwen3ASREngine            (2차, 선택 설치 - import 실패면 목록에서 비활성)
# 결과(TranscribeResult)는 엔진이 달라도 같은 모양 - .stt.json 이 그대로 받는다.

LANGUAGES = ("English", "Korean", "Japanese")
LANG_CODES = {"English": "en", "Korean": "ko", "Japanese": "ja"}
CODE_LANGS = {v: k for k, v in LANG_CODES.items()}


class EngineError(Exception):
    """엔진 로드 · 추론 실패. code 는 E40 ~ E49 (docs/0130 §5-3)."""

    def __init__(self, code, message, detail=None):
        super().__init__("{0} {1}".format(code, message))
        self.code = code
        self.message = message
        self.detail = detail


class Word(object):
    __slots__ = ("start", "end", "text", "probability")

    def __init__(self, start, end, text, probability=None):
        self.start, self.end, self.text, self.probability = start, end, text, probability

    def as_list(self):
        return [round(self.start, 3), round(self.end, 3), self.text,
                None if self.probability is None else round(self.probability, 3)]


class Segment(object):
    def __init__(self, start, end, text, words=None, avg_logprob=None, no_speech_prob=None, compression_ratio=None):
        self.start, self.end, self.text = start, end, text
        self.words = list(words or [])
        self.avg_logprob = avg_logprob
        self.no_speech_prob = no_speech_prob
        self.compression_ratio = compression_ratio

    def as_dict(self):
        d = {"start": round(self.start, 3), "end": round(self.end, 3), "text": self.text,
             "words": [w.as_list() for w in self.words]}
        for k in ("avg_logprob", "no_speech_prob", "compression_ratio"):
            v = getattr(self, k)
            if v is not None:
                d[k] = round(v, 3)
        return d


class TranscribeResult(object):
    """segments 를 이어 붙인 text 와, 감지 언어 · 확률 · 음성 길이 · 걸린 시간."""

    def __init__(self, segments, language=None, language_prob=None, duration=None, seconds=None):
        self.segments = list(segments)
        self.language = language                  # 감지된 언어 코드 (en · ko · ja ...) 또는 None
        self.language_prob = language_prob
        self.duration = duration                  # 음성 길이 (초)
        self.seconds = seconds                    # 추론에 걸린 시간

    @property
    def text(self):
        return " ".join(s.text.strip() for s in self.segments if s.text and s.text.strip())

    @property
    def empty(self):
        return not self.text.strip()

    def suspects(self):
        """환각 · 반복 의심 구간 (W24) - [(start, end, 이유)]. 기준: no_speech_prob > 0.6, compression_ratio > 2.4,
        avg_logprob < -1.0, 같은 3-gram 이 3번 이상."""
        out = []
        for s in self.segments:
            why = []
            if s.no_speech_prob is not None and s.no_speech_prob > 0.6:
                why.append("no_speech_prob {0:.2f}".format(s.no_speech_prob))
            if s.compression_ratio is not None and s.compression_ratio > 2.4:
                why.append("compression_ratio {0:.2f}".format(s.compression_ratio))
            if s.avg_logprob is not None and s.avg_logprob < -1.0:
                why.append("avg_logprob {0:.2f}".format(s.avg_logprob))
            toks = s.text.split()
            if len(toks) >= 9:
                grams = [" ".join(toks[i:i + 3]) for i in range(len(toks) - 2)]
                for g in set(grams):
                    if grams.count(g) >= 3:
                        why.append("repeated '{0}'".format(g))
                        break
            if why:
                out.append((s.start, s.end, ", ".join(why)))
        return out


class TranscribeOptions(object):
    """엔진 공통 옵션 (docs/0130 §5-2 기본값)."""

    def __init__(self, beam_size=5, vad="auto", min_silence_ms=500, word_timestamps=True, initial_prompt="",
                 condition_on_previous_text=False):
        self.beam_size = beam_size
        self.vad = vad                        # True / False / "auto"(converter 가 파일 길이로 정한다, 엔진은 bool 로 받음)
        self.min_silence_ms = min_silence_ms
        self.word_timestamps = word_timestamps
        self.initial_prompt = initial_prompt
        self.condition_on_previous_text = condition_on_previous_text


class Engine(object):
    """서브클래스가 name · load() · transcribe() 를 채운다."""

    name = "base"

    def __init__(self, model_name, device="cpu", compute_type="int8", cache_dir=""):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.cache_dir = cache_dir
        self._model = None
        self.load_seconds = 0.0

    @property
    def loaded(self):
        return self._model is not None

    def describe(self):
        return "{0} {1} on {2}/{3}".format(self.name, self.model_name, self.device, self.compute_type)

    @staticmethod
    def available():
        """패키지가 설치돼 있는가 (UI 콤보 활성 여부)."""
        return False

    def load(self, log=None):
        raise NotImplementedError

    def transcribe(self, wav_path, language, options=None):
        raise NotImplementedError

    def unload(self):
        self._model = None
