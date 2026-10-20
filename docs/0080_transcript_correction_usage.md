# 사용법 — 대본으로 립싱크 보정하기 (VisemeNet Converter v01.01)

> **작성** 2026-10-20 · 대상: `dev` 브랜치의 `VisemeNet Converter` v01.01 · `setup_mfa.bat` · Maya `A00540_JaliLipSync`
> 처음부터 끝까지 따라 하는 순서 안내다. 세부 규격 · 오류 코드 전체는 [0050](0050_converter_guide.md), 설계 이유는 [0060](0060_transcript_mfa_plan.md).

**무엇이 달라졌나**: 지금까지는 **음성(wav)만** 넣었다. v01.01 부터는 같은 발화의 **대본(텍스트)** 을 함께 두면,
대본을 음성에 맞춰 음소마다 시간을 재고(Montreal Forced Aligner, MFA) 그 구간에서 입 모양을 고친다.
특히 **p · b · m 에서 입술이 닫히고 f · v 에서 아랫입술이 윗니에 닿는 것**이 확실해진다.
턱(Jaw) · 입술 크기(Lip)는 지금처럼 음성이 정한다.

```
 ┌ 한 번만 ───────────────────────────┐
 │ ① setup_env.bat   (이미 했으면 생략) │
 │ ② setup_mfa.bat   (설치 폴더 선택)   │
 └────────────────────────────────────┘
 ③ wav 옆에 대본 파일 두기  →  ④ 변환기: Correct 모드로 Convert  →  ⑤ Maya: JALI LipSync 로 리그에 키
```

---

## ① 추론 환경 — `setup_env.bat`

이미 변환기를 쓰고 있었다면 건너뛴다. 처음이면 `setup_env.bat` 더블클릭 → `SETUP OK` ([0050 §1](0050_converter_guide.md)).

---

## ② MFA 설치 — `setup_mfa.bat` (PC 마다 한 번)

`setup_mfa.bat` 더블클릭.

```
[1/5] Install folder
      Install folder [C:\...\JUN_JALI\.mfa]:  ← Enter = 기본, 또는 경로 입력 (예: D:\mfa)
[2/5] Miniforge 26.7.2-0 ...                 ← 내려받아 확인 후 설치 (PC 설정은 바꾸지 않는다)
[3/5] MFA environment ...                    ← 5 ~ 15분
[4/5] Models ...                             ← 영어 · 한국어 · 일본어
[5/5] Self test ...   alignment OK
 MFA SETUP OK  -  D:\mfa
```

| 알아 둘 것 | |
|-----------|--|
| 용량 · 시간 | 약 **6.5 GB**, 처음 5 ~ 15분. 인터넷 필요 |
| 설치 경로 | **공백 · 한글이 없는 경로만** 된다 (`C:\mfa` ○, `C:\My Tools\mfa` ✕, `C:\Users\홍길동\...` ✕). 안 되면 이유를 보여 주고 다시 묻는다 |
| 경로를 바로 주기 | 명령창에서 `setup_mfa.bat D:\mfa` |
| PC 에 남는 것 | 고른 폴더 하나뿐 — PATH · 레지스트리 · 바로가기를 건드리지 않는다. **지우려면 그 폴더만 지운다** |
| 다른 PC | 저장소를 받고 똑같이 `setup_mfa.bat` — 저장소의 `mfa_env.lock.txt` 가 버전을 고정해 같은 환경이 된다 |
| 다시 실행 | 안전하다. 이미 받은 것은 건너뛴다 (빠진 모델만 받는다) |

---

## ③ 대본 준비

### 파일 규칙

| 규칙 | 예 |
|------|-----|
| wav 와 **같은 폴더 · 같은 이름** | `line01.wav` ↔ `line01.lab` |
| 확장자 `.lab` **권장** (`.txt` 도 된다, 둘 다 있으면 `.lab`) | `.txt` 는 결과 파일 이름과 겹친다 → 출력 폴더를 꼭 정한다 (아래 ④) |
| **UTF-8** 로 저장 | 메모장: 다른 이름으로 저장 → 인코딩 `UTF-8` |
| 대본 없는 wav 도 같이 넣어도 된다 | 그 파일은 지금처럼 음성만으로 변환 |

```
voice\
  line01.wav   line01.lab     ← 보정됨
  line02.wav   line02.lab     ← 보정됨
  line03.wav                  ← 음성만 (대본 없음)
```

### 대본 쓰는 법 — **실제로 말한 그대로**

