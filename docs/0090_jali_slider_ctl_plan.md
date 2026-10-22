# JALI 슬라이더 컨트롤러 리그 — 제작 계획서

> **작성** 2026-10-22 · 상태: **S4 완료 — 파일 생성 · 자동 검증 301 항목 통과 (2026-10-22), S5 사용자 GUI 확인 대기** · 대상 Maya 2024 (mayapy 로 생성 · 검증)
> 결과물: `C:\Users\USER\Desktop\JP\0035_maya_src_rig\02_Cage_JALI\A0020_jali_slider_ctl.ma` (배치 미리보기 `.ref/A0020_layout_preview.png`)
> · **direct 버전** `A0020_jali_slider_ctl_direct.ma` (2026-10-22, §0-A C8 — 키가 컨트롤러 ty 에 직접 붙는 버전)
> · **direct + ARKit 버전** `A0030_jali_slider_ctl_direct_arkit.ma` (2026-10-22, §0-A C9 — `ARKIT_OUT` 52 를 같은 파일에서 출력)
> 생성 · 검증 스크립트: `examples/build_jali_slider_ctl.py` (`mayapy build_jali_slider_ctl.py [--direct] [--arkit] <out.ma>` /
> `--verify [--direct] [--arkit] <out.ma>`, direct 파일 베이크 = `bake_ctl_keys()`)
> 참고: 같은 폴더 `.ref/ref_01.png`(모양) · `0001_PJ_portfolio/0040_JULI/scenes/angela_JALI.ma`(어트리뷰트) ·
> 같은 폴더 `A0010_jali_arkit_mapping_ctl.ma`(지금 쓰는 JaLi 2D 박스 + JALI_IN → ARKIT_OUT 노드망, `examples/build_jali_arkit_node.py` 가 만든 것)

---

## 0-A. 확정 사항 (2026-10-22 사용자 답)

