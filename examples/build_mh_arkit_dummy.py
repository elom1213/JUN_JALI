# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# [JUN_JALI] MetaHuman facial GUI <-> ARKit 52 dummy nodes  (docs/0100_mh_arkit_dummy_plan.md)
#
# 만드는 것 (0010_sample_0030.mb 를 열어 더해서 0010_sample_0040.mb 로 저장)
#   |rig|DMY_grp
#     dmy_in   : ARKit 52 (0~1, keyable)  -> bw_dmy_<ctrl>_<axis> (blendWeighted, 가중치 = Epic ARKit 포즈 값)
#                -> pma_dmy_<ctrl>_<axis> (plusMinusAverage: 컨트롤러 로컬값 + 입력) -> 기존 SDK(animCurveUU) -> CTRL_expressions
#                -> GRP_dmy_<ctrl> (FRM 과 CTRL 사이의 오프셋 그룹: 입력만큼 컨트롤러 메시가 움직여 보인다)
#     dmy_out  : ARKit 52 <- CTRL_expressions.* (1:1 직결, 다채널 포즈는 bw_out_<arkit> 평균, tongueOut 은 1/0.769 + clamp)
#   GUI2D_mapped_shader (lambert, 시안) : dmy_in 이 미는 컨트롤러 68개 메시에만 배정
#
# 사용
#   배치:  mayapy build_mh_arkit_dummy.py <in.mb> <out.mb> [--no-visual] [--no-mouthclose]
#   Maya:  import build_mh_arkit_dummy as b; b.build()   (열려 있는 씬에 더한다, 저장은 직접)
# 검증:  mayapy check_mh_arkit_dummy.py <out.mb>

import argparse
import os
import sys
from collections import OrderedDict

import maya.cmds as cmds

ARKIT_52 = [
    'eyeBlinkLeft',
    'eyeLookDownLeft',
    'eyeLookInLeft',
    'eyeLookOutLeft',
    'eyeLookUpLeft',
    'eyeSquintLeft',
    'eyeWideLeft',
    'eyeBlinkRight',
    'eyeLookDownRight',
    'eyeLookInRight',
    'eyeLookOutRight',
    'eyeLookUpRight',
    'eyeSquintRight',
    'eyeWideRight',
    'jawForward',
    'jawLeft',
    'jawRight',
    'jawOpen',
    'mouthFunnel',
    'mouthPucker',
    'mouthLeft',
    'mouthRight',
    'mouthSmileLeft',
    'mouthSmileRight',
    'mouthFrownLeft',
    'mouthFrownRight',
    'mouthDimpleLeft',
    'mouthDimpleRight',
    'mouthStretchLeft',
    'mouthStretchRight',
    'mouthRollLower',
    'mouthRollUpper',
    'mouthShrugLower',
    'mouthShrugUpper',
    'mouthPressLeft',
    'mouthPressRight',
    'mouthLowerDownLeft',
    'mouthLowerDownRight',
    'mouthUpperUpLeft',
    'mouthUpperUpRight',
    'browDownLeft',
    'browDownRight',
    'browInnerUp',
    'browOuterUpLeft',
    'browOuterUpRight',
    'cheekPuff',
    'cheekSquintLeft',
    'cheekSquintRight',
    'noseSneerLeft',
    'noseSneerRight',
    'tongueOut',
    'mouthClose',
]

