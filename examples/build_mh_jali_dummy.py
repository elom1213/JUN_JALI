# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# [JUN_JALI] JALI phoneme dummy nodes on the MetaHuman facial GUI  (docs/0110_jali_mh_dummy_plan.md)
#
# 만드는 것 (0010_sample_0040.mb 를 열어 더해서 0010_sample_0050.mb 로 저장)
#   |rig|DMY_grp
#     DUMMY_IN_JALI      : Jaw Lip (0~1, 기본 0.6 = angela 9) + weight (0~1)      ┐ A00540 jali_slider_dummy_in.json 의
#     DUMMY_IN_PHONEMES  : 음소 16 (0~1, 1.0 = VisemeNet 최댓값 = angela 10)      ├ 노드 이름 · 단위 그대로 -> 그 json 으로
#     DUMMY_IN_COARTIC   : LNTD GK MMM FFF WA_PEDAL YA_PEDAL (0~1)                 ┘ 메타휴먼 파일에 바로 키를 넣을 수 있다
#     dmy_in_jali_arkit  : ARKit 52 (경유 경로 중간값)  <- build_jali_arkit_node 노드망 (prefix jali_)
#     dmy_in_jali_mh     : 혀 · 입술 깨물기 · 턱 비례 동시조음 (직접 경로 중간값) <- jali_bw_mh_* / jali_md_mh_* / jali_cl_mh_*
#   두 중간 노드가 0040 의 bw_dmy_<ctrl>_<axis> 에 입력으로 합류한다 (새 컨트롤러 4개는 bw/pma/GRP 를 새로 만든다).
#
# 사용
#   배치:  mayapy build_mh_jali_dummy.py <0040.mb> <0050.mb> [--no-direct] [--no-visual]
#   Maya:  import build_mh_jali_dummy as b; b.build()            (0040 이 열려 있어야 한다)
#          b.connect_a0020('JALI')   A0020_jali_slider_ctl.ma 를 네임스페이스 JALI 로 레퍼런스한 뒤 DUMMY_OUT_* -> DUMMY_IN_* 연결
# 검증:  mayapy check_mh_jali_dummy.py <0050.mb>

import argparse
import os
import sys
from collections import OrderedDict

import maya.cmds as cmds

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_mh_arkit_dummy as A          # noqa: E402  (0040: ensure_axis / add_inputs / build_input_path / assign_material)
import build_jali_arkit_node as J         # noqa: E402  (JALI -> ARKit 노드망, MAPPING)
import build_jali_slider_ctl as S         # noqa: E402  (A0020 의 PHONEMES / COARTIC 이름 · 순서)

# ---------------------------------------------------------------------------
# 이름 · 단위 (A00540 app/mappings/jali_slider_dummy_in.json 과 같다)
# ---------------------------------------------------------------------------
NODE_JALI = 'DUMMY_IN_JALI'
NODE_PH = 'DUMMY_IN_PHONEMES'
NODE_CO = 'DUMMY_IN_COARTIC'
NODE_ARKIT = 'dmy_in_jali_arkit'
NODE_MH = 'dmy_in_jali_mh'
WEIGHT = 'weight'
PHONEMES = list(S.PHONEMES)                       # A0020 순서 (angela 파일 순서)
COARTIC = [a for a, _mx, _label in S.COARTIC]     # LNTD GK MMM FFF WA_PEDAL YA_PEDAL
JALI_DEFAULT = 0.6        # 0~1 더미에서 angela 9 (실측 조건) 에 해당하는 값
PHONEME_UNIT = 1.0        # 0~1 더미에서 angela 10 (음소를 온전히 발음) 에 해당하는 값
PREFIX = 'jali_'
EXPR_JAWOPEN = A.EXPR + '.jawOpen'

