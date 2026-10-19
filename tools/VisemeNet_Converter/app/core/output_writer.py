# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# VisemeNet Converter - 결과 파일 쓰기 (UI 비의존, docs/0030_tool_plan.md §4.5)
#
# <이름>.txt            : 원본 README 와 똑같이 np.savetxt(path, out, '%.4f') - 기존 문서 · 스크립트와 호환
# <이름>.visemenet.json : 열 이름 · fps · 원본 wav (A00540_JaliLipSync 가 wav 경로를 자동으로 채운다)
# 둘 다 임시 파일에 쓰고 이름을 바꾼다 - 중간에 멈춰도 반쯤 쓴 파일이 남지 않게.

import datetime
import json
import os

import numpy as np


JSON_SUFFIX = ".visemenet.json"
FORMAT_ID = "jun_jali.visemenet/1"


def output_paths(wav_path, out_dir):
    """(txt, json) 경로. out_dir 이 비면 wav 와 같은 폴더."""
    stem = os.path.splitext(os.path.basename(wav_path))[0]
    folder = out_dir or os.path.dirname(os.path.abspath(wav_path))
    return os.path.join(folder, stem + ".txt"), os.path.join(folder, stem + JSON_SUFFIX)


def write_txt(path, outputs):
    tmp = path + ".tmp"
    np.savetxt(tmp, outputs, "%.4f")
    os.replace(tmp, path)


def write_json(path, wav_info, outputs, columns, fps, model_name, converter_name, inference_mode=""):
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
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
