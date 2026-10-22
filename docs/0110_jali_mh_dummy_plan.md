# JALI 음소 ↔ 메타휴먼 페이셜 더미 노드 — 매칭표 · 제작 계획서

> **작성** 2026-10-22 · 상태: **구현 · 검증 완료 (2026-10-22, §12)** — 더미 이름 · 단위는 §0-A 확정(A00540 json 규칙) · 대상 Maya 2024 (mayapy 로 생성 · 검증)
> 원본: `C:\Users\USER\Desktop\JP\0035_maya_src_rig\07_MH_sample_02\0010_sample_0040.mb` — [0100 계획](0100_mh_arkit_dummy_plan.md)으로 만든 ARKit 더미 에셋(`dmy_in` · `dmy_out` · `bw_dmy_*` · `pma_dmy_*` · `GRP_dmy_*`)
> 결과물(안): 같은 폴더 `0010_sample_0050.mb` (0040 을 열어 JALI 더미 · 노드망을 더해 다른 이름으로 저장)
> 참고: [0040 JALI ↔ ARKit 매칭](0040_jali_arkit_mapping.md)(angela 실측 가중치) · [0100 더미 출력 어트리뷰트 안내](0100_jali_dummy_out_attrs_guide.md)(angela 음소별 턱 · 입술 · **혀** 실측, 동시조음 뜻) ·
> [0090 슬라이더 리그](0090_jali_slider_ctl_plan.md)(`02_Cage_JALI/A0020_jali_slider_ctl.ma` 의 `DUMMY_OUT_JALI/PHONEMES/COARTIC`) · `examples/build_jali_arkit_node.py`(JALI → ARKit 노드망) · `examples/build_mh_arkit_dummy.py`(0040 생성 스크립트, 재사용)

---

## 0. 요청 정리

### 0-A. 확정표 (2026-10-22 사용자 답변)

| # | 답 | 반영 |
|---|----|------|
| Q1 | 더미 3개 — 이름은 `A00540_JaliLipSync` 의 `app/mappings/jali_slider_dummy_in.json` 규칙: **`DUMMY_IN_PHONEMES` · `DUMMY_IN_COARTIC` · `DUMMY_IN_JALI`** | §5.1 D1a, T1 |
| Q2 | 단위도 그 json 규칙 — **전부 0~1** (angela 단위 안 씀). 비짐 1.0 = VisemeNet txt 최댓값 = angela 10(실측 조건), `Jaw` `Lip` 0~1 기본 **0.6** (= angela 9, json `fixed_default`) | §5.1 D1b, §5.2 · §5.3 식, T1 · T3 |
| Q3 | 권장대로 — §3 혀 · 입술 직접 매핑 제안값 채택 | §5.3, T2 · T5 |
| Q4 | `FFF` 합산 (`lipBiteD` 0.50 직접 + `lipsRollD` 0.24 경유) | §3, T2 |
| Q5 | `COARTIC.MMM` 계수 0.80 | §3 · §5.3, T5 |
| Q6 | 새 컨트롤러 4개도 같은 시안 | §6, T8 |
| Q7 | 권장대로 — A0020 은 넣지 않고 `connect_a0020()` 만 | §5.5 D5b, T9 |
| Q8 | 권장대로 — `0010_sample_0050.mb`, 스크립트 `JUN_JALI/examples/` | §7 |

**이 확정의 효과**: 세 더미가 json 의 `nodes` 이름 · 0~1 단위와 같으므로 **A00540 이 `jali_slider_dummy_in.json` 그대로 메타휴먼 파일(0050)에 키를 넣을 수 있다** — 매핑 json 추가(옛 S6) 불필요. 아래 §2 · §3 의 가중치는 "음소 10 · Jaw/Lip 9" 기준으로 썼는데, 더미 단위로는 **음소 1.0 · Jaw/Lip 0.6** 이 같은 조건이다(값은 동일). A0020 의 `DUMMY_OUT_*`(angela 단위) 를 이을 때는 × 1/10 (비짐 · 동시조음) · × 1/15 (Jaw Lip) 로 바꾼다(D5b).

| # | 요청 (원문 요지) | 이 계획 |
|---|------------------|---------|
| R1 | 0100 과 같은 형식으로 **JALI ↔ 메타휴먼 매칭표**와 문서를 따로 만든다 | 이 문서 §2 (경유 경로 표) · §3 (직접 경로 표) · §4 (동시조음) |
| R2 | JALI 음소 이름만 가진 더미 노드 (0100 R5, 보류했던 것) | §5 D1 — `dmy_in_jali` · `dmy_in_phonemes` · `dmy_in_coartic` |
| R3 | 더미 → 매핑 노드 → headRig_grp 컨트롤러 (0100 R2 와 같은 규칙) | §5 D2 · D3 — 0040 의 `bw_dmy_* / pma_dmy_* / GRP_dmy_*` 에 합류 |
| R4 | 쓰이는 컨트롤러만 머티리얼로 색 구분 (0100 R7) | §6 — JALI 로 새로 쓰이는 컨트롤러 4개 |
| R5 | 제작 전에 계획서 | 이 문서. 생성은 §10 단계 |

---

## 1. 근거 — 양쪽 리그에서 읽은 것

### 1.1 JALI 쪽 — A0020 슬라이더 리그의 출력 허브 (0090 확정 · 실측 완료)

| 노드 | 어트리뷰트 | 단위 · 범위 | 뜻 |
|------|-----------|-------------|----|
| `DUMMY_OUT_JALI` | `Jaw` `Lip` | 0~15, 기본 **9 · 9** | 모든 음소에 곱해지는 축 — Jaw 는 턱 · 혀 성분, Lip 은 입술 근육 성분의 크기 |
| `DUMMY_OUT_PHONEMES` | `AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP SSH Schwa GK LNTD` (16) | 0~12, **10 = 그 음소를 온전히 발음** (VisemeNet · A00540 최댓값, 실측 조건) | 비짐 한 장 |
| `DUMMY_OUT_COARTIC` | `LNTD GK MMM FFF WA_PEDAL YA_PEDAL` (6) | 0~12 (`YA_PEDAL` 15) | 음소 위에 한 성분만 얹는 보정 채널 (0100 안내 §3) |

- `LNTD` `GK` `FFF` 는 PHONEMES 와 COARTIC 에 **같은 이름으로 둘 다** 있다 → 메타휴먼 쪽 입력 더미도 **노드를 셋으로 나눠야 이름이 그대로 유지**된다(§5 D1).
- `A00540_JaliLipSync` 는 VisemeNet 결과를 `CNT_PHONEMES.*` 0~10 으로 키한다 — 같은 단위를 받으면 매핑 json 의 노드 이름만 바꿔 쓸 수 있다.