| 이렇게 | 이렇게 하지 않는다 | 이유 |
|--------|-------------------|------|
| `twenty eighteen` | `2018` | 숫자 · 기호는 읽는 대로 |
| `This coffee sucks` | `Narrator: This coffee sucks [laughs]` | 화자 이름 · 무대 지시는 말하지 않은 소리 |
| 말한 단어만, 말한 순서로 | 대본 원고(실제 녹음과 다른 부분 포함) | **말하지 않은 단어 · 철자가 다른 단어가 있으면 그 주변이 틀어진다** |
| `curves` (들리는 대로) | `cures` (오타) | 오타면 다른 발음으로 정렬된다 |

언어별 예:

```
English   We present a novel deep learning based approach.
Korean    오늘 날씨가 정말 좋네요.
Japanese  今日はいい天気ですね。       (한자 그대로도 되지만, 읽기가 애매하면 かな 로: きょうはいいてんきですね)
```

- 줄바꿈 · 문장부호는 있어도 된다 (한 줄로 합쳐 쓴다).
- 사전에 없는 단어(이름 · 신조어 — 예 `VizimNet`)도 대부분 된다: 발음을 자동으로 만든다(G2P).

---

## ④ 변환 — `Run_VisemeNet_Converter.bat`

```
┌ Input WAV Files ─────────────────────────────────────────────┐
│ [Add Files...] [Add Folder...]                                │
│  voice\line01.wav                                             │
│  voice\line02.wav                                             │
├ Output ───────────────────────────────────────────────────────┤
│ Folder [D:\project\visemes          ] [Browse...] [Open]      │  ← 정한다 (대본이 .txt 면 필수)
│ [x] Write .visemenet.json info file   [ ] Overwrite existing  │
│ Max length (sec) [120]   Inference [Deterministic (recommended)]│
├ Transcript (optional) ────────────────────────────────────────┤
│ Mode [Correct with transcript (MFA)]  Language [Korean     ]  │  ← 여기
│ MFA folder [                                    ] [Browse...] │  ← 비우면 setup_mfa 가 고른 폴더
│ MFA: D:\mfa                                                   │  ← 찾았는지 표시
├───────────────────────────────────────────────────────────────┤
│ [Check Files]                    [ Convert ]        [Stop]    │
└───────────────────────────────────────────────────────────────┘
```

1. **WAV 넣기** — `Add Files...` / `Add Folder...` / 끌어다 놓기. 대본 파일은 넣지 않는다(wav 만 넣으면 옆의 대본을 알아서 찾는다).
2. **출력 폴더** 지정.
3. **`Transcript` 상자**
   - `Mode` → **`Correct with transcript (MFA)`**
   - `Language` → 음성 · 대본의 언어 (`English` / `Korean` / `Japanese`). **한 번의 변환에 한 언어** — 언어가 섞였으면 나눠서 변환한다.
   - `MFA folder` → 보통 비워 둔다. 아래 줄이 `MFA: not found` 면 ②를 하거나 `Browse...` 로 설치 폴더 지정.
4. **`Check Files`** — 변환 없이 검사. 파일마다 대본을 찾았는지 나온다.
   ```
   [OK] line01.wav  44100 Hz · int16 · 1 ch · 2.31 s
   [INFO] line01.wav  transcript: line01.lab
   [INFO] line03.wav  transcript: none (audio only)
   [DONE] All 3 file(s) passed the check.
   ```
5. **`Convert`** — 대본 있는 파일을 **한 번에** 정렬한 뒤(수십 초 — 대부분 MFA 시작 시간) 하나씩 변환한다. (아래 로그는 모양을 보여 주는 예시)
   ```
   [INFO] MFA align: 2 file(s), Korean (korean_mfa / korean_mfa)
   [INFO] MFA finished in 24.8 s
   [OK] line01.wav  -> line01.txt  (199 rows, corrected, 1.4 s)
   [OK] line02.wav  -> line02.txt  (310 rows, corrected, 1.6 s)
   [OK] line03.wav  -> line03.txt  (280 rows, audio only, 1.5 s)
   [DONE] 3 converted in 31.2 s
   ```
   `corrected` = 대본으로 보정됨, `audio only` = 음성만.

설정(모드 · 언어 · MFA 폴더 포함)은 창을 닫을 때 저장된다.

### 결과 파일

| 파일 | 내용 |
|------|------|
| `<이름>.txt` | 비짐 커브 (10ms 마다 22개 값) — **형식은 이전과 같다**. Maya 툴이 그대로 읽는다 |
| `<이름>.visemenet.json` | 정보 파일. 보정했으면 `correction` 에 언어 · 대본 · MFA 버전 · 보정한 음소 수 |
| `<이름>.phones.json` | 보정했을 때만 — 정렬된 단어 · 음소와 시간 (`[시작초, 끝초, "라벨"]`). 정렬이 맞았는지 볼 때 |