| # | 질문 | 확정 |
|---|------|------|
| Q1 | 더미 노드 | **3쌍** `DUMMY_IN/OUT_JALI` · `_PHONEMES` · `_COARTIC` |
| Q2 | 더미 입력 방식 · 단위 | **부모 `_drv` 그룹을 민다 · 0~1** (권장안) |
| Q3 | `Project` `Enunciate` `dummy` | **뺀다** → 슬라이더 22개 |
| Q4 | COARTIC 라벨 | **ref 식 `LNTDm GKm MMMm FFFm WAp YAp` + 묶음 머리글 `PHONEMES` · `COARTIC` · `JALI`** |
| Q5 | `global_scale` | **만든다** — `JALI_SLIDER_RIG.global_scale`(기본 1, min 0, 키 가능). 비짐 22개 출력에만 곱하고 **Jaw / Lip 은 곱하지 않는다**(축 배율은 비짐 세기가 아니라 비중이라 뜻이 달라진다) |
| Q6 | 파일 · 스크립트 위치 | `02_Cage_JALI/A0020_jali_slider_ctl.ma` · `JUN_JALI/examples/build_jali_slider_ctl.py` |
| Q7 | 기본 `output_max` | angela 범위 (12 · YA_PEDAL 15 · Jaw/Lip 15). 10 등으로 내리는 것은 마야에서 사용자가 직접(2026-10-22) |
| C7 | JaLi 기본값 자리 (2026-10-22, A00540 v01.01 계획) | **`CNT_JaLi` 휴식 위치 0, `DUMMY_IN_JALI.Jaw/Lip` 기본값 0.6** → 출력 기본 9 그대로, 데이터 키가 기본값을 덮으므로 더해지지 않는다. 검증 305 항목 |
| C8 | **direct 버전** (2026-10-22 요청) — "drv 가 키를 받는 버전이 아니라 컨트롤러 ty 에 키가 직접 붙는 버전" | `A0020_jali_slider_ctl_direct.ma` 를 **같은 스크립트 `--direct`** 로 추가 생성. §6.4 D3 의 **대안(`CTL.ty` 직결)** 을 채택: `_drv` · `pma_*` 없음, `DUMMY_IN.X → CTL_<tag>.ty → rv → gs → DUMMY_OUT` (JaLi 는 `DUMMY_IN_JALI.Jaw/Lip → CNT_JaLi.tx/ty`). 컨트롤러 ty 는 연결 상태라 손으로는 못 만지고, **`bake_ctl_keys()`**(DUMMY_IN 의 animCurve 를 통째로 복사, 없으면 `bakeResults`) 또는 Maya *Bake Simulation* 으로 베이크하면 **키가 컨트롤러에 그대로 남고** DUMMY_OUT 은 컨트롤러를 따라간다. 검증 `--verify --direct` **473 항목 통과**(T7 베이크 포함). 원본 A0020 은 그대로(305 통과 재확인) |
| C9 | **direct + ARKit 버전** (2026-10-22 요청) — "A0010 을 거치지 않고 같은 파일이 JALI 규칙 값과 ARKit 52 값을 둘 다 출력" | `A0030_jali_slider_ctl_direct_arkit.ma` = `--direct --arkit`. `JALI_DUMMY_GRP` 아래 **`ARKIT_OUT`**(ARKit 52, 0~1) 을 더하고 `build_jali_arkit_node.build(src_plugs=DUMMY_OUT_*, out_node=ARKIT_OUT, jali_unit 9, phoneme_unit 10)` 로 A0010 과 **같은 노드망**(`bw_* 15 · md_* 17 · cl_* 15`) 을 **`DUMMY_OUT_JALI/PHONEMES/COARTIC`(angela 단위)** 에 직접 붙였다. `JALI_IN` · `JALI_ARKit_GRP` 는 없다. 그래서 `output_min/max` · `global_scale` 이 ARKit 쪽에도 먹고, 컨트롤러를 베이크한 뒤에도 `ARKIT_OUT` 이 컨트롤러 키를 따라간다. 매핑 가중치는 0040 §3 그대로(`bw_<target>.weight[i]`, 아바타에 맞춰 노드에서 수정). 검증 `--verify --direct --arkit` **495 항목 통과**(T8: 52 타겟 전부 A0010 식과 일치 · 축 배율 · global_scale · output_max · 페달 · 베이크 뒤 jawOpen). A0010 · A0020 · A0020_direct 는 그대로 |

## 0-B. 실측 결과 (2026-10-22, mayapy 2024)

| 항목 | 결과 | 설계에 준 영향 |
|------|------|----------------|
| V1 `textCurves` | **된다** (`f="Arial"`, 28.1pt 로 대체 경고만) | 라벨 · 머리글을 스크립트가 만든다 |
| V2 `remapValue` 입력 클램프 | **된다** — 입력 1.3 → `outputMax`, −0.2 → `outputMin`. `setRange` 도 같다 | `clamp` 노드 불필요 |
| V3 부모 ty 연결 + 자식 ty | 자식 `ty` settable, 월드 y = 합 | D3 그대로 |
| T1~T6 (§7) | **301 항목 0 실패** — 저장한 `.ma` 를 다시 열어 검사 | — |

---

## 0. 요청 정리

| # | 요청 | 이 계획 |
|---|------|---------|
| R1 | `.ref/ref_01.png` 와 비슷한 모양의 슬라이더 컨트롤러 | §3 모양, §4 배치 |
| R2 | 컨트롤러 = `angela_JALI.ma` 의 `CNT_PHONEMES` · `CNT_COARTIC` 어트리뷰트와 1:1 | §2 목록 |
| R3 | JALI 를 다루는 데 더 필요한 컨트롤러가 있으면 제시 | §5 |
| R4 | 컨트롤러마다 `output_min` · `output_max` — `ty ∈ [0,1]` 을 `[output_min, output_max]` 로 리맵 | §6.2 |
| R5 | 컨트롤러 → 매핑 노드 → **더미 출력 노드** (어트리뷰트 이름 = 원본 이름). 블렌드셰이프 등에 한 번에 연결하는 허브 | §6.1, §6.3 |
| R6 | **더미 입력 노드** `.AAA` → 컨트롤러 `AAA` 의 y 위치. 외부에서 한 번에 넣는 허브 | §6.4 |
| R7 | 제작 전에 계획서 | 이 문서 |

