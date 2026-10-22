# JALI 음소 ↔ Apple ARKit 52 블렌드셰이프 매칭

> **작성** 2026-10-19 · 근거: `angela_JALI.ma` 리그 **실측**(Maya 2024 mayapy) + FACS 근육 ↔ ARKit 대응
> · 계획서 [0030_tool_plan.md](0030_tool_plan.md) 의 T4

**질문**: JALI 가 요구하는 음소(비짐)마다, ARKit 52 타겟 중 **비슷한 모양이라 대신 · 같이 쓸 수 있는 것**은 무엇인가.
(예: 턱을 벌리는 성분 → `jawOpen`)

---

## 1. 결론 — 한 음소 = ARKit 여러 개의 조합

JALI 음소는 **단일 블렌드셰이프가 아니다.** 리그 안에서 한 음소는 **턱 회전 + 근육 채널 몇 개 + 혀**를 동시에 움직인다.
그래서 매칭은 1:1 이 아니라 **"음소 = ARKit 타겟 몇 개의 가중 합"** 이 된다.

그리고 JALI 의 두 축이 ARKit 에서 깔끔하게 갈린다.

| JALI 축 | 리그에서 하는 일 | ARKit 에서 |
|---------|-----------------|-----------|
| **Jaw** (`CNT_JaLi.tx`) | 음소의 **턱 · 혀** 성분 크기 | **`jawOpen`** (+ `jawForward`, `tongueOut`) |
| **Lip** (`CNT_JaLi.ty`) | 음소의 **입술 근육** 성분 크기 | **`mouth*`** 계열 (+ `cheekPuff`) |

→ ARKit 아바타에서 JALI 말투 조절을 흉내 내려면 **`jawOpen` 쪽 가중치에 Jaw 값을, `mouth*` 쪽 가중치에 Lip 값을 곱하면** 된다.

---

## 2. 어떻게 쟀나

`angela_JALI.ma` 에서 `CNT_JaLi` 를 기본값(9, 9)에 두고, 음소 하나씩 **10**(리그 최대 12, VisemeNet 출력 최대 10)으로 올린 뒤
**바뀐 채널**을 기록했다.

- 근육 = `faceChannels.<근육>` (블렌드셰이프 `faceMuscles` 를 직접 구동하는 0~1 채널)
- 턱 = `Jaw.rx`(벌림, 도), `Jaw.tz`(앞으로)
- 혀 = `tongue*` 조인트 회전

근육 이름 → ARKit 은 **FACS Action Unit** 을 거쳐 이어진다(공부 문서 004300).

| 리그 근육 채널 | FACS | ARKit |
|---------------|------|-------|
| `Jaw.rx` (턱 벌림) | AU26/27 | **`jawOpen`** |
| `Jaw.tz` | AU29 | `jawForward` (방향은 눈으로 확인 필요) |
| `labInf` (하순하제근) | AU16 | **`mouthLowerDownLeft/Right`** |
| `labSup` (상순거근) | AU10 | **`mouthUpperUpLeft/Right`** |
| `zygomatic` (대관골근) | AU12 | **`mouthSmileLeft/Right`** |
| `risPlatysma` (소근 · 광경근) | AU20 | **`mouthStretchLeft/Right`** |
| `buccinator` (협근) | AU14 | **`mouthDimpleLeft/Right`** |
| `incisivus` (입술 앞으로) | AU18 | **`mouthPucker`** |
| `orbOris_loose_hi/lo` (입술 깔때기) | AU22 | **`mouthFunnel`** |
| `orbOris_up_lo` + `orbOris_down_hi` (+) (위아래 입술이 맞닿음) | AU24/AU25 반대 | **`mouthClose`** (+ `mouthPressLeft/Right`) |
| `orbOris_tight_lo` (아랫입술 말아 넣기) | AU28 | **`mouthRollLower`** |
| `orbOris_tight_hi` | AU28 | `mouthRollUpper` |
| `mentalis`, `mentalis_lowerLip` (턱끝근) | AU17 | **`mouthShrugLower`** |
| `blow` | AU33/34 | `cheekPuff` |
| `triangularis` (구각하제근) | AU15 | `mouthFrownLeft/Right` |
| 혀 조인트 | — | `tongueOut` **만 있다** (혀 올림 · 뒤로는 ARKit 에 없음) |

> JALI 근육은 좌우 공용 채널이 대부분이다 → ARKit 의 `Left` / `Right` **둘 다 같은 값**.

---

## 3. 음소별 매칭표 ⭐

값은 음소 = 10 일 때 실측한 크기다. 근육 값은 0~1 블렌드셰이프 가중치라 **ARKit 가중치 시작값으로 그대로** 써 볼 수 있다.
`jawOpen` 은 `AHH`(13.4°)를 **1.0** 으로 둔 상대값.

