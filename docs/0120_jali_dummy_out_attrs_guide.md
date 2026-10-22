# DUMMY_OUT_PHONEMES · DUMMY_OUT_COARTIC 어트리뷰트 안내 — 각 값이 만드는 얼굴 표현

> **작성** 2026-10-22 · 대상: `02_Cage_JALI/A0020_jali_slider_ctl.ma` 의 `DUMMY_OUT_PHONEMES`(16) · `DUMMY_OUT_COARTIC`(6)
> 근거: ① `angela_JALI.ma` **실측** (Maya 2024 mayapy — 어트리뷰트 하나만 **10**, `CNT_JaLi` 9 · 9, 나머지 0 으로 두고 `faceChannels` · `jawChannels` · `tongueChannels` 와 턱 · 혀 조인트의 변화를 기록)
> ② JALI 논문 리그의 `README_JALI_Rig.docx` (Edwards · Landreth · Singh · Fiume, 2016) ③ [0040_jali_arkit_mapping.md](0040_jali_arkit_mapping.md) 의 근육 ↔ ARKit 대응
> 계획서: [0090_jali_slider_ctl_plan.md](0090_jali_slider_ctl_plan.md)

---

## 0. 이 두 노드가 무엇인가

- A0020 리그에서 슬라이더(`CTL_PH_*` · `CTL_CO_*`)의 `ty`(0~1)가 `output_min ~ output_max`(기본 0~12) 로 리맵되어 도착하는 **출력 허브**다.
  어트리뷰트 이름은 angela 원본 `CNT_PHONEMES` · `CNT_COARTIC` 과 같으므로, **원본 리그에서 `CNT_PHONEMES.AAA` 가 하던 일 = `DUMMY_OUT_PHONEMES.AAA`** 로 읽으면 된다.
- 값의 뜻: angela 리그 단위다. **10 = "그 음소를 온전히 발음한 상태"** (VisemeNet 이 내는 최댓값이자 이 문서의 실측 조건). 12 는 리그 최댓값(과장).
- `DUMMY_OUT_JALI.Jaw` · `Lip`(0~15, 기본 9)이 모든 음소에 **곱해진다**: Jaw 는 턱 · 혀 성분, Lip 은 입술 근육 성분의 크기. 아래 수치는 둘 다 9 일 때다.
- 음소 하나를 올린 상태는 "**그 소리를 내는 입 모양 한 장**(viseme)"이다. 애니메이션에서는 소리가 나는 순간마다 해당 음소 하나를 올리고 나머지는 0 으로 둔다(README). 두 개 이상을 동시에 올리면 리그 안의 블렌드 노드가 **더한다**.

```
DUMMY_OUT_PHONEMES.AAA = 10  ──▶  (원본 리그) 턱 8.9° 벌림 + 아랫입술 내림 0.54 + 볼 안쪽 당김 0.50 + … + 혀 끝 내림
```

---

## 1. 읽는 법 — 리그 채널 이름을 말로

| 리그 채널 (`faceChannels.*`) | 근육 | 보이는 모양 | ARKit |
|------------------------------|------|-------------|-------|
| `labInf` | 하순하제근 | **아랫입술이 내려가** 아랫니가 보인다 | `mouthLowerDown` |
| `labSup` | 상순거근 | **윗입술이 올라가** 윗니가 보인다 | `mouthUpperUp` |
| `zygomatic` | 대관골근 | 입꼬리가 **위로** (미소) | `mouthSmile` |
| `risPlatysma` | 소근 · 광경근 | 입꼬리가 **옆으로** 당겨진다 | `mouthStretch` |
| `buccinator` | 협근 | 볼이 안쪽으로 눌려 입꼬리가 조여진다 (보조개) | `mouthDimple` |
| `incisivus` | 절치근 | 입술을 **오므려 앞으로** (우 모양) | `mouthPucker` |
| `orbOris_loose_hi` / `_lo` | 구륜근(느슨) | 위 / 아래 입술이 **깔때기**처럼 벌어져 앞으로 | `mouthFunnel` |
| `orbOris_up_lo` / `orbOris_down_hi` | 구륜근 | 아랫입술 올림 / 윗입술 내림 — **+ 면 입술이 맞닿고, − 면 살짝 떨어진다** | `mouthClose` (+) |
| `orbOris_tight_lo` / `_hi` | 구륜근(조임) | 아랫 / 윗입술을 **안으로 말아 넣음** | `mouthRollLower` / `Upper` |
| `mentalis_lowerLip` | 턱끝근 | 턱끝이 올라와 아랫입술을 **위로 밀어 올림** | `mouthShrugLower` |
| `blow` | — | 볼 부풀림 | `cheekPuff` |
| `jawChannels.rz` = `Jaw.rx` | 턱 관절 | **턱 벌림 각도(°)** | `jawOpen` |
| `Jaw.tz` | | 턱이 앞으로 | `jawForward` |
| `tongueChannels` · `tongue1~5` | 혀 조인트 | 혀 뿌리(`tongue1`) → 끝(`tongue5`) 회전, `Rollback` = 혀 전체를 뒤로 | `tongueOut` 하나뿐 |

