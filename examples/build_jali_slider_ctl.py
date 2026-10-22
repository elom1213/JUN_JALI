# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# [JUN_JALI] JALI 슬라이더 컨트롤러 리그 생성 (docs/0090_jali_slider_ctl_plan.md)
#
# 만드는 것
#   JALI_SLIDER_RIG                      루트 (옮기기 · 크기용, global_scale 어트리뷰트)
#     JALI_CTL_GRP
#       JALI_box_grp / CNT_JaLi          2D 박스 (tx = Jaw, ty = Lip, 0~1, 휴식 0) + jaw/lip_output_min/max
#                                        기본 9 = DUMMY_IN_JALI.Jaw/Lip 의 기본값 0.6 이 민다 (데이터 키가 그 자리를 덮는다)
#       PH_<attr>_grp ×16                PHONEMES 슬라이더 (CTL_PH_<attr>.ty 0~1) + output_min/max
#       CO_<attr>_grp ×6                 COARTIC  슬라이더 (CTL_CO_<attr>.ty 0~1) + output_min/max
#     JALI_DUMMY_GRP
#       DUMMY_IN_JALI / _PHONEMES / _COARTIC     외부 입력 허브 (0~1) → 슬라이더 부모(_drv) 를 민다
#       DUMMY_OUT_JALI / _PHONEMES / _COARTIC    리맵 결과 허브 (어트리뷰트 이름 = angela_JALI.ma 원본)
#
# 계산 (슬라이더 하나마다)
#   pma_<tag> (plusMinusAverage) : drv.ty + ctl.ty            (외부 입력 + 손 조작)
#   rv_<tag>  (remapValue)       : [0,1] → [output_min, output_max]   (입력은 범위로 클램프, 실측)
#   gs_<tag>  (multDoubleLinear) : × JALI_SLIDER_RIG.global_scale     (Jaw / Lip 은 제외)
#   → DUMMY_OUT_<group>.<attr>
#
# direct 모드 (2026-10-22, --direct) — "키가 컨트롤러에 직접 붙는 버전"
#   _drv 그룹과 pma_<tag> 가 없다. DUMMY_IN.<attr> → CTL_<tag>.ty (직결) → rv → gs → DUMMY_OUT.
#   JaLi 박스도 DUMMY_IN_JALI.Jaw/Lip → CNT_JaLi.tx/ty 직결. 컨트롤러 ty 가 "연결됨" 이라 손으로는 못 만지고,
#   bake_ctl_keys() (또는 Maya Bake Simulation) 로 베이크하면 DUMMY_IN 의 키가 컨트롤러 ty 에 그대로 남는다
#   → 베이크 뒤에는 컨트롤러 키를 직접 편집하고 DUMMY_OUT 은 컨트롤러를 따라간다.
#
# 사용
#   Maya Script Editor:  import build_jali_slider_ctl as b; b.build()           (b.build(direct=True))
#   배치:    mayapy build_jali_slider_ctl.py [--direct] [out.ma]
#   검증:    mayapy build_jali_slider_ctl.py --verify [--direct] <out.ma>      (저장한 파일을 다시 열어 T1~T7)
#   베이크:  Maya 에서  import build_jali_slider_ctl as b; b.bake_ctl_keys()    (direct 파일, 선택 없으면 전부)

import os
import re
import sys

import maya.cmds as cmds

# ---------------------------------------------------------------------------
# 어트리뷰트 표 (docs/0090 §2) — angela_JALI.ma 의 CNT_PHONEMES / CNT_COARTIC 순서
# ---------------------------------------------------------------------------
PHONEMES = ['AAA', 'Eh', 'AHH', 'OHH', 'UUU', 'IEE', 'RRR', 'WWW',
            'SSS', 'FFF', 'TTH', 'MBP', 'SSH', 'Schwa', 'GK', 'LNTD']
PHONEME_MAX = 12.0

# (attr, output_max 기본, 라벨 — ref 이미지 식)
COARTIC = [('LNTD', 12.0, 'LNTDm'), ('GK', 12.0, 'GKm'), ('MMM', 12.0, 'MMMm'),
           ('FFF', 12.0, 'FFFm'), ('WA_PEDAL', 12.0, 'WAp'), ('YA_PEDAL', 15.0, 'YAp')]

JALI_MAX = 15.0          # CNT_JaLi 범위 (angela)
JALI_DEFAULT = 0.6       # 0.6 × 15 = 9 (angela 기본 9, 9)

ROOT = 'JALI_SLIDER_RIG'
CTL_GRP = 'JALI_CTL_GRP'
DUMMY_GRP = 'JALI_DUMMY_GRP'
GLOBAL_SCALE = 'global_scale'

# 배치
X_PITCH = 1.5            # 슬라이더 간격
ROW_PITCH = 3.0          # 줄 간격 (트랙 1 + 라벨 + 머리글)
ROW_TOP = ROW_PITCH      # 윗줄 y
ROW_BOTTOM = 0.0         # 아랫줄 y
ROW1_COUNT = 12          # 윗줄 = PHONEMES 12
GAP_COLS = 1             # 아랫줄 PHONEMES 4 와 COARTIC 사이 빈 칸
BOX_POS = (-4.5, 0.0)    # JaLi 박스 왼쪽 아래
BOX_SCALE = 2.0          # 박스 보이는 크기 (컨트롤러 tx/ty 는 0~1 그대로)
LABEL_SCALE = 0.25
HEADER_SCALE = 0.3
FONT = 'Arial'

COLOR_PH = 17            # 노랑
COLOR_CO = 18            # 하늘
COLOR_JALI = 13          # 빨강
REFERENCE = 2            # overrideDisplayType = Reference

LOCK_CHANNELS = ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v')


# ---------------------------------------------------------------------------
# 공용
# ---------------------------------------------------------------------------
def _lock(node, channels):
    for ch in channels:
        cmds.setAttr('%s.%s' % (node, ch), lock=True, keyable=False, channelBox=False)