### 1.2 angela 실측 — 음소가 만드는 것 (0040 §3 · 0100 안내 §2)

음소 = 10, Jaw = Lip = 9 일 때. 0040 의 ARKit 가중치는 이 표의 "입술 근육" 열을 ARKit 이름으로 바꾼 것(`jawOpen` 은 `AHH` 13.4° = 1.0 기준).

| 음소 | 턱 | 입술 근육 → ARKit | 혀 (ARKit 에 없음) |
|------|---:|-------------------|--------------------|
| AHH | 13.4° | `mouthLowerDown` 0.34 | — |
| AAA | 8.9° | `mouthLowerDown` 0.54 · `mouthDimple` 0.50 · `mouthStretch` 0.28 · `mouthUpperUp` 0.27 · `mouthSmile` 0.20 | 끝 내림, 몸통 앞쪽 살짝 올림 |
| Eh | 5.1° | `mouthLowerDown` 0.37 · `mouthStretch` 0.24 · `mouthSmile` 0.15 | 끝 내림(AAA 의 70 %) |
| IEE | 1.7° | `mouthLowerDown` 0.61 · `mouthDimple` 0.37 · `mouthStretch` 0.29 · `mouthUpperUp` 0.27 · `mouthSmile` 0.23 | 끝 내림, 뿌리 올림 |
| OHH | 7.5° | `mouthPucker` 0.41 | 몸통 크게 말림(뒤쪽 올림), 뒤로 |
| UUU | 0.8° | `mouthPucker` 0.61 · `mouthFunnel` 0.26 | 끝 올림, 뒤쪽 몸통 올림 |
| Schwa | 4.0° | — | — |
| RRR | 3.0° | `mouthFunnel` 0.42 · `mouthPucker` 0.27 | **혀끝 올림 +37°**(가장 큼), 앞으로 |
| WWW | 4.0° | `mouthPucker` 0.52 · `mouthClose` 0.37 | UUU 와 같음 |
| SSS | 0° (앞 0.15) | `mouthLowerDown` 0.66 · `mouthFunnel` 0.09 | 끝 내림(아랫니 뒤), 몸통 평평 |
| SSH | 0° (앞 0.26) | `mouthFunnel` 0.44 · `mouthPucker` 0.29 · `mouthLowerDown` 0.25 · `mouthUpperUp` 0.24 · `mouthStretch` 0.11 | 끝 올림 |
| FFF | 1.4° | `mouthDimple` 0.56 · `mouthRollLower` 0.24 · `mouthUpperUp` 0.11 · `mouthShrugLower` 0.09 | — (아랫입술을 윗니 밑으로 = `orbOris_tight_lo` · `mentalis`) |
| TTH | 1.8° | `mouthDimple` 0.54 · `mouthFunnel` 0.27 · `mouthUpperUp` 0.25 · `tongueOut` 0.30(임시) | **혀 앞으로**(tz +0.47), 몸통 아래 |
| MBP | 5.8° | `mouthClose` 0.62 · `mouthPress` 0.07 · `cheekPuff` 0.10 | — |
| GK | 4.0° | — | 뿌리 +13.7° · 몸통 +23.8° 올림, 끝 −25.6° 내림 |
| LNTD | 4.0° | — | **혀끝 +35.7° 올림**, 몸통 앞쪽 올림, 혀 위로 1.4 |
| COARTIC `WA_PEDAL` | 0 | `mouthPucker` 0.48 | — |
| COARTIC `YA_PEDAL` | 0 | `mouthStretch` 0.37 · `mouthDimple` 0.27 · `mouthSmile` 0.12 | — |
| COARTIC `MMM` | 0 | **턱 벌림 각도에 비례**해서만 입술 닫힘 (`AAA` 9° 위에서 `orbOris_up_lo` 0.85 · `_down_hi` 0.80 · `mentalis` 0.60) | — |
| COARTIC `FFF` | 0 | 턱 비례 — `AAA` 위에서 `mentalis` 1.17 · `orbOris_up_lo` 0.64 · `orbOris_tight_lo` 0.36 | — |
| COARTIC `LNTD` | 0 | — | 혀끝 **+58.7°** (PHONEMES 의 1.6배), 몸통 +49/+36°, 혀 위로 1.6 |
| COARTIC `GK` | 0 | — | 끝 **−78.4°**, 몸통 +27°, 뿌리 +22.4°, Rollback 6.6 (PHONEMES 의 3배) |

### 1.3 메타휴먼 쪽 — 0040 에 이미 있는 것 (0100 §1 · §12)

- `dmy_in`(ARKit 52) → 컨트롤러 축 71개의 `bw_dmy_<ctrl>_<axis>`(blendWeighted) → `pma_dmy_*`(컨트롤러 로컬값 + 입력) → SDK → `CTRL_expressions` → RigLogic. `GRP_dmy_<ctrl>` 로 컨트롤러 메시가 움직여 보인다.
- `blendWeighted` 는 입력을 몇 개든 더 받으므로 **JALI 쪽 값을 같은 가중치로 하나 더 꽂으면** ARKit 입력과 가산된다 — 0100 §5.5 의 설계 그대로.
- ARKit 에 없지만 **메타휴먼 GUI 에는 있는** 채널 (0100 §1.1 전수 조사):

| 메타휴먼 컨트롤러.축 | +1 / −1 | angela 의 대응 성분 |
|----------------------|---------|---------------------|
| `CTRL_C_tongue_tipMove.ty` | `tongueTipUp` / `tongueTipDown` | 혀끝 올림 · 내림 (`LNTD` `RRR` `UUU` `SSH` / `GK` `AAA` `Eh` `IEE` `SSS`) |
| `CTRL_C_tongue_bendTwist.ty` | `tongueBendUp` / `tongueBendDown` | 혀 몸통(뒤쪽) 올림 (`GK` `OHH` `UUU` `WWW`) |
| `CTRL_C_tongue_move.ty` | `tongueUp` / `tongueDown` | 혀 전체 위 · 아래 (`LNTD` 위로 1.4 / `TTH` 아래) — 0040 에서 이미 `tongueOut` 포즈가 −0.826 로 씀 |
| `CTRL_C_tongue_inOut.ty` | `tongueIn` / `tongueOut` | 혀 앞으로 (`TTH`) — 0040 에서 이미 씀 |
| `CTRL_L/R_mouth_lipBiteD.ty` | `mouthLowerLipBiteL/R` | **아랫입술을 윗니 밑으로** (`FFF`) — ARKit 의 `mouthRollLower` 보다 정확한 채널 |
| `CTRL_L/R_mouth_lipsTogetherU/D.ty` | `mouthLipsTogether*` | 턱 벌린 채 입술 닫기 (`MBP`, COARTIC `MMM`) — 0040 에서 `mouthClose` 로 이미 씀 |
| `CTRL_L/R_jaw_ChinRaiseD.ty` | `jawChinRaiseDL/R` | 턱끝근(`mentalis`) — COARTIC `FFF` 의 1.17 |

