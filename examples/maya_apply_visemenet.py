# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# [JUN_JALI] VisemeNet 출력(txt) -> JALI 리그(angela_JALI.ma) 키 - 예시 스크립트
#
# 원본 VisemeNet_tensorflow 의 maya_animation.py 를 옮긴 것. 매핑(열 -> 어트리뷰트)은 원본과 같고,
# 다음만 다르다.
#   - 원본은 "4줄마다 1프레임" = 25fps 가정. 여기서는 씬 fps 를 읽어 시간으로 샘플한다(angela = 24fps).
#   - 다시 실행하면 이전 키를 지우고 다시 건다. 전체가 Undo 한 번.
#   - wav 를 주면 사운드 노드를 만들어 타임슬라이더에 붙인다.
#
# 사용 (Maya Script Editor, Python 탭):
#   import sys; sys.path.append(r"<JUN_JALI>/examples")
#   import maya_apply_visemenet as mav
#   mav.apply(r"<JUN_JALI>/out/visemenet_intro.txt", wav=r"<JUN_JALI>/test_audio/visemenet_intro.wav")

import maya.cmds as cmds
import maya.mel as mel


# VisemeNet 출력 열 (22개, 10ms = 100fps 마다 한 줄)
COLUMNS = ['Jaw', 'Lip', 'Ah', 'Aa', 'Eh', 'Ee', 'Ih', 'Oh', 'Uh', 'U', 'Eu', 'Schwa', 'R', 'S',
           'ShChZh', 'Th', 'JY', 'LNTD', 'GK', 'MBP', 'FV', 'W']
MODEL_FPS = 100.0

# 리그 어트리뷰트 <- 열 이름 (여러 개면 max). 원본 maya_animation.py 의 map_i 와 같다.
#   - WWW 는 원본대로 'U' 열 ('W' 열은 COARTIC.WA_PEDAL 로 간다)
#   - COARTIC.YA_PEDAL 은 원본에서도 키가 걸리지 않는다 -> 넣지 않음. Eu / JY 열은 쓰지 않음.
MAPPING = [
    ("CNT_JaLi.translateX", ["Jaw"]),
    ("CNT_JaLi.translateY", ["Lip"]),
    ("CNT_PHONEMES.AAA", ["Aa"]),
    ("CNT_PHONEMES.Eh", ["Eh"]),
    ("CNT_PHONEMES.AHH", ["Ah"]),
    ("CNT_PHONEMES.OHH", ["Oh", "Uh"]),
    ("CNT_PHONEMES.UUU", ["U"]),
    ("CNT_PHONEMES.IEE", ["Ee", "Ih"]),
    ("CNT_PHONEMES.RRR", ["R"]),
    ("CNT_PHONEMES.WWW", ["U"]),
    ("CNT_PHONEMES.SSS", ["S"]),
    ("CNT_PHONEMES.FFF", ["FV"]),
    ("CNT_PHONEMES.TTH", ["Th"]),
    ("CNT_PHONEMES.MBP", ["MBP"]),
    ("CNT_PHONEMES.SSH", ["ShChZh"]),
    ("CNT_PHONEMES.Schwa", ["Schwa"]),
    ("CNT_PHONEMES.GK", ["GK"]),
    ("CNT_PHONEMES.LNTD", ["LNTD"]),
    ("CNT_COARTIC.LNTD", ["LNTD"]),
    ("CNT_COARTIC.GK", ["GK"]),
    ("CNT_COARTIC.MMM", ["MBP"]),
    ("CNT_COARTIC.FFF", ["FV"]),
    ("CNT_COARTIC.WA_PEDAL", ["W"]),
]

# 0~1 로 자른 값에 곱하는 수 (원본과 같음). 리그 범위: 비짐 0~12, CNT_JaLi 0~15.
SCALE = 10.0

_FPS = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0, "show": 48.0,
        "palf": 50.0, "ntscf": 60.0}


def scene_fps():
    unit = cmds.currentUnit(q=True, time=True)
    if unit in _FPS:
        return _FPS[unit]
    return float(unit.replace("fps", ""))      # "23.976fps" 등


def read_rows(txt_path):
    rows = []
    with open(txt_path, "r") as f:
        for line in f:
            if line.strip():
                rows.append([float(v) for v in line.split()])
    if not rows or len(rows[0]) != len(COLUMNS):
        raise ValueError("Expected {0} columns per line: {1}".format(len(COLUMNS), txt_path))
    return rows


def apply(txt_path, wav=None, start=1, namespace=""):
    """VisemeNet 출력 txt 를 JALI 리그 컨트롤에 키로 건다.

    Args:
        txt_path: inference 결과 txt (np.savetxt, 22열).
        wav: 같은 음성 wav. 주면 사운드 노드를 만들어 start 프레임에 놓는다.
        start: 첫 프레임.
        namespace: 리그를 레퍼런스로 불러왔으면 "angela:" 처럼 콜론까지.

    Returns:
        키를 건 마지막 프레임.
    """
    rows = read_rows(txt_path)
    fps = scene_fps()
    n_frames = int(len(rows) / MODEL_FPS * fps)
    idx = {name: i for i, name in enumerate(COLUMNS)}

    targets = [(namespace + attr, cols) for attr, cols in MAPPING]
    missing = [a for a, _ in targets if not cmds.objExists(a)]
    if missing:
        raise RuntimeError("Missing rig attributes (wrong scene or namespace?): "
                           + ", ".join(missing))

    end = start + n_frames
    cmds.undoInfo(openChunk=True, chunkName="VisemeNet apply")
    try:
        for attr, cols in targets:
            # 다시 실행할 때 이전 결과가 섞이지 않게 이 구간의 키를 먼저 지운다.
            cmds.cutKey(attr, time=(start, end), clear=True)
            for f in range(n_frames + 1):
                row = rows[min(int(round(f / fps * MODEL_FPS)), len(rows) - 1)]
                value = max(min(max(row[idx[c]], 0.0), 1.0) for c in cols) * SCALE
                cmds.setKeyframe(attr, time=start + f, value=value)

        cmds.playbackOptions(minTime=start, maxTime=end)
        if wav:
            _attach_sound(wav, start)
    finally:
        cmds.undoInfo(closeChunk=True)

    print("[JUN_JALI] {0} lines @100fps -> frames {1}-{2} @{3}fps, {4} attributes keyed".format(
        len(rows), start, end, fps, len(targets)))
    return end


def _attach_sound(wav, start):
    name = "visemenet_audio"
    if cmds.objExists(name):
        cmds.delete(name)
    node = cmds.sound(file=wav, offset=start, name=name)
    # 타임슬라이더에 파형 표시 + 재생 시 소리 (GUI 에서만, 배치 모드에선 건너뜀)
    if cmds.about(batch=True):
        return node
    try:
        slider = mel.eval("$tmp = $gPlayBackSlider")
        cmds.timeControl(slider, edit=True, sound=node, displaySound=True)
    except RuntimeError:
        pass
    return node