def _reference(node):
    cmds.setAttr(node + '.overrideEnabled', True)
    cmds.setAttr(node + '.overrideDisplayType', REFERENCE)


def _color(shape, index):
    cmds.setAttr(shape + '.overrideEnabled', True)
    cmds.setAttr(shape + '.overrideColor', index)


def _line(name, points, parent):
    crv = cmds.curve(d=1, p=points, n=name)
    shp = cmds.listRelatives(crv, s=True)[0]
    shp = cmds.rename(shp, name + 'Shape')
    cmds.parent(crv, parent, r=True)
    return crv, shp


def _text(name, text, parent, scale, pos, rotate=(0, 0, 0), center=True):
    """textCurves 로 글자 커브를 만들어 parent 아래에 둔다 (Reference). 가로 중앙 정렬."""
    node = cmds.textCurves(ch=False, f=FONT, t=text)[0]
    node = cmds.rename(node, name)
    bb = cmds.exactWorldBoundingBox(node)
    width = bb[3] - bb[0]
    cmds.parent(node, parent, r=True)
    off = -width * scale * 0.5 if center else 0.0
    cmds.setAttr(node + '.t', pos[0] + off, pos[1], pos[2])
    cmds.setAttr(node + '.r', *rotate)
    cmds.setAttr(node + '.s', scale, scale, scale)
    _reference(node)
    return node


def _add_output_range(ctl, prefix, lo, hi):
    """output_min / output_max — 채널박스에 보이되 키는 안 되게."""
    for suffix, val in (('output_min', lo), ('output_max', hi)):
        attr = prefix + suffix
        cmds.addAttr(ctl, ln=attr, at='double', dv=val)
        cmds.setAttr('%s.%s' % (ctl, attr), channelBox=True)
    return prefix + 'output_min', prefix + 'output_max'


def _remap_chain(tag, in_plugs, min_plug, max_plug, out_plug, scale_plug=None):
    """(pma →) rv → (gs) → out_plug. in_plugs 가 둘 이상이면 pma 로 더하고, 하나면 rv 에 직결 (direct)."""
    if len(in_plugs) > 1:
        pma = cmds.createNode('plusMinusAverage', n='pma_' + tag)
        for i, plug in enumerate(in_plugs):
            cmds.connectAttr(plug, '%s.input1D[%d]' % (pma, i))
        src = pma + '.output1D'
    else:
        src = in_plugs[0]
    rv = cmds.createNode('remapValue', n='rv_' + tag)
    cmds.setAttr(rv + '.inputMin', 0.0)
    cmds.setAttr(rv + '.inputMax', 1.0)
    cmds.connectAttr(src, rv + '.inputValue')
    cmds.connectAttr(min_plug, rv + '.outputMin')
    cmds.connectAttr(max_plug, rv + '.outputMax')
    last = rv + '.outValue'
    if scale_plug:
        gs = cmds.createNode('multDoubleLinear', n='gs_' + tag)
        cmds.connectAttr(last, gs + '.input1')
        cmds.connectAttr(scale_plug, gs + '.input2')
        last = gs + '.output'
    cmds.connectAttr(last, out_plug)


# ---------------------------------------------------------------------------
# 슬라이더 하나
# ---------------------------------------------------------------------------
def build_slider(tag, label, parent, pos, color, out_max, dummy_in_plug, dummy_out_plug, scale_plug, direct=False):
    """tag = 'PH_AAA' / 'CO_LNTD'. 돌려주는 것: 컨트롤러 이름.
    direct=True 면 _drv 그룹 없이 DUMMY_IN 을 컨트롤러 ty 에 직결한다."""
    grp = cmds.group(em=True, n=tag + '_grp', p=parent)
    cmds.setAttr(grp + '.t', pos[0], pos[1], 0)

    # 트랙 · 눈금 · 라벨 (Reference)
    deco = cmds.group(em=True, n=tag + '_deco', p=grp)
    _line(tag + '_track', [(0, 0, 0), (0, 1, 0)], deco)
    _line(tag + '_tick_lo', [(-0.3, 0, 0), (0.3, 0, 0)], deco)
    _line(tag + '_tick_hi', [(-0.3, 1, 0), (0.3, 1, 0)], deco)
    _text(tag + '_label', label, deco, LABEL_SCALE, (0, -0.55, 0))
    _reference(deco)

    # 외부 입력이 미는 그룹 → 컨트롤러 (direct 는 그룹 없이 컨트롤러 바로)
    if direct:
        drv = None
        ctl = cmds.group(em=True, n='CTL_' + tag, p=grp)
    else:
        drv = cmds.group(em=True, n=tag + '_drv', p=grp)
        ctl = cmds.group(em=True, n='CTL_' + tag, p=drv)
    _, shp = _line(ctl + '_bar', [(-0.35, 0, 0), (0.35, 0, 0)], ctl)
    cmds.parent(shp, ctl, r=True, s=True)
    cmds.delete(ctl + '_bar')
    shp = cmds.rename(shp, ctl + 'Shape')
    _color(shp, color)
    try:
        cmds.setAttr(shp + '.lineWidth', 3)
    except Exception:
        pass

    cmds.transformLimits(ctl, ty=(0, 1), ety=(True, True))
    _lock(ctl, [c for c in LOCK_CHANNELS if c != 'ty'])
    min_attr, max_attr = _add_output_range(ctl, '', 0.0, out_max)
    min_plug, max_plug = '%s.%s' % (ctl, min_attr), '%s.%s' % (ctl, max_attr)

    if direct:
        cmds.connectAttr(dummy_in_plug, ctl + '.ty')
        _remap_chain(tag, [ctl + '.ty'], min_plug, max_plug, dummy_out_plug, scale_plug)
    else:
        _lock(drv, [c for c in LOCK_CHANNELS if c != 'ty'])
        cmds.setAttr(drv + '.ty', keyable=False, channelBox=False)
        cmds.connectAttr(dummy_in_plug, drv + '.ty')
        _remap_chain(tag, [drv + '.ty', ctl + '.ty'], min_plug, max_plug, dummy_out_plug, scale_plug)
    return ctl


