# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# [JUN_JALI] JALI 음소 -> ARKit 52 블렌드셰이프 변환 노드 생성 (docs/0040_jali_arkit_mapping.md §3)
#
# 만드는 것
#   JALI_ARKit_GRP
#     JALI_IN    : JALI 입력 (CNT_JaLi 의 Jaw/Lip, CNT_PHONEMES 16개, CNT_COARTIC 의 WA/YA_PEDAL)
#     ARKIT_OUT  : ARKit 52 어트리뷰트 (0~1). 아바타 blendShape 에 그대로 연결하면 된다.
#
# 계산 (ARKit 타겟 하나마다)
#   bw_<target>  (blendWeighted) : sum( 음소값 * 가중치 ),  가중치 = 표의 시작 가중치 / 10 (실측이 음소 = 10)
#   md_<target>  (multDoubleLinear): * 축 스케일          jaw/tongue 타겟 = Jaw / 9, 나머지 = Lip / 9 (실측이 9, 9)
#   cl_<target>  (clamp)         : 0~1
#   -> 가중치는 bw_<target>.weight[i] 에 그대로 있으니 아바타에 맞춰 노드에서 바로 고치면 된다.
#   -> Left / Right 쌍은 같은 체인 하나에서 둘 다 받는다 (JALI 근육은 좌우 공용).
#
# 사용
#   Maya Script Editor:  import build_jali_arkit_node as b; b.build()
#   배치:  mayapy build_jali_arkit_node.py [out.ma]
#   컨트롤러: Maya 에서 b.build_controller()  /  배치는 mayapy build_jali_arkit_node.py --ctl [out.ma]
#            (out/jali_arkit_mapping.ma 를 열어 JaLi 2D 슬라이더만 더하고 jali_arkit_mapping_ctl.ma 로 저장)

import os
import sys

import maya.cmds as cmds


PHONEMES = ['AHH', 'AAA', 'Eh', 'IEE', 'OHH', 'UUU', 'WWW', 'RRR', 'SSS', 'SSH', 'FFF', 'TTH',
            'MBP', 'Schwa', 'LNTD', 'GK']
PEDALS = ['WA_PEDAL', 'YA_PEDAL']

PHONEME_MAX = 12.0          # 리그 범위 (VisemeNet 출력은 최대 10)
MEASURED_PHONEME = 10.0     # 실측 시 음소 값
MEASURED_JALI = 9.0         # 실측 시 CNT_JaLi (Jaw, Lip)

ARKIT_52 = [
    'eyeBlinkLeft', 'eyeLookDownLeft', 'eyeLookInLeft', 'eyeLookOutLeft', 'eyeLookUpLeft',
    'eyeSquintLeft', 'eyeWideLeft',
    'eyeBlinkRight', 'eyeLookDownRight', 'eyeLookInRight', 'eyeLookOutRight', 'eyeLookUpRight',
    'eyeSquintRight', 'eyeWideRight',
    'jawForward', 'jawLeft', 'jawRight', 'jawOpen',
    'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthLeft', 'mouthRight',
    'mouthSmileLeft', 'mouthSmileRight', 'mouthFrownLeft', 'mouthFrownRight',
    'mouthDimpleLeft', 'mouthDimpleRight', 'mouthStretchLeft', 'mouthStretchRight',
    'mouthRollLower', 'mouthRollUpper', 'mouthShrugLower', 'mouthShrugUpper',
    'mouthPressLeft', 'mouthPressRight', 'mouthLowerDownLeft', 'mouthLowerDownRight',
    'mouthUpperUpLeft', 'mouthUpperUpRight',
    'browDownLeft', 'browDownRight', 'browInnerUp', 'browOuterUpLeft', 'browOuterUpRight',
    'cheekPuff', 'cheekSquintLeft', 'cheekSquintRight',
    'noseSneerLeft', 'noseSneerRight',
    'tongueOut',
]