---

## 1. 실측 — 참고 자료에서 읽은 것 (2026-10-22)

### 1.1 `ref_01.png`

- 세로 슬라이더 **24개 = 2줄 × 12**. 각 슬라이더 = 세로 트랙(선) + 위아래 끝 가로 눈금 + 트랙 위를 오르내리는 작은 가로 바(컨트롤러) + 아래 글자 라벨.
- 라벨: 윗줄 `A Eh IE IH AH S SH JY TH U OH UH`, 아랫줄 `Schwa LN DT LNTDm GKm BP MMMm FFFm R W WAp YAp`.
- 이 라벨은 VisemeNet 식 24 비짐 묶음이고 **angela 의 어트리뷰트 집합(16 + 6)과 다르다.** `…m` 접미사 4개(`LNTDm GKm MMMm FFFm`)와
  `WAp YAp` 는 angela 의 `CNT_COARTIC` 6개와 짝이 맞는다. → **모양만 따르고 어트리뷰트는 angela 를 따른다**(R2).

### 1.2 `angela_JALI.ma` — `CNT_PHONEMES` · `CNT_COARTIC`

| 노드 | 어트리뷰트 (파일 순서) | 범위 | 비고 |
|------|------------------------|------|------|
| `CNT_PHONEMES` | `AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP SSH Schwa GK LNTD` (16) | 0 ~ 12 | 전부 하류(`MULT_LIP_* / MULT_JAW_* / MULT_TNG_*`, `ADD_LoLip_Ventriloquy`)에 연결됨 |
| `CNT_PHONEMES` | `Project` `Enunciate` | 0 ~ 1.5 (현재값 2 · 1.75) | **하류 연결 없음** (grep 결과 0건) |
| `CNT_PHONEMES` | `dummy` | 제한 없음 | **하류 연결 없음**, 자리표시용 |
| `CNT_PHONEMES` | `SHAPES ____ _____ ______` | enum | 채널박스 구분선 — 어트리뷰트 아님 |
| `CNT_COARTIC` | `LNTD` | 0 ~ 12 | 혀(`FC_ton*`)에 연결 |
| `CNT_COARTIC` | `GK` | **−5** ~ 12 | 혀에 연결 |
| `CNT_COARTIC` | `MMM` `FFF` `WA_PEDAL` | 0 ~ (max 없음) | `MULT_MMM_COARTIC` 등 |
| `CNT_COARTIC` | `YA_PEDAL` | 0 ~ **15** | `MULT_LIP_YA_PEDAL` |
| `CNT_JaLi` | `translateX` = Jaw, `translateY` = Lip | 0 ~ 15 (기본 9, 9), 트랜스폼 제한 | `FC_JAW_Normalize` · `FC_LIP_Normalize` |

- **이름 충돌**: `LNTD` `GK` `FFF` 가 두 노드에 모두 있다. 노드 하나에 같은 이름을 두 번 둘 수 없으므로 더미 노드는 원본처럼
  **PHONEMES / COARTIC 두 노드로 나눠야 이름이 "똑같이" 유지된다** (§6.1 D1).
- VisemeNet → angela 매핑(`A00540` 의 `angela_jali_visemenet.json`)은 비짐을 **0~10** 으로 넣는다(리그 최대 12 는 안 씀).

### 1.3 `A0010_jali_arkit_mapping_ctl.ma` (지금 02_Cage_JALI 에 있는 것)

