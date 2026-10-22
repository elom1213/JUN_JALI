# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# [JUN_JALI] build_mh_jali_dummy.py 결과 검증 (docs/0110_jali_mh_dummy_plan.md §8 T1~T9)
# 사용: mayapy check_mh_jali_dummy.py <0010_sample_0050.mb> [A0020_jali_slider_ctl.ma]
#   T1 더미 이름 · 어트리뷰트 · 순서 · 범위 (A00540 jali_slider_dummy_in.json / A0020 와 동일)
#   T2 입력 하나 = 1.0 -> CTRL_expressions 변화량 == 예측(경유 + 직접, 0.01)   T3 Jaw / Lip / weight 배율
#   T5 동시조음 턱 비례   T6 dmy_out 연동   T7 ARKit 경로 회귀 · 손 조작 자유   T8 머티리얼 · 리그 노드 · 순환   T9 A0020 연결
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds

import build_mh_arkit_dummy as A
import build_mh_jali_dummy as B
import build_jali_arkit_node as J

TOL = 0.01
results = []
X = A.EXPR


def check(name, cond):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name)


def reset():
    for k in A.ARKIT_52:
        cmds.setAttr('%s.%s' % (A.IN_NODE, k), 0.0)
    for a in B.PHONEMES:
        cmds.setAttr('%s.%s' % (B.NODE_PH, a), 0.0)
    for a in B.COARTIC:
        cmds.setAttr('%s.%s' % (B.NODE_CO, a), 0.0)
    cmds.setAttr(B.NODE_JALI + '.Jaw', B.JALI_DEFAULT)
    cmds.setAttr(B.NODE_JALI + '.Lip', B.JALI_DEFAULT)
    cmds.setAttr(B.NODE_JALI + '.' + B.WEIGHT, 1.0)


def predict(inputs, jaw=B.JALI_DEFAULT, lip=B.JALI_DEFAULT, weight=1.0):
    """inputs = {'PH.AAA': v, 'CO.MMM': v, ...} -> {expr: value} (경유 + 직접, SDK 끝값 1 로 clamp)."""
    sj, sl = jaw / B.JALI_DEFAULT * weight, lip / B.JALI_DEFAULT * weight
    arkit = {}
    for channel, weights in J.MAPPING.items():
        v = 0.0
        for src, w in weights.items():
            key = ('CO.' if src in J.PEDALS else 'PH.') + src
            v += inputs.get(key, 0.0) * w / B.PHONEME_UNIT
        v *= sj if channel in J.JAW_CHANNELS else sl
        v = max(0.0, min(1.0, v))
        for t in J._targets(channel):
            arkit[t] = v
    axis = {}
    for t, v in arkit.items():
        for ctl, ax, w, expr in A.ARKIT_TO_CTRL[t]:
            axis[(ctl, ax)] = axis.get((ctl, ax), 0.0) + v * w
    jaw_open = max(0.0, min(1.0, axis.get(('CTRL_C_jaw', 'y'), 0.0)))
    for attr, (ax_name, jaw_factor, weights) in B.DIRECT.items():
        v = sum(inputs.get(k, 0.0) * w / B.PHONEME_UNIT for k, w in weights.items())
        v *= sj if ax_name == 'Jaw' else sl
        if jaw_factor:
            v *= jaw_open
        v = max(0.0, min(1.0, v))
        for ctl, ax, sign in B.DIRECT_TO_CTRL[attr]:
            axis[(ctl, ax)] = axis.get((ctl, ax), 0.0) + v * sign
    # 축값 -> expression: 양방향 축은 +쪽 / -쪽 expression 이 각각, 선형, 0~1 끝값
    expr = {}
    for (ctl, ax), v in axis.items():
        for e, (c2, a2, s, _keys) in EXPR_SIGN.items():
            if c2 == ctl and a2 == A.AXIS_ATTR[ax]:
                val = v * s
                if val > 0:
                    expr[e] = min(1.0, val)
    return expr


