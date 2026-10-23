# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 결과 파일 쓰기 (docs/0130_stt_converter_plan.md D5)
#
# <이름>.lab (또는 .txt) : 정규화한 대본 한 줄, UTF-8(BOM 없음), 끝 줄바꿈 1개 - VisemeNet Converter Correct 모드가 읽는다.
# <이름>.stt.json        : 원문(raw_text) · 세그먼트 · 단어 시각 · 확신도 · 감지 언어 · 엔진 · 모델 · 치환 목록 · 경고 - 검수 · 재현용.
# 둘 다 임시 파일에 쓰고 이름을 바꾼다. backup=True 면 기존 파일을 <이름>.lab.bak 으로 옮긴 뒤 쓴다(.bak 은 덮어쓴다).

import datetime
import json
import os

FORMAT_ID = "jun_jali.stt/1"


def write_transcript(path, text, backup=False):
    if backup and os.path.isfile(path):
        os.replace(path, path + ".bak")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip("\n") + "\n")
    os.replace(tmp, path)


def build_json(job, result, norm, engine, options, converter_name, warnings):
    data = {
        "format": FORMAT_ID,
        "source_wav": os.path.abspath(job.wav_path).replace("\\", "/"),
        "wav": {"sample_rate": job.info.sample_rate, "channels": job.info.channels,
                "seconds": round(job.info.seconds, 3)} if job.info else {},
        "transcript_file": os.path.abspath(job.out_path).replace("\\", "/"),
        "language": job.language,
        "detected_language": result.language,
        "detected_language_prob": None if result.language_prob is None else round(result.language_prob, 3),
        "engine": engine.name,
        "model": engine.model_name,
        "device": engine.device,
        "compute_type": engine.compute_type,
        "options": {"beam_size": options.beam_size, "vad": options.vad, "min_silence_ms": options.min_silence_ms,
                    "condition_on_previous_text": options.condition_on_previous_text,
                    "initial_prompt": options.initial_prompt},
        "raw_text": result.text,
        "text": norm.text if norm is not None else result.text,
        "replaced": [list(r) for r in (norm.replaced if norm is not None else [])],
        "unresolved": [list(u) for u in (norm.unresolved if norm is not None else [])],
        "suspects": [[round(a, 3), round(b, 3), why] for a, b, why in result.suspects()],
        "warnings": [list(w) for w in warnings],
        "segments": [s.as_dict() for s in result.segments],
        "transcribe_seconds": None if result.seconds is None else round(result.seconds, 2),
        "converter": converter_name,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    return data


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
