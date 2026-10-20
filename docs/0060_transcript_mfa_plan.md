# 대본 + MFA 로 페이셜 품질 개선 — 계획서

> **작성** 2026-10-20 · 아직 **실험 전** 계획이다. 실측이 끝나면 각 절에 결과를 덧붙인다.
> 선행 문서: [0010 진단](0010_visemenet_feasibility.md) · [0030 툴 계획](0030_tool_plan.md) · [0040 ARKit 매칭](0040_jali_arkit_mapping.md) · [0050 변환기 사용법](0050_converter_guide.md)

**목표**: 음성(wav)만이 아니라 **같은 발화의 대본**(영어 · 한국어 · 일본어 텍스트)을 함께 넣어,
VisemeNet 단독보다 **정확한 입 모양**(특히 다국어)과 **풍부한 표정**을 만든다.
대본은 선택 입력이다 — 없으면 지금처럼 오디오만으로 동작한다.

---

## 0. 요약

| 무엇을 | 누가 맡나 |
|--------|-----------|
| **어떤 음소인가** (what) | **대본** → MFA 가 음소열로 확정 |
| **언제 시작 · 끝나나** (when) | **MFA** 강제 정렬 (오디오 ↔ 음소, 10ms 단위) |
| **얼마나 세게 · 크게** (how much) | **VisemeNet** Jaw / Lip 2축 (오디오 에너지 · 스펙트럼 기반) |
| **감정 · 강조** (선택) | 대본 문장부호 · 태그 + 오디오 피치 · 에너지 |

이것은 원래 **JALI 논문(Edwards et al., 2016)의 구조**다 — 대본 + forced alignment 로 음소와 타이밍을,
오디오로 JA · LI 2축을 얻었다. VisemeNet 은 그 과정을 **대본 없이** 대체하려 한 후속 연구다.
이 계획은 JALI 구조로 돌아가되, VisemeNet 이 잘하는 Jaw / Lip 커브는 그대로 살린다.

---

## 1. 문제 — 음성만으로 부족한 이유

| # | 증상 | 원인 |
|---|------|------|
| P1 | **입술이 닫혀야 할 때 안 닫힌다** (p · b · m → `MBP` 누락), f · v 가 뭉개진다 (`FV`) | 짧은 폐쇄 구간이 `postprocess.py` 의 임계값 게이트 · hanning smoothing 에서 지워진다 |
| P2 | 한국어 · 일본어에서 **엉뚱한 비짐**이 켜진다 | 학습 데이터가 영어뿐(GRID · SAVEE · BIWI) — 영어에 없는 모음 · 자음을 가까운 영어 음소로 오인 ([0010](0010_visemenet_feasibility.md) §5) |
| P3 | 비짐 경계가 흐릿하고 늦다 | 오디오 → 음소 분류 자체가 불확실 + 24프레임 창 · smoothing |
| P4 | 입 외의 표정(눈썹 · 눈 · 머리)이 없다 | 모델 출력이 22열(입 · 턱)뿐 |

P1 ~ P3 은 "어떤 음소인가" 를 **오디오에서 추측**하기 때문이다. 대본이 있으면 추측할 필요가 없다.

---

## 2. 개선안

| 안 | 내용 | 해결 | 비용 | 판단 |
|----|------|------|------|------|
| **B. 보정 (Correct)** | VisemeNet 출력은 그대로 두고, MFA 음소 구간으로 **재가중** — 구간 밖 비짐은 감쇠, 구간 안 해당 비짐은 최솟값 보장 (예: p 구간 `MBP ≥ 0.8`) | P1 · 일부 P2 | 작음 | **1단계** — 효과를 가장 빨리 본다 |
| **A. 하이브리드 (Hybrid)** | 비짐 20열(열 2 ~ 21)을 **MFA 음소 + 공동조음 규칙으로 새로 생성**. Jaw / Lip(열 0 ~ 1)은 VisemeNet 값 유지 | P1 · P2 · P3 | 중간 | **2단계 — 최종 권장** |
| C. 비립 표현 (Expression) | 대본 문장부호(`?` `!`) · 감정 태그 · 강조 단어 + 피치 · 에너지 피크 → 눈썹 · 눈 · 머리 키 | P4 | 중간 | 3단계 (선택) |
| D. 재학습 | MFA 로 다국어 음소 라벨을 만들어 모델 fine-tune | P2 근본 | 큼 (데이터 수집 · TF1 그래프 재학습) | 보류 |