# ---------------------------------------------------------------------------
# JaLi 2D 박스
# ---------------------------------------------------------------------------
def build_jali_box(parent, dummy_in, dummy_out, direct=False):
    grp = cmds.group(em=True, n='JALI_box_grp', p=parent)
    cmds.setAttr(grp + '.t', BOX_POS[0], BOX_POS[1], 0)
    cmds.setAttr(grp + '.s', BOX_SCALE, BOX_SCALE, BOX_SCALE)

    deco = cmds.group(em=True, n='JALI_deco', p=grp)
    _line('JALI_border', [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 0)], deco)
    _line('JALI_tick_jaw', [(0.5, -0.05, 0), (0.5, 0.05, 0)], deco)
    _line('JALI_tick_lip', [(-0.05, 0.5, 0), (0.05, 0.5, 0)], deco)
    _text('JALI_label_jaw', 'Jaw', deco, LABEL_SCALE / BOX_SCALE, (0.5, -0.25, 0))
    _text('JALI_label_lip', 'Lip', deco, LABEL_SCALE / BOX_SCALE, (-0.12, 0.5, 0), rotate=(0, 0, 90))
    _text('JALI_header', 'JALI', deco, HEADER_SCALE / BOX_SCALE, (0.5, 1.12, 0))
    _reference(deco)

    if direct:
        drv = None
        ctl = cmds.group(em=True, n='CNT_JaLi', p=grp)
    else:
        drv = cmds.group(em=True, n='JALI_drv', p=grp)
        ctl = cmds.group(em=True, n='CNT_JaLi', p=drv)
    for name, pts in (('JALI_cross_h', [(-0.08, 0, 0), (0.08, 0, 0)]),
                      ('JALI_cross_v', [(0, -0.08, 0), (0, 0.08, 0)]),
                      ('JALI_ring', [(-0.05, -0.05, 0), (0.05, -0.05, 0), (0.05, 0.05, 0), (-0.05, 0.05, 0), (-0.05, -0.05, 0)])):
        crv, shp = _line(name, pts, ctl)
        cmds.parent(shp, ctl, r=True, s=True)
        cmds.delete(crv)
        shp = cmds.rename(shp, ctl + 'Shape' if name == 'JALI_ring' else name + 'Shape')
        _color(shp, COLOR_JALI)
        try:
            cmds.setAttr(shp + '.lineWidth', 2)
        except Exception:
            pass

    cmds.transformLimits(ctl, tx=(0, 1), ty=(0, 1), etx=(True, True), ety=(True, True))
    cmds.setAttr(ctl + '.t', 0, 0, 0)        # 휴식 위치 0 — 기본 0.6(=9) 은 DUMMY_IN_JALI 의 기본값이 민다 (0090 C7)
    _lock(ctl, [c for c in LOCK_CHANNELS if c not in ('tx', 'ty')])
    jaw_min, jaw_max = _add_output_range(ctl, 'jaw_', 0.0, JALI_MAX)
    lip_min, lip_max = _add_output_range(ctl, 'lip_', 0.0, JALI_MAX)

    if direct:
        cmds.connectAttr(dummy_in + '.Jaw', ctl + '.tx')
        cmds.connectAttr(dummy_in + '.Lip', ctl + '.ty')
        _remap_chain('JALI_Jaw', [ctl + '.tx'], ctl + '.' + jaw_min, ctl + '.' + jaw_max, dummy_out + '.Jaw')
        _remap_chain('JALI_Lip', [ctl + '.ty'], ctl + '.' + lip_min, ctl + '.' + lip_max, dummy_out + '.Lip')
    else:
        _lock(drv, [c for c in LOCK_CHANNELS if c not in ('tx', 'ty')])
        for ch in ('tx', 'ty'):
            cmds.setAttr('%s.%s' % (drv, ch), keyable=False, channelBox=False)
        cmds.connectAttr(dummy_in + '.Jaw', drv + '.tx')
        cmds.connectAttr(dummy_in + '.Lip', drv + '.ty')
        _remap_chain('JALI_Jaw', [drv + '.tx', ctl + '.tx'], ctl + '.' + jaw_min, ctl + '.' + jaw_max, dummy_out + '.Jaw')
        _remap_chain('JALI_Lip', [drv + '.ty', ctl + '.ty'], ctl + '.' + lip_min, ctl + '.' + lip_max, dummy_out + '.Lip')
    return ctl


# ---------------------------------------------------------------------------
# 더미 노드
# ---------------------------------------------------------------------------
def _dummy(name, attrs, parent, limited, defaults=None):
    """defaults = {attr: 기본값} (없으면 0)."""
    defaults = defaults or {}
    node = cmds.group(em=True, n=name, p=parent)
    for a in attrs:
        if limited:
            cmds.addAttr(node, ln=a, at='double', min=0.0, max=1.0, dv=defaults.get(a, 0.0), k=True)
        else:
            cmds.addAttr(node, ln=a, at='double', dv=defaults.get(a, 0.0), k=True)
    _lock(node, LOCK_CHANNELS)
    return node