- `JALI_CTL_GRP`: `CNT_JaLi`(2D 박스, tx/ty 0~15 제한, 기본 9,9) + 박스 테두리 · `Jaw` `Lip` 글자 커브.
- `JALI_SPEECH_CTL_GRP`: `CNT_PHONEMES`(16) · `CNT_COARTIC`(6) — **모양 없는 트랜스폼, 채널박스로만 조절**. 이번 요청이 이 둘을 슬라이더로 바꾸는 것.
- `JALI_IN`(Jaw Lip + 16 + WA/YA_PEDAL = 20) → `bw_* / md_* / cl_*` → `ARKIT_OUT`(52). `CNT_COARTIC.LNTD GK MMM FFF` 는 **연결 안 됨**(이름 충돌을 피해 간 것).
- `JALI_IN` 이 사실상 "더미 출력 노드" 역할을 이미 하고 있다 → 새 파일의 `DUMMY_OUT_*` 가 이 자리를 이어받고, ARKit 노드망은 소비자로 분리한다(§6.5 D6).

---

## 2. 컨트롤러 · 어트리뷰트 목록 (안)

슬라이더 **22개** + JaLi 2D 박스 1개. 컨트롤러 이름은 충돌을 피해 그룹 접두사를 붙이고, **더미 노드의 어트리뷰트 이름은 원본 그대로**.

| 그룹 | 컨트롤러 (안) | 더미 어트리뷰트 | `output_min` 기본 | `output_max` 기본 | 근거 |
|------|---------------|-----------------|------------------:|------------------:|------|
| PHONEMES | `CTL_PH_AAA` … `CTL_PH_LNTD` (16) | `AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP SSH Schwa GK LNTD` | 0 | 12 | angela 범위 |
| COARTIC | `CTL_CO_LNTD` `CTL_CO_GK` `CTL_CO_MMM` `CTL_CO_FFF` `CTL_CO_WA_PEDAL` | `LNTD GK MMM FFF WA_PEDAL` | 0 | 12 | angela 범위(max 없는 것은 A0010 과 같이 12) · GK 의 −5 는 슬라이더가 0 에서 시작하므로 안 씀 |
| COARTIC | `CTL_CO_YA_PEDAL` | `YA_PEDAL` | 0 | 15 | angela 범위 |
| JALI | `CNT_JaLi` (2D 박스, tx = Jaw, ty = Lip, 둘 다 0~1) | `Jaw` `Lip` | 0 | 15 | angela 범위, 기본 위치 (0.6, 0.6) = 9, 9 |

- 제외(권장): `Project` `Enunciate` `dummy` — angela 에서 **어디에도 연결돼 있지 않다**(§1.2). 넣으면 슬라이더 24개 = ref 와 같은 2×12 가 되긴 한다 → §8 Q3.
- 각 슬라이더 공통 어트리뷰트: `output_min` `output_max` (double, 채널박스 표시, **키 불가**). 2D 박스는 축이 둘이라 `jaw_output_min/max` `lip_output_min/max` 4개.
- 각 슬라이더의 `translateY` 만 열림(제한 0~1, `minTransLimit/maxTransLimit`). `tx tz rx ry rz sx sy sz v` 는 잠금 · 채널박스 숨김.

---

## 3. 슬라이더 한 개의 모양 (ref 와 같게)

```
   ──┬──   ← 윗 눈금 (ty = 1)
     │
     │     ← 트랙 (세로 선, 길이 1 단위) — 선택 안 되게 displayType = Reference
     │
   ──┼──   ← 컨트롤러 (가로 바, 폭 0.6, 선택 · 드래그 대상)  시작 위치 ty = 0
   ──┴──   ← 아랫 눈금 (ty = 0)
    AAA    ← 라벨 (textCurves, Reference)
```

- 트랙 · 눈금 · 라벨 = `nurbsCurve` 1차, 오버라이드 `displayType = Reference`(2) 로 클릭이 안 통과되지 않게.
- 컨트롤러 = 가로 바 커브(1차, 2 CV). 색은 PHONEMES / COARTIC / JaLi 세 그룹을 오버라이드 색으로 구분.
- 라벨 글자 = `textCurves` (A0010 의 `Text_Jaw` 와 같은 방식). **mayapy 에서 `textCurves` 가 되는지 먼저 확인**(§7 V1). 안 되면 라벨만 GUI 세션에서 붙인다.
- COARTIC 라벨 표기: ref 처럼 `LNTDm GKm MMMm FFFm WAp YAp` 로 할지, 어트리뷰트 이름 그대로(`LNTD` … 와 `COARTIC` 묶음 머리글)로 할지 → §8 Q4.