# arkit -> [(controller, axis 'x'|'y', signed weight, CTRL_expressions attr it drives)]
ARKIT_TO_CTRL = {
    'eyeBlinkLeft': [
        ('CTRL_L_eye_blink', 'y', 1.0, 'eyeBlinkL'),
    ],
    'eyeLookDownLeft': [
        ('CTRL_L_eye', 'y', -1.0, 'eyeLookDownL'),
    ],
    'eyeLookInLeft': [
        ('CTRL_L_eye', 'x', -1.0, 'eyeLookRightL'),
    ],
    'eyeLookOutLeft': [
        ('CTRL_L_eye', 'x', 1.0, 'eyeLookLeftL'),
    ],
    'eyeLookUpLeft': [
        ('CTRL_L_eye', 'y', 1.0, 'eyeLookUpL'),
    ],
    'eyeSquintLeft': [
        ('CTRL_L_eye_squintInner', 'y', 1.0, 'eyeSquintInnerL'),
    ],
    'eyeWideLeft': [
        ('CTRL_L_eye_blink', 'y', -1.0, 'eyeWidenL'),
    ],
    'eyeBlinkRight': [
        ('CTRL_R_eye_blink', 'y', 1.0, 'eyeBlinkR'),
    ],
    'eyeLookDownRight': [
        ('CTRL_R_eye', 'y', -1.0, 'eyeLookDownR'),
    ],
    'eyeLookInRight': [
        ('CTRL_R_eye', 'x', 1.0, 'eyeLookLeftR'),
    ],
    'eyeLookOutRight': [
        ('CTRL_R_eye', 'x', -1.0, 'eyeLookRightR'),
    ],
    'eyeLookUpRight': [
        ('CTRL_R_eye', 'y', 1.0, 'eyeLookUpR'),
    ],
    'eyeSquintRight': [
        ('CTRL_R_eye_squintInner', 'y', 1.0, 'eyeSquintInnerR'),
    ],
    'eyeWideRight': [
        ('CTRL_R_eye_blink', 'y', -1.0, 'eyeWidenR'),
    ],
    'jawForward': [
        ('CTRL_C_jaw_fwdBack', 'y', -1.0, 'jawFwd'),
    ],
    'jawLeft': [
        ('CTRL_C_jaw', 'x', -1.0, 'jawLeft'),
    ],
    'jawRight': [
        ('CTRL_C_jaw', 'x', 1.0, 'jawRight'),
    ],
    'jawOpen': [
        ('CTRL_C_jaw', 'y', 1.0, 'jawOpen'),
    ],
    'mouthFunnel': [
        ('CTRL_L_mouth_funnelD', 'y', 1.0, 'mouthFunnelDL'),
        ('CTRL_R_mouth_funnelD', 'y', 1.0, 'mouthFunnelDR'),
        ('CTRL_L_mouth_funnelU', 'y', 1.0, 'mouthFunnelUL'),
        ('CTRL_R_mouth_funnelU', 'y', 1.0, 'mouthFunnelUR'),
    ],
    'mouthPucker': [
        ('CTRL_L_mouth_funnelD', 'y', 0.752, 'mouthFunnelDL'),
        ('CTRL_R_mouth_funnelD', 'y', 0.752, 'mouthFunnelDR'),
        ('CTRL_L_mouth_funnelU', 'y', 0.752, 'mouthFunnelUL'),
        ('CTRL_R_mouth_funnelU', 'y', 0.752, 'mouthFunnelUR'),
        ('CTRL_L_mouth_purseD', 'y', 1.0, 'mouthLipsPurseDL'),
        ('CTRL_R_mouth_purseD', 'y', 1.0, 'mouthLipsPurseDR'),
        ('CTRL_L_mouth_purseU', 'y', 1.0, 'mouthLipsPurseUL'),
        ('CTRL_R_mouth_purseU', 'y', 1.0, 'mouthLipsPurseUR'),
        ('CTRL_L_mouth_towardsD', 'y', 0.412, 'mouthLipsTowardsDL'),
        ('CTRL_R_mouth_towardsD', 'y', 0.412, 'mouthLipsTowardsDR'),
        ('CTRL_L_mouth_towardsU', 'y', 0.412, 'mouthLipsTowardsUL'),
        ('CTRL_R_mouth_towardsU', 'y', 0.412, 'mouthLipsTowardsUR'),
    ],
    'mouthLeft': [
        ('CTRL_C_mouth', 'x', 1.0, 'mouthLeft'),
    ],
    'mouthRight': [
        ('CTRL_C_mouth', 'x', -1.0, 'mouthRight'),
    ],
    'mouthSmileLeft': [
        ('CTRL_L_mouth_cornerPull', 'y', 1.0, 'mouthCornerPullL'),
    ],
    'mouthSmileRight': [
        ('CTRL_R_mouth_cornerPull', 'y', 1.0, 'mouthCornerPullR'),
    ],
    'mouthFrownLeft': [
        ('CTRL_L_mouth_cornerDepress', 'y', 1.0, 'mouthCornerDepressL'),
    ],
    'mouthFrownRight': [
        ('CTRL_R_mouth_cornerDepress', 'y', 1.0, 'mouthCornerDepressR'),
    ],
    'mouthDimpleLeft': [
        ('CTRL_L_mouth_dimple', 'y', 1.0, 'mouthDimpleL'),
    ],
    'mouthDimpleRight': [
        ('CTRL_R_mouth_dimple', 'y', 1.0, 'mouthDimpleR'),
    ],
    'mouthStretchLeft': [
        ('CTRL_L_mouth_stretch', 'y', 1.0, 'mouthStretchL'),
    ],
    'mouthStretchRight': [
        ('CTRL_R_mouth_stretch', 'y', 1.0, 'mouthStretchR'),
    ],
    'mouthRollLower': [
        ('CTRL_L_mouth_lipsRollD', 'y', 1.0, 'mouthLowerLipRollInL'),
        ('CTRL_R_mouth_lipsRollD', 'y', 1.0, 'mouthLowerLipRollInR'),
        ('CTRL_L_mouth_lipsRollU', 'y', 0.499, 'mouthUpperLipRollInL'),
        ('CTRL_R_mouth_lipsRollU', 'y', 0.499, 'mouthUpperLipRollInR'),
    ],
    'mouthRollUpper': [
        ('CTRL_L_mouth_lipsRollU', 'y', 1.0, 'mouthUpperLipRollInL'),
        ('CTRL_R_mouth_lipsRollU', 'y', 1.0, 'mouthUpperLipRollInR'),
    ],
    'mouthShrugLower': [
        ('CTRL_L_jaw_ChinRaiseD', 'y', 1.0, 'jawChinRaiseDL'),
        ('CTRL_R_jaw_ChinRaiseD', 'y', 1.0, 'jawChinRaiseDR'),
    ],
    'mouthShrugUpper': [
        ('CTRL_L_jaw_ChinRaiseU', 'y', 1.0, 'jawChinRaiseUL'),
        ('CTRL_R_jaw_ChinRaiseU', 'y', 1.0, 'jawChinRaiseUR'),
    ],
    'mouthPressLeft': [
        ('CTRL_L_mouth_pressD', 'y', 1.0, 'mouthPressDL'),
        ('CTRL_L_mouth_pressU', 'y', 1.0, 'mouthPressUL'),
    ],
    'mouthPressRight': [
        ('CTRL_R_mouth_pressD', 'y', 1.0, 'mouthPressDR'),
        ('CTRL_R_mouth_pressU', 'y', 1.0, 'mouthPressUR'),
    ],
    'mouthLowerDownLeft': [
        ('CTRL_L_mouth_lowerLipDepress', 'y', 1.0, 'mouthLowerLipDepressL'),
    ],
    'mouthLowerDownRight': [
        ('CTRL_R_mouth_lowerLipDepress', 'y', 1.0, 'mouthLowerLipDepressR'),
    ],
    'mouthUpperUpLeft': [
        ('CTRL_L_mouth_upperLipRaise', 'y', 1.0, 'mouthUpperLipRaiseL'),
    ],
    'mouthUpperUpRight': [
        ('CTRL_R_mouth_upperLipRaise', 'y', 1.0, 'mouthUpperLipRaiseR'),
    ],
    'browDownLeft': [
        ('CTRL_L_brow_down', 'y', 1.0, 'browDownL'),
    ],
    'browDownRight': [
        ('CTRL_R_brow_down', 'y', 1.0, 'browDownR'),
    ],
    'browInnerUp': [
        ('CTRL_L_brow_lateral', 'y', 1.0, 'browLateralL'),
        ('CTRL_R_brow_lateral', 'y', 1.0, 'browLateralR'),
        ('CTRL_L_brow_raiseIn', 'y', 1.0, 'browRaiseInL'),
        ('CTRL_R_brow_raiseIn', 'y', 1.0, 'browRaiseInR'),
    ],
    'browOuterUpLeft': [
        ('CTRL_L_brow_raiseIn', 'y', 1.0, 'browRaiseInL'),
        ('CTRL_L_brow_raiseOut', 'y', 1.0, 'browRaiseOuterL'),
    ],
    'browOuterUpRight': [
        ('CTRL_R_brow_raiseIn', 'y', 1.0, 'browRaiseInR'),
        ('CTRL_R_brow_raiseOut', 'y', 1.0, 'browRaiseOuterR'),
    ],
    'cheekPuff': [
        ('CTRL_L_mouth_suckBlow', 'y', 1.0, 'mouthCheekBlowL'),
        ('CTRL_R_mouth_suckBlow', 'y', 1.0, 'mouthCheekBlowR'),
        ('CTRL_L_mouth_lipsBlow', 'y', 1.0, 'mouthLipsBlowL'),
        ('CTRL_R_mouth_lipsBlow', 'y', 1.0, 'mouthLipsBlowR'),
    ],
    'cheekSquintLeft': [
        ('CTRL_L_eye_cheekRaise', 'y', 1.0, 'eyeCheekRaiseL'),
    ],
    'cheekSquintRight': [
        ('CTRL_R_eye_cheekRaise', 'y', 1.0, 'eyeCheekRaiseR'),
    ],
    'noseSneerLeft': [
        ('CTRL_L_nose', 'y', 1.0, 'noseWrinkleL'),
    ],
    'noseSneerRight': [
        ('CTRL_R_nose', 'y', 1.0, 'noseWrinkleR'),
    ],
    'tongueOut': [
        ('CTRL_C_tongue_move', 'y', -0.826, 'tongueDown'),
        ('CTRL_C_tongue_inOut', 'y', -0.769, 'tongueOut'),
        ('CTRL_C_tongue_wideNarrow', 'y', 0.628, 'tongueWide'),
    ],
    'mouthClose': [
        ('CTRL_L_mouth_lipsTogetherU', 'y', 1.0, 'mouthLipsTogetherUL'),
        ('CTRL_R_mouth_lipsTogetherU', 'y', 1.0, 'mouthLipsTogetherUR'),
        ('CTRL_L_mouth_lipsTogetherD', 'y', 1.0, 'mouthLipsTogetherDL'),
        ('CTRL_R_mouth_lipsTogetherD', 'y', 1.0, 'mouthLipsTogetherDR'),
    ],
}

