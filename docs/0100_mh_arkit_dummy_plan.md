# 메타휴먼 페이셜 ↔ ARKit 52 ↔ JALI 더미 노드 에셋 — 제작 계획서

> **작성** 2026-10-22 · 상태: **계획 (사용자 확인 대기, §9)** · 대상 Maya 2024 (mayapy 로 생성 · 검증)
> 원본: `C:\Users\USER\Desktop\JP\0035_maya_src_rig\07_MH_sample_02\0010_sample_0030.mb` 의 `|rig|head_grp|headRig_grp`
> 결과물(안): 같은 폴더 `0010_sample_0040.mb` (0030 을 열어 더미 노드 · 매핑 노드망 · 머티리얼을 더해 다른 이름으로 저장)
> 참고: `C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\MetaHuman\MetaHumanCharacter\Content\Face\ARKit\{PA,AS}_MetaHuman_ARKit_Mapping.uasset`,
> `07_MH_sample_02\ARKit_Mapping\AS_MetaHuman_ARKit_Mapping*.FBX`, [0040 JALI ↔ ARKit 매칭](0040_jali_arkit_mapping.md),
> `examples/build_jali_arkit_node.py`(JALI → ARKit 노드망), [0090 슬라이더 계획](0090_jali_slider_ctl_plan.md)(더미 입력이 컨트롤러를 미는 방식 D3)

---

## 0. 요청 정리

| # | 요청 (원문 요지) | 이 계획 |
|---|------------------|---------|
| R1 | `headRig_grp` 을 참고한 새 마야 에셋. 생성 전에 계획서 | 이 문서. 생성은 §10 단계 |
| R2 | `dmy_in` → 매핑 노드(`blendWeighted` 등) → **headRig_grp 에서 조절할 수 있는 컨트롤러** → 매핑 노드 → `dmy_out` | §5 노드망 (D2 · D3) |
| R3 | `dmy_in` · `dmy_out` 은 **ARKit 52** 어트리뷰트 | §2 · §3 매핑표, §5.1 |
| R4 | 메타휴먼 컨트롤러가 `dmy_in` · `dmy_out` 의 ARKit 52 와 어떻게 매핑되는 것이 좋은지 제시 | §2 (입력) · §3 (출력) |
| R5 | **JALI 음소 이름만 가진 더미 노드**도 만든다 — 매핑표 · 제작 계획 포함 | §4, §5.5 |
| R6 | UE 5.7 `…\Face\ARKit\` 의 파일과 `ARKit_Mapping\*.FBX` 를 메타휴먼 ↔ ARKit 관계의 근거로 쓴다 | §1.3 실측 — 표 §2 의 모든 수치가 이 파일에서 나왔다 |
| R7 | 매핑에 쓰이는 컨트롤러만 **머티리얼을 바꿔 다른 색**으로, 안 쓰는 것은 그대로 | §6 |
| R8 | 컨트롤러 쉐입은 커브가 아니라 **메시**(`CTRL_L_nose` 등) | §1.1 실측으로 확인 — 머티리얼 교체는 메시 셰이딩 그룹 재배정(§6) |

---

## 1. 실측 — 참고 자료에서 읽은 것 (2026-10-22, mayapy 2024 · 스크립트로 전수 조사)

### 1.1 `0010_sample_0030.mb` 의 `headRig_grp`

```
|rig|head_grp|headRig_grp
   headRigging_grp/eyesSetup_grp        LOC_C_eyeDriver → LOC_L/R_eyeUIDriver · LOC_L/R_eyeAimDriver · LOC_L/R_eyeDriver (orientConstraint, lookAtSwitch)
   headGui_grp/GRP_faceGUI/CTRL_faceGUI/FRM_faceGUI
        FRM_<name>  (검은 틀 메시)
           CTRL_<name>  (노란 · 주황 메시 컨트롤러, 자식 트랜스폼 없음)
        CTRL_expressions  (메시, 사용자 어트리뷰트 252개 → head_rl4Embedded.inputs[0..250])
        FRM_WMmultipliers (주름 마스크 가중치 → shader_head.maskWeight_*)
   headGui_grp/GRP_C_eyesAim/CTRL_C_eyesAim (+ CTRL_L/R_eyeAim)