# ---------------------------------------------------------------------------
# 전체
# ---------------------------------------------------------------------------
def build(direct=False):
    """direct=True: _drv / pma 없이 DUMMY_IN → 컨트롤러 직결 (헤더 'direct 모드')."""
    root = cmds.group(em=True, n=ROOT)
    cmds.addAttr(root, ln=GLOBAL_SCALE, at='double', min=0.0, dv=1.0, k=True)
    scale_plug = '%s.%s' % (root, GLOBAL_SCALE)
    ctl_grp = cmds.group(em=True, n=CTL_GRP, p=root)
    dummy_grp = cmds.group(em=True, n=DUMMY_GRP, p=root)
    _lock(ctl_grp, LOCK_CHANNELS[:-1])
    _lock(dummy_grp, LOCK_CHANNELS[:-1])

    co_attrs = [a for a, _, _ in COARTIC]
    din_jali = _dummy('DUMMY_IN_JALI', ['Jaw', 'Lip'], dummy_grp, True,
                      defaults={'Jaw': JALI_DEFAULT, 'Lip': JALI_DEFAULT})
    din_ph = _dummy('DUMMY_IN_PHONEMES', PHONEMES, dummy_grp, True)
    din_co = _dummy('DUMMY_IN_COARTIC', co_attrs, dummy_grp, True)
    dout_jali = _dummy('DUMMY_OUT_JALI', ['Jaw', 'Lip'], dummy_grp, False)
    dout_ph = _dummy('DUMMY_OUT_PHONEMES', PHONEMES, dummy_grp, False)
    dout_co = _dummy('DUMMY_OUT_COARTIC', co_attrs, dummy_grp, False)

    # 머리글
    header_grp = cmds.group(em=True, n='JALI_headers', p=ctl_grp)
    _text('PHONEMES_header', 'PHONEMES', header_grp, HEADER_SCALE, (0, ROW_TOP + 1.25, 0), center=False)
    co_x0 = (4 + GAP_COLS) * X_PITCH
    _text('COARTIC_header', 'COARTIC', header_grp, HEADER_SCALE, (co_x0, ROW_BOTTOM + 1.25, 0), center=False)
    _reference(header_grp)

    # PHONEMES 16 — 윗줄 12, 아랫줄 4
    for i, attr in enumerate(PHONEMES):
        if i < ROW1_COUNT:
            pos = (i * X_PITCH, ROW_TOP)
        else:
            pos = ((i - ROW1_COUNT) * X_PITCH, ROW_BOTTOM)
        build_slider('PH_' + attr, attr, ctl_grp, pos, COLOR_PH, PHONEME_MAX,
                     '%s.%s' % (din_ph, attr), '%s.%s' % (dout_ph, attr), scale_plug, direct)

    # COARTIC 6 — 아랫줄 이어서
    for j, (attr, out_max, label) in enumerate(COARTIC):
        pos = (co_x0 + j * X_PITCH, ROW_BOTTOM)
        build_slider('CO_' + attr, label, ctl_grp, pos, COLOR_CO, out_max,
                     '%s.%s' % (din_co, attr), '%s.%s' % (dout_co, attr), scale_plug, direct)

    build_jali_box(ctl_grp, din_jali, dout_jali, direct)
    cmds.select(cl=True)
    return root


def build_file(out_path, direct=False):
    cmds.file(new=True, f=True)
    cmds.currentUnit(l='centimeter', a='degree', t='film')
    build(direct)
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    cmds.file(rename=out_path)
    cmds.file(save=True, type='mayaAscii', f=True)
    return out_path


# ---------------------------------------------------------------------------
# 베이크 (direct 파일) — DUMMY_IN 의 키를 컨트롤러 채널에 그대로 남긴다
# ---------------------------------------------------------------------------
CTL_PATTERNS = ('CTL_PH_*', 'CTL_CO_*', 'CNT_JaLi', '*:CTL_PH_*', '*:CTL_CO_*', '*:CNT_JaLi')


def _dummy_in_source(plug):
    """plug 의 상류가 DUMMY_IN_* 어트리뷰트면 (DUMMY_IN 플러그, 그 위 animCurve 또는 None) 을 돌려준다."""
    src = cmds.listConnections(plug, s=True, d=False, p=True, scn=True) or []
    if not src or 'DUMMY_IN_' not in src[0].split('.')[0]:
        return None, None
    curves = cmds.listConnections(src[0], s=True, d=False, type='animCurve', scn=True) or []
    return src[0], (curves[0] if curves else None)


def bake_ctl_keys(nodes=None, start=None, end=None, sample_by=1.0, mode='copy'):
    """direct 파일에서 DUMMY_IN 이 직결된 컨트롤러 채널(ty, JaLi 는 tx/ty)을 베이크한다.

    nodes   : 컨트롤러 목록. None 이면 선택된 것, 선택도 없으면 CTL_PH_* / CTL_CO_* / CNT_JaLi 전부.
    mode    : 'copy' — DUMMY_IN 에 animCurve 가 있으면 그 키를 통째로 복사해 컨트롤러에 붙인다 (키 수 · 탄젠트 그대로).
                       animCurve 가 없는 채널(정적 값 · 다른 노드가 미는 값)은 bakeResults 로 프레임마다 찍는다.
              'bake' — 전부 bakeResults 로 [start, end] 를 sample_by 간격으로 찍는다.
    start/end : bakeResults 범위. None 이면 플레이백 범위.
    돌려주는 것: 베이크된 플러그 목록. 베이크 뒤 DUMMY_IN → 컨트롤러 연결은 끊기고 DUMMY_OUT 은 컨트롤러를 따라간다.
    """
    if nodes is None:
        nodes = cmds.ls(sl=True, type='transform') or cmds.ls(CTL_PATTERNS, type='transform')
    todo = []                      # (plug, dummy_plug, anim_curve)
    for node in nodes:
        for ch in ('tx', 'ty'):
            plug = '%s.%s' % (node, ch)
            if not cmds.objExists(plug) or cmds.getAttr(plug, lock=True):
                continue
            dummy_plug, curve = _dummy_in_source(plug)
            if dummy_plug:
                todo.append((plug, dummy_plug, curve))
    if not todo:
        print('bake_ctl_keys: nothing to bake (no DUMMY_IN connected controller channel)')
        return []

    if start is None:
        start = cmds.playbackOptions(q=True, min=True)
    if end is None:
        end = cmds.playbackOptions(q=True, max=True)

    sampled = []
    for plug, dummy_plug, curve in todo:
        node, attr = plug.split('.', 1)
        if mode == 'copy' and curve:
            dummy_node, dummy_attr = dummy_plug.split('.', 1)
            cmds.disconnectAttr(dummy_plug, plug)
            cmds.copyKey(dummy_node, attribute=dummy_attr, option='curve')
            cmds.pasteKey(node, attribute=attr, option='replaceCompletely')
        else:
            sampled.append(plug)
    if sampled:
        cmds.bakeResults(sampled, t=(start, end), sampleBy=sample_by, simulation=False,
                         preserveOutsideKeys=True, disableImplicitControl=True, minimizeRotation=False)
    done = [p for p, _, _ in todo]
    print('bake_ctl_keys: %d channel(s) baked (%d copied, %d sampled)' % (len(done), len(done) - len(sampled), len(sampled)))
    return done