---

## 4. 배치 (안)

```
JALI_SLIDER_RIG                              ← 루트 (옮기기 · 크기 조절용, 트랜스폼 열어 둠)
├── JALI_CTL_GRP
│   ├── JaLi 2D 박스  (A0010 의 JaliInnerBorder · CNT_JaLi 를 0~1 로 바꿔 옮김)      [왼쪽]
│   ├── PH_<attr>_grp ×16   ─ 윗줄  (AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP)
│   │                        ─ 아랫줄 (SSH Schwa GK LNTD)
│   └── CO_<attr>_grp ×6    ─ 아랫줄 이어서, 사이 간격 1칸 (LNTD GK MMM FFF WA_PEDAL YA_PEDAL)
│       └── PH_<attr>_grp
│           ├── PH_<attr>_track / _tick_lo / _tick_hi / _label     (Reference)
│           └── PH_<attr>_drv                                      ← DUMMY_IN 이 미는 그룹 (§6.4)
│               └── CTL_PH_<attr>                                  ← 애니메이터가 잡는 것
├── JALI_DUMMY_GRP
│   ├── DUMMY_IN_JALI · DUMMY_IN_PHONEMES · DUMMY_IN_COARTIC       (모양 없음, 어트리뷰트만)
│   └── DUMMY_OUT_JALI · DUMMY_OUT_PHONEMES · DUMMY_OUT_COARTIC
└── (DG 노드) pma_<attr>, rv_<attr>                                  (§6)
```

- 칸 간격 x = 1.5, 줄 간격 y = 2.5 (트랙 1 + 라벨 + 여백). 아랫줄 = PHONEMES 4 + 빈 칸 1 + COARTIC 6 = 11칸 (윗줄 12 칸보다 1칸 짧다).
- ref 는 2×12 이지만 angela 어트리뷰트가 22개라 그대로는 못 맞춘다. `Project` `Enunciate` 를 넣으면 24 (§8 Q3).

---

## 5. 추가로 제안하는 컨트롤러 (R3)

| 제안 | 왜 필요한가 | 권장 |
|------|-------------|------|
| **`CNT_JaLi` 2D 박스 (Jaw × Lip)** | JALI 의 핵심 — 비짐은 이 두 축 값으로 턱 / 입술 비중이 곱해진다(`angela` 실측: Jaw 2→14 에 턱 2.4°→16.7°). A0010 에 이미 있다 | **포함** (tx/ty 를 0~1 로 바꾸고 `output_min/max` 0~15 리맵, 기본 0.6 = 9) |
| 루트 트랜스폼 `JALI_SLIDER_RIG` | 얼굴 리그 패널 옆에 통째로 옮기고 크기를 맞추는 용도. 별도 "마스터 컨트롤러" 는 없어도 된다 | 포함 (그룹만) |
| `Project` `Enunciate` 슬라이더 | angela 에 어트리뷰트는 있지만 **연결이 없어서 지금은 아무 일도 안 한다** | 제외 (Q3) |
| 혀 · 눈썹 등 (`CNT_tongue` `CNT_UPFACE` …) | 립싱크 밖 | 제외 (범위 밖) |
| 전체 배율 하나 (`global_scale`) | "출력 전체를 한 번에 줄이기" — `output_max` 를 22개 따로 바꾸는 수고를 던다 | **포함 (Q5 확정)** — `JALI_SLIDER_RIG.global_scale`, `rv_*` 뒤에 `gs_*`(`multDoubleLinear`) 하나씩. Jaw / Lip 제외 |

---

## 6. 노드망 설계