> 거의 모든 음소에 `orbOris_up_lo` −0.16 · `orbOris_down_hi` −0.09 가 같이 붙는다 = "입술이 살짝 떨어진 상태". 아래 표에서는 뺐다.
> 혀 수치는 부호가 조인트 축 기준이다. 아래에서는 **`LNTD` 의 혀끝 방향을 "올림"** 으로 삼아 말로 옮겼다(혀끝 `tongue5` rz 가 +면 올림, −면 내림 · 뒤로).
> `tongueChannels.tz` 는 **`TTH` 의 방향을 "앞으로"** 로 봤다(+ 앞, − 뒤). 둘 다 숫자는 실측, 방향 말은 해석이다 — GUI 에서 한 번 눈으로 맞춰 볼 것.

---

## 2. `DUMMY_OUT_PHONEMES` — 음소(비짐) 16개

### 2.1 한눈에

| 어트리뷰트 | 소리 | 얼굴 표현 (한 줄) | 턱 벌림 | 입술 근육 (0~1) | 혀 |
|-----------|------|-------------------|--------:|-----------------|----|
| **AHH** | f**a**ther, **아** | 가장 크게 벌린 입, 입술은 힘을 뺀 채 | **13.4°** | `labInf` 0.34 | — |
| **AAA** | c**a**t, **애** | 크게 벌리면서 **옆으로도 당긴** 입, 윗니 · 아랫니가 보임 | 8.9° | `labInf` 0.54 · `buccinator` 0.50 · `risPlatysma` 0.28 · `labSup` 0.27 · `zygomatic` 0.20 | 끝 내림, 몸통 앞쪽 살짝 올림 |
| **Eh** | b**e**d, **에** | AAA 보다 덜 벌리고 덜 당긴 중간 모음 | 5.1° | `labInf` 0.38 · `risPlatysma` 0.24 · `zygomatic` 0.15 | 끝 내림 (AAA 의 70%) |
| **IEE** | s**ee**, **이** | 턱은 거의 닫고 입술을 **옆으로 쫙 편** 입 (이— 하는 모양) | 1.7° | `labInf` 0.61 · `buccinator` 0.37 · `risPlatysma` 0.29 · `labSup` 0.27 · `zygomatic` 0.23 | 끝 내림, 뿌리 쪽 올림(혀 앞부분이 입천장에 가까이) |
| **OHH** | g**o**, **오** | 턱을 벌리고 입술을 **둥글게 오므린** 입 | 7.5° | `incisivus` 0.41 | 몸통이 크게 말림(뒤쪽 올림), 뒤로 당김 |
| **UUU** | f**oo**d, **우** | 턱은 거의 닫고 입술을 **앞으로 쭉 내민** 입 | 0.8° | `incisivus` 0.61 · `orbOris_loose_hi/lo` 0.26 | 끝 올림, 뒤쪽 몸통 올림 |
| **Schwa** | **a**bout (약한 "어") | **입술 변화 없이 턱만 조금** 벌린 중립 입 | 4.0° | — | — |
| **RRR** | **r**ed | 입술을 깔때기처럼 벌려 앞으로 + 약간 오므림, 혀끝을 **뒤로 말아 올림** | 3.0° | `orbOris_loose_hi` 0.47 · `_lo` 0.36 · `incisivus` 0.27 | **혀끝 올림이 가장 큼** (+37°), 앞으로 |
| **WWW** | **w**e | UUU 처럼 내밀되 위아래 입술이 **거의 맞닿은** 입 | 4.0° | `incisivus` 0.52 · `orbOris_up_lo` 0.38 · `orbOris_down_hi` 0.36 | UUU 와 같은 혀 |
| **SSS** | **s**ee | 턱은 닫은 채(0°) **아랫입술만 내려 아랫니를 드러내는** 입 (스—) | 0° (앞으로 0.15) | `labInf` 0.66 · `orbOris_loose_hi` 0.09 | 끝 내림(아랫니 뒤), 몸통 평평 |
| **SSH** | **sh**e | 입술을 **앞으로 내민 깔때기**, 위아래 이가 살짝 보임 | 0° (앞으로 0.26) | `orbOris_loose_lo` 0.50 · `_hi` 0.38 · `incisivus` 0.29 · `labInf` 0.25 · `labSup` 0.24 | 끝 올림 |
| **FFF** | **f**an, **v**an | **아랫입술을 안으로 말아 윗니 밑에** 넣은 입, 볼이 조여짐 | 1.4° | `buccinator` 0.56 · `orbOris_tight_lo` 0.24 · `labSup` 0.11 · `mentalis_lowerLip` 0.09 | — |
| **TTH** | **th**ink | 입술을 살짝 벌려 앞으로 + **혀끝을 이 사이로 내민** 입 | 1.8° | `buccinator` 0.54 · `orbOris_loose_hi` 0.33 · `labSup` 0.25 · `_lo` 0.20 | **혀가 앞으로 나옴**(tz +0.47), 몸통 아래로 |
| **MBP** | **m**om **b**oy **p**ie | 턱은 벌어진 채 **입술을 다문** 입 (입술이 맞닿아 눌림), 볼 살짝 부풂 | 5.8° | `orbOris_up_lo` 0.62 · `orbOris_down_hi` 0.60 · `blow` 0.10 · `orbOris_tight_hi` 0.07 | — |
| **GK** | **g**o **k**ey, **ㄱ ㅋ** | 입술은 Schwa 와 같고(중립 + 턱 4°) **혀 뒤쪽을 입천장으로 올림**, 혀끝은 내림 | 4.0° | — | 뿌리 올림 +13.7°, 몸통 +23.8°, 끝 내림 −25.6° |
| **LNTD** | **l**ip **n**o **t**op **d**o, **ㄴ ㄷ ㄹ ㅌ** | 입술은 Schwa 와 같고 **혀끝을 윗잇몸에 붙임** | 4.0° | — | **혀끝 올림 +35.7°**, 몸통 앞쪽 올림, 혀가 위로(ty +1.4) |