# 0040 문서 §3 매칭표. 키 = 채널 이름 (좌우 쌍은 Left/Right 를 뺀 이름), 값 = {입력: 시작 가중치}
# tongueOut 은 문서에 수치가 없어 0.30 을 임시값으로 둔다 (실측 아님).
# jawForward 는 "SSS 소량, 방향 확인 필요" 라 연결만 만들고 가중치 0.
MAPPING = {
    'jawOpen': {'AHH': 1.00, 'AAA': 0.67, 'Eh': 0.38, 'IEE': 0.13, 'OHH': 0.56, 'UUU': 0.06,
                'WWW': 0.30, 'RRR': 0.22, 'FFF': 0.11, 'TTH': 0.13, 'MBP': 0.43,
                'Schwa': 0.30, 'LNTD': 0.30, 'GK': 0.30},
    'jawForward': {'SSS': 0.0},
    'tongueOut': {'TTH': 0.30},
    'mouthLowerDown': {'AHH': 0.34, 'AAA': 0.54, 'Eh': 0.37, 'IEE': 0.61, 'SSS': 0.66,
                       'SSH': 0.25},
    'mouthDimple': {'AAA': 0.50, 'IEE': 0.37, 'FFF': 0.56, 'TTH': 0.54, 'YA_PEDAL': 0.27},
    'mouthStretch': {'AAA': 0.28, 'Eh': 0.24, 'IEE': 0.29, 'SSH': 0.11, 'YA_PEDAL': 0.37},
    'mouthUpperUp': {'AAA': 0.27, 'IEE': 0.27, 'SSH': 0.24, 'FFF': 0.11, 'TTH': 0.25},
    'mouthSmile': {'AAA': 0.20, 'Eh': 0.15, 'IEE': 0.23, 'YA_PEDAL': 0.12},
    'mouthPucker': {'OHH': 0.41, 'UUU': 0.61, 'WWW': 0.52, 'RRR': 0.27, 'SSH': 0.29,
                    'WA_PEDAL': 0.48},
    'mouthFunnel': {'UUU': 0.26, 'RRR': 0.42, 'SSS': 0.09, 'SSH': 0.44, 'TTH': 0.27},
    'mouthClose': {'WWW': 0.37, 'MBP': 0.62},
    'mouthPress': {'MBP': 0.07},
    'mouthRollLower': {'FFF': 0.24},
    'mouthShrugLower': {'FFF': 0.09},
    'cheekPuff': {'MBP': 0.10},
}

JAW_CHANNELS = ('jawOpen', 'jawForward', 'tongueOut')     # 나머지는 Lip 축


def _targets(channel):
    if channel in ARKIT_52:
        return [channel]
    return [channel + 'Left', channel + 'Right']


def _add_attr(node, name, minv, maxv, default=0.0):
    cmds.addAttr(node, ln=name, at='double', min=minv, max=maxv, dv=default, k=True)


