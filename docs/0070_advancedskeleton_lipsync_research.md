# AdvancedSkeleton 의 립싱크 두 기능 — Auto lipsync (MFA) · Audio2Face 조사

> **작성** 2026-10-20 · **코드 분석만** 했다 (실행 · 실측 없음).
> 근거: 로컬 원본 `C:\Users\USER\Desktop\JP\0020_maya_plugin\0040_AdvancedSkeleton\AdvancedSkeleton.mel` (**Version 6.801**) + NVIDIA 공개 문서.
> 공식 도움말([animationstudios.com.au/help](https://animationstudios.com.au/help/))에는 두 기능 설명이 없다 — Phonemes 항목만 있다.
> 선행 문서: [0010 진단](0010_visemenet_feasibility.md) · [0040 ARKit 매칭](0040_jali_arkit_mapping.md) · [0060 대본 + MFA 계획](0060_transcript_mfa_plan.md)

**왜 조사했나**: 현재 툴(VisemeNet)은 음성만으로는 기대만큼 표정이 나오지 않는다. 같은 문제를 상용 리깅 툴은 어떻게 푸는지 보고,
[0060](0060_transcript_mfa_plan.md) 계획에 가져올 것과 대안을 정한다.

---

## 0. 결론

AdvancedSkeleton 의 Selector/Picker 메뉴에는 립싱크 항목이 **두 개** 나란히 있다 (`AdvancedSkeleton.mel:9816-9817`).

| 메뉴 | 정체 | 입력 | 출력 | 한 줄 |
|------|------|------|------|-------|
| **Auto lipsync** | **Montreal Forced Aligner 1.1** 로 대본을 정렬 → 음소 키 | 음성 + **대본** | 음소 컨트롤 16개 키 + 자막 + 무작위 Idle | 0060 계획과 **같은 구조**, 더 단순한 버전 |
| **Audio2Face** | **NVIDIA Audio2Face** 결과(ARKit 52)를 리그 컨트롤로 **리타깃** | 음성만 (NVIDIA 쪽) | 얼굴 전체 컨트롤 키 | AdvancedSkeleton 은 **연결 · 굽기만** 한다 |

사용자가 처음 말한 "auto lip-sync" 는 **Audio2Face** 쪽이다. 둘 다 정리한다.

우리 작업에 주는 의미:

1. **MFA 정렬 방식은 상용 리깅 툴에서 이미 쓰인다** → 0060 방향이 타당하다.
2. **Audio2Face 는 VisemeNet 과 같은 "오디오만" 범주**의 더 크고 최신인 모델이고, 감정 · 윗얼굴까지 만든다. 대본(MFA)과는 **대체가 아니라 조합** 관계다 (§4).
3. angela(JALI 리그)에 쓰려면 AdvancedSkeleton 이 한 일 — **ARKit 52 → 리그 컨트롤 매핑** — 을 우리도 만들어야 한다. [0040](0040_jali_arkit_mapping.md) 의 역방향이다.

---

## 1. Audio2Face

### 1.1 전체 흐름

```
wav ──▶ NVIDIA Audio2Face-3D  (신경망 — GPU 서버 · NIM 또는 NVIDIA 클라우드)
          │  Audio2Emotion: 음성에서 감정 추정 (또는 직접 지정)
          ▼
        ARKit 52 블렌드셰이프 가중치 (0~1, 프레임마다)
          │  Maya-ACE 플러그인이 Maya 의 blendShape 노드에 연결
          ▼
AdvancedSkeleton  Connect  ──▶  가중치 → 페이셜 컨트롤 (Set Driven Key)
          ▼
AdvancedSkeleton  bake     ──▶  컨트롤에 키를 굽고 연결 해제
```

### 1.2 NVIDIA 쪽 — 음성 → ARKit 가중치

- **Maya-ACE** 는 MIT 라이선스 플러그인이고 Audio2Face-3D 서비스의 **클라이언트일 뿐**이다. 추론은 NVIDIA 클라우드(API 키) 또는 직접 띄운 NIM 에서 돈다.
- 출력은 **ARKit 블렌드셰이프 가중치** — Maya blendShape 노드에 바로 연결된다.
- 감정은 **Audio2Emotion** 으로 음성에서 자동 추정하거나 직접 지정한다 → 눈썹 · 눈 · 볼까지 움직인다.
- 논문(arXiv 2508.16401) 구조: 오디오 + 감정 라벨 → 신경망 → 후처리 → **블렌드셰이프 솔브**로 캐릭터에 리타깃.
- **2025-09 공개**: Audio2Face 모델, Audio2Emotion 모델, SDK, Maya · UE 플러그인, 학습 프레임워크.

### 1.3 AdvancedSkeleton 쪽 — Connect

| 단계 | 함수 (행) | 하는 일 |
|------|-----------|---------|
| UI | `asAudio2FaceUI` (16931) | Maya-ACE 가 만든 **blendShape 노드**를 고른다. 리그 자체 블렌드셰이프(`*asFace*`, `*Close*BS*`, `FaceAllSet` 소속)는 목록에서 뺀다 |
| Connect | `asConnectAudio2Face` (14848) | 표시 노드 `Audio2FaceViaConnectARKitUI` 를 만들고 **`asConnectARKit` 을 그대로 호출** |
| 매핑 | `asConnectARKit` (14529) | ARKit 52 이름마다 `asDsSdk` 로 **Set Driven Key** — 아이폰 페이셜 캡처용 기능을 재사용 |
| bake | `asBakeAudio2Face` (16971) | `FaceControlSet` 전체를 재생 범위에 프레임마다 굽고, 변화 없는 채널 삭제 |
| Disconnect | `asDisconnectAudio2Face` (14854) | blendShape 에서 나가는 animCurve 삭제, 빌드 포즈로 복귀 |

**매핑 예** (`asConnectARKit`, 값은 ARKit 1.0 일 때 컨트롤 값):

| ARKit | AdvancedSkeleton 컨트롤 |
|-------|-------------------------|
| `jawOpen` | `ctrlMouth_M.ty` −1 |
| `jawLeft` / `jawRight` / `jawForward` | `ctrlMouth_M.jawSide` ±5 / `.jawForward` 5 (v5.750 이후 리그) |
| `eyeBlinkLeft` | `ctrlEye_L.blink` 10 |
| `eyeLookUp/Down/In/OutLeft` | `ctrlEye_L.ty` / `.tx` ±1 |
| `eyeSquint` · `eyeWide` | `ctrlEye.squint` 10 · `.wide` 10 |
| `mouthSmileLeft` | `ctrlMouthCorner_L.tx` 0.75 + `.ty` 0.75 |
| `mouthFrown` · `mouthStretch` | `ctrlMouthCorner` (tx 0.25, ty −0.25) · (tx 0.5, ty −0.5) |
| `mouthPucker` | `ctrlLips_M.upperPucker` · `lowerPucker` 10 |
| `mouthFunnel` | Pucker 10 + 윗입술 SDK +0.3 · 아랫입술 SDK −0.3 |
| `mouthClose` | 턱을 연 상태의 아랫입술 위치를 재서 윗입술 · 아랫입술 SDK 를 **반씩** 이동 (sticky lips) |
| `mouthPress` | `ctrlLips_M.upperSqueeze` · `lowerSqueeze` 1.5 + 입꼬리 ty 0.25 |
| `mouthRollUpper/Lower` | `ctrlLips_M.upperRoll/lowerRoll` −5 |
| `mouthUpperUp` · `mouthLowerDown` | 입술 SDK ty ±0.4 (+ 중앙 0.3) |
| `browInnerUp` | `ctrlBrow_L/R.tx` 1 |
| `browDown` · `browOuterUp` | `ctrlBrow.ty` −0.75 + `.squeeze` 7.5 · `.outerUpDown` 7.5 |
| `cheekPuff` · `cheekSquint` | `ctrlCheek.tx` 0.4 · `ctrlEye.squint` 3 + 볼 SDK |
| `noseSneer` | `ctrlNose.ty` 0.5 |
| `tongueOut` | `SDKTongue0_M.tx` 1.5 · `.rz` 15 |

- **`mouthClose includes mouthOpen`** 옵션 (기본 켬): 코드 주석 *"option to compensate for audio2face bug"*.
  ARKit 의 `mouthClose` 는 `jawOpen` 과 함께 쓰는 형태인데(턱은 열린 채 입술만 닫음), Audio2Face 출력에서 이 조합이 맞지 않아
  `mouthClose` 가 `ctrlMouth_M.ty` 도 −1 만큼 함께 움직이게 보정한다.
- 블렌드셰이프형 페이셜 리그(`RigType == 1`)에서는 동작하지 않는다 — **조인트형** 페이셜 리그가 필요하다는 오류를 낸다.
- 오른쪽/왼쪽 이름이 `_R`/`_L` 로 바뀐 노드(FaceCap 등)도 받는다. 없는 타깃은 `Missing ARKit BlendShapes target` 을 찍고 건너뛴다.

---

## 2. Auto lipsync (MFA)

### 2.1 UI — `asAutoLipSyncUI` (16987)

- **대사 텍스트** 칸 (비라틴 문자는 별도 텍스트 편집기), **언어**, `phoneme fadeIn` / `fadeOut` (기본 0.05초).
- Idle 체크박스: `Blink` · `Glimpse` · `EyeBrows` · `Head`.
- 오디오는 **타임라인에 올린 sound 노드**를 쓴다.
- 언어 목록 (`asAutoLipSyncLanguages`, 18314): English 외 Bulgarian · Croatian · Czech · French · German · Hausa · **Korean** · Mandarin · Polish ·
  Portuguese · Russian · Spanish · Swahili · Swedish · Thai · Turkish · Ukrainian. **일본어 없음.** (Vietnamese 는 UTF-8 문제로 제외)

### 2.2 처음 실행 — `asAutoLipSyncDownload` (15454) · `asAutoLipSyncLanguageChanged` (18236)

- GitHub 에서 **MFA `v1.1.0-beta.2`** (2019) 단독 실행 파일 zip (win64 / macosx) 을 `AdvancedSkeletonFiles/bin/` 에 받는다.
- 영어 사전: `librispeech-lexicon.txt` (**ARPAbet**).
- 다른 언어: `mfa-models` 에서 음향 모델 `<언어>.zip` + **G2P** `<언어>_g2p.zip` (v1 모델, Mandarin 은 pinyin 변종).

### 2.3 정렬 — `asAutoLipSyncForceAlign` (17108)

1. 임시 폴더 `…/AdvancedSkeleton/autoLipSync/input/` 에 `align.wav` + `align.txt`. 라틴 문자 언어는 `unicodedata` 로 악센트 제거.
2. 영어가 아니면 `mfa_generate_dictionary` 로 **대본 단어마다 G2P → 즉석 사전**.
3. `mfa_align` → `output/align.TextGrid`.
4. 실패 시 ① ffmpeg 재인코딩 후 재시도 ② 언어 파일 재다운로드를 차례로 묻는다.
5. **타임라인 구간이 선택돼 있으면** ffmpeg 로 그 구간만 잘라 다시 정렬 (부분 수정).

### 2.4 키 생성 — `asAutoLipSyncImport` (17300)

- TextGrid 의 `words` · `phones` 티어를 읽고 `(시간 + sound offset) × 씬 fps` 로 프레임 계산.
- `words` → **자막** (텍스트 커브가 타이밍에 맞춰 흐른다. 비라틴은 ImageMagick 으로 글자 이미지를 만들어 평면에 붙인다).
- `phones` → `sil`/`sp`/`spn` 제외 → `asAutoLipSyncPhonemeMapping` (17765) → `ctrlPhonemes_M` 의 **16개 어트리뷰트** 중 하나
  (`aaa eh ahh ohh uuu iee rrr www sss fff tth mbp ssh schwa gk lntd`, 39089행).
- 음소 하나당 키 3개 (17595-17597):

  ```
  0   @ 시작 − fadeIn
  10  @ 구간 중앙
  0   @ 끝 + fadeOut
  ```

- `jaw` · `lip` 은 **상수 0.25** (블렌드셰이프 셋업이면 1). 오디오 강도는 쓰지 않는다.

### 2.5 Idle

눈 깜빡임 + squint, 눈동자 흘끗, 머리 FK 회전, 눈썹을 **`rand` 간격 · `rand` 값**으로 키. 대본 · 오디오 내용과 무관하다. 첫 단어 전에는 넣지 않는다.

### 2.6 코드에서 본 특이점

| 항목 | 내용 |
|------|------|
| 거친 매핑 | `V` → `schwa` (`fff` 아님), `TH`/`DH` → `lntd` 인데 `tth` 는 `IY0`(이 모음)에 쓰임, `Y` → `uuu` |
| 한국어 | `EO`(ㅓ) → `eh`, **`IEO`(ㅕ) → `""` — 키가 안 찍힌다** |
| 언어 구분 없음 | 모든 언어가 **같은 if 체인** — 같은 음소 문자열이면 뒤쪽 언어 매핑이 앞쪽을 덮는다 |
| 죽은 조건 | 입력을 `toupper` 한 뒤 비교하므로 소문자 조건 `"tcp"` · `"x"` 는 절대 맞지 않는다 |
| 균일한 강도 | 모든 음소가 같은 높이(10)까지 — 강세 · 크기 차이 없음 |

---

## 3. 세 방식 비교

| | VisemeNet (현재 툴) | AS Auto lipsync | NVIDIA Audio2Face | 0060 계획 |
|--|--------------------|-----------------|-------------------|-----------|
| 입력 | 음성 | 음성 + 대본 | **음성** | 음성 + 대본 (선택) |
| 음소 결정 | 오디오에서 추측 | MFA 1.1 (2019) | 신경망이 암묵적으로 | **MFA 3.x** (경계 오차 15ms 미만) |
| 음소 표기 | — | ARPAbet + 언어별 v1 로마자 | — | **IPA 공용 표** |
| 일본어 | 영어 학습 모델로 추론 | **없음** | 실험 필요 | `japanese_mfa` |
| 강도 · 크기 | Jaw / Lip 회귀 | 상수 | 신경망 | VisemeNet Jaw / Lip |
| 공동조음 | 모델 + smoothing | 삼각형 키 0.05초 겹침 | 신경망 | 사다리꼴 커브 + 입술 우선 |
| 윗얼굴 · 감정 | 없음 | 무작위 Idle | **Audio2Emotion** | 안 C (계획) |
| 출력 | JALI 22열 | AS 음소 16개 | **ARKit 52** | JALI 22열 |
| 실행 | 로컬 CPU (TF) | 로컬 (MFA 바이너리) | **NVIDIA 클라우드 또는 GPU** | 로컬 CPU + MFA |

---

## 4. 우리 작업에 가져올 것

### 4.1 0060 에 바로 넣을 아이디어 (Auto lipsync 에서)

| 아이디어 | 0060 의 어디에 |
|----------|----------------|
| **타임라인 구간만 다시 정렬** (부분 수정) | 변환기 · A00540 — 대본이 틀린 구간만 고쳐 다시 돌리기 |
| **자막 표시** | `.phones.json` 의 단어 티어를 Maya 에 표시 (디버그 · 대본 확인) |
| 정렬 실패 시 **ffmpeg 재인코딩 후 재시도** | §5.3 정렬 실패 대비 |
| 대본으로 **G2P 즉석 사전** | §3.2 — 이미 계획에 있음, AS 도 같은 방식임을 확인 |
| **무작위 Idle** | 안 C 전까지 쓸 저렴한 기본값 |

**피할 것**: 언어를 섞은 if 체인 매핑, 균일한 강도, 고정 Jaw/Lip — 0060 의 IPA 공용 표 · VisemeNet Jaw/Lip · 공동조음 규칙이 이를 이미 피한다.

### 4.2 대안 — Audio2Face + MFA 보정

Audio2Face 는 **대본을 쓰지 않으므로** 다국어 음소 오인(0060 의 P2)이 해결되는지는 실험해야 한다. 대신 **윗얼굴 · 감정(P4)** 을 크게 해결한다.
그래서 대체가 아니라 조합이 자연스럽다.

```
wav ──▶ Audio2Face ──▶ ARKit 52 (얼굴 전체 · 감정)
                         │
대본 ─▶ MFA ─▶ 음소 구간 ─┴─▶ 보정 (0060 안 B 원리를 ARKit 채널에)
                              p·b·m  → mouthClose · mouthPress 최솟값, jawOpen 제한
                              f·v    → mouthRollLower · mouthUpperUp
                              u·o·w  → mouthPucker · mouthFunnel
                         ▼
                ARKit 52 → angela 컨트롤 매핑 (새로 필요) ──▶ 키
```

- **ARKit → angela 매핑**: AS 의 `asConnectARKit` 표(§1.3)가 형식의 본보기다. [0040](0040_jali_arkit_mapping.md) 은 JALI → ARKit 방향을 실측했으므로
  그 역방향을 만든다. JALI 리그는 근육 기반이라 1:1 이 아니고 **ARKit 하나 → 컨트롤 여러 개** 조합이 된다.
- **ARKit 아바타에 쓴다면** 매핑 없이 바로 쓸 수 있다 ([0030](0030_tool_plan.md) T4-b 와 연결).

---

## 5. 쓰기 전에 확인할 것

| # | 항목 | 내용 |
|---|------|------|
| C1 | 실행 환경 | Audio2Face 추론은 NVIDIA 클라우드 API 키 또는 로컬 NIM(NVIDIA GPU 필요). **이 PC 의 GPU 는 아직 확인하지 않았다** |
| C2 | 라이선스 | SDK · Maya-ACE · UE 플러그인 **MIT**, 학습 프레임워크 **Apache**, 모델은 **Open Weights 또는 평가 전용**(모델마다 다름) |
| C3 | 약관 제한 | NIM 약관에 *"emotion recognition 목적으로 사용 금지"* 조항 — 포트폴리오를 넘는 배포 · 상업 사용 시 확인 |
| C4 | 품질 | 한국어 · 일본어에서 Audio2Face 입 모양 품질 — **실험 필요** |
| C5 | AS 버전 | 이 문서는 v6.801 코드 기준. 다른 버전은 함수 · 행 번호가 다를 수 있다 |

---

## 6. 다음 단계 제안

1. **C1 확인** — 이 PC 의 GPU · NVIDIA 클라우드 키 가능 여부.
2. 가능하면 `test_audio/visemenet_intro.wav` 를 Maya-ACE 로 돌려 ARKit 52 결과를 받고, VisemeNet 결과와 나란히 비교.
3. 0060 의 M0 ~ M2 (MFA 설치 · 영어 정렬 · 안 B) 와 병행 — MFA 출력은 VisemeNet · Audio2Face 양쪽 보정에 똑같이 쓰인다.
4. Audio2Face 를 쓰기로 하면 **ARKit 52 → angela 매핑**을 0040 처럼 리그에서 실측해 만든다.

---

## 참고

- 로컬 원본 `AdvancedSkeleton.mel` v6.801 — 9816 (메뉴), 14529 (`asConnectARKit`), 14848 · 14854 (Connect · Disconnect), 15454 (MFA 다운로드),
  16931 (`asAudio2FaceUI`), 16971 (bake), 16987 (`asAutoLipSyncUI`), 17108 (정렬), 17300 (키 생성), 17765 (음소 매핑), 18236 · 18314 (언어), 39089 (음소 16개)
- [Maya-ACE overview (NVIDIA)](https://docs.nvidia.com/ace/maya-ace/1.2/texts/overview.html) · [Maya-ACE module (latest)](https://docs.nvidia.com/ace/latest/modules/maya_ace/index.html)
- [Audio2Face-3D NIM Documentation](https://docs.nvidia.com/nim/digital-human/a2f-3d/latest/index.html) · [Audio2Face-3D microservice overview 2.0](https://docs.nvidia.com/ace/audio2face-3d-microservice/2.0/text/getting-started/overview.html)
- *Audio2Face-3D* 논문 — [arXiv 2508.16401](https://web3.arxiv.org/pdf/2508.16401)
- [GIGAZINE — NVIDIA open-sources Audio2Face (2025-09-26)](https://gigazine.net/gsc_news/en/20250926-nvidia-audio2face-open-sources)
- [AdvancedSkeleton Help](https://animationstudios.com.au/help/) — 두 기능 설명 없음
- [joaen/maya-auto-lip-sync](https://github.com/joaen/maya-auto-lip-sync) — MFA 를 쓰는 다른 Maya 립싱크 툴