---

## 2. 매핑표 D — JALI → ARKit → 메타휴먼 (경유 경로, 수치 합성)

0040 §3 가중치(음소 10 · Jaw/Lip 9 기준)에 0100 표 A 의 ARKit → 컨트롤러 가중치를 곱해 합친 값. **음소 = 10, Jaw = Lip = 9** 일 때 컨트롤러 축에 더해지는 양이다
(다른 값이면 ×음소/10 ×Jaw/9 또는 ×Lip/9). `L/R` = 양쪽 같은 값. `tx/ty` 생략 = `ty`. 0.1 미만은 표에서 뺐다(노드에는 그대로 있다).

| 음소 | ARKit 경유 (0040) | 메타휴먼 컨트롤러 (합성값) |
|------|-------------------|----------------------------|
| **AHH** | `jawOpen` 1.00 · `mouthLowerDown` 0.34 | `CTRL_C_jaw` +1.00 · `mouth_lowerLipDepress` L/R +0.34 |
| **AAA** | `jawOpen` 0.67 · `mouthLowerDown` 0.54 · `mouthDimple` 0.50 · `mouthStretch` 0.28 · `mouthUpperUp` 0.27 · `mouthSmile` 0.20 | `CTRL_C_jaw` +0.67 · `lowerLipDepress` 0.54 · `dimple` 0.50 · `stretch` 0.28 · `upperLipRaise` 0.27 · `cornerPull` 0.20 (전부 L/R) |
| **Eh** | `jawOpen` 0.38 · `mouthLowerDown` 0.37 · `mouthStretch` 0.24 · `mouthSmile` 0.15 | `CTRL_C_jaw` +0.38 · `lowerLipDepress` 0.37 · `stretch` 0.24 · `cornerPull` 0.15 |
| **IEE** | `jawOpen` 0.13 · `mouthLowerDown` 0.61 · `mouthDimple` 0.37 · `mouthStretch` 0.29 · `mouthUpperUp` 0.27 · `mouthSmile` 0.23 | `lowerLipDepress` 0.61 · `dimple` 0.37 · `stretch` 0.29 · `upperLipRaise` 0.27 · `cornerPull` 0.23 · `CTRL_C_jaw` +0.13 |
| **OHH** | `jawOpen` 0.56 · `mouthPucker` 0.41 | `CTRL_C_jaw` +0.56 · `purseU/D` 0.41 · `funnelU/D` 0.31 · `towardsU/D` 0.17 |
| **UUU** | `mouthPucker` 0.61 · `mouthFunnel` 0.26 · `jawOpen` 0.06 | `funnelU/D` 0.72 · `purseU/D` 0.61 · `towardsU/D` 0.25 |
| **Schwa** | `jawOpen` 0.30 | `CTRL_C_jaw` +0.30 |
| **RRR** | `mouthFunnel` 0.42 · `mouthPucker` 0.27 · `jawOpen` 0.22 | `funnelU/D` 0.62 · `purseU/D` 0.27 · `CTRL_C_jaw` +0.22 · `towardsU/D` 0.11 |
| **WWW** | `mouthPucker` 0.52 · `mouthClose` 0.37 · `jawOpen` 0.30 | `purseU/D` 0.52 · `funnelU/D` 0.39 · `lipsTogetherU/D` 0.37 · `CTRL_C_jaw` +0.30 · `towardsU/D` 0.21 |
| **SSS** | `mouthLowerDown` 0.66 · `mouthFunnel` 0.09 | `lowerLipDepress` 0.66 (+ `funnelU/D` 0.09) |
| **SSH** | `mouthFunnel` 0.44 · `mouthPucker` 0.29 · `mouthLowerDown` 0.25 · `mouthUpperUp` 0.24 · `mouthStretch` 0.11 | `funnelU/D` 0.66 · `purseU/D` 0.29 · `lowerLipDepress` 0.25 · `upperLipRaise` 0.24 · `towardsU/D` 0.12 · `stretch` 0.11 |
| **FFF** | `mouthDimple` 0.56 · `mouthRollLower` 0.24 · `mouthUpperUp` 0.11 · `jawOpen` 0.11 · `mouthShrugLower` 0.09 | `dimple` 0.56 · `lipsRollD` 0.24 · `lipsRollU` 0.12 · `upperLipRaise` 0.11 · `CTRL_C_jaw` +0.11 (+ `jaw_ChinRaiseD` 0.09) |
| **TTH** | `mouthDimple` 0.54 · `tongueOut` 0.30 · `mouthFunnel` 0.27 · `mouthUpperUp` 0.25 · `jawOpen` 0.13 | `dimple` 0.54 · `funnelU/D` 0.27 · `upperLipRaise` 0.25 · `CTRL_C_tongue_move` −0.25 · `CTRL_C_tongue_inOut` −0.23 · `CTRL_C_tongue_wideNarrow` +0.19 · `CTRL_C_jaw` +0.13 |
| **MBP** | `mouthClose` 0.62 · `jawOpen` 0.43 · `cheekPuff` 0.10 · `mouthPress` 0.07 | `lipsTogetherU/D` 0.62 · `CTRL_C_jaw` +0.43 · `suckBlow` 0.10 · `lipsBlow` 0.10 (+ `pressU/D` 0.07) |
| **GK** | `jawOpen` 0.30 | `CTRL_C_jaw` +0.30 — 혀는 §3 |
| **LNTD** | `jawOpen` 0.30 | `CTRL_C_jaw` +0.30 — 혀는 §3 |
| **WA_PEDAL** | `mouthPucker` 0.48 | `purseU/D` 0.48 · `funnelU/D` 0.36 · `towardsU/D` 0.20 |
| **YA_PEDAL** | `mouthStretch` 0.37 · `mouthDimple` 0.27 · `mouthSmile` 0.12 | `stretch` 0.37 · `dimple` 0.27 · `cornerPull` 0.12 |