# ---------------------------------------------------------------------------
# 직접 경로 (docs/0110 §3 · §5.3) — 값은 음소 1.0 · Jaw/Lip 0.6 일 때 컨트롤러 축에 더해지는 양 (제안값)
#   attr: (축 'Jaw'|'Lip', × CTRL_expressions.jawOpen 여부, {입력: 가중치})   입력 = 'PH.<음소>' | 'CO.<채널>'
# ---------------------------------------------------------------------------
DIRECT = OrderedDict([
    ('tongueTipUp',    ('Jaw', False, {'PH.LNTD': 0.61, 'PH.RRR': 0.63, 'PH.UUU': 0.20, 'PH.SSH': 0.20, 'CO.LNTD': 1.00})),
    ('tongueTipDown',  ('Jaw', False, {'PH.GK': 0.44, 'PH.SSS': 0.20, 'PH.AAA': 0.20, 'PH.Eh': 0.14, 'PH.IEE': 0.20, 'CO.GK': 1.00})),
    ('tongueBendUp',   ('Jaw', False, {'PH.GK': 0.40, 'PH.UUU': 0.20, 'PH.OHH': 0.30, 'PH.WWW': 0.20, 'CO.GK': 0.46})),
    ('tongueUp',       ('Jaw', False, {'PH.LNTD': 0.30, 'CO.LNTD': 0.35})),
    ('tongueOutExtra', ('Jaw', False, {'PH.RRR': 0.15})),
    ('lowerLipBite',   ('Lip', False, {'PH.FFF': 0.50})),
    ('lipsTogetherCo', ('Lip', True,  {'CO.MMM': 0.80})),
    ('lowerLipBiteCo', ('Lip', True,  {'CO.FFF': 0.60})),
    ('chinRaiseCo',    ('Lip', True,  {'CO.FFF': 0.50})),
])
# 직접 경로 중간값 -> 컨트롤러 축 (부호)
DIRECT_TO_CTRL = {
    'tongueTipUp':    [('CTRL_C_tongue_tipMove', 'y', 1.0)],
    'tongueTipDown':  [('CTRL_C_tongue_tipMove', 'y', -1.0)],
    'tongueBendUp':   [('CTRL_C_tongue_bendTwist', 'y', 1.0)],
    'tongueUp':       [('CTRL_C_tongue_move', 'y', 1.0)],
    'tongueOutExtra': [('CTRL_C_tongue_inOut', 'y', -1.0)],
    'lowerLipBite':   [('CTRL_L_mouth_lipBiteD', 'y', 1.0), ('CTRL_R_mouth_lipBiteD', 'y', 1.0)],
    'lipsTogetherCo': [('CTRL_L_mouth_lipsTogetherU', 'y', 1.0), ('CTRL_R_mouth_lipsTogetherU', 'y', 1.0),
                       ('CTRL_L_mouth_lipsTogetherD', 'y', 1.0), ('CTRL_R_mouth_lipsTogetherD', 'y', 1.0)],
    'lowerLipBiteCo': [('CTRL_L_mouth_lipBiteD', 'y', 1.0), ('CTRL_R_mouth_lipBiteD', 'y', 1.0)],
    'chinRaiseCo':    [('CTRL_L_jaw_ChinRaiseD', 'y', 1.0), ('CTRL_R_jaw_ChinRaiseD', 'y', 1.0)],
}
# A0020 DUMMY_OUT_* (angela 단위) -> 이 더미 (0~1): 곱하는 값
A0020_FACTOR = {'JALI': 1.0 / 15.0, 'PHONEMES': 1.0 / 10.0, 'COARTIC': 1.0 / 10.0}


class BuildError(A.BuildError):
    pass


def _src_plug(key):
    kind, name = key.split('.', 1)
    return '%s.%s' % (NODE_PH if kind == 'PH' else NODE_CO, name)


def _lock_transform(node):
    for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'):
        cmds.setAttr(node + '.' + a, lock=True, keyable=False, channelBox=False)