def load_expr_sign():
    """CTRL_expressions attr -> (ctrl, axis attr, sign) — ARKIT_TO_CTRL 에서 역으로 (여기에 없는 expression 은 SDK 에서 직접 읽는다)."""
    out = {}
    for rows in A.ARKIT_TO_CTRL.values():
        for ctl, ax, w, e in rows:
            out[e] = (ctl, A.AXIS_ATTR[ax], 1.0 if w > 0 else -1.0, None)
    # 직접 경로가 쓰는 expression (ARKit 표에 없는 것): SDK 곡선에서 부호를 읽는다
    for attr, rows in B.DIRECT_TO_CTRL.items():
        for ctl, ax, _sign in rows:
            plug = '%s.%s' % (A._ctrl_path(ctl), A.AXIS_ATTR[ax])
            pma = A.axis_nodes(ctl, ax)[1]
            src_plug = pma + '.output1D' if cmds.objExists(pma) else plug
            for cu in cmds.listConnections(src_plug, s=False, d=True, type='animCurveUU', skipConversionNodes=True) or []:
                dst = cmds.listConnections(cu + '.output', s=False, d=True, p=True, skipConversionNodes=True) or []
                if not dst or not dst[0].startswith('CTRL_expressions.'):
                    continue
                e = dst[0].split('.')[1]
                keys = cmds.keyframe(cu, q=True, fc=True) or []
                s = 1.0 if max(keys) > 0 else -1.0
                out.setdefault(e, (ctl, A.AXIS_ATTR[ax], s, keys))
    return out