def build(prefix=''):
    """노드를 만들고 (grp, in_node, out_node) 를 돌려준다."""
    p = prefix
    grp = cmds.createNode('transform', n=p + 'JALI_ARKit_GRP')
    in_node = cmds.createNode('transform', n=p + 'JALI_IN', p=grp)
    out_node = cmds.createNode('transform', n=p + 'ARKIT_OUT', p=grp)
    for node in (in_node, out_node):
        for ch in ('t', 'r', 's'):
            for ax in 'xyz':
                cmds.setAttr('{0}.{1}{2}'.format(node, ch, ax), k=False, cb=False)
        cmds.setAttr(node + '.v', k=False, cb=False)

    # 입력
    _add_attr(in_node, 'Jaw', 0.0, 15.0, MEASURED_JALI)
    _add_attr(in_node, 'Lip', 0.0, 15.0, MEASURED_JALI)
    for name in PHONEMES + PEDALS:
        _add_attr(in_node, name, 0.0, PHONEME_MAX)

    # 축 스케일 = Jaw / 9, Lip / 9
    scale = {}
    for axis in ('Jaw', 'Lip'):
        md = cmds.createNode('multDoubleLinear', n=p + 'md_scale' + axis)
        cmds.connectAttr(in_node + '.' + axis, md + '.input1')
        cmds.setAttr(md + '.input2', 1.0 / MEASURED_JALI)
        scale[axis] = md + '.output'

    # 출력 52개 (매핑이 없는 타겟도 만들어 둔다 -> 아바타 연결이 균일)
    for name in ARKIT_52:
        _add_attr(out_node, name, 0.0, 1.0)

    for channel, weights in MAPPING.items():
        bw = cmds.createNode('blendWeighted', n=p + 'bw_' + channel)
        for i, (src, w) in enumerate(weights.items()):
            cmds.connectAttr('{0}.{1}'.format(in_node, src), '{0}.input[{1}]'.format(bw, i))
            cmds.setAttr('{0}.weight[{1}]'.format(bw, i), w / MEASURED_PHONEME)

        md = cmds.createNode('multDoubleLinear', n=p + 'md_' + channel)
        cmds.connectAttr(bw + '.output', md + '.input1')
        cmds.connectAttr(scale['Jaw' if channel in JAW_CHANNELS else 'Lip'], md + '.input2')

        cl = cmds.createNode('clamp', n=p + 'cl_' + channel)
        cmds.setAttr(cl + '.maxR', 1.0)
        cmds.connectAttr(md + '.output', cl + '.inputR')
        for target in _targets(channel):
            cmds.connectAttr(cl + '.outputR', '{0}.{1}'.format(out_node, target))

    cmds.select(in_node)
    return grp, in_node, out_node


def _curve(name, points, parent, color, degree=1):
    crv = cmds.curve(n=name, d=degree, p=points)
    cmds.parent(crv, parent, r=True)
    shape = cmds.listRelatives(crv, s=True)[0]
    cmds.rename(shape, name + 'Shape')
    cmds.setAttr(name + 'Shape.overrideEnabled', 1)
    cmds.setAttr(name + 'Shape.overrideColor', color)
    return crv


def _text(name, label, parent, pos, rot_z, scale):
    """textCurves 로 라벨 커브를 만들고 선택 불가(reference)로 둔다."""
    tmp = cmds.textCurves(t=label, f='Arial', ch=False)[0]
    grp = cmds.group(em=True, n=name, p=parent)
    for shape in cmds.listRelatives(tmp, ad=True, type='nurbsCurve', f=True) or []:
        xf = cmds.listRelatives(shape, p=True, f=True)[0]
        cmds.parent(xf, grp)
    cmds.delete(tmp)
    cmds.xform(grp, t=pos, ro=(0, 0, rot_z), s=(scale, scale, scale))
    cmds.setAttr(grp + '.overrideEnabled', 1)
    cmds.setAttr(grp + '.overrideDisplayType', 2)
    cmds.setAttr(grp + '.overrideColor', 24)
    return grp