def create_dummies():
    for n in (NODE_JALI, NODE_PH, NODE_CO, NODE_ARKIT, NODE_MH):
        if cmds.objExists(n):
            raise BuildError('%s already exists - run on 0010_sample_0040.mb' % n)
    if not cmds.objExists(A.DMY_GRP) or not cmds.objExists(A.IN_NODE):
        raise BuildError('%s / %s not found - build the ARKit dummies first (build_mh_arkit_dummy.py)' % (A.DMY_GRP, A.IN_NODE))
    jali = cmds.group(empty=True, name=NODE_JALI, parent=A.DMY_GRP)
    for a in ('Jaw', 'Lip'):
        cmds.addAttr(jali, longName=a, attributeType='double', minValue=0.0, maxValue=1.0, defaultValue=JALI_DEFAULT, keyable=True)
    cmds.addAttr(jali, longName=WEIGHT, attributeType='double', minValue=0.0, maxValue=1.0, defaultValue=1.0, keyable=True)
    ph = cmds.group(empty=True, name=NODE_PH, parent=A.DMY_GRP)
    for a in PHONEMES:
        cmds.addAttr(ph, longName=a, attributeType='double', minValue=0.0, maxValue=1.0, defaultValue=0.0, keyable=True)
    co = cmds.group(empty=True, name=NODE_CO, parent=A.DMY_GRP)
    for a in COARTIC:
        cmds.addAttr(co, longName=a, attributeType='double', minValue=0.0, maxValue=1.0, defaultValue=0.0, keyable=True)
    ark = cmds.group(empty=True, name=NODE_ARKIT, parent=A.DMY_GRP)
    for a in A.ARKIT_52:
        cmds.addAttr(ark, longName=a, attributeType='double', defaultValue=0.0, keyable=False)
    mh = cmds.group(empty=True, name=NODE_MH, parent=A.DMY_GRP)
    for a in DIRECT:
        cmds.addAttr(mh, longName=a, attributeType='double', defaultValue=0.0, keyable=False)
    for n in (jali, ph, co, ark, mh):
        _lock_transform(n)
    return jali, ph, co, ark, mh


def build_via_arkit():
    """DUMMY_IN_* -> jali_* 노드망 -> dmy_in_jali_arkit -> 0040 의 bw_dmy_* 에 같은 가중치로 합류. 반환: (닿은 축 수, 추가 입력 수)."""
    src = {'Jaw': NODE_JALI + '.Jaw', 'Lip': NODE_JALI + '.Lip'}
    for p in J.PHONEMES:
        src[p] = NODE_PH + '.' + p
    for p in J.PEDALS:
        src[p] = NODE_CO + '.' + p
    J.build(prefix=PREFIX, src_plugs=src, out_node=NODE_ARKIT, jali_unit=JALI_DEFAULT, phoneme_unit=PHONEME_UNIT,
            weight_plug='%s.%s' % (NODE_JALI, WEIGHT))
    targets = []
    for channel in J.MAPPING:
        targets.extend(J._targets(channel))
    per_axis = OrderedDict()
    for t in targets:
        for ctl, ax, w, _expr in A.ARKIT_TO_CTRL[t]:
            per_axis.setdefault((ctl, ax), []).append((NODE_ARKIT + '.' + t, w))
    n_inputs = 0
    for (ctl, ax), inputs in per_axis.items():
        bw = A.axis_nodes(ctl, ax)[0]
        if not cmds.objExists(bw):
            raise BuildError('%s not found - 0040 should already map %s.%s' % (bw, ctl, ax))
        n_inputs += A.add_inputs(bw, inputs)
    return len(per_axis), n_inputs


def build_direct(visual=True):
    """DUMMY_IN_* -> jali_bw_mh_* -> jali_md_mh_* (× Jaw/Lip 배율 × weight [× jawOpen]) -> jali_cl_mh_* -> dmy_in_jali_mh
    -> bw_dmy_* (새 축은 만든다). 반환: (새로 만든 컨트롤러 목록, 끊어 이은 연결 수)."""
    scale = {'Jaw': '%smd_weightJaw.output' % PREFIX, 'Lip': '%smd_weightLip.output' % PREFIX}
    for p in scale.values():
        if not cmds.objExists(p.split('.')[0]):
            raise BuildError('%s not found - build_via_arkit() first' % p)
    for attr, (axis, jaw_factor, weights) in DIRECT.items():
        bw = cmds.createNode('blendWeighted', name='%sbw_mh_%s' % (PREFIX, attr))
        for i, (key, w) in enumerate(weights.items()):
            cmds.connectAttr(_src_plug(key), '%s.input[%d]' % (bw, i))
            cmds.setAttr('%s.weight[%d]' % (bw, i), w / PHONEME_UNIT)
        md = cmds.createNode('multDoubleLinear', name='%smd_mh_%s' % (PREFIX, attr))
        cmds.connectAttr(bw + '.output', md + '.input1')
        cmds.connectAttr(scale[axis], md + '.input2')
        out = md + '.output'
        if jaw_factor:
            mj = cmds.createNode('multDoubleLinear', name='%smdjaw_mh_%s' % (PREFIX, attr))
            cmds.connectAttr(out, mj + '.input1')
            cmds.connectAttr(EXPR_JAWOPEN, mj + '.input2')
            out = mj + '.output'
        cl = cmds.createNode('clamp', name='%scl_mh_%s' % (PREFIX, attr))
        cmds.setAttr(cl + '.minR', 0.0)
        cmds.setAttr(cl + '.maxR', 1.0)
        cmds.connectAttr(out, cl + '.inputR')
        cmds.connectAttr(cl + '.outputR', '%s.%s' % (NODE_MH, attr))
    per_axis = OrderedDict()
    for attr, rows in DIRECT_TO_CTRL.items():
        for ctl, ax, sign in rows:
            per_axis.setdefault((ctl, ax), []).append((attr, sign))
    before = set(cmds.ls('bw_dmy_*', type='blendWeighted'))
    _groups, n_rewired = A.build_input_path(visual=visual, src_node=NODE_MH, per_axis=per_axis)
    new_axes = [k for k in per_axis if A.axis_nodes(*k)[0] not in before]
    new_ctrls = []
    for ctl, _ax in new_axes:
        if ctl not in new_ctrls:
            new_ctrls.append(ctl)
    return new_ctrls, n_rewired