### 2.2 묶어서 보면

- **모음 — 턱이 정한다**: `AHH`(13°) > `AAA`(9°) > `OHH`(7.5°) > `Eh`(5°) > `Schwa`(4°) > `IEE`(1.7°) > `UUU`(0.8°).
  여기에 입꼬리 방향이 붙는다 — **옆으로**(`AAA` `Eh` `IEE`: `risPlatysma` · `zygomatic` · `labInf`) 또는 **앞으로**(`OHH` `UUU`: `incisivus`).
- **입술 둥근 소리** `OHH` `UUU` `WWW` `RRR` `SSH`: 공통 성분은 `incisivus`(오므림). `UUU/WWW` 는 내밀기, `RRR/SSH` 는 깔때기(`orbOris_loose`), `WWW` 는 거기에 입술 맞닿음이 더해진다.
- **이 사이 소리** `SSS` `FFF` `TTH`: 턱이 거의 0° 인 대신 입술이 이를 드러낸다 — `SSS` 는 아랫입술 내림, `FFF` 는 아랫입술 말아 넣기, `TTH` 는 혀 내밀기.
- **입술 닫는 소리** `MBP`: 턱이 벌어진 채 입술만 닫힌다 → ARKit 의 `mouthClose` 정의와 같다(`jawOpen` 과 같이 써야 의미가 있다).
- **혀만 쓰는 소리** `GK` `LNTD`: 입술은 Schwa 와 완전히 같다. 입을 안 보여 주면 Schwa 와 구별이 안 되고, **혀가 보이는 클로즈업에서만 차이가 난다.** 그래서 같은 이름이 `DUMMY_OUT_COARTIC` 에 한 번 더 있다(§3).

### 2.3 ARKit 로 옮길 때

위 표의 "입술 근육" 열을 §1 의 ARKit 열로 바꾸면 0040 §3 의 시작 가중치가 된다 (`jawOpen` 은 `AHH` 13.4° 를 1.0 으로 둔 상대값). 혀는 `TTH` 의 `tongueOut` 만 옮길 수 있다.