- 경유 경로가 건드리는 메타휴먼 컨트롤러 **44개** (전부 0040 에서 이미 시안으로 매핑된 것) — 새 노드 없이 기존 `bw_dmy_*` 에 입력만 는다.
- `mouthPucker` 가 `purse` 뿐 아니라 `funnel` 0.752 · `towards` 0.412 를 끌고 오는 것은 Epic 포즈의 성질(0100 표 A). `OHH` `UUU` 처럼 pucker 와 funnel 이 같이 있는 음소는 `funnelU/D` 가 합산돼 커진다(UUU 0.72). 과하면 0040 의 `bw_dmy_*_mouth_funnel*` 가중치가 아니라 **이 경로의 `jali_bw_mouthPucker` 가중치**를 줄인다(§5 D2).
- `tongueOut` 의 JALI 가중치 0.30 은 0040 문서대로 **임시값**(실측 없음) — §3 의 직접 경로가 혀를 맡으므로 여기서는 그대로 둔다.

---

## 3. 매핑표 E — JALI 전용 직접 매핑 (ARKit 로 옮길 수 없는 성분, **제안값**)

angela 의 혀 · 입술 실측(§1.2)을 메타휴먼의 해당 채널에 **뜻으로** 옮긴 것이다. 수치는 angela 각도를 **COARTIC `LNTD` 의 혀끝 +58.7° = 1.0** 으로 정규화했다(1° ≈ 0.017).
메타휴먼 쪽은 실측하지 않았으므로 GUI 에서 눈으로 맞춘 뒤 `jali_bw_mh_*` 가중치로 조정한다(§9 Q3). 음소 = 10, Jaw = 9 기준이고 전부 **Jaw 축**(혀는 턱 · 혀 성분)에 곱한다. 입술 깨물기(FFF)만 Lip 축.

| JALI 입력 | 메타휴먼 컨트롤러.축 (+ / −) | 값 | 근거 (angela) |
|-----------|------------------------------|---:|---------------|
| `PHONEMES.LNTD` | `CTRL_C_tongue_tipMove.ty` + (tipUp) | **0.61** | 혀끝 +35.7° |
| | `CTRL_C_tongue_move.ty` + (tongueUp) | 0.30 | 혀 위로 1.4 (COARTIC 1.6 = 0.35 기준) |
| `PHONEMES.GK` | `CTRL_C_tongue_bendTwist.ty` + (bendUp) | **0.40** | 몸통 +23.8° |
| | `CTRL_C_tongue_tipMove.ty` − (tipDown) | 0.44 | 끝 −25.6° |
| `PHONEMES.RRR` | `CTRL_C_tongue_tipMove.ty` + | **0.63** | 혀끝 +37° (가장 큼) |
| | `CTRL_C_tongue_inOut.ty` − (tongueOut) | 0.15 | 앞으로 (TTH 의 1/3 로 둠) |
| `PHONEMES.TTH` | (경유 경로의 `tongueOut` 0.30 이 이미 `inOut` −0.23 · `move` −0.25 · `wideNarrow` +0.19 를 만든다) | — | tz +0.47 — 경유값으로 충분, 추가 없음 |
| `PHONEMES.UUU` | `CTRL_C_tongue_tipMove.ty` + | 0.20 | 끝 올림 (각도 미기록, 작게) |
| | `CTRL_C_tongue_bendTwist.ty` + | 0.20 | 뒤쪽 몸통 올림 |
| `PHONEMES.OHH` · `WWW` | `CTRL_C_tongue_bendTwist.ty` + | 0.30 · 0.20 | 몸통 크게 말림 / UUU 와 같음 |
| `PHONEMES.SSH` | `CTRL_C_tongue_tipMove.ty` + | 0.20 | 끝 올림 |
| `PHONEMES.SSS` | `CTRL_C_tongue_tipMove.ty` − | 0.20 | 끝 내림(아랫니 뒤) |
| `PHONEMES.AAA` · `Eh` · `IEE` | `CTRL_C_tongue_tipMove.ty` − | 0.20 · 0.14 · 0.20 | 끝 내림 (Eh 는 AAA 의 70 %) |
| `PHONEMES.FFF` | `CTRL_L/R_mouth_lipBiteD.ty` + (lowerLipBite) | **0.50** | `orbOris_tight_lo` 0.24 + `mentalis` 0.09 — "아랫입술을 윗니 밑으로" 의 직접 채널. 경유 경로의 `lipsRollD` 0.24 는 그대로 둔다(합산) — Q4 |
| `COARTIC.LNTD` | `CTRL_C_tongue_tipMove.ty` + | **1.00** | 혀끝 +58.7° (정규화 기준) |
| | `CTRL_C_tongue_move.ty` + | 0.35 | 혀 위로 1.6 |
| `COARTIC.GK` | `CTRL_C_tongue_tipMove.ty` − | 1.00 (clamp) | 끝 −78.4° → 1.0 을 넘어 clamp |
| | `CTRL_C_tongue_bendTwist.ty` + | 0.46 | 몸통 +27° |
| `COARTIC.MMM` | `CTRL_L/R_mouth_lipsTogetherU/D.ty` + **× `CTRL_expressions.jawOpen`** | 0.80 | angela `EXP_COARTIC_Lip` = 턱 각도 비례. `AAA`(jawOpen 0.67) 위에서 0.80 × 0.67 ≈ 0.54 → 입술이 거의 닫힘(실측 0.85 는 9° 기준이라 0.80 × 0.67 보다 크다 — 실측에 맞추려면 1.2, Q5) |
| `COARTIC.FFF` | `CTRL_L/R_mouth_lipBiteD.ty` + × `jawOpen` | 0.60 | `orbOris_tight_lo` 0.36 · `orbOris_up_lo` 0.64 (턱 비례) |
| | `CTRL_L/R_jaw_ChinRaiseD.ty` + × `jawOpen` | 0.50 | `mentalis_lowerLip` 1.17 (턱 비례, 1.0 clamp 를 감안해 0.5) |
| `COARTIC.WA_PEDAL` · `YA_PEDAL` | (경유 경로로 충분) | — | 입술 근육만 — ARKit 로 다 옮겨진다 |

- 새로 쓰이는 컨트롤러 **4개**: `CTRL_C_tongue_tipMove` · `CTRL_C_tongue_bendTwist` · `CTRL_L_mouth_lipBiteD` · `CTRL_R_mouth_lipBiteD` → 0040 에 없는 `bw_dmy_* / pma_dmy_* / GRP_dmy_*` 를 새로 만들고 시안 머티리얼(§6).
  나머지(`tongue_move` · `tongue_inOut` · `lipsTogether*` · `jaw_ChinRaiseD`)는 0040 의 기존 노드에 입력만 는다.