def connect_a0020(namespace=''):
    """레퍼런스된 A0020 의 DUMMY_OUT_JALI / PHONEMES / COARTIC 를 (× 1/15, × 1/10) 로 이 더미에 잇는다. 반환: 연결 수."""
    ns = (namespace + ':') if namespace and not namespace.endswith(':') else namespace
    pairs = [('JALI', NODE_JALI, ['Jaw', 'Lip']), ('PHONEMES', NODE_PH, PHONEMES), ('COARTIC', NODE_CO, COARTIC)]
    n = 0
    for role, dst_node, attrs in pairs:
        src_node = '%sDUMMY_OUT_%s' % (ns, role)
        if not cmds.objExists(src_node):
            raise BuildError('%s not found - reference A0020_jali_slider_ctl.ma first' % src_node)
        for a in attrs:
            if not cmds.attributeQuery(a, node=src_node, exists=True):
                continue
            md = cmds.createNode('multDoubleLinear', name='a20_md_%s_%s' % (role, a))
            cmds.connectAttr('%s.%s' % (src_node, a), md + '.input1')
            cmds.setAttr(md + '.input2', A0020_FACTOR[role])
            cmds.connectAttr(md + '.output', '%s.%s' % (dst_node, a), force=True)
            n += 1
    return n


def build(visual=True, direct=True):
    if not cmds.pluginInfo(A.RIGLOGIC_PLUGIN, query=True, loaded=True):
        raise BuildError('plugin %s is not loaded' % A.RIGLOGIC_PLUGIN)
    create_dummies()
    n_axes, n_inputs = build_via_arkit()
    new_ctrls, n_rewired = ([], 0)
    shapes = []
    if direct:
        new_ctrls, n_rewired = build_direct(visual)
        shapes = A.assign_material(new_ctrls)
    info = {'via_axes': n_axes, 'via_inputs': n_inputs, 'direct_attrs': len(DIRECT) if direct else 0,
            'new_controllers': new_ctrls, 'rewired': n_rewired, 'shapes_added': len(shapes)}
    print('BUILD JALI: %s' % info)
    return info


def _main(argv):
    ap = argparse.ArgumentParser(description='Add JALI phoneme dummy nodes to the MetaHuman ARKit dummy file (0040 -> 0050).')
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--no-direct', action='store_true', help='ARKit path only (no tongue / lip-bite / coarticulation extras)')
    ap.add_argument('--no-visual', action='store_true', help='no GRP_dmy offset groups for the new controllers')
    args = ap.parse_args(argv)
    src, dst = os.path.abspath(args.src), os.path.abspath(args.dst)
    if not os.path.isfile(src):
        raise BuildError('not found: ' + src)
    if os.path.normcase(src) == os.path.normcase(dst):
        raise BuildError('src and dst are the same file')
    import maya.standalone
    maya.standalone.initialize(name='python')
    cmds.file(src, open=True, force=True, ignoreVersion=True)
    build(visual=not args.no_visual, direct=not args.no_direct)
    cmds.file(rename=dst)
    cmds.file(save=True, type='mayaBinary', force=True)
    print('SAVED: %s' % dst)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(_main(sys.argv[1:]))
    except A.BuildError as exc:
        print('BUILD FAILED: %s' % exc)
        sys.exit(1)