```

- 트랜스폼 457개, 메시 412개, 커브 4개. **컨트롤러(`CTRL_*`) 쉐입은 전부 `mesh`** (R8 확인). 셰이딩: `GUI2D_yellow_shader`(lambert, 1,1,0 — 160 멤버)
  · `GUI2D_orange_shader`(1, 0.583, 0 — 19 멤버, 스위치 · 보조 컨트롤러) · `GUI2D_black_shader`(틀 · 글자 230 멤버) · `GUIAnalog_yellow/red_shader`(eyeAim).
- 컨트롤러 규칙: **열린 축만 `translateX/Y`**, 트랜스폼 제한 `ty 0~1`(한 방향) 또는 `−1~1`(양방향), `tx 0` 고정 또는 `−1~1`(2D 패드). 다른 채널은 잠김.
- 값 경로: `CTRL_<name>.ty` → `unitConversion` → **`animCurveUU`(SDK, 선형 `[0,0]→[1,1]` 또는 `[−1,1]→[0,0]`)** → `CTRL_expressions.<expr>`(0~1)
  → `head_rl4Embedded.inputs[i]`(RigLogic). 양방향 축은 곡선 두 개가 +쪽 · −쪽을 각각 받는다 (예 `CTRL_C_mouth.tx` : +1 → `mouthLeft`, −1 → `mouthRight`).
  SDK 곡선은 전부 pre/post infinity = constant 이므로 입력이 범위를 넘어도 끝값(0 또는 1)을 유지한다 — **별도 clamp 없이 안전**.
- 예외 경로: 눈 `CTRL_L/R_eye.tx/ty` 와 `CTRL_C_eye` 는 각도(±40°/−30°)로 바뀌어 `blendWeighted1~4` → `LOC_*_eyeUIDriver.rotate` → (orientConstraint, `CTRL_expressions.lookAtSwitch`
  0 = UI 모드) → `LOC_*_eyeDriver.rotate` → SDK → `eyeLook{Up,Down,Left,Right}{L,R}`. `lookAtSwitch = 1`(에임 모드)이면 GUI 눈 컨트롤러는 무시된다.
- `CTRL_expressions` 252개는 전부 GUI 컨트롤러가 직접 민다(고아 없음). 기존 `blendWeighted` 4개 · `multiplyDivide` 8개 · `plusMinusAverage` 2개는 눈 · 목 보정용이라 이번 노드망과 이름이 겹치지 않게 접두사를 둔다(§5.6).
- 양방향 컨트롤러의 부호 (이번 매핑에 쓰이는 것만, 전체는 생성 스크립트 상수표):

| 컨트롤러.축 | +1 | −1 |
|-------------|----|----|
| `CTRL_C_jaw.tx` | `jawRight` | `jawLeft` |
| `CTRL_C_jaw_fwdBack.ty` | `jawBack` | `jawFwd` |
| `CTRL_C_mouth.tx` | `mouthLeft` | `mouthRight` |
| `CTRL_L/R_eye_blink.ty` | `eyeBlinkL/R` | `eyeWidenL/R` |
| `CTRL_L/R_nose.ty` | `noseWrinkleL/R` | `noseNostrilDepressL/R` |
| `CTRL_C_tongue_inOut.ty` | `tongueIn` | `tongueOut` |
| `CTRL_C_tongue_move.ty` | `tongueUp` | `tongueDown` |
| `CTRL_C_tongue_wideNarrow.ty` | `tongueWide` | `tongueNarrow` |
| `CTRL_L_eye.tx` / `.ty` | `eyeLookLeftL`(= ARKit `eyeLookOutLeft`) / `eyeLookUpL` | `eyeLookRightL`(= `eyeLookInLeft`) / `eyeLookDownL` |
| `CTRL_R_eye.tx` / `.ty` | `eyeLookLeftR`(= `eyeLookInRight`) / `eyeLookUpR` | `eyeLookRightR`(= `eyeLookOutRight`) / `eyeLookDownR` |

### 1.2 ARKit 52 의 이름 · 순서

Apple 표준 순서(`build_jali_arkit_node.py` 의 `ARKIT_52`, UE LiveLink 과 같음): `eyeBlinkLeft … eyeWideLeft`(7) · 오른쪽 7 · `jawForward jawLeft jawRight jawOpen` ·
`mouthClose mouthFunnel mouthPucker mouthLeft mouthRight mouthSmileL/R mouthFrownL/R mouthDimpleL/R mouthStretchL/R mouthRollLower mouthRollUpper mouthShrugLower
mouthShrugUpper mouthPressL/R mouthLowerDownL/R mouthUpperUpL/R` · `browDownL/R browInnerUp browOuterUpL/R` · `cheekPuff cheekSquintL/R` · `noseSneerL/R` · `tongueOut`.
더미 노드 어트리뷰트 이름은 이 철자 그대로(소문자 시작 camelCase, `Left/Right` 풀네임) — ARKit 커브 · A00320 · A0010 `ARKIT_OUT` 과 이름 매칭이 바로 된다.

### 1.3 Epic 의 메타휴먼 ↔ ARKit 매핑 파일 해석

| 파일 | 내용 | 읽은 방법 |
|------|------|----------|
| `PA_MetaHuman_ARKit_Mapping.uasset` (PoseAsset) | 포즈 이름 배열 = ARKit 이름 **51개** (Apple 순서에서 **`MouthClose` 만 없음**). 각 포즈가 `AS_` 의 한 프레임을 가리킨다 | 이름 테이블 + FName 배열을 바이너리에서 직접 읽음 |
| `AS_MetaHuman_ARKit_Mapping.uasset` (AnimSequence) | 커브 `CTRL_expressions_*`(메타휴먼 컨트롤 리그 이름 = 마야 `CTRL_expressions.*` 와 같은 이름) 66 프레임 | 바이너리라 FBX 로 대신 |
| `ARKit_Mapping\AS_MetaHuman_ARKit_Mapping.FBX` (+ `_Baked`, `_Baked_02`) | 위 AS 를 FBX 로 내보낸 것. `root` 조인트 사용자 어트리뷰트에 2038 커브, **프레임 1~51 = 위 51개 포즈를 Apple 순서로**(f0 = 중립, f52~65 = 마지막 포즈 홀드). 세 파일의 `CTRL_expressions_*` 커브는 동일 | mayapy FBX import → 프레임별 0 이 아닌 커브 추출 |

- 포즈당 `CTRL_expressions_*` 가 1~12개 켜진다. 값은 대부분 1.0, 일부 보조값(0.752 · 0.499 · 0.412 …). `browLateralL = 0.031`, `tongueRight = 0.07` 처럼 **0.1 미만은 잡음으로 보고 버린다**.
- 항상 1.0 인 커브 `noseWrinkleUpperL/R` · `rigLogic_OffOn` 은 포즈가 아니라 시퀀스 상수 → 무시.
- `tongueOut` 포즈의 `tongueRollDown`(0.247) 은 이 마야 리그의 `CTRL_expressions` 에 없는 이름(UE 쪽 추가 커브) → 대응 없음.
- **`MouthClose` 는 Epic 매핑에 없다.** ARKit 정의("턱이 벌어진 채 입술을 다묾")에 맞는 메타휴먼 채널은 `mouthLipsTogetherUL/UR/DL/DR`(컨트롤러 `CTRL_L/R_mouth_lipsTogetherU/D`, 주황)
  → **제안값으로 넣는다** (§9 Q3). 넣지 않으면 `dmy_in.mouthClose` 는 아무것도 안 하고 `dmy_out.mouthClose` 는 0.

### 1.4 기존 JALI 자산 (재사용)

- `examples/build_jali_arkit_node.py` : `JALI_IN`(Jaw Lip + 음소 16 + WA/YA_PEDAL = 20) → `bw_<target>`(blendWeighted, 가중치 = 0040 §3 실측/10) → `md_<target>`(Jaw/9 또는 Lip/9) →
  `cl_<target>`(clamp 0~1) → `ARKIT_OUT`(52). 15개 채널만 값이 있고 나머지 37개는 0. 이 노드망을 **그대로 `dmy_in_jali` 뒤에 붙인다**(§5.5).
- `A00540_JaliLipSync`(VisemeNet → `CNT_PHONEMES.*` 키) · `A00550_PoseMapper` 가 소비자 후보 (0090 S6 과 같은 후속).

---

## 2. 매핑표 A — `dmy_in`(ARKit 52) → 메타휴먼 컨트롤러 (입력 방향)

`dmy_in.<arkit>` 값 × 가중치를 해당 컨트롤러 축에 **더한다**(§5.2). 가중치 = §1.3 FBX 포즈 값, 부호 = §1.1 표. `X.` = `CTRL_expressions.`.
`mouthClose` 행은 Epic 매핑에 없는 **제안값**. 0.1 미만은 제외했다.

| ARKit | 메타휴먼 `CTRL_expressions` (포즈 값) ← 컨트롤러.축 (부호·가중치) |
|-------|------------------------------------------------------------------|
| `eyeBlinkLeft` | `eyeBlinkL` 1 ← `CTRL_L_eye_blink.ty` +1 |
| `eyeLookDownLeft` | `eyeLookDownL` 1 ← `CTRL_L_eye.ty` −1 |
| `eyeLookInLeft` | `eyeLookRightL` 1 ← `CTRL_L_eye.tx` −1 |
| `eyeLookOutLeft` | `eyeLookLeftL` 1 ← `CTRL_L_eye.tx` +1 |
| `eyeLookUpLeft` | `eyeLookUpL` 1 ← `CTRL_L_eye.ty` +1 |
| `eyeSquintLeft` | `eyeSquintInnerL` 1 ← `CTRL_L_eye_squintInner.ty` +1 |
| `eyeWideLeft` | `eyeWidenL` 1 ← `CTRL_L_eye_blink.ty` −1 |
| `eyeBlinkRight` | `eyeBlinkR` 1 ← `CTRL_R_eye_blink.ty` +1 |
| `eyeLookDownRight` | `eyeLookDownR` 1 ← `CTRL_R_eye.ty` −1 |
| `eyeLookInRight` | `eyeLookLeftR` 1 ← `CTRL_R_eye.tx` +1 |
| `eyeLookOutRight` | `eyeLookRightR` 1 ← `CTRL_R_eye.tx` −1 |
| `eyeLookUpRight` | `eyeLookUpR` 1 ← `CTRL_R_eye.ty` +1 |
| `eyeSquintRight` | `eyeSquintInnerR` 1 ← `CTRL_R_eye_squintInner.ty` +1 |
| `eyeWideRight` | `eyeWidenR` 1 ← `CTRL_R_eye_blink.ty` −1 |
| `jawForward` | `jawFwd` 0.999 ← `CTRL_C_jaw_fwdBack.ty` −1 |
| `jawLeft` | `jawLeft` 1 ← `CTRL_C_jaw.tx` −1 |
| `jawRight` | `jawRight` 1 ← `CTRL_C_jaw.tx` +1 |
| `jawOpen` | `jawOpen` 1 ← `CTRL_C_jaw.ty` +1 |
| `mouthClose` (제안) | `mouthLipsTogetherUL/UR/DL/DR` 1 ← `CTRL_L/R_mouth_lipsTogetherU/D.ty` +1 (4개) |
| `mouthFunnel` | `mouthFunnelUL/UR/DL/DR` 1 ← `CTRL_L/R_mouth_funnelU/D.ty` +1 (4개) |
| `mouthPucker` | `mouthLipsPurseUL/UR/DL/DR` 1 ← `CTRL_L/R_mouth_purseU/D.ty` +1 (4개)<br>`mouthFunnelUL/UR/DL/DR` 0.752 ← `CTRL_L/R_mouth_funnelU/D.ty` +0.752 (4개)<br>`mouthLipsTowardsUL/UR/DL/DR` 0.412 ← `CTRL_L/R_mouth_towardsU/D.ty` +0.412 (4개) |
| `mouthLeft` | `mouthLeft` 1 ← `CTRL_C_mouth.tx` +1 |
| `mouthRight` | `mouthRight` 1 ← `CTRL_C_mouth.tx` −1 |
| `mouthSmileLeft` | `mouthCornerPullL` 1 ← `CTRL_L_mouth_cornerPull.ty` +1 |
| `mouthSmileRight` | `mouthCornerPullR` 1 ← `CTRL_R_mouth_cornerPull.ty` +1 |
| `mouthFrownLeft` | `mouthCornerDepressL` 1 ← `CTRL_L_mouth_cornerDepress.ty` +1 |
| `mouthFrownRight` | `mouthCornerDepressR` 1 ← `CTRL_R_mouth_cornerDepress.ty` +1 |
| `mouthDimpleLeft` | `mouthDimpleL` 1 ← `CTRL_L_mouth_dimple.ty` +1 |
| `mouthDimpleRight` | `mouthDimpleR` 1 ← `CTRL_R_mouth_dimple.ty` +1 |
| `mouthStretchLeft` | `mouthStretchL` 1 ← `CTRL_L_mouth_stretch.ty` +1 |
| `mouthStretchRight` | `mouthStretchR` 1 ← `CTRL_R_mouth_stretch.ty` +1 |
| `mouthRollLower` | `mouthLowerLipRollInL/R` 1 ← `CTRL_L/R_mouth_lipsRollD.ty` +1<br>`mouthUpperLipRollInL/R` 0.499 ← `CTRL_L/R_mouth_lipsRollU.ty` +0.499 |
| `mouthRollUpper` | `mouthUpperLipRollInL/R` 0.998 ← `CTRL_L/R_mouth_lipsRollU.ty` +1 |
| `mouthShrugLower` | `jawChinRaiseDL/DR` 1 ← `CTRL_L/R_jaw_ChinRaiseD.ty` +1 |
| `mouthShrugUpper` | `jawChinRaiseUL/UR` 1 ← `CTRL_L/R_jaw_ChinRaiseU.ty` +1 |
| `mouthPressLeft` | `mouthPressUL` · `mouthPressDL` 1 ← `CTRL_L_mouth_pressU.ty` · `CTRL_L_mouth_pressD.ty` +1 |
| `mouthPressRight` | `mouthPressUR` · `mouthPressDR` 1 ← `CTRL_R_mouth_pressU.ty` · `CTRL_R_mouth_pressD.ty` +1 |
| `mouthLowerDownLeft` | `mouthLowerLipDepressL` 1 ← `CTRL_L_mouth_lowerLipDepress.ty` +1 |
| `mouthLowerDownRight` | `mouthLowerLipDepressR` 1 ← `CTRL_R_mouth_lowerLipDepress.ty` +1 |
| `mouthUpperUpLeft` | `mouthUpperLipRaiseL` 1 ← `CTRL_L_mouth_upperLipRaise.ty` +1 |
| `mouthUpperUpRight` | `mouthUpperLipRaiseR` 1 ← `CTRL_R_mouth_upperLipRaise.ty` +1 |
| `browDownLeft` | `browDownL` 1 ← `CTRL_L_brow_down.ty` +1 |
| `browDownRight` | `browDownR` 1 ← `CTRL_R_brow_down.ty` +1 |
| `browInnerUp` | `browRaiseInL/R` 1 ← `CTRL_L/R_brow_raiseIn.ty` +1<br>`browLateralL/R` 1 ← `CTRL_L/R_brow_lateral.ty` +1 |
| `browOuterUpLeft` | `browRaiseOuterL` 1 ← `CTRL_L_brow_raiseOut.ty` +1<br>`browRaiseInL` 1 ← `CTRL_L_brow_raiseIn.ty` +1 |
| `browOuterUpRight` | `browRaiseOuterR` 1 ← `CTRL_R_brow_raiseOut.ty` +1<br>`browRaiseInR` 1 ← `CTRL_R_brow_raiseIn.ty` +1 |
| `cheekPuff` | `mouthCheekBlowL/R` 1 ← `CTRL_L/R_mouth_suckBlow.ty` +1<br>`mouthLipsBlowL/R` 1 ← `CTRL_L/R_mouth_lipsBlow.ty` +1 |
| `cheekSquintLeft` | `eyeCheekRaiseL` 1 ← `CTRL_L_eye_cheekRaise.ty` +1 |
| `cheekSquintRight` | `eyeCheekRaiseR` 1 ← `CTRL_R_eye_cheekRaise.ty` +1 |
| `noseSneerLeft` | `noseWrinkleL` 1 ← `CTRL_L_nose.ty` +1 |
| `noseSneerRight` | `noseWrinkleR` 1 ← `CTRL_R_nose.ty` +1 |
| `tongueOut` | `tongueDown` 0.826 ← `CTRL_C_tongue_move.ty` −0.826<br>`tongueOut` 0.769 ← `CTRL_C_tongue_inOut.ty` −0.769<br>`tongueWide` 0.628 ← `CTRL_C_tongue_wideNarrow.ty` +0.628<br>(`tongueRollDown` 0.247 — 이 리그에 없음) |

**쓰이는 컨트롤러 68개** (`mouthClose` 제안 4개 포함, 빼면 64개) — 눈 8(`eye`·`eye_blink`·`eye_squintInner`·`eye_cheekRaise` L/R), 눈썹 8, 코 2, 턱 6(`C_jaw`·`C_jaw_fwdBack`·`jaw_ChinRaiseU/D` L/R),
입 41, 혀 3. 컨트롤러 축으로는 **72개**(`CTRL_C_jaw` · `CTRL_C_mouth` · `CTRL_L/R_eye` 는 2축). 나머지 106개 컨트롤러는 건드리지 않는다.

가중치를 그대로 쓰면 **한 ARKit 값이 1 일 때 Epic 의 포즈와 같은 메타휴먼 포즈**가 된다 (= UE 에서 ARKit 캡처를 재생한 모습). 두 ARKit 값이 같은 컨트롤러에 들어오면
합산되고(`mouthFunnel` 1 + `mouthPucker` 1 → `funnelU` 1.752 → SDK 끝값 1 로 멈춤) 이것도 UE 의 PoseAsset 가산 동작과 같다.

---

## 3. 매핑표 B — 메타휴먼 컨트롤러 → `dmy_out`(ARKit 52) (출력 방향)

출력은 GUI 컨트롤러 메시가 아니라 **`CTRL_expressions.*` 에서 읽는다**(§5.3 D3). 1:1 인 것은 직결, 포즈가 여러 채널인 것은 **그 포즈의 주 채널(값 1.0)들의 평균**(`blendWeighted`, 가중치 1/n).
`X.` = `CTRL_expressions.`. 평균식은 노드의 `weight[i]` 를 바꾸면 바로 조정된다.

| ARKit (`dmy_out.`) | 식 | 비고 |
|--------------------|----|------|
| `eyeBlinkLeft` · `eyeBlinkRight` | `X.eyeBlinkL` · `X.eyeBlinkR` | |
| `eyeLookDownLeft` · `…Right` | `X.eyeLookDownL` · `X.eyeLookDownR` | 에임 모드(`lookAtSwitch` 1)여도 값이 나온다 |
| `eyeLookInLeft` / `eyeLookOutLeft` | `X.eyeLookRightL` / `X.eyeLookLeftL` | 왼눈의 In = 오른쪽(코 쪽) |
| `eyeLookInRight` / `eyeLookOutRight` | `X.eyeLookLeftR` / `X.eyeLookRightR` | |
| `eyeLookUpLeft` · `…Right` | `X.eyeLookUpL` · `X.eyeLookUpR` | |
| `eyeSquintLeft` · `…Right` | `X.eyeSquintInnerL` · `X.eyeSquintInnerR` | |
| `eyeWideLeft` · `…Right` | `X.eyeWidenL` · `X.eyeWidenR` | |
| `jawForward` | `X.jawFwd` | |
| `jawLeft` · `jawRight` · `jawOpen` | `X.jawLeft` · `X.jawRight` · `X.jawOpen` | |
| `mouthClose` (제안) | avg(`X.mouthLipsTogetherUL UR DL DR`) | Q3 에서 빼면 0 |
| `mouthFunnel` | avg(`X.mouthFunnelUL UR DL DR`) | |
| `mouthPucker` | avg(`X.mouthLipsPurseUL UR DL DR`) | 보조 채널(funnel 0.752 · towards 0.412)은 안 읽는다 — `mouthFunnel` 과 섞이지 않게 |
| `mouthLeft` · `mouthRight` | `X.mouthLeft` · `X.mouthRight` | |
| `mouthSmileLeft` · `…Right` | `X.mouthCornerPullL` · `X.mouthCornerPullR` | |
| `mouthFrownLeft` · `…Right` | `X.mouthCornerDepressL` · `X.mouthCornerDepressR` | |
| `mouthDimpleLeft` · `…Right` | `X.mouthDimpleL` · `X.mouthDimpleR` | |
| `mouthStretchLeft` · `…Right` | `X.mouthStretchL` · `X.mouthStretchR` | |
| `mouthRollLower` | avg(`X.mouthLowerLipRollInL`, `X.mouthLowerLipRollInR`) | |
| `mouthRollUpper` | avg(`X.mouthUpperLipRollInL`, `X.mouthUpperLipRollInR`) | `dmy_in.mouthRollLower` 1 이 upperRollIn 0.499 를 켜므로 이때 `mouthRollUpper` 출력 0.5 (교차) |
| `mouthShrugLower` · `mouthShrugUpper` | avg(`X.jawChinRaiseDL`, `DR`) · avg(`X.jawChinRaiseUL`, `UR`) | |
| `mouthPressLeft` · `…Right` | avg(`X.mouthPressUL`, `DL`) · avg(`X.mouthPressUR`, `DR`) | |
| `mouthLowerDownLeft` · `…Right` | `X.mouthLowerLipDepressL` · `R` | |
| `mouthUpperUpLeft` · `…Right` | `X.mouthUpperLipRaiseL` · `R` | |
| `browDownLeft` · `…Right` | `X.browDownL` · `X.browDownR` | |
| `browInnerUp` | avg(`X.browRaiseInL`, `X.browRaiseInR`, `X.browLateralL`, `X.browLateralR`) | `browOuterUpL` 1 → `browInnerUp` 0.25 (교차, Epic 포즈가 `raiseIn` 을 공유) |
| `browOuterUpLeft` · `…Right` | avg(`X.browRaiseOuterL`, `X.browRaiseInL`) · avg(`…R`) | `browInnerUp` 1 → `browOuterUp` 0.5 (교차). 교차가 싫으면 `X.browRaiseOuterL` 단독 (Q4) |
| `cheekPuff` | avg(`X.mouthCheekBlowL`, `R`, `X.mouthLipsBlowL`, `R`) | |
| `cheekSquintLeft` · `…Right` | `X.eyeCheekRaiseL` · `X.eyeCheekRaiseR` | |
| `noseSneerLeft` · `…Right` | `X.noseWrinkleL` · `X.noseWrinkleR` | |
| `tongueOut` | `X.tongueOut` | Epic 포즈의 `tongueDown` · `tongueWide` 는 안 읽는다 |

- 왕복 성질: `dmy_in.<k>` = 1 (다른 입력 0) → 표 A 로 컨트롤러 → `CTRL_expressions` → 표 B → `dmy_out.<k>` = **1** 이 52개 전부에서 성립하도록 B 를 골랐다(교차 항목은 다른 출력에 0.25~0.5 가 더 나올 뿐). 검증 T3.
- ARKit 에 없는 메타휴먼 채널(`mouthStickyU/D*`, `neck*`, `teeth*`, `eyelashes*`, `eyelid*`, `mouthCorner*`, `jawClench` 등 약 190개)은 출력에 반영되지 않는다 — ARKit 52 의 표현 범위 밖.

---

## 4. 매핑표 C — JALI 더미 노드

### 4.1 `dmy_in_jali` → ARKit (→ 표 A 의 입력으로 합류)

어트리뷰트 = `A0010` `JALI_IN` 과 같은 **20개**: `Jaw Lip`(0~15, 기본 9), 음소 16 `AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP SSH Schwa GK LNTD`(0~12), `WA_PEDAL YA_PEDAL`(0~12 · 0~15).
`CNT_COARTIC` 의 `LNTD GK MMM FFF` 는 0040 실측에서 단독 변화가 없고 음소와 이름이 겹쳐 **넣지 않는다**(A0010 과 동일, Q5).

노드망은 `build_jali_arkit_node.build()` 그대로 — ARKit 타겟마다 `bw_<target>`(음소 × 가중치/10) → `md_<target>`(× Jaw/9 또는 Lip/9) → `cl_<target>`(0~1).
가중치(0040 §3 실측, 음소 = 10 일 때):

| ARKit 타겟 | 입력 음소 : 시작 가중치 | 축 |
|------------|-------------------------|----|
| `jawOpen` | AHH 1.00 · AAA 0.67 · OHH 0.56 · MBP 0.43 · Eh 0.38 · WWW 0.30 · Schwa 0.30 · LNTD 0.30 · GK 0.30 · RRR 0.22 · IEE 0.13 · TTH 0.13 · FFF 0.11 · UUU 0.06 | Jaw |
| `jawForward` | SSS 0 (연결만, 방향 미확인) | Jaw |
| `tongueOut` | TTH 0.30 (임시값) | Jaw |
| `mouthLowerDownL/R` | SSS 0.66 · IEE 0.61 · AAA 0.54 · Eh 0.37 · AHH 0.34 · SSH 0.25 | Lip |
| `mouthDimpleL/R` | FFF 0.56 · TTH 0.54 · AAA 0.50 · IEE 0.37 · YA_PEDAL 0.27 | Lip |
| `mouthStretchL/R` | YA_PEDAL 0.37 · IEE 0.29 · AAA 0.28 · Eh 0.24 · SSH 0.11 | Lip |
| `mouthUpperUpL/R` | AAA 0.27 · IEE 0.27 · TTH 0.25 · SSH 0.24 · FFF 0.11 | Lip |
| `mouthSmileL/R` | IEE 0.23 · AAA 0.20 · Eh 0.15 · YA_PEDAL 0.12 | Lip |
| `mouthPucker` | UUU 0.61 · WWW 0.52 · WA_PEDAL 0.48 · OHH 0.41 · SSH 0.29 · RRR 0.27 | Lip |
| `mouthFunnel` | SSH 0.44 · RRR 0.42 · TTH 0.27 · UUU 0.26 · SSS 0.09 | Lip |
| `mouthClose` | MBP 0.62 · WWW 0.37 | Lip |
| `mouthPressL/R` | MBP 0.07 | Lip |
| `mouthRollLower` | FFF 0.24 | Lip |
| `mouthShrugLower` | FFF 0.09 | Lip |
| `cheekPuff` | MBP 0.10 | Lip |

- 나머지 37개 ARKit 타겟(눈 · 눈썹 · 코 · 볼 등)은 JALI 에서 0 — 더미에는 어트리뷰트를 두지 않고 ARKit 측 합류 노드에 연결하지 않는다.
- **`mouthClose` 가 JALI 에서 가장 중요한 축 중 하나(MBP)** 이므로 §1.3 의 `mouthClose → lipsTogether` 제안을 넣어야 JALI 입력에서 입술이 닫힌다 (Q3 의 근거).
- JALI 경로의 결과는 `dmy_in_jali_arkit`(ARKit 52, 읽기 전용 중간 노드) 에 모이고, 표 A 의 컨트롤러별 `blendWeighted` 가 `dmy_in` 과 **같은 가중치로 하나 더 입력받는다**(§5.5). 두 입력은 가산.
- `dmy_in_jali.weight`(0~1, 기본 1) 하나로 JALI 경로 전체를 끌 수 있게 음소 20개 앞에 `multDoubleLinear` 를 둔다.

### 4.2 `dmy_out_jali` ← ARKit (`dmy_out`) — 역방향은 근사

음소 → ARKit 은 "여러 타겟의 가중 합" 이라 역은 유일하지 않다. 제안(Q6 에서 넣을지 결정):

```
dmy_out_jali.<ph> = clamp( Σ_k w_k · dmy_out.<k>  /  Σ_k w_k , 0, 1 ) × dmy_out_jali.scale     (k = 표 4.1 에서 <ph> 가 들어간 타겟, w_k = 그 가중치)
```

- `blendWeighted`(가중치 w_k / Σw) + `clamp` + `multDoubleLinear`(`scale`, 기본 10 = VisemeNet · A00540 단위) = 음소당 3 노드, 20개 → 60 노드.
- `Jaw` = `dmy_out.jawOpen` × 15, `Lip` = max 류가 없어 `mouthPucker mouthFunnel mouthClose` 평균 × 15 (거친 근사).
- 성질: `AHH` 만 넣은 경우 `jawOpen` 1 → `AHH` 출력 10 이지만 `Schwa`(jawOpen 0.30) 도 10 이 나온다 — **음소 구분은 못 한다.** "메타휴먼 → JALI 리그로 역이식" 이 실제로 필요할 때만 넣는다. 기본 권장: **이번엔 빼고** `dmy_in_jali` 만 (Q6).

---

## 5. 노드망 설계

### 5.1 D1 — 더미 노드 4개 (`transform`, 쉐입 없음, `DMY_grp` 아래)

| 노드 | 어트리뷰트 | 범위 · 키 | 역할 |
|------|-----------|-----------|------|
| `dmy_in` | ARKit 52 (double) | 0~1 (`-min 0 -max 1`), 키 가능 | 외부(ARKit 캡처 · A00320 · 다른 리그)가 넣는 입력 허브 |
| `dmy_out` | ARKit 52 (double) | 제한 없음(값은 0~1), 키 가능, **노드망이 연결** | 블렌드셰이프 · 다른 리그 · A00550 에 한 번에 연결하는 출력 허브 |
| `dmy_in_jali` | `Jaw Lip` + 음소 16 + `WA_PEDAL YA_PEDAL` + `weight` | A0010 범위 (0~12 / 0~15), `weight` 0~1 | VisemeNet(A00540) · JALI 리그 키를 받는 입력 |
| `dmy_out_jali` (선택, Q6) | 음소 16 + `Jaw Lip` + `scale` | 연결됨 | 역방향 근사 |
| `dmy_in_jali_arkit` | ARKit 52 | 연결됨, 채널박스 숨김 | JALI 경로의 중간 결과 (디버그 · 가중치 점검용) |

이름은 요청대로 `dmy_in` · `dmy_out` (접두사 없음). ARKit 어트리뷰트 순서는 §1.2 (채널박스에서 Apple 순서로 보인다).

### 5.2 D2 — `dmy_in` 이 컨트롤러를 미는 방법: **SDK 앞에 합산 노드를 끼우고, 보이는 위치는 오프셋 그룹으로**

이 리그의 SDK 곡선은 `CTRL_<name>.ty` **로컬값**을 읽는다. 0090 D3 처럼 부모 그룹만 밀면 **표정은 안 바뀐다**(로컬 ty 가 그대로). 그래서 값 경로와 시각 경로를 나눈다.

```
dmy_in.mouthFunnel ─┐
dmy_in.mouthPucker ─┤ (가중치 1, 0.752)              ┌→ GRP_dmy_CTRL_L_mouth_funnelU.translateY   (시각: 컨트롤러가 눈에 보이게 올라감)
dmy_in_jali_arkit.* ┘  bw_dmy_CTRL_L_mouth_funnelU_y ─┤
                                                     └→ pma_dmy_CTRL_L_mouth_funnelU_y.input1D[1] ─┐