B 와 A 는 **같은 MFA 출력**을 쓴다. B 로 파이프라인을 검증하고 A 로 넘어가면 버리는 작업이 없다.

---

## 3. Montreal Forced Aligner (MFA) 의 역할

### 3.1 하는 일

- 입력: `utt.wav` + 같은 이름의 대본 `utt.txt`(또는 `.lab`).
- 출력: **TextGrid** — `words` 티어와 `phones` 티어. 음소마다 `(시작, 끝, IPA 기호)`.
- 정확도: MFA 3.0 논문(Interspeech 2026)에서 영어 · 일본어 · 한국어 벤치마크 **평균 경계 오차 15ms 미만**.
  우리 해상도가 10ms(100fps)이므로 사실상 프레임 단위다.
- 시간축: MFA 기본 프레임 간격은 10ms 로 알고 있다 (**설치 후 확인 — V1**). 맞다면 VisemeNet 100fps 행과 그대로 맞물린다.
  다르더라도 TextGrid 는 초 단위 시간이라 `row = round(t × 100)` 으로 옮기면 된다.

### 3.2 언어별 준비물

| 언어 | 음향 모델 · 사전 | 추가 의존성 | 상태 |
|------|-----------------|-------------|------|
| 영어 | `english_mfa` (IPA) — `english_us_arpa` (ARPAbet) 도 있음 | 없음 | 문서 확인 |
| 일본어 | `japanese_mfa` | SudachiPy · `sudachidict-core` (단어 분리) | 공식 문서 확인 |
| 한국어 | `korean_mfa` | 단어 분리 의존성 **미확인** | 설치하며 확인 — **V2** |
| 공통 | G2P 모델 (`mfa g2p`) | — | 사전에 없는 단어(고유명사 · 신조어)의 발음 생성 |

**IPA 로 통일**하는 `*_mfa` 모델을 쓴다 → 언어마다 매핑을 따로 만들지 않고 **IPA → 비짐 표 하나**를 공용한다(§4).

### 3.3 설치 위치

- MFA 는 Kaldi 기반이고 **conda-forge** 로 설치한다. 현재 추론 환경(`.venv`, Python 3.11 + `tensorflow-cpu` 2.15.1)과 **섞지 않는다.**
- 별도 conda 환경 `mfa` 를 두고, 변환기가 `mfa align` 을 **서브프로세스**로 부른다. 경로는 설정(`settings.py`)에 저장.
- `setup_env.bat` 확장 여부는 §9 Q2.

### 3.4 파이프라인

```
utt.wav ─┬──────────────▶ VisemeNet ──▶ (N, 22)  100fps ──────────────┐
         │                                                             │
utt.txt ─┴─▶ mfa align ─▶ utt.TextGrid ─▶ phones (t0, t1, ipa) ─┐      │
                                                                ▼      ▼
                                          IPA → 비짐 매핑 (§4) ─▶ 병합 (§5)
                                                                   │  B: 보정  /  A: 교체
                                                                   ▼
                                                     utt.txt + utt.visemenet.json  ──▶ A00540
```

---

## 4. IPA → JALI 비짐 매핑표 (초안)

JALI 비짐 20개: `Ah Aa Eh Ee Ih Oh Uh U Eu Schwa R S ShChZh Th JY LNTD GK MBP FV W`.
**초안이다 — angela 메시로 음소별 확인이 필요하다 (V5).** 파일은 `saved_params/ipa_to_jali.json` 로 둔다.

### 4.1 자음