| JALI 음소 | 대표 소리 | ARKit 조합 (시작 가중치) | 비고 |
|-----------|----------|--------------------------|------|
| **AHH** | f**a**ther | `jawOpen` **1.00** · `mouthLowerDown` 0.34 | 가장 크게 벌린 입 |
| **AAA** | c**a**t | `jawOpen` 0.67 · `mouthLowerDown` 0.54 · `mouthDimple` 0.50 · `mouthStretch` 0.28 · `mouthUpperUp` 0.27 · `mouthSmile` 0.20 | 벌림 + 옆으로 |
| **Eh** | b**e**d | `jawOpen` 0.38 · `mouthLowerDown` 0.37 · `mouthStretch` 0.24 · `mouthSmile` 0.15 | |
| **IEE** | s**ee** | `jawOpen` 0.13 · `mouthLowerDown` 0.61 · `mouthDimple` 0.37 · `mouthStretch` 0.29 · `mouthUpperUp` 0.27 · `mouthSmile` 0.23 | 거의 다문 턱 + 옆으로 편 입술 |
| **OHH** | g**o** | `jawOpen` 0.56 · `mouthPucker` 0.41 | 실측엔 Funnel 이 없다. 일반 관행은 `mouthFunnel` 도 섞는다 |
| **UUU** | f**oo**d | `mouthPucker` 0.61 · `mouthFunnel` 0.26 · `jawOpen` 0.06 | |
| **WWW** | **w**e | `mouthPucker` 0.52 · `mouthClose` 0.37 · `jawOpen` 0.30 | 오므린 채 입술이 거의 닿음 |
| **RRR** | **r**ed | `mouthFunnel` 0.42 · `mouthPucker` 0.27 · `jawOpen` 0.22 | |
| **SSS** | **s**ee | `mouthLowerDown` 0.66 · `mouthFunnel` 0.09 · `jawOpen` 0 · (`jawForward` 소량) | 이를 드러내는 입. 혀 끝 올림은 ARKit 에 없음 |
| **SSH** | **sh**e | `mouthFunnel` 0.44 · `mouthPucker` 0.29 · `mouthLowerDown` 0.25 · `mouthUpperUp` 0.24 · `mouthStretch` 0.11 | 앞으로 내민 깔때기 |
| **FFF** | **f**an | `mouthDimple` 0.56 · `mouthRollLower` 0.24 · `mouthUpperUp` 0.11 · `mouthShrugLower` 0.09 · `jawOpen` 0.11 | ARKit 관행상 **`mouthRollLower` 가 주 성분** — 아바타에선 이 값을 키워 볼 것 |
| **TTH** | **th**ink | `mouthDimple` 0.54 · `mouthFunnel` 0.27 · `mouthUpperUp` 0.25 · `jawOpen` 0.13 · `tongueOut` (혀 앞으로) | `tongueOut` 이 유일하게 쓰이는 음소 |
| **MBP** | **m**om | `mouthClose` 0.62 · `jawOpen` 0.43 · `mouthPress` 0.07 · `cheekPuff` 0.10 | ⭐ 턱은 벌어진 채 입술이 닫힌다 = **ARKit `mouthClose` 의 정의 그대로** (`mouthClose` 는 `jawOpen` 과 같이 써야 의미가 있다) |
| **Schwa** | **a**bout | `jawOpen` 0.30 | 입술은 중립 |
| **LNTD** | **l**ip · **n**o · **t**op · **d**o | `jawOpen` 0.30 | 혀 끝을 올리는 소리 — **입술 성분 없음**, ARKit 로는 턱만 |
| **GK** | **g**o **k**ey | `jawOpen` 0.30 | 혀 뒤를 올리는 소리 — 위와 같음 |

**동시조음 컨트롤 (`CNT_COARTIC`)**

| 채널 | 실측 | ARKit |
|------|------|-------|
| `WA_PEDAL` (입술 오므림을 따로 얹기) | `incisivus` 0.48 | `mouthPucker` |
| `YA_PEDAL` (입술 펴기) | `risPlatysma` 0.37 · `buccinator` 0.27 · `zygomatic` 0.12 | `mouthStretch` · `mouthDimple` · `mouthSmile` |
| `LNTD` · `GK` · `MMM` · `FFF` | **단독으로는 근육 · 턱 변화 없음** — ⚠️ 2026-10-22 정정: `LNTD` `GK` 는 **혀가 크게 움직인다**(이 표는 혀 채널을 빼고 쟀다), `MMM` `FFF` 는 **턱이 벌어진 만큼 곱해져** 턱이 닫히면 0 | `MMM` ≈ `jawOpen` × `mouthClose`, `FFF` ≈ `jawOpen` × `mouthRollLower` · `mouthShrugLower`. 혀는 ARKit 에 없음. 상세는 [0100](0100_jali_dummy_out_attrs_guide.md) §3 |

