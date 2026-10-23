# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - faster-whisper 엔진 (1차, docs/0130_stt_converter_plan.md D2)
#
# 모델 이름: faster-whisper 의 크기 이름(large-v3-turbo · large-v3 · distil-large-v3.5 ...) 또는 Hugging Face repo
# (예: kotoba-tech/kotoba-whisper-v2.0-faster, CT2 로 변환한 BuzzASR/korean). 캐시는 cache_dir(models/) - HF_HOME 과 같다.
# 언어는 UI 가 강제한다(D4). 감지 언어 · 확률은 info 에서 받아 W20 비교에 쓴다.
# import 는 load() 안에서 - 패키지가 없어도 UI 가 뜨고 콤보가 비활성으로 알린다.

import os
import time

from . import base


MODEL_CHOICES = (
    ("large-v3-turbo (recommended)", "large-v3-turbo"),
    ("large-v3 (slower, retry when turbo is wrong)", "large-v3"),
    ("distil-large-v3.5 (English only)", "distil-large-v3.5"),
    ("kotoba-whisper-v2.0 (Japanese)", "kotoba-tech/kotoba-whisper-v2.0-faster"),
    ("Custom Hugging Face repo / local folder...", ""),
)


class FasterWhisperEngine(base.Engine):

    name = "faster-whisper"

    @staticmethod
    def available():
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self, log=None):
        if self._model is not None:
            return
        from .. import device as device_mod
        if self.device != "cpu":
            forced = device_mod.force_cpu_reason()
            if forced:                                   # CUDA 금지 PC - 건드리지 않고 E44 -> converter 가 CPU 로 폴백(W21)
                raise base.EngineError("E44", "CUDA is disabled on this PC ({0})".format(forced))
            device_mod.add_nvidia_dlls()
        # Windows 는 심볼릭 링크를 못 써 HF 캐시가 파일을 복사한다 - 동작엔 문제 없으니 경고만 끈다 (M0-1 실측)
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        if self.cache_dir:
            os.environ.setdefault("HF_HOME", self.cache_dir)
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise base.EngineError("E40", "faster-whisper is not installed - run setup_stt.bat", repr(e))
        t0 = time.perf_counter()
        kwargs = {}
        if self.cache_dir:
            kwargs["download_root"] = os.path.join(self.cache_dir, "hub")
        try:
            self._model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type, **kwargs)
        except Exception as e:                           # 캐시 없음 + 오프라인 · CUDA 초기화 실패 등
            text = repr(e)
            code = "E41" if ("huggingface" in text.lower() or "connection" in text.lower()
                             or "not found" in text.lower()) else "E44"
            raise base.EngineError(code, "model load failed ({0})".format(self.describe()), text)
        self.load_seconds = time.perf_counter() - t0
        if log:
            log("INFO", "model loaded: {0} ({1:.1f} s)".format(self.describe(), self.load_seconds))

    def transcribe(self, wav_path, language, options=None):
        if self._model is None:
            self.load()
        o = options or base.TranscribeOptions()
        code = base.LANG_CODES.get(language, language)
        t0 = time.perf_counter()
        try:
            segments, info = self._model.transcribe(
                wav_path, language=code, beam_size=o.beam_size, word_timestamps=o.word_timestamps,
                vad_filter=bool(o.vad) if o.vad != "auto" else True,
                vad_parameters=dict(min_silence_duration_ms=o.min_silence_ms),
                condition_on_previous_text=o.condition_on_previous_text,
                initial_prompt=o.initial_prompt or None)
            out = []
            for s in segments:                            # 제너레이터 - 여기서 실제 추론이 돈다
                words = [base.Word(w.start, w.end, w.word, w.probability) for w in (s.words or [])]
                out.append(base.Segment(s.start, s.end, s.text, words, s.avg_logprob, s.no_speech_prob,
                                        s.compression_ratio))
        except Exception as e:
            raise base.EngineError("E45", "transcription failed: {0}".format(os.path.basename(wav_path)), repr(e))
        return base.TranscribeResult(out, info.language, info.language_probability, info.duration,
                                     time.perf_counter() - t0)