---

## ⑤ Maya — `JALI LipSync` (A00540)

이전과 같다 ([A00540 문서](../../Maya_Python/JUN_All/docs/A00540_JaliLipSync.md) — Maya_Python 저장소).

1. 셸프의 `JaliLipSync` 버튼 (처음이면 `__dragDrop_A00540.py` 를 뷰포트로 드롭해 설치).
2. `Viseme TXT` 의 `...` → ④의 `<이름>.txt`. **WAV 는 자동으로 채워진다** (json 의 원본 경로).
3. `Apply`.

보정 결과 txt 도 열 구성이 같아 A00540 은 고칠 것이 없다 (v01.01 결과로 읽기 · WAV 자동 찾기 확인).

### 보정 전후 비교하기

같은 wav 를 **출력 폴더만 다르게** 두 번 변환한다 — `Mode = Audio only` → `...\audio`, `Mode = Correct` → `...\correct`.
각각 Apply 해서 p · b · m · f · v 가 나오는 곳을 재생해 본다.
예시 음성으로 만든 비교 장면: `out\m2\angela_JALI_visemenet_intro_audio.ma` / `..._correct.ma` (이 PC 에만 있다 — gitignore).

---

## 문제가 생기면

| 로그 | 뜻 | 할 일 |
|------|-----|------|
| `MFA: not found` (상자 안) · `E30 MFA not found` | MFA 설치를 못 찾음 | ② 실행, 또는 `MFA folder` 지정 |
| `E31 MFA model missing for Korean` | 그 언어 모델이 없음 | `setup_mfa.bat` 다시 실행 |
| `E32 transcript is empty` / `not UTF-8` | 대본 파일 문제 | UTF-8 로 다시 저장, 내용 확인 |
| `E34 output would overwrite the transcript` | 출력 폴더를 비워 둬서 결과 `.txt` 가 대본 `.txt` 를 덮게 됨 | 출력 폴더 지정, 또는 대본을 `.lab` 으로 |
| `W10 alignment failed - audio only` | 그 파일은 정렬 실패 → 음성만으로 변환됨 | 대본이 실제 녹음과 같은지 (빠진 말 · 더한 말 · 다른 언어) |
| `W11 N word(s) not in the dictionary` | 발음을 못 만든 단어 → 그 구간은 보정 안 함 | 철자 확인, 읽는 대로 풀어 쓰기 |
| `W13 phones not in ipa_to_jali.json` | 매핑표에 없는 음소 → 그 구간은 보정 안 함 | 그대로 써도 된다. 자주 나오면 알려 줄 것 (표에 추가) |
| `(…, audio only, …)` 인데 대본을 뒀다 | 대본을 못 찾음 | 이름이 wav 와 같은지, 같은 폴더인지, `Mode` 가 Correct 인지 |

나머지 코드(E01 ~ E24)는 [0050 §3](0050_converter_guide.md).

---

## 자주 묻는 것

**대본이 꼭 있어야 하나?** — 아니다. 대본이 없는 wav 는 이전과 똑같이 변환된다. `Mode = Audio only` 면 대본이 있어도 쓰지 않는다.

**한국어 · 일본어도 되나?** — 정렬 · 보정은 된다(모델 설치 · 음소 매핑 완료). 다만 **실제 한국어 · 일본어 녹음으로 품질을 본 적은 아직 없다**
(0060 M4). 또 리그 적용 매핑이 `Eu` · `JY` 열을 쓰지 않아, ㅡ · う 같은 모음은 입 모양이 일부만 반영된다(0060 M3 에서 다룬다).

**보정 세기를 바꿀 수 있나?** — 지금은 코드 값(입술 음소 최솟값 0.8, 그 밖의 음소 0.6, 다른 비짐 ×0.5, 무음 ×0.2)이다.
보고 너무 세거나 약하면 알려 줄 것 — 초안 값이다.

**MFA 를 지우려면?** — ②에서 고른 폴더를 지운다. 저장소의 `mfa_path.local.txt` 도 지우면 흔적이 없다.

**처음 Convert 가 느리다** — 모델 로드(몇 초) + MFA 시작(20초 안팎)이다. 파일이 많아도 정렬은 한 번만 하므로, **여러 파일을 한 번에** 넣는 편이 빠르다.