### 6.1 D1 — 더미 노드는 원본처럼 셋으로

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| D1 | 더미 노드 개수 | **3쌍** `DUMMY_IN/OUT_JALI`(Jaw Lip) · `_PHONEMES`(16) · `_COARTIC`(6) | `LNTD GK FFF` 충돌 때문에 한 노드로는 이름을 그대로 못 둔다(§1.2). 원본의 두 컨트롤러 구조와 같아서 `A00540` 매핑 json 의 `CNT_PHONEMES.X` → `DUMMY_IN_PHONEMES.X` 치환이 기계적이다 |
| | 대안 | 2쌍 (Jaw Lip 을 PHONEMES 노드에 얹음 = A0010 의 `JALI_IN` 과 같은 모양) | 노드가 하나 줄지만 "원본 어트리뷰트와 똑같이" 에서 벗어난다 |

### 6.2 D2 — 매핑 노드 = `remapValue`

```
CTL_PH_AAA.output_min ──→ rv_AAA.outputMin
CTL_PH_AAA.output_max ──→ rv_AAA.outputMax
(ty 합, §6.4)         ──→ rv_AAA.inputValue   (inputMin 0, inputMax 1, value 램프 기본 = 선형)
rv_AAA.outValue       ──→ DUMMY_OUT_PHONEMES.AAA
```

- 요청의 의미(`[0,1] → [min,max]`)와 어트리뷰트 이름(`outputMin/outputMax`)이 그대로 맞는다. 램프를 두면 나중에 슬라이더별 이징도 넣을 수 있다.
- 대안 `setRange`(`oldMin/oldMax/min/max`) — 같은 일, 램프 없음. 둘 다 입력을 범위로 **클램프**하는지 §7 V2 에서 실측.
- 슬라이더당 노드: `pma_<tag>`(§6.4) 1 + `rv_<tag>` 1 + `gs_<tag>`(global_scale) 1 = 3개 × 22 + JaLi 2축 4개(gs 없음) = **70 DG 노드**. tag = `PH_AAA` · `CO_LNTD` · `JALI_Jaw`.

### 6.3 더미 출력 노드

- `DUMMY_OUT_PHONEMES` : `AAA … LNTD` 16개 (double, 키 가능, 범위 제한 없음 — 리맵 결과를 그대로 받음).
- `DUMMY_OUT_COARTIC` : `LNTD GK MMM FFF WA_PEDAL YA_PEDAL`. `DUMMY_OUT_JALI` : `Jaw Lip`.
- 소비자 연결 예: `DUMMY_OUT_*.X → JALI_IN.X`(A0010 ARKit 노드망, 이름이 같으니 이름 매칭 한 번) · `A00550 PoseMapper` 의 Source 노드로 지정.

### 6.4 D3 — 더미 입력은 컨트롤러 **위의 그룹**을 민다 (직결 아님)

```
DUMMY_IN_PHONEMES.AAA ──→ PH_AAA_drv.translateY          (drv 그룹이 올라가면 컨트롤러도 보이는 위치가 올라간다)
PH_AAA_drv.translateY ──→ pma_AAA.input1D[0]  ┐
CTL_PH_AAA.translateY ──→ pma_AAA.input1D[1]  ┴→ pma_AAA.output1D ──→ rv_AAA.inputValue
```

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| D3 | `DUMMY_IN.X` 가 미는 곳 | **`<attr>_drv` 그룹의 ty** (컨트롤러 부모) | `CTL.ty` 에 직결하면 ty 가 "연결됨" 상태가 되어 **뷰포트 드래그 · 수동 키가 막힌다.** 부모를 밀면 외부 입력(VisemeNet 키 등) 위에 애니메이터가 손으로 더할 수 있고, 슬라이더가 눈에 보이게 움직인다 |
| | 대안 | `CTL.ty` 직결 | 노드 2개 덜 쓰지만 컨트롤러를 손으로 못 만진다. "더미 입력만 쓰고 손은 안 댄다" 가 확실할 때만 |
| D4 | `DUMMY_IN` 단위 | **컨트롤러와 같은 0~1** | 요청 문구("컨트롤러 y 위치 입력값")대로 노드 없이 직결. `A00540` 은 매핑 json 의 `"scale": 10` 을 `1` 로 바꾼 파일 하나로 대응 |
| | 대안 | angela 단위 0~12 | 원본 리그 키를 그대로 복사해 넣을 수 있지만 슬라이더마다 역리맵 노드가 하나 더 든다 |