def build_controller(in_node='JALI_IN', prefix='', position=(0.0, 0.0, 0.0)):
    """angela 리그의 JaLi 컨트롤을 본뜬 2D 슬라이더를 만들어 JALI_IN.Jaw / Lip 에 연결한다.

    X = Jaw, Y = Lip, 범위 0~15 (안쪽 박스 0~10, 바깥 박스 0~15), 기본 (9, 9).
    """
    p = prefix
    grp = cmds.createNode('transform', n=p + 'JALI_CTL_GRP')
    cmds.xform(grp, t=position)
    border = cmds.createNode('transform', n=p + 'JaliInnerBorder', p=grp)
    box = [(0, 10, 0), (10, 10, 0), (10, 0, 0), (0, 0, 0), (0, 10, 0)]
    _curve(p + 'JaLi_box', box, border, 21)
    outer = cmds.createNode('transform', n=p + 'JaliOuterBorder', p=border)
    cmds.setAttr(outer + '.s', 1.5, 1.5, 1.5)
    _curve(p + 'JaLi_outerBox', box, outer, 21)
    for node in (border, outer):
        cmds.setAttr(node + '.overrideEnabled', 1)
        cmds.setAttr(node + '.overrideDisplayType', 2)      # reference: 클릭해도 선택되지 않게
    _text(p + 'Text_Jaw', 'Jaw', border, (2.7, -2.3, 0), 0, 1.4)
    _text(p + 'Text_Lip', 'Lip', border, (-1.0, 2.8, 0), 90, 1.4)

    # 핸들: 원(XY 평면) + tx/ty 만 키 가능, 0~15 제한
    ctl = cmds.circle(n=p + 'CNT_JaLi', nr=(0, 0, 1), r=0.94, ch=False)[0]
    cmds.parent(ctl, grp, r=True)
    cmds.rename(cmds.listRelatives(ctl, s=True)[0], p + 'CNT_JaLiShape')
    cmds.setAttr(p + 'CNT_JaLiShape.overrideEnabled', 1)
    cmds.setAttr(p + 'CNT_JaLiShape.overrideColor', 10)
    cmds.transformLimits(ctl, tx=(0, 15), ty=(0, 15), etx=(True, True), ety=(True, True))
    for attr in ('tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'):
        cmds.setAttr('{0}.{1}'.format(ctl, attr), l=True, k=False, cb=False)
    cmds.setAttr(ctl + '.tx', MEASURED_JALI)
    cmds.setAttr(ctl + '.ty', MEASURED_JALI)

    cmds.connectAttr(ctl + '.tx', in_node + '.Jaw', f=True)
    cmds.connectAttr(ctl + '.ty', in_node + '.Lip', f=True)
    cmds.select(ctl)
    return grp, ctl


def connect_rig(in_node='JALI_IN', namespace=''):
    """angela 리그 컨트롤 -> JALI_IN 연결 (리그와 같은 씬에 있을 때)."""
    ns = namespace + ':' if namespace and not namespace.endswith(':') else namespace
    pairs = [(ns + 'CNT_JaLi.translateX', 'Jaw'), (ns + 'CNT_JaLi.translateY', 'Lip')]
    pairs += [(ns + 'CNT_PHONEMES.' + n, n) for n in PHONEMES]
    pairs += [(ns + 'CNT_COARTIC.' + n, n) for n in PEDALS]
    for src, dst in pairs:
        if cmds.objExists(src):
            cmds.connectAttr(src, '{0}.{1}'.format(in_node, dst), f=True)


def connect_blendshape(blendshape, out_node='ARKIT_OUT'):
    """ARKIT_OUT -> 아바타 blendShape (같은 이름의 타겟만). 연결한 개수를 돌려준다."""
    count = 0
    for name in ARKIT_52:
        dst = '{0}.{1}'.format(blendshape, name)
        if cmds.objExists(dst):
            cmds.connectAttr('{0}.{1}'.format(out_node, name), dst, f=True)
            count += 1
    return count


def _main(argv):
    import maya.standalone
    maya.standalone.initialize(name='python')
    try:
        # --ctl : 기존 jali_arkit_mapping.ma 를 열어 노드는 그대로 두고 컨트롤러만 더해 _ctl.ma 로 저장
        ctl_mode = '--ctl' in argv
        args = [a for a in argv[1:] if a != '--ctl']
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out')
        base = os.path.abspath(os.path.join(out_dir, 'jali_arkit_mapping.ma'))
        default = base.replace('.ma', '_ctl.ma') if ctl_mode else base
        out = os.path.abspath(args[0] if args else default)
        if not os.path.isdir(os.path.dirname(out)):
            os.makedirs(os.path.dirname(out))
        if ctl_mode:
            cmds.file(base, open=True, force=True)
            build_controller()
        else:
            cmds.file(new=True, force=True)
            build()
        cmds.file(rename=out)
        cmds.file(save=True, type='mayaAscii')
        print('Saved: ' + out)
    finally:
        maya.standalone.uninitialize()


if __name__ == '__main__':
    _main(sys.argv)