def main(path, a0020=None):
    global EXPR_SIGN
    cmds.file(path, open=True, force=True, ignoreVersion=True)
    EXPR_SIGN = load_expr_sign()
    all_expr = cmds.listAttr(X, userDefined=True)
    # ---- T1
    check('T1 %s attrs == A0020 PHONEMES (%d, same order)' % (B.NODE_PH, len(B.PHONEMES)), cmds.listAttr(B.NODE_PH, userDefined=True) == B.PHONEMES)
    check('T1 %s attrs == A0020 COARTIC (%d)' % (B.NODE_CO, len(B.COARTIC)), cmds.listAttr(B.NODE_CO, userDefined=True) == B.COARTIC)
    check('T1 %s attrs == Jaw Lip weight' % B.NODE_JALI, cmds.listAttr(B.NODE_JALI, userDefined=True) == ['Jaw', 'Lip', B.WEIGHT])
    check('T1 Jaw / Lip default %.1f, ranges 0..1' % B.JALI_DEFAULT,
          abs(cmds.addAttr(B.NODE_JALI + '.Jaw', q=True, defaultValue=True) - B.JALI_DEFAULT) < 1e-6
          and all(cmds.attributeQuery(a, node=B.NODE_PH, maximum=True) == [1.0] for a in B.PHONEMES)
          and all(cmds.attributeQuery(a, node=B.NODE_CO, maximum=True) == [1.0] for a in B.COARTIC))
    cmds.setAttr('CTRL_lookAtSwitch.translateY', 0)
    reset()
    base = {e: cmds.getAttr('%s.%s' % (X, e)) for e in all_expr}
    # ---- T2 (경유 + 직접 예측과 비교)
    cases = [('PH.' + p, {'PH.' + p: 1.0}) for p in B.PHONEMES] + [('CO.' + c, {'CO.' + c: 1.0}) for c in B.COARTIC]
    cases += [('PH.AAA + CO.MMM', {'PH.AAA': 1.0, 'CO.MMM': 1.0}), ('PH.AAA + CO.FFF', {'PH.AAA': 1.0, 'CO.FFF': 1.0}),
              ('PH.OHH + CO.WA_PEDAL', {'PH.OHH': 1.0, 'CO.WA_PEDAL': 1.0})]
    bad = []
    for label, inputs in cases:
        reset()
        for k, v in inputs.items():
            cmds.setAttr(B._src_plug(k), v)
        exp = predict(inputs)
        for e in all_expr:
            d = cmds.getAttr('%s.%s' % (X, e)) - base[e]
            if abs(d - exp.get(e, 0.0)) > TOL:
                bad.append('%s: %s=%.3f (predicted %.3f)' % (label, e, d, exp.get(e, 0.0)))
    check('T2 %d inputs reproduce the predicted via + direct values on all %d expressions (%.2f)' % (len(cases), len(all_expr), TOL), not bad)
    for b in bad[:25]:
        print('     ', b)
    # 대표값 몇 개를 수치로 (문서 §12 기록용)
    reset(); cmds.setAttr(B.NODE_PH + '.MBP', 1.0)
    print('INFO MBP=1: lipsTogetherUL %.3f jawOpen %.3f' % (cmds.getAttr(X + '.mouthLipsTogetherUL'), cmds.getAttr(X + '.jawOpen')))
    reset(); cmds.setAttr(B.NODE_PH + '.LNTD', 1.0)
    print('INFO LNTD=1: tongueTipUp %.3f tongueUp %.3f jawOpen %.3f' % (cmds.getAttr(X + '.tongueTipUp'), cmds.getAttr(X + '.tongueUp'), cmds.getAttr(X + '.jawOpen')))
    reset(); cmds.setAttr(B.NODE_PH + '.GK', 1.0)
    print('INFO GK=1: tongueBendUp %.3f tongueTipDown %.3f' % (cmds.getAttr(X + '.tongueBendUp'), cmds.getAttr(X + '.tongueTipDown')))
    reset(); cmds.setAttr(B.NODE_PH + '.FFF', 1.0)
    print('INFO FFF=1: mouthLowerLipBiteL %.3f mouthLowerLipRollInL %.3f mouthDimpleL %.3f' % (cmds.getAttr(X + '.mouthLowerLipBiteL'), cmds.getAttr(X + '.mouthLowerLipRollInL'), cmds.getAttr(X + '.mouthDimpleL')))
    # ---- T3 배율
    reset(); cmds.setAttr(B.NODE_PH + '.AHH', 1.0)
    full_jaw, full_lip = cmds.getAttr(X + '.jawOpen'), cmds.getAttr(X + '.mouthLowerLipDepressL')
    cmds.setAttr(B.NODE_JALI + '.Jaw', 0.3)
    half_jaw, lip_same = cmds.getAttr(X + '.jawOpen'), cmds.getAttr(X + '.mouthLowerLipDepressL')
    cmds.setAttr(B.NODE_JALI + '.Jaw', B.JALI_DEFAULT); cmds.setAttr(B.NODE_JALI + '.Lip', 0.3)
    jaw_same, half_lip = cmds.getAttr(X + '.jawOpen'), cmds.getAttr(X + '.mouthLowerLipDepressL')
    cmds.setAttr(B.NODE_JALI + '.Lip', B.JALI_DEFAULT); cmds.setAttr(B.NODE_JALI + '.' + B.WEIGHT, 0.0)
    w0 = max(abs(cmds.getAttr('%s.%s' % (X, e)) - base[e]) for e in all_expr)
    check('T3 Jaw 0.3 halves jawOpen (%.2f -> %.2f), lips unchanged' % (full_jaw, half_jaw), abs(half_jaw - full_jaw / 2) < TOL and abs(lip_same - full_lip) < TOL)
    check('T3 Lip 0.3 halves lips (%.2f -> %.2f), jaw unchanged' % (full_lip, half_lip), abs(half_lip - full_lip / 2) < TOL and abs(jaw_same - full_jaw) < TOL)
    check('T3 weight 0 -> no change (max delta %.3f)' % w0, w0 < TOL)
    # ---- T5 동시조음 턱 비례
    reset(); cmds.setAttr(B.NODE_CO + '.MMM', 1.0)
    alone = cmds.getAttr(X + '.mouthLipsTogetherUL') - base['mouthLipsTogetherUL']
    cmds.setAttr(B.NODE_PH + '.AAA', 1.0)
    with_aaa = cmds.getAttr(X + '.mouthLipsTogetherUL') - base['mouthLipsTogetherUL']
    jaw_aaa = cmds.getAttr(X + '.jawOpen')
    check('T5 COARTIC.MMM alone -> lipsTogether 0 (%.3f); with AAA -> 0.80 x jawOpen %.2f = %.3f (got %.3f)' % (alone, jaw_aaa, 0.8 * jaw_aaa, with_aaa),
          abs(alone) < TOL and abs(with_aaa - 0.8 * jaw_aaa) < TOL)
    reset(); cmds.setAttr(B.NODE_CO + '.LNTD', 1.0)
    check('T5 COARTIC.LNTD -> tongueTipUp 1.0 (got %.3f)' % cmds.getAttr(X + '.tongueTipUp'), abs(cmds.getAttr(X + '.tongueTipUp') - 1.0) < TOL)
    # ---- T6 dmy_out 연동
    reset(); cmds.setAttr(B.NODE_PH + '.MBP', 1.0)
    mc, jo = cmds.getAttr(A.OUT_NODE + '.mouthClose'), cmds.getAttr(A.OUT_NODE + '.jawOpen')
    check('T6 MBP=1 -> dmy_out.mouthClose 0.62 (%.3f), jawOpen 0.43 (%.3f)' % (mc, jo), abs(mc - 0.62) < TOL and abs(jo - 0.43) < TOL)
    # ---- T7 ARKit 경로 회귀 · 손 조작
    reset(); cmds.setAttr(A.IN_NODE + '.jawOpen', 1.0); cmds.setAttr(A.IN_NODE + '.mouthFunnel', 1.0)
    check('T7 dmy_in.jawOpen / mouthFunnel = 1 still reach 1.0', abs(cmds.getAttr(X + '.jawOpen') - 1) < TOL and abs(cmds.getAttr(X + '.mouthFunnelUL') - 1) < TOL)
    reset()
    axes = list(A.used_controllers().keys()) + [(c, ax) for rows in B.DIRECT_TO_CTRL.values() for c, ax, _s in rows]
    driven = sorted({c for c, ax in axes if cmds.listConnections('%s.%s' % (A._ctrl_path(c), A.AXIS_ATTR[ax]), s=True, d=False)})
    check('T7 no mapped controller axis is driven (hand control free)', not driven)
    tip = A._ctrl_path('CTRL_C_tongue_tipMove')
    cmds.setAttr(tip + '.translateY', 0.3); cmds.setAttr(B.NODE_PH + '.LNTD', 1.0)
    v = cmds.getAttr(X + '.tongueTipUp')
    cmds.setAttr(tip + '.translateY', 0.0); reset()
    check('T7 hand 0.3 + LNTD 0.61 -> tongueTipUp 0.91 (got %.3f)' % v, abs(v - 0.91) < TOL)
    grp = cmds.ls('GRP_dmy_CTRL_C_tongue_tipMove')
    check('T7 GRP_dmy_CTRL_C_tongue_tipMove exists and tipMove is its child', bool(grp) and cmds.listRelatives(tip, parent=True)[0] == 'GRP_dmy_CTRL_C_tongue_tipMove')
    # ---- T8
    sg = A.MAPPED_SHADER + 'SG'
    n_map = len(cmds.sets(sg, q=True) or []); n_yel = len(cmds.sets('GUI2D_yellow_shaderSG', q=True) or []); n_org = len(cmds.sets('GUI2D_orange_shaderSG', q=True) or [])
    check('T8 shader members mapped 72 / yellow 92 / orange 15 (got %d / %d / %d)' % (n_map, n_yel, n_org), (n_map, n_yel, n_org) == (72, 92, 15))
    counts = {t: len(cmds.ls(type=t) or []) for t in ('embeddedNodeRL4', 'joint', 'mesh', 'unknown')}
    check('T8 rig nodes preserved %s' % counts, counts == {'embeddedNodeRL4': 2, 'joint': 1212, 'mesh': 520, 'unknown': 101})
    new = {p: len(cmds.ls(p + '*') or []) for p in ('jali_bw_', 'jali_md_', 'jali_cl_', 'jali_mdjaw_', 'bw_dmy_', 'pma_dmy_', 'GRP_dmy_')}
    print('INFO node counts new:', new)
    try:
        cyc = cmds.cycleCheck(all=True)
        check('T8 cycleCheck -all -> %s' % cyc, not cyc)
    except Exception as exc:  # pragma: no cover
        print('INFO cycleCheck not available:', exc)
    # ---- T9 A0020
    if a0020 and os.path.isfile(a0020):
        cmds.file(a0020, reference=True, namespace='JALI', ignoreVersion=True)
        reset()
        n = B.connect_a0020('JALI')      # 이제 DUMMY_IN_* 은 연결됨 - 값은 A0020 슬라이더로 넣는다 (기본 0, JaLi 박스 0.6)
        cmds.setAttr('JALI:CTL_PH_MBP.translateY', 10.0 / 12.0)
        v = cmds.getAttr(X + '.mouthLipsTogetherUL') - base['mouthLipsTogetherUL']
        check('T9 A0020 referenced, %d connections; CTL_PH_MBP.ty 10/12 -> lipsTogether 0.62 (got %.3f)' % (n, v), n == 24 and abs(v - 0.62) < TOL)
        jaw = cmds.getAttr(B.NODE_JALI + '.Jaw')
        check('T9 A0020 DUMMY_OUT_JALI.Jaw 9 -> DUMMY_IN_JALI.Jaw 0.6 (got %.3f)' % jaw, abs(jaw - 0.6) < TOL)
    else:
        print('SKIP T9 (A0020 file not given / not found)')
    n_fail = results.count(False)
    print('RESULT', 'OK' if not n_fail else '%d FAILED' % n_fail)
    return 0 if not n_fail else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