# arkit <- [(CTRL_expressions attr, weight)]  (weights of one target sum to 1, except tongueOut 1/0.769 -> clamped)
OUT_FROM_EXPR = {
    'eyeBlinkLeft': [('eyeBlinkL', 1.0)],
    'eyeLookDownLeft': [('eyeLookDownL', 1.0)],
    'eyeLookInLeft': [('eyeLookRightL', 1.0)],
    'eyeLookOutLeft': [('eyeLookLeftL', 1.0)],
    'eyeLookUpLeft': [('eyeLookUpL', 1.0)],
    'eyeSquintLeft': [('eyeSquintInnerL', 1.0)],
    'eyeWideLeft': [('eyeWidenL', 1.0)],
    'eyeBlinkRight': [('eyeBlinkR', 1.0)],
    'eyeLookDownRight': [('eyeLookDownR', 1.0)],
    'eyeLookInRight': [('eyeLookLeftR', 1.0)],
    'eyeLookOutRight': [('eyeLookRightR', 1.0)],
    'eyeLookUpRight': [('eyeLookUpR', 1.0)],
    'eyeSquintRight': [('eyeSquintInnerR', 1.0)],
    'eyeWideRight': [('eyeWidenR', 1.0)],
    'jawForward': [('jawFwd', 1.0)],
    'jawLeft': [('jawLeft', 1.0)],
    'jawRight': [('jawRight', 1.0)],
    'jawOpen': [('jawOpen', 1.0)],
    'mouthFunnel': [('mouthFunnelDL', 0.25), ('mouthFunnelDR', 0.25), ('mouthFunnelUL', 0.25), ('mouthFunnelUR', 0.25)],
    'mouthPucker': [('mouthLipsPurseUL', 0.25), ('mouthLipsPurseUR', 0.25), ('mouthLipsPurseDL', 0.25), ('mouthLipsPurseDR', 0.25)],
    'mouthLeft': [('mouthLeft', 1.0)],
    'mouthRight': [('mouthRight', 1.0)],
    'mouthSmileLeft': [('mouthCornerPullL', 1.0)],
    'mouthSmileRight': [('mouthCornerPullR', 1.0)],
    'mouthFrownLeft': [('mouthCornerDepressL', 1.0)],
    'mouthFrownRight': [('mouthCornerDepressR', 1.0)],
    'mouthDimpleLeft': [('mouthDimpleL', 1.0)],
    'mouthDimpleRight': [('mouthDimpleR', 1.0)],
    'mouthStretchLeft': [('mouthStretchL', 1.0)],
    'mouthStretchRight': [('mouthStretchR', 1.0)],
    'mouthRollLower': [('mouthLowerLipRollInL', 0.5), ('mouthLowerLipRollInR', 0.5)],
    'mouthRollUpper': [('mouthUpperLipRollInL', 0.5), ('mouthUpperLipRollInR', 0.5)],
    'mouthShrugLower': [('jawChinRaiseDL', 0.5), ('jawChinRaiseDR', 0.5)],
    'mouthShrugUpper': [('jawChinRaiseUL', 0.5), ('jawChinRaiseUR', 0.5)],
    'mouthPressLeft': [('mouthPressDL', 0.5), ('mouthPressUL', 0.5)],
    'mouthPressRight': [('mouthPressDR', 0.5), ('mouthPressUR', 0.5)],
    'mouthLowerDownLeft': [('mouthLowerLipDepressL', 1.0)],
    'mouthLowerDownRight': [('mouthLowerLipDepressR', 1.0)],
    'mouthUpperUpLeft': [('mouthUpperLipRaiseL', 1.0)],
    'mouthUpperUpRight': [('mouthUpperLipRaiseR', 1.0)],
    'browDownLeft': [('browDownL', 1.0)],
    'browDownRight': [('browDownR', 1.0)],
    'browInnerUp': [('browLateralL', 0.25), ('browLateralR', 0.25), ('browRaiseInL', 0.25), ('browRaiseInR', 0.25)],
    'browOuterUpLeft': [('browRaiseInL', 0.5), ('browRaiseOuterL', 0.5)],
    'browOuterUpRight': [('browRaiseInR', 0.5), ('browRaiseOuterR', 0.5)],
    'cheekPuff': [('mouthCheekBlowL', 0.25), ('mouthCheekBlowR', 0.25), ('mouthLipsBlowL', 0.25), ('mouthLipsBlowR', 0.25)],
    'cheekSquintLeft': [('eyeCheekRaiseL', 1.0)],
    'cheekSquintRight': [('eyeCheekRaiseR', 1.0)],
    'noseSneerLeft': [('noseWrinkleL', 1.0)],
    'noseSneerRight': [('noseWrinkleR', 1.0)],
    'tongueOut': [('tongueOut', 1.3004)],
    'mouthClose': [('mouthLipsTogetherUL', 0.25), ('mouthLipsTogetherUR', 0.25), ('mouthLipsTogetherDL', 0.25), ('mouthLipsTogetherDR', 0.25)],
}