| IPA | 예 | 비짐 | 비고 |
|-----|----|------|------|
| p b m (p̚ 포함) | 영 *map*, 한 ㅂ ㅁ, 일 ぱ ま | **MBP** | 받침 ㅂ · ㅁ 은 파열이 없어도 **입술은 닫힌다** → 유지 |
| f v | 영 *five* | **FV** | 한 · 일에 없음. 일본어 ふ(ɸ) 는 FV 약하게 + U 검토 |
| w | 영 *we*, 한 ㅘ ㅝ 의 w, 일 わ | **W** | |
| s z ts dz | 한 ㅅ ㅆ, 일 す つ | **S** | |
| ʃ ʒ tʃ dʒ ɕ tɕ dʑ | 영 *she*, 한 시 · ㅈ ㅊ, 일 し ち じ | **ShChZh** | 한국어 ㅈ ㅊ 은 입술 돌출이 영어보다 약하다 → 가중치 조정 |
| θ ð | 영 *think* | **Th** | 한 · 일에 없음 |
| j ʝ | 영 *yes*, 한 ㅑ ㅕ 의 j, 일 や | **JY** | |
| l n t d ɾ ɲ | 한 ㄴ ㄷ ㄹ, 일 な た ら | **LNTD** | 한국어 ㄹ · 일본어 ら(ɾ) 탄설음 포함 |
| k g ŋ ɴ | 한 ㄱ ㅇ(받침), 일 か | **GK** | |
| ɹ ɻ | 영 *red* | **R** | 한 · 일에 없음 |
| h ç | 한 ㅎ, 일 は ひ | (없음) | 이웃 모음 모양을 따른다 — 공동조음 |

### 4.2 모음

| IPA | 예 | 비짐 | 비고 |
|-----|----|------|------|
| a ɑ | 한 ㅏ, 일 あ | **Ah** / Aa | 일본어 あ는 영어보다 덜 벌린다 → 강도 0.8 부터 |
| æ | 영 *cat* | **Aa** | |
| e ɛ | 한 ㅔ ㅐ, 일 え | **Eh** | |
| i | 한 ㅣ, 일 い | **Ee** | |
| ɪ | 영 *sit* | **Ih** | |
| o ɔ | 한 ㅗ, 일 お | **Oh** | |
| ʌ | 영 *cup*, 한 ㅓ | **Uh** | |
| u | 영 *food*, 한 ㅜ | **U** | |
| ʊ | 영 *book* | **Eu** | |
| ɯ ɨ | 한 ㅡ, 일 う | **Ih + Eu 혼합** | **입술을 둥글게 하지 않는다** — U 로 보내면 너무 둥글다 |
| ə | 영 *about* | **Schwa** | |
| 이중모음 | 영 *aɪ*, 한 ㅢ | 앞 · 뒤 비짐을 구간 안에서 시간 분할 | MFA 가 한 음소로 줄 때만 |

### 4.3 언어별 주의

- **일본어 ん(ɴ)** — 뒤 자음에 동화된다(ま 앞 → 입술 닫힘). MFA 가 ɴ 하나로 주면 **다음 음소를 보고** MBP / LNTD / GK 를 고른다.
- **일본어 무성화 모음** (*です* 의 す, *した* 의 し) — MFA 가 모음 구간을 생략할 수 있다. 입 모양은 남으므로 자음 구간 뒤쪽에 모음 비짐을 약하게 덧댄다.
- **한국어 경음 · 격음** (ㅃ ㅍ) — 같은 MBP. 격음은 개방 직후 Jaw 가 더 열리는데, 이건 VisemeNet Jaw 에 맡긴다.

---

## 5. 병합 규칙

### 5.1 안 B — 보정

VisemeNet 출력 `V[row, col]` 에 음소 구간 마스크를 곱한다.

1. 각 음소 구간 `[t0, t1)` → 행 `[r0, r1)` (`r = round(t × 100)`).
2. 그 음소의 비짐 열 `c`: `V[r0:r1, c] = max(V[r0:r1, c], floor_c)` — 기본 `floor` 0.6, **MBP · FV 는 0.8** (폐쇄 보장).
3. 같은 구간의 **다른 비짐 열**: `× 0.5` 감쇠 (공동조음 여지는 남긴다).
4. **무음 구간**(MFA 의 빈 라벨 · `sil` · `spn`) — 비짐 전부 `× 0.2`, Jaw / Lip 은 그대로.
5. 경계 램프: 앞뒤 3행(30ms)에 선형 보간 — 계단 튐 방지.

