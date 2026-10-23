# -*- coding: utf-8 -*-
# STT Converter 시험용 가짜 엔진 - 모델 없이 코어 · UI 경로를 돈다. 파일 이름에 따라 정해진 결과를 돌려준다.
#   *_empty.wav  -> 세그먼트 없음 (W22)
#   *_ja.wav     -> detected 'ja' (선택 언어가 Korean 이면 W20)
#   *_num.wav    -> "1등이 될 거예요 KWI" (정규화 치환 + W23)
#   *_rep.wav    -> 같은 3-gram 반복 + compression_ratio 3.0 (W24)
#   *_fail.wav   -> transcribe 에서 E45
#   그 외        -> "안녕하세요 테스트입니다"
# device="cuda" 로 만들면 load() 에서 E44 - converter 의 CPU 폴백(W21) 경로 시험용. calls 에 받은 옵션을 기록한다.
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from tools.STT_Converter.app.core.engines import base   # noqa: E402


class FakeEngine(base.Engine):
    name = "fake"
    calls = []                                   # [(wav basename, language, vad bool)]
    load_count = 0
    delay = 0.0                                  # UI 시험용: 로드 · 추론을 이만큼 늦춰 팝업 단계가 보이게

    @staticmethod
    def available():
        return True

    def load(self, log=None):
        if self.device == "cuda":
            raise base.EngineError("E44", "fake CUDA failure", "no cuda here")
        FakeEngine.load_count += 1
        time.sleep(FakeEngine.delay)
        self._model = object()
        if log:
            log("INFO", "fake model loaded ({0})".format(self.describe()))

    def transcribe(self, wav_path, language, options=None):
        if self._model is None:
            self.load()
        o = options or base.TranscribeOptions()
        time.sleep(FakeEngine.delay)
        FakeEngine.calls.append((os.path.basename(wav_path), language, o.vad))
        stem = os.path.splitext(os.path.basename(wav_path))[0]
        if stem.endswith("_fail"):
            raise base.EngineError("E45", "transcription failed: {0}".format(os.path.basename(wav_path)), "boom")
        if stem.endswith("_empty"):
            return base.TranscribeResult([], "ko", 0.3, 1.5, 0.01)
        lang = "ja" if stem.endswith("_ja") else base.LANG_CODES.get(language, "ko")
        if stem.endswith("_num"):
            text = "1등이 될 거예요 KWI"
        elif stem.endswith("_rep"):
            text = "다시 다시 다시 다시 다시 다시 다시 다시 다시 다시"
        else:
            text = "안녕하세요 테스트입니다" if language == "Korean" else "hello this is a test"
        seg = base.Segment(0.3, 1.2, text, [base.Word(0.3, 0.7, text.split()[0], 0.9)],
                           avg_logprob=-0.2, no_speech_prob=0.05,
                           compression_ratio=3.0 if stem.endswith("_rep") else 1.1)
        return base.TranscribeResult([seg], lang, 0.97, 1.5, 0.02)
