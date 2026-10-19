# VisemeNet 으로 다국어 음성 → JALI 립싱크 — 진단 · 조건 · 수정 계획

> **작성** 2026-10-19 · **갱신** 2026-10-19 (포크 후 추론 실측 — §1 · §6 · §8) · 대상 저장소 [`junhwanjang/visemenet-inference`](https://github.com/junhwanjang/visemenet-inference) (HEAD `c20ec78`)
> · 원본 [`yzhou359/VisemeNet_tensorflow`](https://github.com/yzhou359/VisemeNet_tensorflow)
> · 아바타 `C:\Users\USER\Desktop\JP\0001_PJ_portfolio\0040_JULI\scenes\angela_JALI.ma`
> · 배경 공부 문서 `JUN_Study/Graphics/004500_viseme_lipsync_and_reusable_facial_units.md`

**목표**: 같은 의미 · 다른 언어로 녹음한 음성 파일 여러 개를 Maya(→ 이후 Unreal)로 불러와, **각 음성에 맞는 립싱크**를
JALI 리그에 자동으로 만든다.

---

## 1. 결론

**조건부로 가능하다.** 세 부분으로 나눠 보면 상태가 다르다.

| 부분 | 상태 | 근거 |
|------|------|------|
| **리그 연결** (모델 출력 → angela 리그 키) | ✅ **그대로 맞는다 — 실측** | 원본 Maya 스크립트가 쓰는 어트리뷰트 이름 23개가 angela_JALI.ma 에 **전부 있다**. 참조 출력을 걸어 턱 · 블렌드셰이프가 움직이는 것까지 확인 (§3) |
| **추론** (wav → 22개 커브) | ✅ **이 PC 에서 동작 — 실측** | Python 3.11 + `tensorflow-cpu` 2.15.1 에서 원본 코드 수정 없이 돌았고, 원본 저자의 참조 출력과 거의 같다. 사용법은 [0020](0020_usage_example_maya.md). 알려진 버그는 남아 있다 (§4) |
| **다국어 품질** | ❓ **미검증 — 가장 큰 리스크** | 대본 없이 **오디오만** 쓰므로 어느 언어든 *돌아는 간다*. 하지만 학습 데이터는 영어(GRID · SAVEE · BIWI)다 (§5) |

즉 **예시 음성 → 리그 키까지는 이미 돌아간다**(0020 문서). 남은 것은 다국어 품질이고, **"한국어 · 일본어에서 좋아 보이는가" 는 실험으로 확인해야 한다.**

> 이유 한 줄 — VisemeNet 은 **JALI 논문 저자 그룹과 함께 이 리그(JALI 공개 리그)를 대상으로 학습한 모델**이다.
> 그래서 출력 이름이 리그와 1:1 로 맞는다. 다른 리그였다면 매핑부터 만들어야 했다.

---

## 2. VisemeNet 이 하는 일

```
wav (44.1kHz · 16bit)
  │  python_speech_features : MFCC 13 + logfbank 26 + SSC 26 = 65차원, 100Hz (10ms 간격)
  │  saved_params/wav_mean_std.csv 로 정규화, 24프레임 윈도우
  ▼
visemenet_frozen.pb  (TF1.1 그래프를 freeze — LSTM 3갈래: JALI / 비짐 on-off / 비짐 강도)
  ▼
postprocess.py : medfilt · hanning smooth · 임계값 게이트 · 피크 보정
  ▼
(N, 22) 배열 = 10ms 마다 한 줄   ← 헤더 없는 공백 구분 txt
  열 0~1  : Jaw, Lip            (JALI 2축)
  열 2~21 : Ah Aa Eh Ee Ih Oh Uh U Eu Schwa R S ShChZh Th JY LNTD GK MBP FV W
```

- **대본(transcript) 불필요** — 오디오만 넣는다. 논문: *"trained to recognize these phoneme groups from audio without any text or phonetic transcript."*
- 출력은 **100fps** 다. 원본 Maya 스크립트는 4줄마다 하나씩 써서 **25fps 로 가정**한다(씬 fps 를 읽지 않는다).
- 값은 대략 0~1, 클립하지 않는다(JALI 2축은 회귀값이라 음수 · 1 초과 가능). 원본 Maya 스크립트가 **0~1 로 자른 뒤 ×10**.
- **visemenet-inference 저장소에는 Maya 스크립트가 없다.** 리그 적용은 원본 저장소의 `maya_animation.py` 에만 있다.

---

## 3. 아바타 진단 — `angela_JALI.ma` (실측, Maya 2024 mayapy)

### 3.1 리그 구조

Maya **2015** 파일이지만 2024 에서 열린다(mental ray 노드 관련 읽기 경고만, 리그 동작에는 영향 없음). 시간 단위 **film = 24fps**.

| 컨트롤 | 역할 | 범위 |
|--------|------|------|
| `CNT_PHONEMES` | 비짐 18개: `AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP SSH Schwa GK LNTD` (+ `Project` `Enunciate`) | 0 ~ 12 |
| `CNT_COARTIC` | 동시조음: `LNTD GK MMM FFF WA_PEDAL YA_PEDAL` | 0 ~ 12 (GK −5 ~ 12) |
| `CNT_JaLi` | **translateX = Jaw, translateY = Lip** (기본 9, 9) | 0 ~ 15 |
| `CNT_UPFACE` `CNT_MIDFACE` `CNT_LOFACE` | 눈썹 · 눈 · 미소 · 찡그림 등 FACS 근육 (립싱크 아님) | −2 ~ 15 |

구동 체인: `CNT_PHONEMES.<비짐>` → `MULT_LIP_* / MULT_JAW_* / MULT_TNG_*`(`CNT_JaLi` 값으로 스케일) → set-driven-key 커브
→ 블렌드셰이프 **`faceMuscles`(타깃 36개)** + `Jaw` 조인트 + 혀. (리그 README `README_JALI_Rig.docx` 와 일치)

### 3.2 컨트롤이 실제로 얼굴을 움직이는가

| 입력 | 턱 회전 변화 | 블렌드셰이프 변화 |
|------|-------------|------------------|
| `AAA = 12` | 10.7° | 2.62 |
| └ `CNT_JaLi.tx` 2 → 14 (Jaw) | 2.4° → **16.7°** | — |
| └ `CNT_JaLi.ty` 2 → 14 (Lip) | — | 0.81 → **3.92** |
| `MBP = 12` | 6.9° | 1.72 |
| `UUU = 12` | 1.0° | 1.65 → (Lip 14) 2.40 |

→ JALI 2축이 **설계대로 턱 / 입술 비중을 따로 바꾼다.**

### 3.3 모델 출력을 리그에 걸어 보기

원본 저장소에 들어 있는 **참조 출력** `data/output_viseme/visemenet_intro/mayaparam_viseme.txt`
(VisemeNet 이 실제로 낸 1,452줄 = 14.5초)를 원본 스크립트와 **같은 매핑**으로 24fps 에 맞춰 키를 걸었다.

- **빠진 어트리뷰트 0개** — 23개 전부 키가 걸림
- 재생 중 턱 회전 1.9° ~ 6.8°, 블렌드셰이프 합 0.17 ~ 2.30 으로 **말하는 동안 움직인다**
- 이 클립에서 한 번도 켜지지 않은 열: `Ih`, `Eu`, `JY`, `LNTD`, `GK`

### 3.4 원본 매핑 (모델 열 → 리그 어트리뷰트)

| 리그 어트리뷰트 | 모델 열 | 비고 |
|----------------|---------|------|
| `CNT_JaLi.translateX` / `translateY` | Jaw / Lip | ×10 → 0~10 (리그 범위 0~15) |
| `CNT_PHONEMES.AAA` · `Eh` · `AHH` | Aa · Eh · Ah | |
| `CNT_PHONEMES.OHH` | **max(Oh, Uh)** | 다대일 |
| `CNT_PHONEMES.IEE` | **max(Ee, Ih)** | 다대일 |
| `CNT_PHONEMES.UUU` | U | |
| `CNT_PHONEMES.WWW` | **U** | ⚠️ `W` 열이 아니라 `U` 열 — 의도인지 실수인지 불명 |
| `CNT_PHONEMES.RRR` `SSS` `FFF` `TTH` `MBP` `SSH` `Schwa` `GK` `LNTD` | R S FV Th MBP ShChZh Schwa GK LNTD | |
| `CNT_COARTIC.LNTD` `GK` `MMM` `FFF` `WA_PEDAL` | LNTD GK MBP FV W | 같은 열을 PHONEMES 와 **이중으로** 씀 |
| `CNT_COARTIC.YA_PEDAL` | — | ⚠️ 매핑 목록이 23개뿐이라 **키가 안 걸림**(버그) |
| — | `Eu`, `JY` | 쓰이지 않음 |

비짐 값은 0~10 으로 들어가므로 리그 최대치(12)는 쓰지 않는다.

---

## 4. 추론 쪽 — 실행 전에 알아야 할 것

| 항목 | 내용 |
|------|------|
| 환경 | README 요구: TF 2.x · numpy · scipy · `python_speech_features` (버전 고정 없음, requirements.txt 없음). CPU 로 충분. Windows 는 `tensorflow-cpu` 2.10~2.15 + Python 3.10 을 권장(**미검증**) |
| 모델 파일 | `visemenet_frozen.pb`(58MB) 가 저장소에 포함 — 따로 받을 것 없음 |
| **오디오 규격** | **44.1kHz · 16bit 정수 PCM** 이어야 한다. 리샘플을 안 하고, 정규화 값(`wav_mean_std.csv`)이 44.1kHz 기준이다. 스테레오면 첫 채널만 쓴다. float WAV · 48kHz 는 조용히 틀린 결과를 낸다 |
| `Warning, truncation` | 44.1kHz 에서 25ms 창이 `nfft=512` 보다 길어서 나는 경고. **학습 때도 같았으므로 정상**(원본 저자 확인). 16kHz 로 바꾸면 재학습이 필요 |
| 길이 | 전체 파일을 한 번에 넣는다. 긴 파일은 메모리 한계 미검증 → 청크 분할이 필요할 수 있음 |
| **추론이 무작위** | 원본 `model.py` 가 `net2` LSTM 7개에 dropout 0.5 를 **상수로** 넣어 추론 때도 돈다 → 같은 wav 도 매번 결과가 다르다(최대 차 0.64, 2026-10-19 실측). 변환기는 그 상수를 1.0 으로 바꿔 불러오는 결정적 모드가 기본 — [0050](0050_converter_guide.md) §4.1 |
| 출력 길이 | 음성 끝 0.32초가 빠진다(시작은 맞다) — `net2` 의 64줄 창 · 앞쪽 32줄 패딩. [0050](0050_converter_guide.md) §4.2 |
| 버그 | `postprocess.py` 가 `import scipy as sp` 뒤 `sp.signal.medfilt` 호출(SciPy 버전에 따라 `AttributeError`) · `raise(ValueError, ...)` 문법 오류 · 활성 구간 끝 프레임 1개 누락 · 첫 루프 `break` 가 해당 비짐 처리 전체를 조기 종료 · 경로가 현재 폴더 상대경로 |
| 라이선스 | 이 포크는 Apache-2.0 이라 표기하지만 **원본은 GPLv3 또는 상용**(UMass). 가중치는 표기 없음. **포트폴리오 · 학습용은 무리 없지만 상업 프로젝트에 쓰려면 UMass 확인이 필요하다** |

---

## 5. 다국어 — 무엇을 기대할 수 있나

**된다고 할 수 있는 것**
- 오디오만 쓰므로 **한국어 · 일본어 음성을 넣어도 동작은 한다.** 대본 · 언어별 사전 · G2P 가 필요 없다.
- 같은 의미의 다른 언어 음성은 **파일마다 따로** 추론하므로, 각 음성의 타이밍(길이 · 쉼 · 강세)에 맞는 커브가 나온다 — 목표의 "각 음성에 맞도록" 은 구조적으로 충족된다.
- 논문은 *"truly language agnostic"*, *"generalization to ... different languages"* 를 주장한다.

**보장되지 않는 것**
- 인식 대상은 **영어 기준 음소 그룹 20개**다. 영어에 없는 소리는 가장 가까운 그룹으로 투영될 것이다(**미검증 가설**):

| 한국어 | 가까울 것으로 보는 그룹 | 메모 |
|--------|----------------------|------|
| ㅏ | Ah / Aa | |
| ㅓ | Schwa / Uh → `OHH` | 영어에 정확한 짝 없음 — 오인식 후보 1순위 |
| ㅗ · ㅜ | Oh · U | 원순 모음, 잘 맞을 것 |
| ㅡ | Eu? / Ih | **평순 고모음** — 영어에 없다. 입술을 펴야 하는데 `UUU` 로 가면 틀린 입모양 |
| ㅣ · ㅔ · ㅐ | Ee · Eh | |
| ㅁ ㅂ ㅍ | MBP | 잘 맞을 것 (입술 닫힘은 언어 무관) |
| ㄴ ㄷ ㅌ ㄹ / ㄱ ㅋ | LNTD / GK | 혀 비짐 — 입술에 영향 적음(공부 문서 §4.2 규칙 5) |
| ㅅ ㅈ ㅊ | S / ShChZh | |

  일본어는 모음이 5개(あいうえお)라 대응이 더 단순하지만, **う 는 평순**이라 ㅡ 와 같은 문제가 있다.
- 공부 문서 §6.1 의 Cyberpunk 2077 (JALI 상용 제품)은 **언어별 음향 모델 + 발음 사전 + G2P** 를 따로 둔다.
  VisemeNet 은 그 단계 없이 오디오 → 비짐을 한 번에 하는 대신 **언어 적응 수단이 없다.**

**→ 판단은 실험으로.** §7 M5 의 비교 실험이 이 프로젝트의 첫 번째 실질 산출물이다.

---

## 6. 목표 달성에 필요한 조건 (체크리스트)

1. [x] **추론 환경** — `.venv` + `requirements.txt` (Python 3.11.9 · `tensorflow-cpu` 2.15.1). `.pb` 가 TF2 에서 로드됨 — 실측
2. [ ] **오디오 정규화** — 모든 입력을 44.1kHz · 16bit · mono WAV 로 변환(48kHz 녹음이 흔하다)
3. [x] **리그 이름 일치** — angela_JALI 는 그대로 맞는다(실측). 다른 리그면 매핑 표가 필요
4. [x] **fps 맞춤** — `examples/maya_apply_visemenet.py` 가 씬 fps 로 샘플한다(angela = 24). 원본의 "4줄마다" 는 25fps 전용
5. [ ] **다국어 품질 확인** — 같은 문장 EN / KO / JA 녹음으로 비교, 입모양 오류 유형 기록
6. [ ] **Unreal 경로 결정** — angela 는 Maya 전용 리그다. UE 로 가려면 (a) 결과를 블렌드셰이프 가중치 + 턱 조인트로 **구워 FBX** 로, 또는 (b) **MetaHuman 등 UE 리그용 매핑 표**를 따로 만든다
7. [ ] **라이선스** — 용도(포트폴리오 / 상업)에 따라 원본 GPLv3 · 가중치 사용 조건 확인

---

## 7. 내가 수정 · 추가할 수 있는 것 (작업 계획)

포크 위치: `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI` (이 문서는 `docs/` 에 있다).

| 단계 | 내용 | 결과물 |
|------|------|--------|
| **M1 추론 정비** | `requirements.txt` 고정 · `scipy.signal` import 수정 · `__file__` 기준 경로 · §4 버그 수정 · 입력 검증/자동 변환(44.1kHz · int16 · mono) · CLI `python run.py in.wav -o out.json` | 이 PC 에서 wav → 커브가 나온다 |
| **M2 출력 포맷** | 헤더 없는 txt 대신 **열 이름 · fps · 원본 오디오 경로**를 담은 json/csv | 이후 단계가 열 순서를 외우지 않아도 된다 |
| **M3 Maya 적용 툴** | 원본 `maya_animation.py` 를 다시 쓴다: **매핑 json**(열 → 어트리뷰트, max/sum, 스케일, clamp) · 씬 fps 로 리샘플 · 키를 한 번에 생성(현재는 프레임마다 `currentTime` + `setKeyframe`) · 오디오 노드 import + 타임슬라이더 연결 · Undo 한 번 · 누락 어트리뷰트 보고 · `YA_PEDAL` / `WWW`←`W` 선택 옵션. 다른 툴처럼 **드래그&드롭 셸프 설치** | 셸프 버튼 → json 고르면 립싱크 키 |
| **M4 다국어 배치** | 모델을 한 번 로드하고 폴더의 wav 전부 추론 · 언어 태그(`_ko` `_ja` `_en`) 별 출력 · Maya 에선 언어별 **씬 또는 애니메이션 레이어**로 나란히 비교 | 같은 대사 3개 언어를 한 번에 |
| **M5 언어 비교 실험** | 같은 문장 EN/KO/JA → 비짐 활성 타임라인을 그래프로 비교, ㅓ · ㅡ · う 같은 오류 후보 관찰. 결과에 따라 **언어별 보정 훅**(임계값 · 스케일 · 특정 비짐 재매핑) | 품질 판단 근거 |
| **M6 Unreal 내보내기** | (a) 블렌드셰이프 가중치 + Jaw 조인트를 구워 FBX(morph target 커브) 또는 (b) 커브 CSV → UE 에디터 Python 이 AnimSequence 커브 생성. MetaHuman 대상이면 비짐 → MetaHuman 컨트롤 매핑 표 추가 | UE 에서 재생 |
| **M7 (선택) TF 제거** | `.pb` → ONNX(`tf2onnx`) → `onnxruntime` 으로 **mayapy 안에서** 추론 — 외부 Python 없이 Maya 툴 하나로(변환 가능 여부 미검증) | 설치 단순화 |

**품질이 모자랄 때의 대안** (M5 결과에 따라)
- **Forced alignment 혼합** — Montreal Forced Aligner 는 한국어 · 일본어 모델이 있다. 대본이 있으면 음소 **타이밍**은
  정렬기로, **JALI 2축과 강도**는 VisemeNet 으로 → 공부 문서 §4.2 의 동시조음 규칙을 직접 구현.
- 상용 대안: JALI Research 제품, NVIDIA Audio2Face-3D(오픈소스, MetaHuman 매핑 제공) — 공부 문서 §6.

---

## 8. 실측 기록

| 항목 | 방법 | 결과 |
|------|------|------|
| 씬 열기 | Maya 2024 mayapy, `executeScriptNodes=False` | 열림, mental ray 관련 읽기 경고만 |
| 컨트롤 구동 | `CNT_PHONEMES.*` = 12, `CNT_JaLi.tx/ty` 2 ↔ 14 | §3.2 표 |
| 출력 적용 | 원본 참조 출력 1,452줄을 원본 매핑으로 24fps 키 | 23/23 어트리뷰트 키, 재생 시 턱 · 블렌드셰이프 움직임 |
| 추론 | `.venv` 에서 README 예시 그대로 | `visemenet_intro` (1452, 22) 3.7초 — 참조 출력과 Jaw/Lip 평균 차이 0.005 |
| 예시 → 리그 | `examples/maya_apply_visemenet.py` | 23개 어트리뷰트 349키 (24fps), 결과 씬 `out/` |
| 저장소 분석 | 코드 읽기만, 실행 안 함 | §2 · §4 |

> 🔧 **포크 구성 (2026-10-19)** — `origin` = `https://github.com/elom1213/JUN_JALI.git`(푸시 대상, `main`),
> `upstream` = `https://github.com/junhwanjang/visemenet-inference.git`(원본, `c20ec78` 위에 작업). 원본 갱신은 `git fetch upstream` 후 병합.