### 5.2 안 A — 하이브리드 (비짐 생성)

1. 음소마다 **목표 비짐 · 목표 강도**(§4 표).
2. **공동조음**: 각 비짐을 사다리꼴 커브로 — 시작 120ms 전부터 올라가 끝 120ms 후까지 내려간다(JALI 논문의 onset / offset 개념, 값은 실험으로 조정).
   - **입술 음소(MBP · FV · W)가 우선** — 겹치면 다른 비짐을 눌러 폐쇄가 반드시 보이게 한다.
   - 같은 비짐이 연속하면 하나로 잇는다(입이 떨렸다 닫혔다 하지 않게).
3. **Jaw / Lip 열**은 VisemeNet 값을 그대로 쓴다. 단 MBP 구간에서는 Jaw 를 위 · 아래 입술이 닫힐 만큼 제한한다.
4. 결과 22열은 지금과 같은 형식 → **A00540 은 수정 없이** 읽는다.

### 5.3 정렬 실패 대비

- MFA 가 실패한 파일 → 경고(W) 를 남기고 **오디오만 결과로 되돌린다**(중단하지 않는다 — 대본은 선택 입력이므로).
- 부분 불일치(애드립 · 말실수) → MFA 로그의 정렬 점수가 낮은 구간은 **VisemeNet 원본 값으로 되돌린다.**

---

## 6. 툴 변경

### 6.1 VisemeNet Converter (`tools/VisemeNet_Converter/`)

| 항목 | 변경 |
|------|------|
| UI | TSL 에 `Transcript` 열 — 같은 폴더 · 같은 이름 `.txt` 를 자동으로 찾고, 없으면 `(audio only)` |
| UI | `Language` 콤보 (`English` / `Korean` / `Japanese`) · `Mode` 콤보 (`Audio only` / `Correct` / `Hybrid`) |
| UI | 설정 → `MFA environment` 경로 |
| 코어 | `app/core/aligner.py` — `mfa align` 호출 · TextGrid 파싱 → `[(t0, t1, ipa)]` |
| 코어 | `app/core/viseme_merge.py` — §5 B · A 규칙 (순수 numpy, UI 비의존 → 단위 테스트) |
| 출력 | 같은 이름 `.phones.json` (음소 구간, 디버그 · Maya 표시용) |
| 출력 | `.visemenet.json` 에 `"transcript"`, `"language"`, `"mode"`, `"aligner"` 필드 추가 (기존 필드는 그대로) |

UI 문자열은 영어로 한다.

### 6.2 새 오류 코드 (0050 의 E01 ~ E24 와 겹치지 않게)

| 코드 | 메시지 (영어) | 처리 |
|------|---------------|------|
| E30 | `MFA not found - set the MFA environment in Settings` | Correct / Hybrid 모드에서 사전 검사로 중단 |
| E31 | `MFA model missing for <language>` | 사전 검사로 중단 (`mfa model download` 안내) |
| E32 | `transcript is empty or unreadable (need UTF-8)` | 사전 검사로 중단 |
| W10 | `alignment failed - fell back to audio only` | 경고 후 계속 |
| W11 | `<n> words not in dictionary - G2P used` | 경고 후 계속 |
| W12 | `low alignment score in <a>-<b> s - audio values kept` | 경고 후 계속 |

### 6.3 A00540_JaliLipSync (Maya_Python)

- 22열 형식이 같아 **필수 변경 없음.**
- 선택: `.phones.json` 이 있으면 타임라인에 음소 라벨 표시(디버그) — 3단계 이후.

---

## 7. 단계와 검증