---

## 3. `DUMMY_OUT_COARTIC` — 동시조음(co-articulation) 6개

### 3.1 동시조음이란 (README 의 설명)

> "Sue" 의 **S** 는 뒤에 오는 **U** 때문에 입술이 오므라진 채 발음되지만, "See" 의 S 는 그렇지 않다. `WA_PEDAL` 은 이런 **입술 오므림을 주변 음소의 타이밍과 독립적으로** 얹는 채널이다.
> 나머지 채널은 입술 닫힘(`MMM`) · 입술-이(`FFF`) · 혀만 쓰는(`LNTD` `GK`) 소리를 `CNT_PHONEMES` 로 키한 **인접 음소 위에 겹치기** 위한 것이다.

즉 `DUMMY_OUT_COARTIC` 은 **음소 하나를 통째로 만드는 게 아니라, 음소 위에 "한 가지 성분만" 얹는 보정 채널**이다. 음소 슬라이더와 함께 쓴다.

### 3.2 한눈에

| 어트리뷰트 | 얹는 성분 | 단독(10)으로 보이는 것 | 음소와 같이 쓸 때 | 비고 |
|-----------|-----------|-------------------------|-------------------|------|
| **WA_PEDAL** | **입술 오므림** (우 모양) | `incisivus` 0.48 — 그것뿐 | 어떤 음소 위에서도 **똑같이 0.48** 더해진다 (`AAA` · `UUU` · `SSS` 실측 동일) | "**W**ill" "S**ue**" 처럼 다음 음소의 둥근 입술이 앞 소리에 미리 나타나는 것 |
| **YA_PEDAL** | **입술 옆으로 펴기** (이 모양) | `risPlatysma` 0.37 · `buccinator` 0.27 · `zygomatic` 0.12 | 어떤 음소 위에서도 똑같이 더해진다 | "**Y**es" "S**ee**" 의 펴진 입술을 앞 소리에 미리. WA 의 반대 방향 |
| **MMM** | **입술 닫기** (턱은 그대로) | **아무 변화 없음** | 턱이 벌어진 만큼 입술이 닫힌다 — `AAA`(9°) 위에서 `orbOris_up_lo` 0.85 · `orbOris_down_hi` 0.80 · `mentalis_lowerLip` 0.60, `UUU`(0.8°) 위에선 0.08, `SSS`(0°) 위에선 0 | 모음을 내는 중간에 입술만 다무는 "**m**a-**m**a" 식 겹침. 리그 안 `EXP_COARTIC_Lip` 이 `(턱 각도) / 30` 을 곱한다 |
| **FFF** | **아랫입술을 윗니 밑으로** (턱은 그대로) | **아무 변화 없음** | 턱이 벌어진 만큼 — `AAA` 위에서 `mentalis_lowerLip` 1.17 · `orbOris_up_lo` 0.64 · `orbOris_tight_lo` 0.36, `UUU` 위에선 0.10, `SSS` 위에선 0 | 모음 중간의 f/v. MMM 과 같은 턱 비례 곱 |
| **LNTD** | **혀끝 올려 윗잇몸에** (입술 · 턱 변화 없음) | 혀끝 +58.7°, 몸통 +49 / +36°, 혀 위로 1.6 — `PHONEMES.LNTD`(혀끝 +35.7°) 보다 **1.6배 세고 턱은 안 벌린다** | 모음 위에 그대로 더해진다 (`AAA` 위 혀끝 +58.7°, 몸통은 모음 혀와 합쳐져 줄어듦) | 모음을 내는 입 모양을 유지한 채 혀만 l/n/t/d |
| **GK** | **혀 뒤쪽 올려 입천장에**, 혀끝 내림 (입술 · 턱 변화 없음) | 혀끝 −78.4°, 몸통 +27°, 뿌리 +22.4°, `Rollback` 6.6 — `PHONEMES.GK` 보다 **3배 세고 턱은 안 벌린다** | 모음 위에 그대로 더해진다 | 모음 입 모양 유지한 채 혀만 g/k. angela 원본 범위는 −5~12 (음수 = 반대로) |

### 3.3 `PHONEMES.LNTD / GK` 와 `COARTIC.LNTD / GK` 의 차이