- 합(drv + ctl)이 1 을 넘을 수 있다 → `rv_*` 의 입력 클램프로 막는다 (V2 에서 확인, 안 되면 `clamp` 1개 추가).
- `DUMMY_IN_*` 어트리뷰트: double, 키 가능, 범위 0~1 (`-min 0 -max 1`).

### 6.5 D5 · D6 — 파일 범위

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| D5 | JaLi 2D 박스의 축 범위 | **0~1 로 바꾸고 `jaw/lip_output_min/max` 로 0~15 리맵** | 슬라이더와 규칙이 같아진다. A0010 의 0~15 직결(`CNT_JaLi.tx → JALI_IN.Jaw`)은 버린다 |
| D6 | ARKit 노드망(`JALI_IN → ARKIT_OUT`) 포함 여부 | **포함하지 않는다** — 새 파일 = 컨트롤러 + 더미 노드까지 | 더미 출력이 허브라는 요청 취지. ARKit 쪽은 `A0010` 을 레퍼런스하고 `DUMMY_OUT_* → JALI_IN` 을 이름으로 잇거나 `A00550` 로 BS 에 직접 건다. 파일 하나가 하는 일이 하나라 고치기 쉽다 |

---

## 7. 제작 · 검증 방법

- **생성 스크립트** `JUN_JALI/examples/build_jali_slider_ctl.py` (mayapy 배치 → `.ma` 저장, Maya 안에서 `build()` 도 가능).
  `build_jali_arkit_node.py` 와 같은 자리 · 같은 사용법. 어트리뷰트 표(§2)는 스크립트 상단 상수 하나로 둔다.
- **실측 선행 (V)** — 계획을 확정하기 전에 mayapy 로 먼저 확인:
  - V1 `textCurves` 가 mayapy(GUI 없음)에서 커브를 만드는가. 안 되면 라벨은 GUI 세션에서 한 번 붙이고 저장.
  - V2 `remapValue` 가 `inputValue > inputMax` 를 클램프하는가(합이 1 을 넘는 경우). `setRange` 도 같이.
  - V3 부모(`_drv`)의 ty 가 연결된 상태에서 자식 컨트롤러를 뷰포트에서 드래그할 수 있는가 — GUI 확인(사용자).
- **자동 검증 (T, mayapy)** — 저장한 `.ma` 를 다시 열어:
  - T1 더미 어트리뷰트 집합 == angela 집합 (`CNT_PHONEMES` 16 · `CNT_COARTIC` 6, 구분선 · `Project/Enunciate/dummy` 제외) — angela `.ma` 를 파싱해 비교.
  - T2 슬라이더마다 `ty=0 → out = output_min`, `ty=1 → output_max`, `ty=0.5 → 중간값`. `output_min=1, output_max=12` 로 바꾸면 `[1,12]`(요청 예).
  - T3 `DUMMY_IN.X = 1` → 컨트롤러 월드 y +1, `out = output_max`. `DUMMY_IN 0.7 + ctl 0.6` → 클램프로 `output_max`.
  - T4 잠금 · 제한: `ty` 제한 0~1, 나머지 채널 잠김 · 숨김, 트랙/라벨 displayType Reference.
  - T5 GK 등 이름이 겹치는 어트리뷰트가 **서로 다른 더미 노드**로 간다 (`CTL_CO_GK → DUMMY_OUT_COARTIC.GK`, `CTL_PH_GK → DUMMY_OUT_PHONEMES.GK`).
- **사용자 확인 (GUI)** — 모양이 ref 와 비슷한가, 바 두께 · 간격 · 색, 라벨 크기, 드래그 느낌(V3).