- 혀 값의 부호 해석("+ = 올림", "tz + = 앞으로")은 0100 안내 §1 의 해석을 따른다 — angela 와 메타휴먼 양쪽 GUI 에서 한 번씩 눈으로 확인(§8 끝).

---

## 4. 왕복 · 역방향

- 역방향(`dmy_out_jali`, 메타휴먼 → JALI 음소)은 0100 Q6 에서 **뺀다**로 확정됐다. 이 문서도 입력 방향만 다룬다.
- 입력 → 0040 의 `dmy_out`(ARKit 52) 은 자동으로 따라온다: `MBP` 10 → `lipsTogether` 0.62 → `dmy_out.mouthClose` 0.62, `jawOpen` 0.43. 즉 **JALI → 메타휴먼 → ARKit** 변환기가 0050 하나로 된다(검증 T6).

---

## 5. 노드망 설계

### 5.1 D1 — 입력 더미 3개 (`|rig|DMY_grp` 아래, A0020 출력 허브와 이름 · 단위 동일)

| 노드 | 어트리뷰트 | 범위 · 기본 | A0020 에서 오는 연결 |
|------|-----------|-------------|---------------------|
| `DUMMY_IN_JALI` | `Jaw` `Lip` + **`weight`** | 0~1, 기본 **0.6 · 0.6** / `weight` 0~1 기본 1 | `DUMMY_OUT_JALI.Jaw × 1/15 → DUMMY_IN_JALI.Jaw` … (json: `Jaw` `Lip` 열) |
| `DUMMY_IN_PHONEMES` | `AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP SSH Schwa GK LNTD` | 0~1 (1.0 = angela 10) | `DUMMY_OUT_PHONEMES.X × 1/10 → DUMMY_IN_PHONEMES.X` (16, 이름 매칭) |
| `DUMMY_IN_COARTIC` | `LNTD GK MMM FFF WA_PEDAL YA_PEDAL` | 0~1 | `DUMMY_OUT_COARTIC.X × 1/10 → DUMMY_IN_COARTIC.X` (6; json 은 `YA_PEDAL` 을 안 쓴다) |
| `dmy_in_jali_arkit` | ARKit 52 | 연결됨, 채널박스 숨김 | 경유 경로의 중간 결과 (디버그) |
| `dmy_in_jali_mh` | §3 의 직접 채널 (아래 D3 목록) | 연결됨, 숨김 | 직접 경로의 중간 결과 |

| ID | 결정 | 권장 | 이유 · 대안 |
|----|------|------|------------|
| D1a | 노드 수 · 이름 | **3개**, 이름은 A00540 json 의 `nodes` 그대로 (`DUMMY_IN_PHONEMES` · `DUMMY_IN_COARTIC` · `DUMMY_IN_JALI`) — **확정 Q1** | `LNTD GK FFF` 가 두 노드에 있어 하나로는 이름을 못 지킨다. A00540 이 json 수정 없이 이 파일에 키를 넣고, A0020 `DUMMY_OUT_*` 3개와도 1:1 (`connect_a0020()`) |
| D1b | 단위 | **0~1** (json 규칙: `viseme_scale` 1, `clamp` [0,1], `jali.range` [0,1], `fixed_default` [0.6, 0.6]) — **확정 Q2** | 비짐 1.0 = angela 10, Jaw/Lip 0.6 = angela 9 로 두면 0040 §3 가중치를 **나누지 않고 그대로** 쓴다(`phoneme_unit` 1.0, `jali_unit` 0.6). angela 단위안은 기각 |
| D1c | `weight` | `DUMMY_IN_JALI.weight` 하나 — Jaw · Lip 축 배율 노드에 곱한다(`jali_md_weightJaw/Lip`) | 모든 채널이 Jaw 또는 Lip 배율을 거치므로 노드 2개로 전체를 끈다. json 은 이 어트리뷰트를 건드리지 않는다 |

### 5.2 D2 — 경유 경로: `build_jali_arkit_node` 노드망 재사용 → 0040 의 `bw_dmy_*` 에 합류

```
DUMMY_IN_PHONEMES.*  ─┐
DUMMY_IN_COARTIC.WA/YA_PEDAL ─┤→ jali_bw_<target> (음소 × 0040 가중치) → jali_md_<target> (× Jaw/0.6 또는 Lip/0.6 × weight) → jali_cl_<target> (0~1) → dmy_in_jali_arkit.<52>
DUMMY_IN_JALI.Jaw/Lip ────────┘                                                     ↓
dmy_in_jali_arkit.mouthFunnel ──→ bw_dmy_CTRL_L_mouth_funnelU_y.input[k]  (dmy_in.mouthFunnel 과 같은 가중치 1 — 0100 §5.5)
```

- `build_jali_arkit_node.build()` 를 **인자화**했다 (S2): `build(prefix='', src_plugs=None, out_node=None, jali_unit=9, phoneme_unit=10, weight_plug=None)` — 기존 호출(`build()`)은 그대로 동작,
  이 계획은 `src_plugs` 로 `DUMMY_IN_PHONEMES`(음소) · `DUMMY_IN_COARTIC`(`WA/YA_PEDAL`) · `DUMMY_IN_JALI`(Jaw Lip) 를 어트리뷰트별로 주고 `jali_unit=0.6`, `phoneme_unit=1.0` 을 쓴다.
- `jali_md_scaleJaw/Lip` = `Jaw/0.6`, `jali_md_weightJaw/Lip` = × `weight` (multDoubleLinear 2개 직렬).
- 0040 의 71개 `bw_dmy_*` 중 JALI 가 쓰는 ARKit 타겟 15개(§2)가 닿는 축에 `dmy_in_jali_arkit.<target>` 입력을 **`dmy_in.<target>` 과 같은 가중치**로 추가. 노드 추가 없음.
- 노드: `jali_bw` 15 · `jali_md` 15 + 2 scale + 2 weight · `jali_cl` 15 = **49**.

### 5.3 D3 — 직접 경로: `dmy_in_jali_mh` → 새 축 4개 + 기존 축 입력 추가

`dmy_in_jali_mh` 어트리뷰트 (0~1, 각각 §3 의 한 행 묶음) 과 만드는 식 (입력은 0~1 더미값, w = `DUMMY_IN_JALI.weight`):