CTRL_L_mouth_funnelU.translateY ─────────────────────→ pma_….input1D[0]                            ├→ output1D → (기존) unitConversion → animCurveUU → CTRL_expressions.mouthFunnelUL
```

| ID | 결정 | 권장 | 이유 · 대안 |
|----|------|------|------------|
| D2a | 값 경로 | `CTRL.ty` → `animCurveUU.input` 연결을 끊고 사이에 **`plusMinusAverage`(sum)** 를 끼운다. `input1D[0]` = 컨트롤러 로컬값(손 조작), `[1]` = `bw_dmy_*` 출력 | 손으로 더 밀 수 있다(R2 "조절할 수 있는 컨트롤러"). 대안 = `dmy_in → CTRL.ty` 직결: 노드 72개가 줄지만 컨트롤러가 잠겨 손으로 못 만지고 뷰포트 드래그가 막힌다 |
| D2b | 시각 경로 | `FRM_<name>` 과 `CTRL_<name>` 사이에 **`GRP_dmy_<name>`** 트랜스폼을 끼우고 `bw` 출력을 그 `ty`(2D 는 `tx`)에 연결 | 입력이 들어오면 컨트롤러 메시가 그만큼 움직여 보이고, 손 조작은 그 위에 더해진다(월드 위치 = 합과 일치). 대안 = 시각 경로 생략(노드 68개 절약, 입력이 들어와도 GUI 는 제자리) — Q2 |
| D2c | 범위 | 합이 1 을 넘거나 −1 아래로 가도 SDK 곡선이 끝값을 유지하므로 clamp 를 두지 않는다. `GRP_dmy` 의 이동은 제한하지 않는다(틀 밖으로 조금 나갈 수 있음) | 눈 2D 패드는 ±40°/−30° 곡선이 같은 식으로 끝값을 유지 |
| D2d | 눈 | `CTRL_L/R_eye.tx/ty` 에 D2a·b 를 적용(`eyeLookIn/Out` 부호는 표 A). `lookAtSwitch` 가 1 이면 UE 처럼 GUI 눈이 무시된다 — 문서에 적고 기본값 0 유지 | `LOC_*_eyeDriver.rotate` 에 직접 넣는 대안은 에임 모드와 충돌 |

노드 수: 컨트롤러 축 72 × (`bw` 1 + `pma` 1) = 144 + `GRP_dmy` 68 = **212** (`mouthClose` 제안 제외 시 200).

### 5.3 D3 — `dmy_out` 은 `CTRL_expressions` 에서 읽는다

- `CTRL_expressions` 는 headRig_grp 안의 컨트롤러(메시, 노란색)이자 **모든 GUI 컨트롤러 값이 0~1 로 정규화되어 모이는 곳**이다. 여기서 읽으면 ① 부호 · 2D 축 처리가 필요 없고 ② 손 조작과 `dmy_in` 입력이 합쳐진 최종값이 나오며 ③ 눈 에임 모드 결과까지 포함된다.
- 1:1 (34개): `CTRL_expressions.X` → `dmy_out.Y` 직결. 평균 (18개): `bw_out_<arkit>`(blendWeighted, weight 1/n) → `dmy_out.Y`. 값은 0~1 안이라 clamp 없음. 노드 **18**.
- 대안(GUI 컨트롤러 `ty` 에서 직접 읽기)은 양방향 축 분리 · 눈 각도 역변환이 더 필요해 기각.

### 5.4 D4 — 원본은 복사본에서 고친다

`0010_sample_0030.mb` 를 열어 작업하고 **`0010_sample_0040.mb` 로 저장**한다. 레퍼런스 방식(0030 을 참조하고 새 씬에 더미만)은 SDK 연결을 끊는 D2a 가 레퍼런스 편집으로 남아
깨지기 쉽다. 0030 은 손대지 않는다(`backup/` 에 이미 BU 있음).

### 5.5 D5 — JALI 경로

```
dmy_in_jali.AAA ─→ mdl_jali_AAA (× dmy_in_jali.weight) ─→ JALI_IN 자리 (build_jali_arkit_node 의 bw_/md_/cl_ 노드망, prefix 'jali_') ─→ dmy_in_jali_arkit.<52>
dmy_in_jali_arkit.mouthFunnel ─→ bw_dmy_CTRL_L_mouth_funnelU_y.input[k]  (dmy_in.mouthFunnel 과 같은 가중치 1)
```

- `build()` 의 입력 노드를 `dmy_in_jali` 로, 출력 노드를 `dmy_in_jali_arkit` 로 지정할 수 있게 **함수 인자**(`in_node`, `out_node`, `prefix`)를 쓴다 — `connect_rig` · `build_controller` 는 안 쓴다.
- 표 A 의 `bw_dmy_*` 는 `dmy_in` 입력 뒤에 `dmy_in_jali_arkit` 입력을 같은 가중치로 하나 더 받는다 → 입력 수 2배, 노드 수 그대로. JALI 가 쓰는 15개 타겟만 연결(37개는 0).
- 노드: `mdl` 20 + A0010 노드망 47(bw 15 · md 17 · cl 15) = **67**.

### 5.6 이름 규칙 · 그룹

- 접두사 `dmy_` / `bw_dmy_` / `pma_dmy_` / `GRP_dmy_` / `bw_out_` / `jali_` — 원본의 `blendWeighted1~4` · `MDV_*` · `SUB_*` · `multiplyDivide_head*` 와 겹치지 않는다.
- DG 노드는 이름으로만 구분(그룹 불가), 더미 트랜스폼 4~5개는 `|rig|DMY_grp` 아래. `DMY_grp` 는 `head_grp` 옆(`rig` 바로 아래)에 둔다 — headRig_grp 안에 넣으면 `CTRL_faceGUI` 의 팔로우 컨스트레인트를 따라 움직여 혼동.
- 합계 노드: 212 + 18 + 67 = **297** (+ `dmy_out_jali` 60). 재생 부하는 RigLogic 에 비해 무시할 수준.

---

## 6. 머티리얼 — 쓰이는 컨트롤러만 색을 바꾼다 (R7)

- 새 `lambert` **`GUI2D_mapped_shader`** 색 (0.0, 0.8, 1.0)(시안, 기존 노랑 · 주황 · 빨강 · 검정과 구분) + 셰이딩 그룹 `GUI2D_mapped_shaderSG`.
- 표 A 의 **68개 컨트롤러 메시 쉐입**(`CTRL_<name>Shape`)만 `cmds.sets(shape, e=True, forceElement=SG)` 로 재배정. 컨트롤러 메시는 페이스 단위 배정이 없어(전수 확인) 오브젝트 단위로 바꿔도 된다.
- 주황이던 `CTRL_L/R_mouth_lipsTogetherU/D`(`mouthClose` 제안) 도 시안으로 — "주황 = 보조" 구분보다 "시안 = 매핑됨" 을 우선 (Q7 로 확인).
- 안 쓰는 106개, 틀(`FRM_*`, 검정), 글자, `CTRL_expressions`, `CTRL_faceGUI` 는 그대로. `dmy_out` 이 읽는 `CTRL_expressions` 는 색을 바꾸지 않는다(눈에 보이는 GUI 가 아님).
- 머티리얼 원본 색은 건드리지 않으므로 되돌릴 때는 셰이딩 그룹만 원래 것으로 재배정하면 된다(스크립트에 `--revert` 옵션).

---

## 7. 파일 · 스크립트

| 파일 | 내용 |
|------|------|
| `07_MH_sample_02/0010_sample_0040.mb` | 결과 에셋 (0030 + 더미 4~5 + 노드망 + 머티리얼) |
| `JUN_JALI/examples/build_mh_arkit_dummy.py` | 생성 스크립트. `mayapy build_mh_arkit_dummy.py <in.mb> <out.mb> [--no-jali] [--no-visual] [--no-mouthclose] [--revert]`. Maya 안에서는 `build()` |
| 〃 상수 | `ARKIT_52`(§1.2 순서), `ARKIT_TO_CTRL = {arkit: [(ctrl, axis, weight), …]}`(표 A, 부호 포함 가중치), `OUT_FROM_EXPR = {arkit: [expr, …]}`(표 B), `MAPPED_COLOR`, `JALI_*` 는 `build_jali_arkit_node` 에서 import |
| `JUN_JALI/examples/check_mh_arkit_dummy.py` | 검증 T1~T8 (mayapy, 결과 파일을 다시 열어 실행, `RESULT OK` / `N FAILED`) |
| `docs/0100_mh_arkit_dummy_plan.md` | 이 문서. 완료 후 확정표 · 검증 결과를 §12 에 기록 |

생성 스크립트 순서: ① 파일 열기(`embeddedRL4` 로드 확인) → ② `DMY_grp` · 더미 4~5 생성(어트리뷰트 추가) → ③ 표 A 로 컨트롤러 축마다 `bw_dmy` · `pma_dmy` · `GRP_dmy`(D2) →
④ 표 B 로 `dmy_out` 연결 → ⑤ JALI 노드망(D5) → ⑥ 머티리얼(§6) → ⑦ `file -rename` + 저장 → ⑧ `check_…` 실행.

---

## 8. 검증 (mayapy, `check_mh_arkit_dummy.py`)

| # | 검사 | 기준 |
|---|------|------|
| T1 | 더미 어트리뷰트 집합 | `dmy_in` · `dmy_out` = ARKit 52 정확히(순서 포함), `dmy_in_jali` = A0010 `JALI_IN` 20 + `weight` |
| T2 | 입력 → 포즈 | 52개 각각 `dmy_in.k = 1`(나머지 0) → `CTRL_expressions` 의 켜진 채널과 값이 §1.3 FBX 포즈(0.1 이상)와 **오차 0.01 이내** (`mouthClose` 는 제안값 기준, `tongueRollDown` 제외) |
| T3 | 왕복 | 같은 상태에서 `dmy_out.k == 1`, 다른 출력은 교차 항목(§3 비고) 외 0 |
| T4 | 손 조작 유지 | `CTRL_L_mouth_funnelU.ty = 0.4` + `dmy_in.mouthFunnel = 0.4` → `X.mouthFunnelUL = 0.8`; `dmy_in.mouthFunnel = 1` + 손 0.5 → 1.0(끝값). 컨트롤러 `ty` 는 **연결되지 않은 상태**(`listConnections` 빈 값) |
| T5 | 시각 경로 | `dmy_in.jawOpen = 1` → `CTRL_C_jaw` 월드 y 가 `GRP_dmy_CTRL_C_jaw.ty` 만큼 이동, `tx` 축도 동일 |
| T6 | JALI | `dmy_in_jali` 기본(Jaw Lip 9) + `MBP = 10` → `dmy_in_jali_arkit.mouthClose ≈ 0.62`, `X.mouthLipsTogetherUL ≈ 0.62`; `weight = 0` 이면 전부 0 |
| T7 | 머티리얼 | 시안 SG 멤버 = 표 A 컨트롤러 쉐입 68개와 정확히 일치, 나머지 쉐입의 SG 는 0030 과 동일 |
| T8 | 원본 불변 | 0030 의 파일 해시가 전과 같다 |

사용자 GUI 확인: 0040 을 열어 시안 컨트롤러 분포가 맞는지, `dmy_in.jawOpen` 을 채널박스에서 올리면 턱 컨트롤러가 올라가며 입이 벌어지는지, 그 상태에서 컨트롤러를 손으로 더 밀 수 있는지.

---

## 9. 확인이 필요한 것 (답을 받으면 §0-A 확정표로 올린다)

| # | 질문 | 권장 |
|---|------|------|
| Q1 | 값 경로 D2a — SDK 앞에 `plusMinusAverage` 를 끼워 손 조작을 살리는 방식 vs `dmy_in → CTRL.ty` 직결(컨트롤러 잠김) | 끼우기 (R2 의 "조절할 수 있는 컨트롤러") |
| Q2 | 시각 경로 D2b — `GRP_dmy_*` 오프셋 그룹으로 컨트롤러 메시가 움직여 보이게 할지 | 넣는다 (입력이 눈에 보임) |
| Q3 | `mouthClose` → `mouthLipsTogetherUL/UR/DL/DR` **제안값** 채택 여부 (Epic 매핑엔 없음, JALI 의 MBP 가 쓴다) | 채택 |
| Q4 | 표 B 의 교차 항목(`browInnerUp` · `browOuterUp` · `mouthRollUpper`) — Epic 포즈 그대로 평균 vs 고유 채널만 | Epic 그대로(가중치 노드에서 나중에 조정) |
| Q5 | `dmy_in_jali` 에 `CNT_COARTIC` 의 `LNTD GK MMM FFF` 를 넣을지 (단독 효과 없음 · 이름 충돌) | 넣지 않는다 (A0010 과 동일) |
| Q6 | `dmy_out_jali`(역방향 근사, 음소 구분 불가) 를 만들지 | 이번엔 뺀다 — 필요해지면 §4.2 식으로 추가 |
| Q7 | 색 — 시안 (0, 0.8, 1) 하나로, 주황 컨트롤러도 시안으로 | 그대로 |
| Q8 | 결과 파일 이름 `0010_sample_0040.mb`, 스크립트는 `JUN_JALI/examples/` | 그대로 |

---

## 10. 단계

| 단계 | 할 일 | 결과물 |
|------|-------|--------|
| S0 | §9 답 확인 → §0-A 확정표 | 이 문서 갱신 |
| S1 | `build_mh_arkit_dummy.py` — 상수표(§2 · §3) · 더미 생성 · D2 노드망 · 머티리얼 | 스크립트 |
| S2 | `build_jali_arkit_node.build(in_node, out_node, prefix)` 인자화 + D5 연결 | 스크립트 수정 (기존 사용법 유지) |
| S3 | mayapy 로 0030 → 0040 생성, `check_mh_arkit_dummy.py` T1~T8 | `0010_sample_0040.mb` + 검증 로그 |
| S4 | 사용자 GUI 확인(§8 끝) → 수정 | 완료, §12 기록 |
| S5 (후속) | `A00540` 매핑 json 에 `dmy_in_jali` 대상 추가 · `A00550` 에서 `dmy_out` 을 Source 로 쓰는 예 | 별도 턴 |

---

## 11. 알려진 위험

- **RigLogic(`embeddedRL4`) 플러그인**: 0030 을 열 때 `embeddedRL4` 가 로드돼야 저장 시 `head_rl4Embedded` 가 보존된다(mayapy 에서 로드 확인됨, unknown 노드 101개는 Arnold 등 무관 플러그인). 플러그인이 없는 Maya 에서 열어 저장하면 리그가 깨진다 — 스크립트 시작에서 `pluginInfo` 검사 후 중단.
- D2a 는 원본 SDK 연결 72개를 끊고 다시 잇는다 — `check` T4 · T2 가 통과하면 복구된 것. 실수를 되돌리려면 0030 에서 다시 생성한다(스크립트는 멱등이 아니다: 0040 에 다시 돌리면 `dmy_` 노드가 있을 때 중단).
- Epic 포즈 가중치는 **메타휴먼 표준 얼굴 기준**이라 캐릭터마다 과한 채널이 있을 수 있다 — `bw_dmy_*.weight[i]` 에서 조정한다.
- `mouthClose` 제안은 실측이 아니라 ARKit 정의에 따른 선택이다. 눈으로 확인 후 `lipsTogether` 대신 `mouthLipsPress` 등으로 바꿀 수 있다(노드 입력만 교체).
- `lookAtSwitch = 1` 이면 `dmy_in.eyeLook*` 는 표정에 영향이 없다(UE 와 같은 동작). 캡처 데이터를 그대로 재생할 때는 0 으로.
- `dmy_out` 은 `CTRL_expressions` 를 읽으므로 **외부에서 `CTRL_expressions` 를 직접 키 잡아도** 출력이 따라온다 — 의도된 동작이지만 "컨트롤러를 거쳐야만 나온다" 로 오해하지 말 것.
