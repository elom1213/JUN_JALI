# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# [JUN_JALI] build_mh_arkit_dummy.py 결과 검증 (docs/0100_mh_arkit_dummy_plan.md §8 T1~T7)
# 사용: mayapy check_mh_arkit_dummy.py <0010_sample_0040.mb>
#   T1 더미 어트리뷰트 집합 · 순서   T2 dmy_in.k = 1 -> CTRL_expressions 가 Epic 포즈와 같다(오차 0.01)
#   T3 왕복 dmy_out.k == 1, 다른 출력은 예측된 교차값   T4 손 조작 + 입력 합산, 컨트롤러 축은 연결되지 않은 상태
#   T5 시각 오프셋 그룹이 움직인다   T7 시안 머티리얼 멤버 = 쓰이는 컨트롤러 쉐입
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds

import build_mh_arkit_dummy as B

TOL = 0.01
results = []


def check(name, cond):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name)


def set_all_in(value):
    for k in B.ARKIT_52:
        cmds.setAttr('%s.%s' % (B.IN_NODE, k), value)


def expected_expr(k):
    """dmy_in.k = 1 일 때 CTRL_expressions 기대값 {expr: value}."""
    out = {}
    for _ctl, _ax, w, expr in B.ARKIT_TO_CTRL[k]:
        out[expr] = out.get(expr, 0.0) + abs(w)
    return out


def predicted_out(expr_values):
    """CTRL_expressions 값 -> dmy_out 예측 (OUT_FROM_EXPR, 합이 1 을 넘으면 clamp)."""
    pred = {}
    for k in B.ARKIT_52:
        s = sum(expr_values.get(e, 0.0) * w for e, w in B.OUT_FROM_EXPR[k])
        pred[k] = max(0.0, min(1.0, s))
    return pred