| 어트리뷰트 | 식 (`jali_bw_mh_*` → `jali_md_mh_*` → `jali_cl_mh_*`) | 간다 |
|-----------|---------------------------------------------------------|------|
| `tongueTipUp` | (LNTD 0.61 · RRR 0.63 · UUU 0.2 · SSH 0.2 + CO.LNTD 1.0) × Jaw/0.6 × w | `bw_dmy_CTRL_C_tongue_tipMove_y` **+** |
| `tongueTipDown` | (GK 0.44 · SSS 0.2 · AAA 0.2 · Eh 0.14 · IEE 0.2 + CO.GK 1.0) × Jaw/0.6 × w | 〃 **−** |
| `tongueBendUp` | (GK 0.40 · UUU 0.2 · OHH 0.3 · WWW 0.2 + CO.GK 0.46) × Jaw/0.6 × w | `bw_dmy_CTRL_C_tongue_bendTwist_y` + |
| `tongueUp` | (LNTD 0.30 + CO.LNTD 0.35) × Jaw/0.6 × w | 기존 `bw_dmy_CTRL_C_tongue_move_y` + (입력 추가) |
| `tongueOutExtra` | (RRR 0.15) × Jaw/0.6 × w | 기존 `bw_dmy_CTRL_C_tongue_inOut_y` − |
| `lowerLipBite` | (FFF 0.50) × Lip/0.6 × w | `bw_dmy_CTRL_L/R_mouth_lipBiteD_y` + (새 축 2) |
| `lipsTogetherCo` | (CO.MMM 0.80) × Lip/0.6 × w × **`CTRL_expressions.jawOpen`** | 기존 `bw_dmy_CTRL_L/R_mouth_lipsTogetherU/D_y` + (4) |
| `lowerLipBiteCo` | (CO.FFF 0.60) × Lip/0.6 × w × `jawOpen` | `bw_dmy_CTRL_L/R_mouth_lipBiteD_y` + |
| `chinRaiseCo` | (CO.FFF 0.50) × Lip/0.6 × w × `jawOpen` | 기존 `bw_dmy_CTRL_L/R_jaw_ChinRaiseD_y` + |

- `× jawOpen` 은 `multDoubleLinear` 하나를 더 끼운다 (`jali_md_jaw_<attr>`, `input2 ← CTRL_expressions.jawOpen`). `jawOpen` 은 `CTRL_C_jaw` 쪽 체인이고 입술 · 턱끝 컨트롤러는 다른 체인이라 **DG 순환이 없다** (S1 에서 `cycleCheck` 로 확인).
- 새 축 4개(`tongue_tipMove.ty` · `tongue_bendTwist.ty` · `mouth_lipBiteD` L/R `.ty`)는 `build_mh_arkit_dummy.build_input_path()` 와 **같은 함수**로 만든다 — 그 함수를 "축별 입력 목록" 을 인자로 받게 일반화(S1). 양방향 축 `tipMove.ty` 는 `tongueTipUp` +1 · `tongueTipDown` −1 두 입력.
- 노드: `jali_bw_mh` 9 · `jali_md_mh` 9 · `jali_cl_mh` 9 · `jali_md_jaw` 3 + 새 축 `bw_dmy` 4 · `pma_dmy` 4 · `GRP_dmy` 4 = **42**.

### 5.4 D4 — 두 경로의 합과 clamp

- 같은 컨트롤러에 경유값과 직접값이 함께 오면(`tongue_move.ty`: TTH 경유 −0.25 + LNTD 직접 +0.30) **blendWeighted 에서 더해진다**. SDK 끝값(0100 §1.1)이 1 을 막으므로 clamp 는 중간 노드(`jali_cl_*`)에만 둔다.
- `COARTIC.GK` 의 `tongueTipDown` 1.0 과 `PHONEMES.GK` 0.44 를 같이 올리면 1.44 → SDK 끝값 1.0 — angela 에서도 둘을 같이 쓰지 않는다(0100 안내 §3.3).

### 5.5 D5 — 파일 · 입력 소스 · 색

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| D5a | 파일 | 0040 을 열어 **`0010_sample_0050.mb`** 로 저장 (0100 D4 와 같은 복사본 규칙) | 0040 은 ARKit 전용으로 남고, 0050 = ARKit + JALI |
| D5b | A0020 연결 | 스크립트 `connect_a0020(namespace)` 함수만 제공 — 0050 에 A0020 을 **넣지 않는다** | 0090 D6 과 같은 "파일 하나 = 역할 하나". 사용자가 0050 을 열고 A0020 을 레퍼런스한 뒤 한 번 호출하면 `DUMMY_OUT_* → (× 1/10, Jaw Lip × 1/15) → DUMMY_IN_*` 24개가 이름으로 이어진다 (angela 단위 → 0~1) |
| D5c | 색 | 새로 쓰이는 4개 컨트롤러도 **같은 시안** `GUI2D_mapped_shader` | "시안 = 외부 입력이 민다" 한 가지 뜻 유지. 대안 = 자홍 (1, 0, 0.8) 으로 "JALI 전용" 구분 — Q6 |

- 합계 노드 49 + 42 = **91** (0050 전체 225 + 91 = 316).

---

## 6. 머티리얼

- 0040 의 `GUI2D_mapped_shaderSG` 에 `CTRL_C_tongue_tipMoveShape` · `CTRL_C_tongue_bendTwistShape` · `CTRL_L/R_mouth_lipBiteDShape` 4개를 추가 배정 → 시안 68 → **72**, 노랑 96 → 92 (네 컨트롤러 모두 노랑이었음, 0100 §1.1 전수표).
- 경유 경로가 쓰는 44개는 이미 시안.

---

## 7. 파일 · 스크립트

| 파일 | 내용 |
|------|------|
| `07_MH_sample_02/0010_sample_0050.mb` | 결과 에셋 (0040 + JALI 더미 3 + 중간 노드 2 + 노드망 90 + 머티리얼 4) |
| `JUN_JALI/examples/build_mh_jali_dummy.py` | 생성 스크립트. `mayapy build_mh_jali_dummy.py <0040.mb> <0050.mb> [--no-direct] [--no-visual]`. Maya 안에서 `build()`. `connect_a0020(ns='')` 포함 |
| 〃 상수 | `JALI_VIA_ARKIT`(= `build_jali_arkit_node.MAPPING` import), `JALI_DIRECT = {attr: {src: weight}}`(§3 · §5.3 표), `DIRECT_TO_CTRL = {attr: [(ctrl, axis, sign)]}`, `JAW_FACTOR_ATTRS` |
| `JUN_JALI/examples/build_jali_arkit_node.py` | `build(prefix, src_plugs, out_node, jali_unit, phoneme_unit, weight_plug)` 인자화 — 기존 `build()` 동작 유지(회귀 확인: 노드 15 · 17 · 15, `MBP` 10 → `mouthClose` 0.62) |
| `JUN_JALI/examples/build_mh_arkit_dummy.py` | `ensure_axis()` · `add_inputs()` · `build_input_path(src_node, per_axis)` 로 일반화, `assign_material()` 은 있는 셰이더를 재사용 — 0040 재생성 후 0100 검증 `RESULT OK` 확인 |
| `JUN_JALI/examples/check_mh_jali_dummy.py` | 검증 §8 |
| `docs/0110_jali_mh_dummy_plan.md` | 이 문서. 완료 후 §0-A · §12 |

