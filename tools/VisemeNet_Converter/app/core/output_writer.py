# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-20
# VisemeNet Converter - 결과 파일 쓰기 (UI 비의존, docs/0030_tool_plan.md §4.5)
#
# <이름>.txt            : 원본 README 와 똑같이 np.savetxt(path, out, '%.4f') - 기존 문서 · 스크립트와 호환
# <이름>.visemenet.json : 열 이름 · fps · 원본 wav (A00540_JaliLipSync 가 wav 경로를 자동으로 채운다)
#                         Correct 모드면 "correction" (대본 · 언어 · MFA · 보정값) 이 더 붙는다
# <이름>.phones.json    : Correct 모드에서만 - MFA 단어 · 음소 구간 (디버그 · 표시용)
# 둘 다 임시 파일에 쓰고 이름을 바꾼다 - 중간에 멈춰도 반쯤 쓴 파일이 남지 않게.

import datetime
import json
import os

import numpy as np


JSON_SUFFIX = ".visemenet.json"
PHONES_SUFFIX = ".phones.json"
FORMAT_ID = "jun_jali.visemenet/1"
PHONES_FORMAT_ID = "jun_jali.phones/1"


def output_paths(wav_path, out_dir):
    """(txt, json) 경로. out_dir 이 비면 wav 와 같은 폴더."""
    stem = os.path.splitext(os.path.basename(wav_path))[0]
    folder = out_dir or os.path.dirname(os.path.abspath(wav_path))
    return os.path.join(folder, stem + ".txt"), os.path.join(folder, stem + JSON_SUFFIX)


def write_txt(path, outputs):
    tmp = path + ".tmp"
    np.savetxt(tmp, outputs, "%.4f")
    os.replace(tmp, path)


def phones_path(txt_path):
    return os.path.splitext(txt_path)[0] + PHONES_SUFFIX


def write_json(path, wav_info, outputs, columns, fps, model_name, converter_name, inference_mode="",
               correction=None):
    data = {
        "format": FORMAT_ID,
        "source_wav": os.path.abspath(wav_info.path).replace("\\", "/"),
        "wav": {"sample_rate": wav_info.sample_rate, "channels": wav_info.channels,
                "seconds": round(wav_info.seconds, 4)},
        "fps": fps,
        "rows": int(outputs.shape[0]),
        "start_seconds": 0.0,
        "covered_seconds": round(outputs.shape[0] / float(fps), 2),
        "columns": list(columns),
        "model": model_name,
        "inference_mode": inference_mode,
        "converter": converter_name,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    if correction is not None:
        data["correction"] = correction
    _write_json_file(path, data)


def write_phones(path, wav_info, words, phones, correction):
    data = {
        "format": PHONES_FORMAT_ID,
        "source_wav": os.path.abspath(wav_info.path).replace("\\", "/"),
        "language": correction["language"],
        "aligner": correction["aligner"],
        "words": [[round(a, 3), round(b, 3), t] for a, b, t in words],
        "phones": [[round(a, 3), round(b, 3), t] for a, b, t in phones],
    }
    _write_json_file(path, data)


def _write_json_file(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