HEAD_RIG = '|rig|head_grp|headRig_grp'
EXPR = HEAD_RIG + '|headGui_grp|GRP_faceGUI|CTRL_faceGUI|FRM_faceGUI|CTRL_expressions'
RIG_ROOT = '|rig'
DMY_GRP = 'DMY_grp'
IN_NODE = 'dmy_in'
OUT_NODE = 'dmy_out'
MAPPED_SHADER = 'GUI2D_mapped_shader'
MAPPED_COLOR = (0.0, 0.8, 1.0)
AXIS_ATTR = {'x': 'translateX', 'y': 'translateY'}
RIGLOGIC_PLUGIN = 'embeddedRL4'


class BuildError(Exception):
    pass


def _ctrl_path(name):
    """짧은 이름 -> 유일한 긴 경로 (headRig_grp 아래)."""
    found = [p for p in (cmds.ls(name, long=True, type='transform') or []) if p.startswith(HEAD_RIG)]
    if len(found) != 1:
        raise BuildError('controller %s: expected 1 under headRig_grp, found %s' % (name, found))
    return found[0]


def _add_arkit_attrs(node, limit):
    for k in ARKIT_52:
        kw = dict(longName=k, attributeType='double', defaultValue=0.0, keyable=True)
        if limit:
            kw.update(minValue=0.0, maxValue=1.0)
        cmds.addAttr(node, **kw)