생성 순서: ① 0040 열기(`embeddedRL4` · `dmy_in` 존재 확인) → ② 더미 3 + 중간 2 → ③ 경유 노드망(D2) → ④ 직접 노드망(D3) → ⑤ 기존 `bw_dmy_*` 입력 추가 → ⑥ 머티리얼 → ⑦ 저장 → ⑧ check.

---

## 8. 검증 (mayapy, `check_mh_jali_dummy.py`)

| # | 검사 | 기준 |
|---|------|------|
| T1 | 더미 이름 · 어트리뷰트 | `DUMMY_IN_PHONEMES` = `build_jali_slider_ctl.PHONEMES` 16(순서 포함), `DUMMY_IN_COARTIC` = `COARTIC` 6, `DUMMY_IN_JALI` = `Jaw Lip weight`, 범위 0~1, Jaw/Lip 기본 0.6 |
| T2 | 입력 → 컨트롤러 (경유 + 직접) | 입력 하나 = 1.0 (Jaw Lip 0.6, 나머지 0) 22개 + 조합 3개 → `CTRL_expressions` 252개 변화량이 **예측식(§2 경유 + §3 직접)** 과 0.01 이내 — `dmy_in` 은 0 |
| T3 | 축 배율 | `Jaw` 0.3 → `jawOpen` 절반, 입술 그대로; `Lip` 0.3 → 입술 절반, 턱 그대로; `weight` 0 → 전부 0 |
| T4 | 직접 경로 (T2 에 포함, 대표값은 INFO 로 출력) | `LNTD` 1 → `tongueTipUp` 0.61 · `tongueUp` 0.30; `GK` 1 → `tongueBendUp` 0.40 · `tongueTipDown` 0.44; `FFF` 1 → `mouthLowerLipBiteL/R` 0.50 (+ `lipsRollD` 0.24 경유) |
| T5 | 동시조음 턱 비례 | `COARTIC.MMM` 1 단독 → `lipsTogether*` 0; `AAA` 1 + `MMM` 1 → `lipsTogether*` = 0.80 × 0.67 = 0.536; `COARTIC.LNTD` 1 → `tongueTipUp` 1.0 |
| T6 | ARKit 출력 연동 | `MBP` 1 → `dmy_out.mouthClose` 0.62 · `dmy_out.jawOpen` 0.43 |
| T7 | 손 조작 · 시각 · 0040 회귀 | `dmy_in.jawOpen` · `mouthFunnel` 1 → 1.0 그대로; 매핑된 축(71 + 4) 모두 연결되지 않음; 손 0.3 + `LNTD` 1 → `tongueTipUp` 0.91; `GRP_dmy_CTRL_C_tongue_tipMove` 아래에 컨트롤러 |
| T8 | 머티리얼 · 리그 보존 · 순환 | 시안 72 · 노랑 92 · 주황 15, `embeddedNodeRL4` 2 · joint 1212 · mesh 520 · unknown 101, `cycleCheck -all` 없음 |
| T9 | A0020 연결 | 0050 에 A0020(ns `JALI`) 레퍼런스 → `connect_a0020('JALI')` → 24 연결, `JALI:CTL_PH_MBP.ty = 10/12`(출력 10 → × 1/10 = 1.0) → `lipsTogether*` 0.62, `DUMMY_OUT_JALI.Jaw` 9 → `DUMMY_IN_JALI.Jaw` 0.6 |

사용자 GUI 확인: 0050 을 열어 `dmy_in_phonemes.LNTD` · `GK` · `RRR` 를 올렸을 때 혀 모양이 angela(0100 안내 §2.1)와 같은 뜻으로 움직이는지(§3 부호 해석), `FFF` 에서 아랫입술이 윗니 밑으로 들어가는지, `AAA` + `COARTIC.MMM` 에서 입술만 닫히는지.

---

## 9. 확인이 필요한 것 (답을 받으면 §0-A 확정표로 올린다)

| # | 질문 | 권장 |
|---|------|------|
| Q1 | 입력 더미를 **3개**(`dmy_in_jali` · `_phonemes` · `_coartic`, A0020 와 이름 1:1)로 (D1a) | 3개 |
| Q2 | 단위 — angela 단위(0~12 · 15, 기본 Jaw Lip 9) vs 0~1 (D1b) | angela 단위 |
| Q3 | §3 혀 · 입술 직접 매핑 **제안값** 채택 (눈으로 본 뒤 가중치 조정 전제) | 채택 |
| Q4 | `FFF` — `lipBiteD` 0.50 직접 + 경유 `lipsRollD` 0.24 **둘 다** vs 직접만 | 둘 다 (합산) |
| Q5 | `COARTIC.MMM` 계수 0.80 (jawOpen 0.67 에서 0.54) vs 1.2 (angela 실측 0.85 에 맞춤) | 0.80 — 과하면 입술이 뚫고 들어간다, 눈으로 확인 후 조정 |
| Q6 | 새 컨트롤러 4개 색 — 같은 시안 vs 자홍 "JALI 전용" (D5c) | 같은 시안 |
| Q7 | A0020 은 0050 에 넣지 않고 `connect_a0020()` 함수만 (D5b) | 그대로 |
| Q8 | 결과 파일 `0010_sample_0050.mb`, 스크립트 `JUN_JALI/examples/` | 그대로 |

---

## 10. 단계

