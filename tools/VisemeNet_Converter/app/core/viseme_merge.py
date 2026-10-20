# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-20
# VisemeNet Converter - 대본 정렬(MFA 음소 구간)로 VisemeNet 비짐을 보정한다 (UI 비의존, 순수 numpy)
#
# docs/0060_transcript_mfa_plan.md §4 (IPA -> 비짐 표) · §5.1 (안 B: 보정).
# 출력 형식은 그대로 (N, 22) - 열 0~1 (Jaw, Lip) 은 건드리지 않고 열 2~21 (비짐 20개) 만 바꾼다.
#
# 보정 = 음소 구간마다
#   ① 그 음소의 비짐 열에 최솟값(floor) 보장 - 기본 0.6, 입술 비짐(MBP · FV)은 0.8 (폐쇄가 반드시 보이게)
#   ② 같은 구간의 다른 비짐 열은 감쇠(x0.5) - 공동조음 여지는 남긴다
#   ③ 무음 구간은 비짐 전부 x0.2 (Jaw / Lip 은 그대로)
#   ④ 경계 램프 3행(30ms) - 계단 튐 방지
# 'spn'(사전에 없는 단어) 구간과 h 같은 중립 음소는 VisemeNet 값을 그대로 둔다.

import json
import os

import numpy as np


ROW_FPS = 100
FIRST_VISEME_COL = 2
LIP_VISEMES = ("MBP", "FV")


class Params(object):
    """안 B 보정값. 값은 0060 §5.1 초안 - 리그에서 보며 조정한다."""

    def __init__(self, floor=0.6, lip_floor=0.8, other_scale=0.5, silence_scale=0.2, ramp_rows=3):
        self.floor = floor
        self.lip_floor = lip_floor
        self.other_scale = other_scale
        self.silence_scale = silence_scale
        self.ramp_rows = ramp_rows

    def as_dict(self):
        return dict(self.__dict__)


class PhoneMap(object):
    """saved_params/ipa_to_jali.json - MFA 음소(IPA) -> {비짐: 가중치}."""

    def __init__(self, data, columns):
        self.columns = list(columns)
        visemes = self.columns[FIRST_VISEME_COL:]
        self.phones = {}
        for phone, weights in data["phones"].items():
            for name in weights:
                if name not in visemes:
                    raise ValueError("unknown viseme '{0}' for phone '{1}'".format(name, phone))
            self.phones[phone] = dict(weights)
        self.strip_chars = list(data.get("strip", []))
        self.silence = set(data.get("silence", []))
        self.keep = set(data.get("keep", []))
        self.assimilate = set(data.get("assimilate", []))
        self.neutral = set(data.get("neutral", []))

    @classmethod
    def load(cls, path, columns):
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f), columns)

    def is_assimilating(self, label):
        return label in self.assimilate or self._strip(label) in self.assimilate

    def _strip(self, label):
        for ch in self.strip_chars:
            label = label.replace(ch, "")
        return label

    def lookup(self, label):
        """음소 하나 -> [{비짐: 가중치}, ...] (여러 개면 구간을 시간으로 나눈다).

        Returns:
            list - 비짐 조각들. [] = 중립(그대로 둔다). None = 표에 없음.
        """
        if label in self.neutral:
            return []
        if label in self.phones:
            return [self.phones[label]]
        base = self._strip(label)
        if base in self.neutral:
            return []
        if base in self.phones:
            return [self.phones[base]]
        # 이중모음 등 여러 기호 - 기호마다 찾는다 (ts · dʒ 같은 두 글자 음소는 위에서 이미 걸린다)
        parts = []
        for ch in base:
            if ch in self.phones:
                parts.append(self.phones[ch])
            elif ch in self.neutral:
                continue
            else:
                return None
        return parts or None


def load_default_map(repo_root, columns):
    return PhoneMap.load(os.path.join(repo_root, "saved_params", "ipa_to_jali.json"), columns)


def _rows(t, n_rows):
    return int(min(max(round(t * ROW_FPS), 0), n_rows))


def _resolve_assimilation(phones, phone_map):
    """일본어 ん(ɴ) - 뒤 자음의 비짐(MBP · LNTD · GK)을 따른다. 뒤가 없거나 다른 소리면 GK."""
    out = []
    for i, (t0, t1, label) in enumerate(phones):
        if phone_map.is_assimilating(label):
            target = {"GK": 1.0}
            for _t0, _t1, nxt in phones[i + 1:i + 2]:
                parts = phone_map.lookup(nxt) or []
                if parts and set(parts[0]) & {"MBP", "LNTD", "GK"}:
                    target = parts[0]
            out.append((t0, t1, label, [target]))
        else:
            out.append((t0, t1, label, None))
    return out