def used_controllers(mouthclose=True):
    """ARKIT_TO_CTRL 에서 쓰이는 (컨트롤러, 축) -> [(arkit, weight)]  (Apple 순서 유지)."""
    per_axis = OrderedDict()
    for k in ARKIT_52:
        if k == 'mouthClose' and not mouthclose:
            continue
        for ctl, ax, w, _expr in ARKIT_TO_CTRL[k]:
            per_axis.setdefault((ctl, ax), []).append((k, w))
    return per_axis


def create_dummies():
    if cmds.objExists(IN_NODE) or cmds.objExists(OUT_NODE) or cmds.objExists(DMY_GRP):
        raise BuildError('%s / %s / %s already exist - run on the original file' % (DMY_GRP, IN_NODE, OUT_NODE))
    grp = cmds.group(empty=True, name=DMY_GRP, parent=RIG_ROOT)
    dmy_in = cmds.group(empty=True, name=IN_NODE, parent=grp)
    dmy_out = cmds.group(empty=True, name=OUT_NODE, parent=grp)
    for n in (dmy_in, dmy_out):
        for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'):
            cmds.setAttr(n + '.' + a, lock=True, keyable=False, channelBox=False)
    _add_arkit_attrs(dmy_in, limit=True)
    _add_arkit_attrs(dmy_out, limit=False)
    return dmy_in, dmy_out