| 단계 | 할 일 | 결과물 |
|------|-------|--------|
| S0 | §9 답 확인 → §0-A 확정표 | 이 문서 갱신 |
| S1 | `build_mh_arkit_dummy.build_input_path()` 일반화 (소스 노드 · 축별 입력 인자) — 0040 재생성해 0100 검증 재통과 확인 | 스크립트 수정 |
| S2 | `build_jali_arkit_node.build()` 인자화 (`src_plugs` · `out_node` · `prefix`) — 기존 `out/jali_arkit_mapping.ma` 재생성해 동일 확인 | 스크립트 수정 |
| S3 | `build_mh_jali_dummy.py` — 더미 3 · 경유(D2) · 직접(D3) · 머티리얼 · `connect_a0020()` | 스크립트 |
| S4 | mayapy 로 0040 → 0050, `check_mh_jali_dummy.py` T1~T9 | `0010_sample_0050.mb` + 검증 로그 |
| S5 | 사용자 GUI 확인(§8 끝) → §3 가중치 조정 → §12 기록 | 완료 |
| S6 | (불필요해짐) — 더미가 `jali_slider_dummy_in.json` 의 이름 · 단위와 같아 A00540 이 그 json 으로 0050 에 바로 키를 넣는다 | — |

---

## 11. 알려진 위험

- **§3 은 전부 제안값**이다 — angela 의 혀 각도를 메타휴먼 혀 컨트롤러 0~1 로 옮기는 비율(58.7° = 1.0)은 가정. 메타휴먼 혀가 더 크게 움직이면 전체를 0.7 배 등으로 줄인다(`jali_bw_mh_*` 가중치 또는 `dmy_in_jali.weight`).
- 혀 부호 해석(0100 안내 §1: `LNTD` 의 혀끝 방향 = "올림")이 틀리면 §3 의 `tipMove` 부호가 통째로 뒤집힌다 — T4 는 수치만 보므로 **GUI 확인이 필수**.
- `× jawOpen` 노드가 `CTRL_expressions` 를 읽는다 — `CTRL_C_jaw` 체인과 입술 체인은 분리돼 있어 순환이 없지만, 나중에 `jawOpen` 을 입술 쪽에서 미는 매핑을 추가하면 순환이 생긴다. `cycleCheck` 를 T8 에 둔다.
- 경유 경로의 `mouthPucker` 는 Epic 포즈 때문에 `funnel` · `towards` 를 함께 끈다 — `OHH` `UUU` `WWW` `RRR` `SSH` `WA_PEDAL` 이 겹치는 입(둥근 입)에서 `funnelU/D` 가 커질 수 있다. 조정은 `jali_bw_mouthPucker` 가중치에서.
- `tongueOut` 의 JALI 가중치 0.30(TTH) 은 0040 부터 임시값이다.
- A0020 `global_scale` 과 이 문서의 `DUMMY_IN_JALI.weight` 는 둘 다 세기 배율이다 — 두 리그를 이으면 곱해진다. 보통 한쪽만 쓴다.
- A0020 의 슬라이더 꼭대기는 `output_max` 12 = angela 12 → 이 더미로는 **1.2** 가 들어온다(0040 §3 가중치의 1.2배, SDK 끝값 1 이 막는다). VisemeNet 1.0 = angela 10 을 지키려면 A0020 의 `output_max` 를 10 으로 두거나 `global_scale` 0.83 을 쓴다.

---

## 12. 구현 · 검증 결과 (2026-10-22, 이 PC · mayapy 2024)

- 결과 파일 **`07_MH_sample_02/0010_sample_0050.mb`** (28.2 MB) = 0040 + JALI. 0040 · 0030 은 그대로.
- 스크립트: `examples/build_mh_jali_dummy.py` (`DIRECT` · `DIRECT_TO_CTRL` 상수 = §3 · §5.3, `connect_a0020()`), `examples/check_mh_jali_dummy.py`.
  S1 · S2 의 일반화는 회귀 확인 — 0040 재생성 → 0100 검증 `RESULT OK`, `build_jali_arkit_node.build()` 기본 호출 노드 15 · 17 · 15 · `MBP` 10 → `mouthClose` 0.62.
- 만든 것: `DUMMY_IN_JALI` (Jaw Lip 0.6, weight) · `DUMMY_IN_PHONEMES` 16 · `DUMMY_IN_COARTIC` 6 · `dmy_in_jali_arkit` 52 · `dmy_in_jali_mh` 9;
  `jali_bw_*` 24 · `jali_md_*` 28 · `jali_cl_*` 24 · `jali_mdjaw_*` 3; 경유 경로가 0040 의 45개 축에 입력 49개 추가; 새 컨트롤러 4개(`tongue_tipMove` · `tongue_bendTwist` · `mouth_lipBiteD` L/R)에 `bw_dmy/pma_dmy/GRP_dmy` → 합계 `bw_dmy_*` 75 · `GRP_dmy_*` 72. 시안 68 → 72, 노랑 96 → 92.
- `check_mh_jali_dummy.py` → **`RESULT OK`** (T1 · T2 25 케이스 × 252 채널 · T3 · T5 · T6 · T7 · T8 · T9).
  - 대표값(입력 1.0, Jaw Lip 0.6): `MBP` → `lipsTogether*` 0.620 · `jawOpen` 0.430; `LNTD` → `tongueTipUp` 0.610 · `tongueUp` 0.300 · `jawOpen` 0.300;
    `GK` → `tongueBendUp` 0.400 · `tongueTipDown` 0.440; `FFF` → `mouthLowerLipBiteL` 0.500 · `mouthLowerLipRollInL` 0.240 · `mouthDimpleL` 0.560;
    `AAA` + `COARTIC.MMM` → `lipsTogether*` 0.536 (= 0.80 × 0.67), `MMM` 단독 0.
  - `cycleCheck -all` 순환 없음(`× jawOpen` 노드 3개 포함). 손 조작 자유(75축 모두 비연결).
  - T9: A0020 을 `JALI` 네임스페이스로 레퍼런스 → `connect_a0020('JALI')` 24 연결, `CTL_PH_MBP.ty` 10/12 → `lipsTogether*` 0.62, `Jaw` 9 → 0.6.
- **미확인 (사용자 GUI)**: §3 혀 부호 해석 — 0050 에서 `DUMMY_IN_PHONEMES.LNTD` · `GK` · `RRR`, `DUMMY_IN_COARTIC.LNTD` · `GK` 를 올려 혀가 angela 와 같은 뜻으로 움직이는지, `FFF` 의 아랫입술, `AAA` + `COARTIC.MMM` 의 입술 닫힘. 틀리면 `build_mh_jali_dummy.DIRECT` 의 값 · `DIRECT_TO_CTRL` 의 부호만 고쳐 다시 생성.
- A00540 로 키 넣기: 0050 을 열고 `jali_slider_dummy_in.json` 을 고르면 `DUMMY_IN_*` 세 노드에 바로 키가 들어간다 (A00540 쪽 변경 없음 — 실제 실행은 아직 안 해 봤다).