| 단계 | 할 일 | 완료 조건 |
|------|-------|-----------|
| **M0 설치 확인** | conda 환경 `mfa` 설치, `english_mfa` · `korean_mfa` · `japanese_mfa` 다운로드 | **V1** 프레임 간격 확인 · **V2** 한국어 의존성 확인 · Windows 11 에서 `mfa align` 동작 |
| **M1 영어 정렬** | `test_audio/visemenet_intro.wav` + 대본으로 TextGrid 생성 | **V3** 음소 경계가 파형 · VisemeNet 피크와 ±20ms 안에서 맞는지 (Praat 로 육안) |
| **M2 안 B** | `viseme_merge.correct()` + 변환기 `Correct` 모드 | **V4** angela 에서 p · b · m · f · v 폐쇄가 **매번** 보인다 (전 · 후 플레이블라스트 비교) |
| **M3 매핑표** | §4 표를 json 으로, angela 에서 음소별 확인 | **V5** 한 · 일 고유 모음(ㅡ · ㅓ · う) · 자음(ɕ · ɾ) 모양 확인 |
| **M4 다국어 B** | 한국어 · 일본어 짧은 녹음(5 ~ 10초) + 대본 각 1개 | **V6** Audio only 대비 개선이 육안으로 분명한가 |
| **M5 안 A** | `viseme_merge.hybrid()` + `Hybrid` 모드 | **V7** 3개 언어에서 B 보다 낫거나 같은가 — 아니면 B 를 기본으로 |
| M6 (선택) | 안 C 비립 표현 | 별도 계획 |

단위 테스트: `tests/test_merge.py` — 합성 음소열로 B · A 규칙(폐쇄 floor · 감쇠 · 램프 · 무음) 검사, TextGrid 파서 고정 샘플.

---

## 8. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 대본 ≠ 실제 발화 (애드립 · 반복) | 그 구간 음소가 틀린다 | §5.3 — 낮은 점수 구간은 오디오 값 유지 |
| 일본어 한자 읽기 오류 | 음소가 틀린다 | 대본을 **가나**로 받는 옵션 (§9 Q4) |
| 한국어 토큰화 · 사전 누락 | 정렬 실패 | G2P 폴백 + W11 |
| 노래 · 외침 · 속삭임 | 정렬 품질 저하 | W12 로 드러내고 오디오 값 유지 |
| MFA 설치가 무겁다 (conda · Kaldi) | 다른 PC 셋업 부담 | Correct / Hybrid 는 **선택 기능** — 없으면 Audio only 로 동작 |
| 라이선스 | MFA 는 MIT, 모델 · 사전은 모델별 라이선스 | 배포 시 확인 ([0030](0030_tool_plan.md) Q10 과 함께) |

---

## 9. 정해 주거나 제공해야 할 것

| # | 질문 | 권장 / 기본값 | 왜 필요한가 |
|---|------|--------------|------------|
| **Q1** | 우선 언어 순서 | 영어 → 한국어 → 일본어 | M1 · M4 순서 |
| **Q2** | MFA 설치를 `setup_env.bat` 에 넣을까, 별도 `setup_mfa.bat` 으로 둘까 | 별도 bat (선택 기능이므로) | conda 가 없는 PC 에 Miniforge 를 까는 일이 된다 |
| **Q3** | 테스트용 **한국어 · 일본어 녹음 + 대본** | 5 ~ 10초 각 1개 이상 | 내가 만들 수 없는 데이터 — M4 의 전제 |
| **Q4** | 일본어 대본 표기 — 한자 혼용 그대로? 가나 전용? | 둘 다 받되 가나 권장 | 읽기 오류 리스크 |
| **Q5** | 기본 모드 | 대본이 있으면 `Correct`, 없으면 `Audio only` (M5 결과에 따라 `Hybrid` 로) | UI 기본값 |
| **Q6** | 안 C(눈썹 · 눈 · 머리)까지 갈까 | M5 이후 별도 판단 | 범위 |

> 답이 없으면 **권장 / 기본값**으로 진행한다. Q3 은 제공이 필요하다.

---

## 참고

- McAuliffe et al., *Montreal Forced Aligner and the state of speech-to-text alignment in 2026* — [arXiv 2606.18466](https://arxiv.org/pdf/2606.18466)
- MFA 문서 — [Example: Aligning a demo corpus](https://montreal-forced-aligner.readthedocs.io/en/latest/first_steps/alignment_example.html) (일본어 Sudachi 의존성 포함)
- Edwards et al., *JALI: An Animator-Centric Viseme Model for Expressive Lip Synchronization*, SIGGRAPH 2016
- Zhou et al., *VisemeNet: Audio-Driven Animator-Centric Speech Animation*, SIGGRAPH 2018