---

## 8. 확인이 필요한 것 (답을 받으면 §0-A 로 올린다)

| # | 질문 | 권장 |
|---|------|------|
| Q1 | 더미 노드를 3쌍(`JALI / PHONEMES / COARTIC`)으로 나누는 것(D1) | 3쌍 |
| Q2 | `DUMMY_IN` 이 컨트롤러 부모 그룹을 밀고 손 조작은 그 위에 더해지는 방식(D3) · 단위 0~1(D4) | 둘 다 권장안 |
| Q3 | `Project` `Enunciate`(연결 없음) · `dummy` 를 뺄지 | 뺀다 (22개). 넣으면 ref 와 같은 2×12 |
| Q4 | COARTIC 라벨 — ref 식 `LNTDm GKm MMMm FFFm WAp YAp` vs 어트리뷰트 이름 그대로 + 묶음 머리글 | 어트리뷰트 이름 그대로 (더미 이름과 눈으로 맞추기 쉬움) |
| Q5 | `global_scale` 어트리뷰트 하나 (§5) | 이번엔 뺀다, 필요해지면 추가 |
| Q6 | 결과 파일 이름 · 위치 — `02_Cage_JALI/A0020_jali_slider_ctl.ma`, 스크립트는 `JUN_JALI/examples/` | 그대로 |
| Q7 | 기본 `output_max` — angela 범위(12 · YA 15 · Jaw/Lip 15) vs VisemeNet 실사용 10 | angela 범위 (요청 예시도 12) |

---

## 9. 단계

| 단계 | 할 일 | 결과물 |
|------|-------|--------|
| S0 ✅ | §8 답 확인 → §0-A 확정표 | 이 문서 갱신 |
| S1 ✅ | 실측 V1 · V2 · V3 (mayapy) | §0-B |
| S2 ✅ | `build_jali_slider_ctl.py` — 어트리뷰트 표 · 슬라이더 1개 생성 함수 · 배치 | `examples/build_jali_slider_ctl.py` |
| S3 ✅ | 더미 노드 3쌍 · `pma_* / rv_* / gs_*` 노드망 · JaLi 박스(0~1, 보이는 크기 ×2) | 〃 |
| S4 ✅ | mayapy 로 생성 → `A0020_jali_slider_ctl.ma` 저장 → T1~T6 자동 검증 **301 항목 통과** | `.ma` (320KB, 커브 217개) + `.ref/A0020_layout_preview.png` |
| S5 | **사용자 GUI 확인** — 모양 · 바 두께(`lineWidth` 3) · 라벨 크기 · 색(PH 노랑 17 · CO 하늘 18 · JaLi 빨강 13) · 드래그 느낌 → 수정 | 대기 |
| S6 ✅ | `A00540` v01.01 (2026-10-22): 매핑 json 역할표 `nodes` · 새 규칙 `jali_slider_dummy_in`(scale 1) · Target Auto/Manual · JaLi scale — Maya_Python `docs/plans/A00540_JaliLipSync_v0101_rules_manual_plan.md` | 완료 (마야 GUI 미확인) |

---

## 10. 알려진 위험

- ~~`textCurves` 가 headless 에서 실패할 수 있다(V1)~~ → 실측 통과(§0-B).
- ~~`remapValue` 의 램프 평가(V2)~~ → 실측 통과, 범위 밖은 끝값(§0-B).
- 뷰포트 드래그 느낌 · 글자 커브의 선택 통과(Reference) 는 **GUI 에서만 확인된다** (S5).
- `A00540_JaliLipSync` · `A00550_PoseMapper` 는 `CNT_PHONEMES` 를 리그 표식으로 찾는다. 새 파일에는 그 이름이 없으므로 **지금은 두 툴이 새 파일을 리그로 인식하지 않는다** (S6 후속).
- ref 이미지의 비짐 묶음(24)과 angela(22)가 다르다 — 이 계획은 angela 를 따른다. ref 의 `IH JY DT UH` 등은 대응 어트리뷰트가 없다.