def main(path):
    cmds.file(path, open=True, force=True, ignoreVersion=True)
    X = B.EXPR
    # ---- T1
    for node, limited in ((B.IN_NODE, True), (B.OUT_NODE, False)):
        attrs = cmds.listAttr(node, userDefined=True) or []
        check('T1 %s attributes == ARKit 52 in order' % node, attrs == B.ARKIT_52)
        if limited:
            check('T1 %s range 0..1' % node, all(cmds.attributeQuery(a, node=node, maximum=True) == [1.0] for a in attrs))
    # lookAtSwitch off (UI eye mode) for T2/T3
    cmds.setAttr('CTRL_lookAtSwitch.translateY', 0)
    check('T0 lookAtSwitch == 0 (UI eye mode)', abs(cmds.getAttr(X + '.lookAtSwitch')) < 1e-6)
    all_expr = cmds.listAttr(X, userDefined=True)
    # ---- T2 / T3
    set_all_in(0.0)
    base = {e: cmds.getAttr('%s.%s' % (X, e)) for e in all_expr}
    rest_on = sorted(e for e, v in base.items() if abs(v) > TOL)
    print('INFO expressions non-zero at rest (file default, compared as delta):', rest_on)
    bad2, bad3 = [], []
    for k in B.ARKIT_52:
        set_all_in(0.0)
        cmds.setAttr('%s.%s' % (B.IN_NODE, k), 1.0)
        exp = expected_expr(k)
        vals = {e: cmds.getAttr('%s.%s' % (X, e)) for e in all_expr}
        for e in all_expr:
            delta = vals[e] - base[e]
            if abs(delta - exp.get(e, 0.0)) > TOL:
                bad2.append('%s: %s=%.3f (expected %.3f)' % (k, e, delta, exp.get(e, 0.0)))
        outs = {j: cmds.getAttr('%s.%s' % (B.OUT_NODE, j)) for j in B.ARKIT_52}
        pred = predicted_out(vals)
        if abs(outs[k] - 1.0) > TOL:
            bad3.append('%s: dmy_out.%s=%.3f (expected 1)' % (k, k, outs[k]))
        for j in B.ARKIT_52:
            if abs(outs[j] - pred[j]) > TOL:
                bad3.append('%s: dmy_out.%s=%.3f (predicted %.3f)' % (k, j, outs[j], pred[j]))
    check('T2 dmy_in.k = 1 reproduces the Epic pose for all 52 as a delta from rest (within %.2f)' % TOL, not bad2)
    for b in bad2[:20]:
        print('     ', b)
    check('T3 round trip dmy_out.k == 1 and other outputs == predicted cross values', not bad3)
    for b in bad3[:20]:
        print('     ', b)
    # cross-talk report (informational)
    cross = []
    for k in B.ARKIT_52:
        pred = predicted_out(expected_expr(k))
        for j in B.ARKIT_52:
            if j != k and pred[j] > 0.0:
                cross.append('%s -> %s %.3f' % (k, j, pred[j]))
    print('INFO cross-talk:', '; '.join(cross))
    set_all_in(0.0)
    # ---- T4
    ctl = B._ctrl_path('CTRL_L_mouth_funnelU')
    cmds.setAttr(ctl + '.translateY', 0.4)
    cmds.setAttr(B.IN_NODE + '.mouthFunnel', 0.4)
    v1 = cmds.getAttr(X + '.mouthFunnelUL')
    cmds.setAttr(ctl + '.translateY', 0.5)
    cmds.setAttr(B.IN_NODE + '.mouthFunnel', 1.0)
    v2 = cmds.getAttr(X + '.mouthFunnelUL')
    cmds.setAttr(ctl + '.translateY', 0.0)
    set_all_in(0.0)
    check('T4 hand 0.4 + input 0.4 -> 0.8 (got %.3f)' % v1, abs(v1 - 0.8) < TOL)
    check('T4 hand 0.5 + input 1.0 -> 1.0 end value (got %.3f)' % v2, abs(v2 - 1.0) < TOL)
    driven = [c for (c, ax), _ in B.used_controllers().items()
              if cmds.listConnections('%s.%s' % (B._ctrl_path(c), B.AXIS_ATTR[ax]), source=True, destination=False)]
    check('T4 no mapped controller axis is driven (hand control free)', not driven)
    # ---- T5
    jaw = B._ctrl_path('CTRL_C_jaw')
    grp = cmds.ls('GRP_dmy_CTRL_C_jaw', long=True)
    if grp:
        y0 = cmds.xform(jaw, query=True, worldSpace=True, translation=True)[1]
        cmds.setAttr(B.IN_NODE + '.jawOpen', 1.0)
        y1 = cmds.xform(jaw, query=True, worldSpace=True, translation=True)[1]
        gy = cmds.getAttr(grp[0] + '.translateY')
        cmds.setAttr(B.IN_NODE + '.jawLeft', 1.0)
        gx = cmds.getAttr(grp[0] + '.translateX')
        set_all_in(0.0)
        check('T5 jawOpen 1 -> GRP_dmy_CTRL_C_jaw.ty == 1 (got %.3f) and controller moved in world (%.3f)' % (gy, y1 - y0),
              abs(gy - 1.0) < TOL and abs(y1 - y0) > 1e-4)
        check('T5 jawLeft 1 -> GRP_dmy_CTRL_C_jaw.tx == -1 (got %.3f)' % gx, abs(gx + 1.0) < TOL)
        check('T5 controller stays a child of its GRP_dmy', cmds.listRelatives(jaw, parent=True)[0] == 'GRP_dmy_CTRL_C_jaw')
    else:
        print('SKIP T5 (built with --no-visual)')
    # ---- T7
    sg = B.MAPPED_SHADER + 'SG'
    members = set(cmds.ls(cmds.sets(sg, query=True) or [], long=True))
    expected = set()
    for ctl in sorted({c for c, _ax in B.used_controllers()}):
        for s in cmds.listRelatives(B._ctrl_path(ctl), shapes=True, noIntermediate=True, fullPath=True) or []:
            expected.add(s)
    check('T7 mapped shader members == used controller shapes (%d)' % len(expected), members == expected and len(expected) >= 64)
    col = cmds.getAttr(B.MAPPED_SHADER + '.color')[0]
    check('T7 mapped shader color %s' % (tuple(round(c, 2) for c in col),), tuple(round(c, 2) for c in col) == tuple(round(c, 2) for c in B.MAPPED_COLOR))
    n_yellow = len(cmds.sets('GUI2D_yellow_shaderSG', query=True) or []) if cmds.objExists('GUI2D_yellow_shaderSG') else -1
    n_orange = len(cmds.sets('GUI2D_orange_shaderSG', query=True) or []) if cmds.objExists('GUI2D_orange_shaderSG') else -1
    print('INFO shader members: yellow %d, orange %d, mapped %d' % (n_yellow, n_orange, len(members)))
    # ---- INFO node counts (compare with the original: embeddedNodeRL4 2, joint 1212, mesh 520, unknown 101)
    counts = {t: len(cmds.ls(type=t) or []) for t in ('embeddedNodeRL4', 'joint', 'mesh', 'unknown')}
    new = {p: len(cmds.ls(p + '*') or []) for p in ('bw_dmy_', 'pma_dmy_', 'GRP_dmy_', 'bw_out_', 'cl_out_')}
    print('INFO node counts:', counts, 'new:', new)
    check('T8 rig nodes preserved (embeddedNodeRL4 2, joints 1212, meshes 520, unknown 101)',
          counts == {'embeddedNodeRL4': 2, 'joint': 1212, 'mesh': 520, 'unknown': 101})
    # ---- summary
    n_fail = results.count(False)
    print('RESULT', 'OK' if not n_fail else '%d FAILED' % n_fail)
    return 0 if not n_fail else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