# ---------------------------------------------------------------------------
# 검증 (docs/0090 §7 T1~T7) — 저장한 .ma 를 다시 연다
# ---------------------------------------------------------------------------
ANGELA = r'C:\Users\USER\Desktop\JP\0001_PJ_portfolio\0040_JULI\scenes\angela_JALI.ma'
_SKIP = {'Project', 'Enunciate', 'dummy'}


def _angela_attrs(node):
    """angela .ma 에서 node 의 double addAttr 이름 (구분선 enum · Project/Enunciate/dummy 제외)."""
    if not os.path.isfile(ANGELA):
        return None
    names, inside = [], False
    with open(ANGELA, 'r', encoding='cp949', errors='replace') as f:
        for line in f:
            if line.startswith('createNode'):
                inside = ('-n "%s"' % node) in line
                continue
            if inside and line.strip().startswith('addAttr') and '-at "double"' in line:
                m = re.search(r'-ln "([^"]+)"', line)
                if m and m.group(1) not in _SKIP:
                    names.append(m.group(1))
    return names


def verify(path, direct=False):
    cmds.file(path, o=True, f=True)
    fails = []
    checks = [0]

    def ok(cond, msg):
        checks[0] += 1
        if not cond:
            fails.append(msg)
            print('  FAIL', msg)

    def user_attrs(node):
        return cmds.listAttr(node, ud=True) or []

    def world_y(node):
        return cmds.xform(node, q=True, ws=True, t=True)[1]

    def src_of(plug):
        s = cmds.listConnections(plug, s=True, d=False, p=True, scn=True) or []
        return s[0] if s else None

    if direct:
        return _verify_direct(ok, user_attrs, world_y, src_of, checks, fails)

    # T1 어트리뷰트 집합 == angela
    ph = _angela_attrs('CNT_PHONEMES')
    co = _angela_attrs('CNT_COARTIC')
    if ph is None:
        print('  T1 skipped (angela_JALI.ma not found)')
    else:
        ok(ph == user_attrs('DUMMY_OUT_PHONEMES') == user_attrs('DUMMY_IN_PHONEMES'), 'T1 PHONEMES attrs %s' % ph)
        ok(co == user_attrs('DUMMY_OUT_COARTIC') == user_attrs('DUMMY_IN_COARTIC'), 'T1 COARTIC attrs %s' % co)
    ok(user_attrs('DUMMY_OUT_JALI') == ['Jaw', 'Lip'], 'T1 JALI attrs')

    sliders = [('PH_' + a, 'DUMMY_IN_PHONEMES.' + a, 'DUMMY_OUT_PHONEMES.' + a, PHONEME_MAX) for a in PHONEMES]
    sliders += [('CO_' + a, 'DUMMY_IN_COARTIC.' + a, 'DUMMY_OUT_COARTIC.' + a, mx) for a, mx, _ in COARTIC]

    for tag, din, dout, mx in sliders:
        ctl = 'CTL_' + tag
        # T2 리맵
        cmds.setAttr(din, 0)
        for ty, expect in ((0.0, 0.0), (0.5, mx * 0.5), (1.0, mx)):
            cmds.setAttr(ctl + '.ty', ty)
            ok(abs(cmds.getAttr(dout) - expect) < 1e-6, 'T2 %s ty=%s -> %s (expect %s)' % (tag, ty, cmds.getAttr(dout), expect))
        cmds.setAttr(ctl + '.output_min', 1); cmds.setAttr(ctl + '.output_max', 12)
        cmds.setAttr(ctl + '.ty', 0); ok(abs(cmds.getAttr(dout) - 1) < 1e-6, 'T2 %s [1,12] lo' % tag)
        cmds.setAttr(ctl + '.ty', 1); ok(abs(cmds.getAttr(dout) - 12) < 1e-6, 'T2 %s [1,12] hi' % tag)
        cmds.setAttr(ctl + '.ty', 0.5); ok(abs(cmds.getAttr(dout) - 6.5) < 1e-6, 'T2 %s [1,12] mid' % tag)
        cmds.setAttr(ctl + '.output_min', 0); cmds.setAttr(ctl + '.output_max', mx)
        # T3 더미 입력 → 부모 그룹 → 합 · 클램프
        cmds.setAttr(ctl + '.ty', 0)
        y0 = world_y(ctl)
        cmds.setAttr(din, 1)
        ok(abs(world_y(ctl) - y0 - 1) < 1e-6, 'T3 %s world y moves by 1' % tag)
        ok(abs(cmds.getAttr(dout) - mx) < 1e-6, 'T3 %s din=1 -> max' % tag)
        cmds.setAttr(din, 0.7); cmds.setAttr(ctl + '.ty', 0.6)
        ok(abs(cmds.getAttr(dout) - mx) < 1e-6, 'T3 %s 0.7+0.6 clamped to max' % tag)
        cmds.setAttr(din, 0); cmds.setAttr(ctl + '.ty', 0)
        # T4 제한 · 잠금 · Reference
        ok(cmds.transformLimits(ctl, q=True, ty=True) == [0.0, 1.0] and cmds.transformLimits(ctl, q=True, ety=True) == [True, True],
           'T4 %s ty limits' % tag)
        ok(all(cmds.getAttr('%s.%s' % (ctl, c), lock=True) for c in LOCK_CHANNELS if c != 'ty'), 'T4 %s locks' % tag)
        ok(cmds.getAttr(tag + '_deco.overrideDisplayType') == REFERENCE, 'T4 %s deco reference' % tag)
        ok(not cmds.getAttr(ctl + '.output_min', k=True) and cmds.getAttr(ctl + '.output_min', cb=True), 'T4 %s output_min channelBox only' % tag)

    # T5 이름이 겹치는 어트리뷰트가 서로 다른 더미 노드로 간다
    for a in ('LNTD', 'GK', 'FFF'):
        for grp, node in (('PH', 'DUMMY_OUT_PHONEMES'), ('CO', 'DUMMY_OUT_COARTIC')):
            hist = cmds.listHistory('%s.%s' % (node, a)) or []
            ok(('CTL_%s_%s' % (grp, a)) in hist and ('CTL_%s_%s' % ('CO' if grp == 'PH' else 'PH', a)) not in hist,
               'T5 %s.%s fed by CTL_%s_%s only' % (node, a, grp, a))

    # T6 global_scale — 비짐만, Jaw / Lip 은 그대로
    cmds.setAttr('CTL_PH_AAA.ty', 1); cmds.setAttr('CTL_CO_YA_PEDAL.ty', 1)
    cmds.setAttr(ROOT + '.' + GLOBAL_SCALE, 0.5)
    ok(abs(cmds.getAttr('DUMMY_OUT_PHONEMES.AAA') - 6) < 1e-6, 'T6 AAA halves')
    ok(abs(cmds.getAttr('DUMMY_OUT_COARTIC.YA_PEDAL') - 7.5) < 1e-6, 'T6 YA_PEDAL halves')
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Jaw') - JALI_DEFAULT * JALI_MAX) < 1e-6, 'T6 Jaw unaffected (%s)' % cmds.getAttr('DUMMY_OUT_JALI.Jaw'))
    cmds.setAttr(ROOT + '.' + GLOBAL_SCALE, 1.0)
    cmds.setAttr('CTL_PH_AAA.ty', 0); cmds.setAttr('CTL_CO_YA_PEDAL.ty', 0)

    # JaLi 박스 — 컨트롤러 휴식 0, DUMMY_IN_JALI 기본 0.6 → 출력 9
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Jaw') - 9) < 1e-6 and abs(cmds.getAttr('DUMMY_OUT_JALI.Lip') - 9) < 1e-6, 'JaLi default 9, 9')
    ok(cmds.getAttr('CNT_JaLi.tx') == 0 and cmds.getAttr('CNT_JaLi.ty') == 0, 'JaLi controller rests at 0, 0')
    ok(abs(cmds.getAttr('DUMMY_IN_JALI.Jaw') - JALI_DEFAULT) < 1e-6, 'DUMMY_IN_JALI.Jaw default 0.6')
    cmds.setAttr('CNT_JaLi.ty', 0.4)
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Lip') - 15) < 1e-6, 'JaLi Lip dummy 0.6 + ctl 0.4 -> 15')
    cmds.setAttr('CNT_JaLi.ty', 0)
    cmds.setAttr('DUMMY_IN_JALI.Jaw', 0)
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Jaw')) < 1e-6, 'JaLi Jaw dummy 0 -> 0')
    cmds.setAttr('DUMMY_IN_JALI.Jaw', 1.0)
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Jaw') - 15) < 1e-6, 'JaLi Jaw dummy 1 -> 15 (nothing added)')
    cmds.setAttr('DUMMY_IN_JALI.Jaw', JALI_DEFAULT)
    ok(cmds.transformLimits('CNT_JaLi', q=True, tx=True) == [0.0, 1.0], 'JaLi tx limits')

    print('verify: %d checks, %d failed' % (checks[0], len(fails)))
    return not fails


