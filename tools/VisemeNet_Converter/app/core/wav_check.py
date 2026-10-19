# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# VisemeNet Converter - 입력 wav 검사 (UI 비의존, docs/0030_tool_plan.md §4.3)
#
# VisemeNet 은 리샘플을 하지 않고 정규화 값(saved_params/wav_mean_std.csv)이 44.1kHz · 16bit 기준이라
# 규격이 다른 파일은 **에러 없이 틀린 결과**를 낸다. 그래서 변환 전에 여기서 막는다.
# 오류는 WavError(code, message) 로 던지고, 계속해도 되는 문제는 WavInfo.warnings 에 담는다.

import os
import warnings

import numpy as np
import scipy.io.wavfile as wavfile


REQUIRED_RATE = 44100
MIN_SECONDS = 0.5
DEFAULT_MAX_SECONDS = 120.0
CLIP_LEVEL = 32760              # int16 최대 32767 근처
CLIP_RATIO_WARN = 0.001         # 0.1 % 넘으면 경고


class WavError(Exception):
    """변환을 멈춰야 하는 문제. code 는 E01 ~ E11 (계획서 §4.3)."""

    def __init__(self, code, message):
        super().__init__("{0} {1}".format(code, message))
        self.code = code
        self.message = message


class WavInfo(object):
    def __init__(self, path, sample_rate, dtype, channels, seconds, warnings_, n_samples=0):
        self.path = path
        self.n_samples = n_samples
        self.sample_rate = sample_rate
        self.dtype = dtype
        self.channels = channels
        self.seconds = seconds
        self.warnings = warnings_       # [(code, message), ...]

    def summary(self):
        return "{0} Hz · {1} · {2} ch · {3:.2f} s".format(
            self.sample_rate, self.dtype, self.channels, self.seconds)


def check_wav(path, max_seconds=DEFAULT_MAX_SECONDS):
    """wav 하나를 검사한다. 통과하면 WavInfo, 아니면 WavError."""
    if not os.path.isfile(path):
        raise WavError("E01", "file not found")

    try:
        with warnings.catch_warnings():
            # WavFileWarning (메타데이터 청크 등) 은 읽기에 지장이 없다.
            warnings.simplefilter("ignore")
            rate, data = wavfile.read(path)
    except Exception as e:
        raise WavError("E02", "cannot read as PCM WAV (damaged, compressed, or not really a WAV): "
                              "{0}".format(str(e).strip() or type(e).__name__))

    if rate != REQUIRED_RATE:
        raise WavError("E03", "sample rate {0} Hz - VisemeNet needs {1} Hz "
                              "(re-export the file at 44.1 kHz)".format(rate, REQUIRED_RATE))

    if data.dtype != np.int16:
        raise WavError("E04", "sample format {0} - need 16-bit integer PCM".format(_format_name(data.dtype)))

    channels = 1 if data.ndim == 1 else data.shape[1]
    if channels > 2:
        raise WavError("E05", "{0} channels - need mono or stereo".format(channels))

    seconds = data.shape[0] / float(rate)
    if seconds < MIN_SECONDS:
        raise WavError("E06", "too short ({0:.2f} s, minimum {1} s)".format(seconds, MIN_SECONDS))
    if max_seconds and seconds > max_seconds:
        raise WavError("E07", "too long ({0:.1f} s > {1:g} s) - split the file".format(seconds, max_seconds))

    # 모델은 왼쪽(첫) 채널만 쓴다 - 무음 · 클리핑도 그 채널로 본다.
    mono = data if channels == 1 else data[:, 0]
    peak = int(np.abs(mono.astype(np.int32)).max()) if mono.size else 0
    if peak == 0:
        raise WavError("E08", "silent audio")

    found = []
    if channels == 2:
        found.append(("W01", "stereo - only the left channel is used"))
    clipped = float(np.count_nonzero(np.abs(mono.astype(np.int32)) >= CLIP_LEVEL)) / mono.size
    if clipped > CLIP_RATIO_WARN:
        found.append(("W02", "clipping detected ({0:.1f} % of samples)".format(clipped * 100.0)))

    return WavInfo(path, rate, "int16", channels, seconds, found, n_samples=int(data.shape[0]))


def _format_name(dtype):
    """사람이 읽는 샘플 형식 이름. 24bit wav 는 scipy 가 int32 로 읽는다."""
    names = {np.dtype(np.float32): "32-bit float", np.dtype(np.float64): "64-bit float",
             np.dtype(np.int32): "32/24-bit integer", np.dtype(np.uint8): "8-bit integer"}
    return names.get(np.dtype(dtype), str(dtype))