def build_input_path(visual=True, mouthclose=True):
    """dmy_in -> bw -> pma(SDK 앞) + GRP_dmy(시각). 반환: {ctrl: GRP 또는 None}."""
    per_axis = used_controllers(mouthclose)
    groups = {}
    n_rewired = 0
    for (ctl, ax), inputs in per_axis.items():
        path = _ctrl_path(ctl)
        attr = AXIS_ATTR[ax]
        plug = path + '.' + attr
        bw = cmds.createNode('blendWeighted', name='bw_dmy_%s_%s' % (ctl, ax))
        for i, (k, w) in enumerate(inputs):
            cmds.connectAttr('%s.%s' % (IN_NODE, k), '%s.input[%d]' % (bw, i))
            cmds.setAttr('%s.weight[%d]' % (bw, i), w)
        pma = cmds.createNode('plusMinusAverage', name='pma_dmy_%s_%s' % (ctl, ax))
        cmds.setAttr(pma + '.operation', 1)
        dsts = cmds.listConnections(plug, source=False, destination=True, plugs=True) or []
        if not dsts:
            raise BuildError('%s has no outgoing connection (SDK expected)' % plug)
        for d in dsts:
            cmds.disconnectAttr(plug, d)
            cmds.connectAttr(pma + '.output1D', d)
            n_rewired += 1
        cmds.connectAttr(plug, pma + '.input1D[0]')
        cmds.connectAttr(bw + '.output', pma + '.input1D[1]')
        if visual:
            if ctl not in groups:
                parent = cmds.listRelatives(path, parent=True, fullPath=True)[0]
                grp = cmds.group(empty=True, name='GRP_dmy_%s' % ctl, parent=parent)
                cmds.parent(path, grp, relative=True)
                groups[ctl] = grp
            cmds.connectAttr(bw + '.output', groups[ctl] + '.' + attr)
        else:
            groups.setdefault(ctl, None)
    return groups, n_rewired