def correct(values, phones, phone_map, params=None):
    """안 B - VisemeNet 출력을 음소 구간으로 보정한다.

    Args:
        values: (N, 22) VisemeNet 출력 (100fps).
        phones: [(start_sec, end_sec, label)] - MFA TextGrid 의 phones 티어.
        phone_map: PhoneMap.
        params: Params 또는 None(기본값).

    Returns:
        (corrected (N, 22), report dict) - report: unmapped(표에 없는 음소 목록), segments(보정한 구간 수),
        silence_rows, beyond_rows(모델 출력 끝 0.32초 밖이라 못 쓴 음소 수).
    """
    params = params or Params()
    values = np.asarray(values, dtype=np.float64)
    n_rows = values.shape[0]
    columns = phone_map.columns
    n_vis = len(columns) - FIRST_VISEME_COL
    vis_index = {name: i for i, name in enumerate(columns[FIRST_VISEME_COL:])}
    lip_cols = [vis_index[name] for name in LIP_VISEMES if name in vis_index]

    scale = np.ones((n_rows, n_vis))
    floor = np.zeros((n_rows, n_vis))
    unmapped, segments, silence_rows, beyond = [], 0, 0, 0
    ramp = max(int(params.ramp_rows), 0)

    for t0, t1, label, forced in _resolve_assimilation(phones, phone_map):
        r0, r1 = _rows(t0, n_rows), _rows(t1, n_rows)
        if r1 <= r0:
            if round(t0 * ROW_FPS) >= n_rows:
                beyond += 1
            continue
        if label in phone_map.silence:
            scale[r0:r1, :] = np.minimum(scale[r0:r1, :], params.silence_scale)
            silence_rows += r1 - r0
            continue
        if label in phone_map.keep:
            continue
        parts = forced if forced is not None else phone_map.lookup(label)
        if parts is None:
            if label not in unmapped:
                unmapped.append(label)
            continue
        if not parts:
            continue                                    # 중립 음소 (h 등)
        segments += 1
        bounds = np.linspace(r0, r1, len(parts) + 1).round().astype(int)
        for k, weights in enumerate(parts):
            a, b = bounds[k], bounds[k + 1]
            if b <= a:
                continue
            others = np.ones(n_vis, dtype=bool)
            for name, w in weights.items():
                c = vis_index[name]
                others[c] = False
                level = (params.lip_floor if c in lip_cols else params.floor) * float(w)
                _apply_floor(floor, c, a, b, level, ramp)
            scale[a:b, others] = np.minimum(scale[a:b, others], params.other_scale)

    if ramp:
        scale = _smooth_rows(scale, ramp)
    out = values.copy()
    vis = out[:, FIRST_VISEME_COL:] * scale
    out[:, FIRST_VISEME_COL:] = np.maximum(vis, floor)
    report = {"unmapped": unmapped, "segments": segments, "silence_rows": silence_rows,
              "beyond_rows": beyond, "params": params.as_dict()}
    return out, report


def _apply_floor(floor, col, a, b, level, ramp):
    """구간 [a, b) 에 level, 앞뒤 ramp 행은 0 -> level 선형. 겹치면 큰 값."""
    n = floor.shape[0]
    floor[a:b, col] = np.maximum(floor[a:b, col], level)
    for i in range(1, ramp + 1):
        v = level * (ramp + 1 - i) / float(ramp + 1)
        if a - i >= 0:
            floor[a - i, col] = max(floor[a - i, col], v)
        if b - 1 + i < n:
            floor[b - 1 + i, col] = max(floor[b - 1 + i, col], v)


def _smooth_rows(m, ramp):
    """열마다 이동 평균(폭 2*ramp+1) - 감쇠의 경계를 선형으로 잇는다. 양 끝은 가장자리 값으로 채운다."""
    k = 2 * ramp + 1
    padded = np.pad(m, ((ramp, ramp), (0, 0)), mode="edge")
    c = np.cumsum(padded, axis=0)
    c = np.vstack([np.zeros((1, m.shape[1])), c])
    return (c[k:] - c[:-k]) / float(k)