| | `DUMMY_OUT_PHONEMES.*` | `DUMMY_OUT_COARTIC.*` |
|---|---|---|
| 턱 | 4° 벌림 (Schwa 와 같음) | **안 움직임** |
| 입술 | Schwa 와 같은 중립 | **안 움직임** |
| 혀 | 중간 세기 | **강함** (LNTD 1.6배, GK 3배) |
| 쓰임 | 그 자음을 **단독 비짐**으로 찍을 때 (앞뒤가 쉼이거나 입이 닫혀 있을 때) | 모음 **사이**에 자음을 끼울 때 — 모음 입 모양은 그대로 두고 혀만 |

### 3.4 `MMM` · `FFF` 는 왜 단독으로는 0 인가

리그의 `EXP_COARTIC_Lip` 식: `-(jawChannels.rz − FC_jawRotZ_lipLock) / 30` — **현재 턱 벌림 각도에 비례**하는 계수를 `MMM` · `FFF` 값에 곱한다.
턱이 닫혀 있으면(0°) 입술은 이미 닿아 있으니 "닫을 것이 없다"는 설계다. 그래서

- `MMM` 만 10 → 변화 0. `AAA` 10 + `MMM` 10 → 턱 9° 그대로인 채 입술 0.8 만큼 닫힘(거의 다묾).
- 이 채널을 **ARKit 로 옮길 때는 `jawOpen` 값을 곱한 `mouthClose`** 로 보면 된다 (`MMM` 단독은 `mouthClose` 0, `jawOpen` 0.67 위에선 ≈ 0.8).

---

## 4. 같이 쓰는 예

| 말 | 음소 슬라이더 | 동시조음 슬라이더 | 결과 |
|----|---------------|-------------------|------|
| "See" | `SSS` → `IEE` | — | 아랫니 드러낸 S, 펴진 이 |
| "Sue" | `SSS` → `UUU` | `SSS` 구간에 **`WA_PEDAL`** | S 를 내는 동안 이미 입술이 오므라짐 |
| "Yes" | `IEE` → `Eh` → `SSS` | 앞쪽에 **`YA_PEDAL`** | 펴진 입술이 미리 나타남 |
| "Mama" | `AHH`(또는 `AAA`) 유지 | m 순간에 **`MMM`** | 턱은 벌어진 채 입술만 닫혔다 열림 (턱을 닫았다 열지 않는다) |
| "Never" | `Eh` 유지 | n 순간에 **`LNTD`** | 모음 입 모양에서 혀끝만 윗잇몸으로 |
| "Go" | `OHH` 유지 | g 순간에 **`GK`** | 둥근 입술 그대로, 혀 뒤만 올림 |
| 쉼 뒤 "Top" | `LNTD` → `OHH` → `MBP` | — | 앞뒤가 쉼이면 PHONEMES 쪽 `LNTD` 로 충분(턱 4° 포함) |

---

## 5. 주의 · 한계

- 수치는 **angela 리그 전용**이다. 다른 얼굴에서는 같은 어트리뷰트가 같은 "뜻"(§2.1 둘째 열)을 가지되 크기는 그 얼굴의 블렌드셰이프에 맞춰 다시 잡아야 한다(`A00550 PoseMapper`).
- `Jaw` · `Lip` 을 9 가 아닌 값으로 두면 턱 · 혀(Jaw)와 입술 근육(Lip) 성분이 각각 비례해서 바뀐다. `README` 의 예: Jaw 2 · Lip 14 면 "이 사이로 R 을 발음하는" 얼굴.
- **0040 §3 동시조음 표의 "`LNTD` `GK` `MMM` `FFF` 단독으로는 근육 · 턱 변화 없음" 은 반만 맞다** — 근육 · 턱은 안 변하지만 `LNTD` `GK` 는 **혀가 크게** 움직이고(0040 은 혀 채널을 빼고 쟀다), `MMM` `FFF` 는 **턱이 벌어져 있어야** 작동한다. 이 문서 §3 이 정정본이다.
- ARKit 로는 혀 올림 · 뒤로(`LNTD` `GK` `RRR` `SSS` 의 혀)를 표현할 수 없다(`tongueOut` 뿐). 입 안이 보이는 샷이면 혀 조인트를 따로 둔다.
- 실측 스크립트: 이 문서를 만들 때 쓴 mayapy 스크립트는 저장소에 넣지 않았다. 같은 측정을 다시 하려면 `CNT_PHONEMES.<attr> = 10` 으로 두고 `faceChannels` · `jawChannels` · `tongueChannels` · `Jaw` · `tongue*` 조인트의 값 차이를 기록하면 된다.