def build_output_path(mouthclose=True):
    n_direct = n_avg = 0
    for k in ARKIT_52:
        rows = OUT_FROM_EXPR[k]
        if k == 'mouthClose' and not mouthclose:
            continue
        dst = '%s.%s' % (OUT_NODE, k)
        if len(rows) == 1 and abs(rows[0][1] - 1.0) < 1e-6:
            cmds.connectAttr('%s.%s' % (EXPR, rows[0][0]), dst)
            n_direct += 1
            continue
        bw = cmds.createNode('blendWeighted', name='bw_out_%s' % k)
        for i, (expr, w) in enumerate(rows):
            cmds.connectAttr('%s.%s' % (EXPR, expr), '%s.input[%d]' % (bw, i))
            cmds.setAttr('%s.weight[%d]' % (bw, i), w)
        if sum(w for _e, w in rows) > 1.0 + 1e-6:
            cl = cmds.createNode('clamp', name='cl_out_%s' % k)
            cmds.setAttr(cl + '.minR', 0.0)
            cmds.setAttr(cl + '.maxR', 1.0)
            cmds.connectAttr(bw + '.output', cl + '.inputR')
            cmds.connectAttr(cl + '.outputR', dst)
        else:
            cmds.connectAttr(bw + '.output', dst)
        n_avg += 1
    return n_direct, n_avg


def assign_material(controllers):
    """쓰이는 컨트롤러의 메시 쉐입에 시안 lambert 를 배정. 반환: 쉐입 목록."""
    if cmds.objExists(MAPPED_SHADER):
        raise BuildError('%s already exists' % MAPPED_SHADER)
    mat = cmds.shadingNode('lambert', asShader=True, name=MAPPED_SHADER)
    cmds.setAttr(mat + '.color', *MAPPED_COLOR, type='double3')
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=MAPPED_SHADER + 'SG')
    cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader')
    shapes = []
    for ctl in controllers:
        path = _ctrl_path(ctl)
        for s in cmds.listRelatives(path, shapes=True, noIntermediate=True, fullPath=True) or []:
            if cmds.nodeType(s) == 'mesh':
                cmds.sets(s, edit=True, forceElement=sg)
                shapes.append(s)
    return shapes


def build(visual=True, mouthclose=True):
    if not cmds.pluginInfo(RIGLOGIC_PLUGIN, query=True, loaded=True):
        raise BuildError('plugin %s is not loaded - the rig would be lost on save' % RIGLOGIC_PLUGIN)
    if not cmds.objExists(EXPR):
        raise BuildError('%s not found' % EXPR)
    create_dummies()
    groups, n_rewired = build_input_path(visual, mouthclose)
    n_direct, n_avg = build_output_path(mouthclose)
    shapes = assign_material(list(groups))
    info = {'controllers': len(groups), 'axes': len(used_controllers(mouthclose)), 'rewired': n_rewired,
            'out_direct': n_direct, 'out_avg': n_avg, 'shapes': len(shapes), 'linear_unit': cmds.currentUnit(query=True, linear=True)}
    print('BUILD: %s' % info)
    return info


def _main(argv):
    ap = argparse.ArgumentParser(description='Add ARKit 52 dummy nodes to a MetaHuman Maya file.')
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--no-visual', action='store_true', help='no GRP_dmy offset groups (controllers do not move visually)')
    ap.add_argument('--no-mouthclose', action='store_true', help='leave mouthClose unconnected (Epic mapping has no pose)')
    args = ap.parse_args(argv)
    src, dst = os.path.abspath(args.src), os.path.abspath(args.dst)
    if not os.path.isfile(src):
        raise BuildError('not found: ' + src)
    if os.path.normcase(src) == os.path.normcase(dst):
        raise BuildError('src and dst are the same file')
    import maya.standalone
    maya.standalone.initialize(name='python')
    cmds.file(src, open=True, force=True, ignoreVersion=True)
    info = build(visual=not args.no_visual, mouthclose=not args.no_mouthclose)
    cmds.file(rename=dst)
    cmds.file(save=True, type='mayaBinary', force=True)
    print('SAVED: %s' % dst)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(_main(sys.argv[1:]))
    except BuildError as exc:
        print('BUILD FAILED: %s' % exc)
        sys.exit(1)