def _verify_direct(ok, user_attrs, world_y, src_of, checks, fails):
    """direct 파일 검증 — 컨트롤러 ty 가 DUMMY_IN 에 직결돼 있으므로 값은 DUMMY_IN 으로 넣는다."""
    # T1 어트리뷰트 집합 == angela
    ph = _angela_attrs('CNT_PHONEMES')
    co = _angela_attrs('CNT_COARTIC')
    if ph is None:
        print('  T1 skipped (angela_JALI.ma not found)')
    else:
        ok(ph == user_attrs('DUMMY_OUT_PHONEMES') == user_attrs('DUMMY_IN_PHONEMES'), 'T1 PHONEMES attrs %s' % ph)
        ok(co == user_attrs('DUMMY_OUT_COARTIC') == user_attrs('DUMMY_IN_COARTIC'), 'T1 COARTIC attrs %s' % co)
    ok(user_attrs('DUMMY_OUT_JALI') == ['Jaw', 'Lip'], 'T1 JALI attrs')

    sliders = [('PH_' + a, 'DUMMY_IN_PHONEMES.' + a, 'DUMMY_OUT_PHONEMES.' + a, PHONEME_MAX) for a in PHONEMES]
    sliders += [('CO_' + a, 'DUMMY_IN_COARTIC.' + a, 'DUMMY_OUT_COARTIC.' + a, mx) for a, mx, _ in COARTIC]

    for tag, din, dout, mx in sliders:
        ctl = 'CTL_' + tag
        # T2 리맵 (DUMMY_IN → ctl.ty → out)
        for v, expect in ((0.0, 0.0), (0.5, mx * 0.5), (1.0, mx)):
            cmds.setAttr(din, v)
            ok(abs(cmds.getAttr(ctl + '.ty') - v) < 1e-6, 'T2 %s din=%s -> ctl.ty %s' % (tag, v, cmds.getAttr(ctl + '.ty')))
            ok(abs(cmds.getAttr(dout) - expect) < 1e-6, 'T2 %s din=%s -> %s (expect %s)' % (tag, v, cmds.getAttr(dout), expect))
        cmds.setAttr(ctl + '.output_min', 1); cmds.setAttr(ctl + '.output_max', 12)
        cmds.setAttr(din, 0); ok(abs(cmds.getAttr(dout) - 1) < 1e-6, 'T2 %s [1,12] lo' % tag)
        cmds.setAttr(din, 1); ok(abs(cmds.getAttr(dout) - 12) < 1e-6, 'T2 %s [1,12] hi' % tag)
        cmds.setAttr(din, 0.5); ok(abs(cmds.getAttr(dout) - 6.5) < 1e-6, 'T2 %s [1,12] mid' % tag)
        cmds.setAttr(ctl + '.output_min', 0); cmds.setAttr(ctl + '.output_max', mx)
        # T3 직결 — 컨트롤러가 직접 움직이고, 더해지는 것이 없다
        cmds.setAttr(din, 0)
        y0 = world_y(ctl)
        cmds.setAttr(din, 1)
        ok(abs(world_y(ctl) - y0 - 1) < 1e-6, 'T3 %s world y moves by 1' % tag)
        cmds.setAttr(din, 0.7)
        ok(abs(cmds.getAttr(dout) - mx * 0.7) < 1e-6, 'T3 %s din=0.7 -> 0.7*max (nothing added)' % tag)
        cmds.setAttr(din, 0)
        # T4 제한 · 잠금 · Reference · 직결 구조
        ok(cmds.transformLimits(ctl, q=True, ty=True) == [0.0, 1.0] and cmds.transformLimits(ctl, q=True, ety=True) == [True, True],
           'T4 %s ty limits' % tag)
        ok(all(cmds.getAttr('%s.%s' % (ctl, c), lock=True) for c in LOCK_CHANNELS if c != 'ty'), 'T4 %s locks' % tag)
        ok(cmds.getAttr(tag + '_deco.overrideDisplayType') == REFERENCE, 'T4 %s deco reference' % tag)
        ok(not cmds.getAttr(ctl + '.output_min', k=True) and cmds.getAttr(ctl + '.output_min', cb=True), 'T4 %s output_min channelBox only' % tag)
        ok(src_of(ctl + '.ty') == din, 'T4 %s ctl.ty <- %s (got %s)' % (tag, din, src_of(ctl + '.ty')))
        ok(src_of('rv_%s.inputValue' % tag) == ctl + '.translateY', 'T4 %s rv.inputValue <- ctl.ty' % tag)
        ok(not cmds.objExists(tag + '_drv') and not cmds.objExists('pma_' + tag), 'T4 %s no _drv / pma' % tag)
        ok(cmds.listRelatives(ctl, p=True)[0] == tag + '_grp', 'T4 %s ctl parent is _grp' % tag)
        ok(cmds.getAttr(ctl + '.ty', k=True), 'T4 %s ctl.ty keyable' % tag)

    # T5 이름이 겹치는 어트리뷰트가 서로 다른 더미 노드로 간다
    for a in ('LNTD', 'GK', 'FFF'):
        for grp, node in (('PH', 'DUMMY_OUT_PHONEMES'), ('CO', 'DUMMY_OUT_COARTIC')):
            hist = cmds.listHistory('%s.%s' % (node, a)) or []
            ok(('CTL_%s_%s' % (grp, a)) in hist and ('CTL_%s_%s' % ('CO' if grp == 'PH' else 'PH', a)) not in hist,
               'T5 %s.%s fed by CTL_%s_%s only' % (node, a, grp, a))

    # T6 global_scale — 비짐만, Jaw / Lip 은 그대로
    cmds.setAttr('DUMMY_IN_PHONEMES.AAA', 1); cmds.setAttr('DUMMY_IN_COARTIC.YA_PEDAL', 1)
    cmds.setAttr(ROOT + '.' + GLOBAL_SCALE, 0.5)
    ok(abs(cmds.getAttr('DUMMY_OUT_PHONEMES.AAA') - 6) < 1e-6, 'T6 AAA halves')
    ok(abs(cmds.getAttr('DUMMY_OUT_COARTIC.YA_PEDAL') - 7.5) < 1e-6, 'T6 YA_PEDAL halves')
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Jaw') - JALI_DEFAULT * JALI_MAX) < 1e-6, 'T6 Jaw unaffected (%s)' % cmds.getAttr('DUMMY_OUT_JALI.Jaw'))
    cmds.setAttr(ROOT + '.' + GLOBAL_SCALE, 1.0)
    cmds.setAttr('DUMMY_IN_PHONEMES.AAA', 0); cmds.setAttr('DUMMY_IN_COARTIC.YA_PEDAL', 0)

    # JaLi 박스 — DUMMY_IN_JALI 기본 0.6 이 컨트롤러를 직접 0.6 에 두고 출력 9
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Jaw') - 9) < 1e-6 and abs(cmds.getAttr('DUMMY_OUT_JALI.Lip') - 9) < 1e-6, 'JaLi default 9, 9')
    ok(abs(cmds.getAttr('CNT_JaLi.tx') - JALI_DEFAULT) < 1e-6 and abs(cmds.getAttr('CNT_JaLi.ty') - JALI_DEFAULT) < 1e-6,
       'JaLi controller sits at 0.6, 0.6 (direct)')
    ok(src_of('CNT_JaLi.tx') == 'DUMMY_IN_JALI.Jaw' and src_of('CNT_JaLi.ty') == 'DUMMY_IN_JALI.Lip', 'JaLi tx/ty <- DUMMY_IN_JALI')
    ok(not cmds.objExists('JALI_drv') and not cmds.objExists('pma_JALI_Jaw') and not cmds.objExists('pma_JALI_Lip'), 'JaLi no _drv / pma')
    cmds.setAttr('DUMMY_IN_JALI.Lip', 1.0)
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Lip') - 15) < 1e-6, 'JaLi Lip dummy 1 -> 15')
    cmds.setAttr('DUMMY_IN_JALI.Lip', JALI_DEFAULT)
    cmds.setAttr('DUMMY_IN_JALI.Jaw', 0)
    ok(abs(cmds.getAttr('DUMMY_OUT_JALI.Jaw')) < 1e-6, 'JaLi Jaw dummy 0 -> 0')
    cmds.setAttr('DUMMY_IN_JALI.Jaw', JALI_DEFAULT)
    ok(cmds.transformLimits('CNT_JaLi', q=True, tx=True) == [0.0, 1.0], 'JaLi tx limits')

    # T7 베이크 — DUMMY_IN 의 키가 컨트롤러에 그대로 남고, 그 뒤 DUMMY_OUT 은 컨트롤러를 따라간다
    keys = [(1, 0.0), (12, 1.0), (24, 0.25)]
    for t, v in keys:
        cmds.setKeyframe('DUMMY_IN_PHONEMES.AAA', t=t, v=v)
        cmds.setKeyframe('DUMMY_IN_JALI.Jaw', t=t, v=v)
    cmds.setKeyframe('DUMMY_IN_COARTIC.GK', t=1, v=0.3)       # 키 하나 (정적에 가까운 입력)
    cmds.playbackOptions(min=1, max=24)
    # (a) copy 모드: 키가 통째로 옮겨진다
    done = bake_ctl_keys(['CTL_PH_AAA', 'CNT_JaLi'])
    ok(sorted(done) == ['CNT_JaLi.tx', 'CNT_JaLi.ty', 'CTL_PH_AAA.ty'], 'T7 baked plugs %s' % done)
    ok(src_of('CTL_PH_AAA.ty') is not None and cmds.nodeType(src_of('CTL_PH_AAA.ty').split('.')[0]).startswith('animCurve'),
       'T7 CTL_PH_AAA.ty now driven by animCurve (%s)' % src_of('CTL_PH_AAA.ty'))
    ok(cmds.keyframe('CTL_PH_AAA.ty', q=True, tc=True) == [1.0, 12.0, 24.0], 'T7 CTL_PH_AAA.ty key times == DUMMY_IN keys (%s)' % cmds.keyframe('CTL_PH_AAA.ty', q=True, tc=True))
    ok(cmds.keyframe('CTL_PH_AAA.ty', q=True, vc=True) == [0.0, 1.0, 0.25], 'T7 CTL_PH_AAA.ty key values')
    ok(cmds.keyframe('DUMMY_IN_PHONEMES.AAA', q=True, tc=True) == [1.0, 12.0, 24.0], 'T7 DUMMY_IN keys kept')
    ok(cmds.keyframe('CNT_JaLi.tx', q=True, vc=True) == [0.0, 1.0, 0.25], 'T7 CNT_JaLi.tx key values')
    lip_vals = cmds.keyframe('CNT_JaLi.ty', q=True, vc=True) or []
    ok(len(lip_vals) == 24 and all(abs(v - JALI_DEFAULT) < 1e-6 for v in lip_vals),
       'T7 CNT_JaLi.ty (no DUMMY_IN curve) sampled 24 x 0.6 (%d keys)' % len(lip_vals))
    for t, v in keys:
        cmds.currentTime(t)
        ok(abs(cmds.getAttr('CTL_PH_AAA.ty') - v) < 1e-6 and abs(cmds.getAttr('DUMMY_OUT_PHONEMES.AAA') - v * PHONEME_MAX) < 1e-6,
           'T7 f%d ctl %s out %s' % (t, cmds.getAttr('CTL_PH_AAA.ty'), cmds.getAttr('DUMMY_OUT_PHONEMES.AAA')))
    # 베이크 뒤 컨트롤러 키를 고치면 DUMMY_OUT 이 따라간다 (DUMMY_IN 은 더 이상 영향 없음)
    cmds.currentTime(12)
    cmds.setKeyframe('CTL_PH_AAA.ty', t=12, v=0.5)
    cmds.setAttr('DUMMY_IN_PHONEMES.AAA', 1.0)
    cmds.dgdirty(a=True); cmds.currentTime(12)          # standalone 은 setKeyframe 뒤 하류가 바로 안 갱신된다 (실측)
    ok(abs(cmds.getAttr('DUMMY_OUT_PHONEMES.AAA') - 6) < 1e-6, 'T7 edited ctl key -> out 6 (DUMMY_IN ignored)')
    # (b) bake 모드: 프레임마다 샘플
    done = bake_ctl_keys(['CTL_CO_GK'], mode='bake', start=1, end=24)
    ok(done == ['CTL_CO_GK.ty'] and len(cmds.keyframe('CTL_CO_GK.ty', q=True, tc=True) or []) == 24, 'T7 bake mode 24 samples (%s)' % done)
    cmds.currentTime(10)
    ok(abs(cmds.getAttr('CTL_CO_GK.ty') - 0.3) < 1e-6, 'T7 bake mode value 0.3')
    # 아직 안 베이크된 컨트롤러는 그대로 연결돼 있다
    ok(src_of('CTL_PH_Eh.ty') == 'DUMMY_IN_PHONEMES.Eh', 'T7 untouched ctl still connected')

    print('verify(direct): %d checks, %d failed' % (checks[0], len(fails)))
    return not fails


if __name__ == '__main__':
    import maya.standalone
    maya.standalone.initialize(name='python')
    args = [a for a in sys.argv[1:]]
    direct = '--direct' in args
    do_verify = '--verify' in args
    pos = [a for a in args if not a.startswith('--')]
    if do_verify:
        result = verify(pos[0], direct=direct)
        maya.standalone.uninitialize()
        sys.exit(0 if result else 1)
    here = os.path.dirname(os.path.abspath(__file__))
    default_name = 'jali_slider_ctl_direct.ma' if direct else 'jali_slider_ctl.ma'
    out = pos[0] if pos else os.path.join(os.path.dirname(here), 'out', default_name)
    print('saved:', build_file(out, direct=direct))
    maya.standalone.uninitialize()