**거의 모든 음소에 공통**으로 `orbOris_up_lo` −0.16 · `orbOris_down_hi` −0.09 (입술이 살짝 떨어짐)가 붙는다.
ARKit 에선 무시하거나 `mouthUpperUp` / `mouthLowerDown` 에 소량 더하는 정도로 충분하다.

---

## 4. 반대 방향 — ARKit 52 중 무엇을 쓰고 무엇이 남나

| 묶음 | ARKit 타겟 | JALI 음성에서 |
|------|-----------|---------------|
| **턱** | `jawOpen` ⭐ · `jawForward` | 쓴다 (Jaw 축) |
| | `jawLeft` · `jawRight` | 안 쓴다 |
| **입 — 음성 핵심** | `mouthClose` · `mouthPucker` · `mouthFunnel` · `mouthLowerDownL/R` · `mouthUpperUpL/R` · `mouthStretchL/R` · `mouthDimpleL/R` · `mouthSmileL/R` · `mouthRollLower` · `mouthShrugLower` | 쓴다 (Lip 축) |
| **입 — 보조** | `mouthPressL/R` · `mouthRollUpper` · `cheekPuff` | 소량 |
| | `mouthShrugUpper` · `mouthFrownL/R` · `mouthLeft` · `mouthRight` | 음성에선 안 쓴다 (표정 · 비대칭) |
| **혀** | `tongueOut` | `TTH` 에서만 |
| **눈 · 눈썹 · 코 · 볼** | `eyeBlink*` `eyeLook*` `eyeSquint*` `eyeWide*` `browDown*` `browInnerUp` `browOuterUp*` `cheekSquint*` `noseSneer*` (25개) | **립싱크와 무관** — 리그의 `CNT_UPFACE` · `CNT_MIDFACE` · `blink` 쪽 (아래 §5) |

**ARKit 로 표현할 수 없는 것**: 혀를 올리거나 뒤로 당기는 모양(`LNTD` · `GK` · `SSS` 의 혀) — ARKit 에는 `tongueOut` 하나뿐이다.
입 안이 잘 보이는 클로즈업이면 혀 조인트를 따로 두는 편이 낫다.

---

## 5. 참고 — 표정 컨트롤 ↔ ARKit (이름 · FACS 기준 추정, 실측 아님)

| angela 컨트롤 | ARKit |
|---------------|-------|
| `CNT_UPFACE.frontalis` / `medFrontalis` | `browOuterUpL/R` / `browInnerUp` |
| `CNT_UPFACE.browFurrow` | `browDownL/R` |
| `CNT_UPFACE.squint(L/R)` · `loSquint(L/R)` | `eyeSquintL/R` · `cheekSquintL/R` |
| `CNT_MIDFACE.smile` · `smirkL/R` | `mouthSmileL/R` |
| `CNT_MIDFACE.sneer(L/R)` | `noseSneerL/R` (+ `mouthUpperUp`) |
| `CNT_LOFACE.pucker` | `mouthPucker` |
| `CNT_LOFACE.lipLock` | `mouthPressL/R` |
| `CNT_LOFACE.UpLipIn` / `LoLipIn` | `mouthRollUpper` / `mouthRollLower` |
| `CNT_LOFACE.upLipOut` / `loLipOut` | `mouthShrugUpper` / `mouthShrugLower` |
| `CNT_LOFACE.frown(_L/_R)` | `mouthFrownL/R` |
| `CNT_LOFACE.grimace(L/R)` | `mouthStretchL/R` |
| `CNT_LOFACE.mentalis` | `mouthShrugLower` |
| `CNT_LOFACE.blow` · `buccinator` | `cheekPuff` · `mouthDimpleL/R` |
| `blink` 컨트롤 | `eyeBlinkL/R` |

---

## 6. 쓰는 법과 한계

- 위 가중치는 **시작값**이다. 아바타마다 ARKit 타겟을 조각한 강도가 달라서, 같은 0.5 라도 모양이 다르다.
  **아바타를 정하면 음소 16개를 한 장씩 렌더해 angela 와 나란히 보고 조정**하는 단계가 필요하다(계획서 T4-b).
- 표를 그대로 json 으로 옮기면 A00540 매핑 파일 형식(계획서 §5.4)으로 **ARKit 아바타에 VisemeNet 결과를 거는 모드**를 만들 수 있다.
  그러려면 대상 아바타(블렌드셰이프 이름 포함)가 필요하다 → 계획서 §8 질문 9.
- 실측은 `CNT_JaLi` = (9, 9) 에서만 했다. 다른 Jaw/Lip 값에서는 §1 처럼 턱 성분과 입술 성분이 각각 비례해 커지고 작아진다(진단 문서 §3.2 에서 확인).
