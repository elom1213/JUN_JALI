# 예시 음성으로 JALI 립싱크 만들기 — 사용 안내 (Maya)

> **작성** 2026-10-19 · 이 PC 에서 아래 순서를 그대로 실행해 확인했다(§6).
> 진단 · 배경은 [0010_visemenet_feasibility.md](0010_visemenet_feasibility.md).

전체 흐름은 두 단계다. **모델은 Maya 밖(일반 Python)에서 돌리고, Maya 는 결과 txt 를 키로 건다.**

```
test_audio/visemenet_intro.wav
   │  ① 추론 (JUN_JALI/.venv 의 Python + TensorFlow)
   ▼
out/visemenet_intro.txt          ← 10ms 마다 한 줄, 22개 값
   │  ② Maya 에서 examples/maya_apply_visemenet.py
   ▼
angela_JALI.ma 의 CNT_JaLi · CNT_PHONEMES · CNT_COARTIC 에 키 + 타임슬라이더에 음성
```

| 경로 | 무엇 |
|------|------|
| `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI` | 이 저장소 (아래 `<JUN_JALI>`) |
| `<JUN_JALI>\test_audio\` | 예시 음성 2개 — `visemenet_intro.wav`(14.9초), `coffee_xxxx.wav`(4.0초). 둘 다 44.1kHz · 16bit · 스테레오, 영어 |
| `<JUN_JALI>\out\` | 결과 폴더 (git 에 안 올라간다) |
| `C:\Users\USER\Desktop\JP\0001_PJ_portfolio\0040_JULI\scenes\angela_JALI.ma` | JALI 리그 아바타 |

---

## 0. 가장 빨리 보기 — 이미 만들어 둔 결과 씬

이 PC 에서 아래 과정을 한 번 돌려 둔 결과가 `out\` 에 있다. **Maya 2024 에서 열고 재생만 하면 된다.**

- `<JUN_JALI>\out\angela_JALI_visemenet_intro.ma` (프레임 1 ~ 349)
- `<JUN_JALI>\out\angela_JALI_coffee_xxxx.ma` (프레임 1 ~ 88)

음성(`visemenet_audio` 노드)은 씬에 들어 있지만 **타임슬라이더에는 직접 붙여야 소리가 난다** —
타임슬라이더 우클릭 → `Audio` → `visemenet_audio`. 재생 속도는 `Playback speed = Real-time (24 fps)` 로 둘 것
(`Play every frame` 이면 소리와 입이 어긋난다).

> `out\` 은 git 에 올리지 않으므로 다른 PC 에는 없다. 그때는 §1 부터 하면 된다.

---

## 1. 한 번만 — 추론 환경 만들기

PowerShell 에서:

```powershell
cd C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

`requirements.txt` 는 이 PC 에서 확인한 조합이다: Python 3.11.9 · `tensorflow-cpu` 2.15.1 · numpy 1.26.4 · scipy 1.17.1 ·
`python_speech_features`. GPU 는 필요 없다. `.venv\` 도 git 에 안 올라간다.

---

## 2. 추론 — wav → txt

```powershell
cd C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI
mkdir out -Force
.venv\Scripts\python -c "import numpy as np; from inference import VisemeRegressor; r = VisemeRegressor(pb_filepath='./visemenet_frozen.pb'); np.savetxt('./out/visemenet_intro.txt', r.predict_outputs(wav_file_path='./test_audio/visemenet_intro.wav'), '%.4f')"
```

- 처음에 TensorFlow 경고(`oneDNN`, `deprecated`)와 텐서 이름 4줄(`input/Placeholder_1` …)이 찍힌다 — 정상이다.
- `WavFileWarning` 이나 `Warning, truncation` 도 정상이다(44.1kHz 에서 원래 나는 경고, 학습 때도 같았다).
- 14.9초 음성이 이 PC 에서 약 4초 걸렸다.

### 결과 txt 읽는 법

한 줄 = 10ms(100fps), 공백으로 나뉜 22개 값(대략 0~1). 헤더는 없다. 열 순서:

| 열 | 0 | 1 | 2~21 |
|----|---|---|------|
| 이름 | **Jaw** | **Lip** | Ah Aa Eh Ee Ih Oh Uh U Eu Schwa R S ShChZh Th JY LNTD GK MBP FV W |
| 뜻 | JALI 턱 비중 | JALI 입술 비중 | 비짐 강도 (안 쓰는 동안 0) |

`visemenet_intro.wav` 는 1,452줄 = 14.52초가 나온다.

---

## 3. Maya — 리그에 키 걸기

1. Maya 2024 에서 `angela_JALI.ma` 를 연다.
   `Errors have occurred while reading this scene` 경고가 뜨면 **무시해도 된다** — 2015 년 파일의 mental ray 노드 때문이고 리그는 정상 동작한다.
   원본을 덮어쓰지 않도록 바로 **다른 이름으로 저장**해 두는 것을 권한다.
2. `Windows > General Editors > Script Editor` → **Python** 탭에 붙여 넣고 실행:

```python
import sys
JALI = r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI"
if JALI + r"\examples" not in sys.path:
    sys.path.append(JALI + r"\examples")

import maya_apply_visemenet as mav
mav.apply(JALI + r"\out\visemenet_intro.txt",
          wav=JALI + r"\test_audio\visemenet_intro.wav")
```

3. 스크립트 에디터에 이렇게 찍히면 끝이다:
   `[JUN_JALI] 1452 lines @100fps -> frames 1-349 @24.0fps, 23 attributes keyed`
4. 재생(`Alt+V`). 타임슬라이더에 파형이 보이고 소리와 함께 입이 움직인다.
   재생 속도는 §0 처럼 `Real-time` 으로.

### 무엇이 바뀌었나

| 컨트롤 | 키가 걸린 채널 |
|--------|---------------|
| `CNT_JaLi` | `translateX`(Jaw) · `translateY`(Lip) — 0~10 |
| `CNT_PHONEMES` | `AAA Eh AHH OHH UUU IEE RRR WWW SSS FFF TTH MBP SSH Schwa GK LNTD` — 0~10 |
| `CNT_COARTIC` | `LNTD GK MMM FFF WA_PEDAL` — 0~10 |

- 프레임마다 키(24fps 면 1초에 24개)가 들어간다. 그래프 에디터에서 위 컨트롤을 선택하면 커브로 보인다.
- 타임라인 범위가 결과 길이(1 ~ 349)로 바뀌고, `visemenet_audio` 사운드 노드가 1프레임에 놓인다.
- **전체가 Undo 한 번**이다(`Ctrl+Z`).
- **다시 실행하면** 그 구간의 이전 키를 지우고 새로 건다 — 같은 씬에서 다른 txt 로 바꿔 걸어도 섞이지 않는다.

### `apply()` 옵션

| 인자 | 기본 | 뜻 |
|------|------|-----|
| `txt_path` | — | §2 의 결과 txt |
| `wav` | `None` | 주면 사운드 노드를 만들어 타임슬라이더에 붙인다 |
| `start` | `1` | 첫 프레임. 대사를 프레임 100 부터 두려면 `start=100` |
| `namespace` | `""` | 리그를 **레퍼런스로** 불러왔으면 `"angela:"` 처럼 콜론까지 |

다른 음성이면 txt · wav 경로만 바꾼다 — 예: `coffee_xxxx` → 프레임 1 ~ 88.

---

## 4. 결과 다듬기 — JALI 로 말투 바꾸기

모델이 `CNT_JaLi` 에도 키를 건다. 그래서 **박스 안 컨트롤을 손으로 옮겨도 다음 프레임에서 키 값으로 돌아간다.**
말투를 바꾸려면:

- **전체를 더 크게 / 작게** — 그래프 에디터에서 `CNT_JaLi.translateX`(턱) 또는 `translateY`(입술) 커브를 모두 선택하고
  값 방향으로 스케일. 턱을 키우면 크게 벌리는 말투, 입술을 키우면 또박또박한 말투가 된다(진단 문서 §3.2 실측).
- **JALI 를 고정값으로** — `CNT_JaLi` 의 두 채널 키를 지우고 원하는 위치에 둔다(리그 기본값 9, 9). 비짐 타이밍은 그대로 두고 말투만 일정하게.
- **비짐 전체 세기** — `examples/maya_apply_visemenet.py` 의 `SCALE`(기본 10, 리그 최대 12)을 바꾼 뒤 다시 실행.

> 원본 매핑을 그대로 따랐기 때문에 `CNT_PHONEMES.WWW` 는 모델의 `U` 열을 쓰고(`W` 열은 `CNT_COARTIC.WA_PEDAL` 로),
> `CNT_COARTIC.YA_PEDAL` 과 `Eu` · `JY` 열은 쓰지 않는다. 바꾸려면 스크립트의 `MAPPING` 표를 고친다.

---

## 5. 내 음성(다른 언어)으로 해 보기

**입력 규격이 맞아야 한다 — 44.1kHz · 16bit 정수 PCM WAV.** 모델은 리샘플을 안 한다.
48kHz 나 32bit float 녹음을 그대로 넣으면 **에러 없이 틀린 결과**가 나온다. 스테레오는 왼쪽 채널만 쓴다.

- 변환: Audacity → 프로젝트 레이트 `44100` → `Export Audio` → `WAV (Microsoft) signed 16-bit PCM`.
  (ffmpeg 가 있다면 `ffmpeg -i in.wav -ar 44100 -ac 1 -sample_fmt s16 out.wav` — 이 PC 에는 ffmpeg 가 없어 확인하지 않았다)
- 그 다음은 §2 의 wav · txt 이름만 바꿔서 같다. 대본은 필요 없다.
- 같은 대사의 한국어 · 일본어 · 영어 파일을 각각 돌려 **씬을 언어별로 저장**해 두면 나란히 비교하기 좋다.
  한국어 ㅓ · ㅡ, 일본어 う 처럼 영어에 없는 모음이 어떻게 나오는지가 관찰 포인트다(진단 문서 §5).

---

## 6. 문제 해결

| 증상 | 원인 · 해결 |
|------|-------------|
| `Missing rig attributes (wrong scene or namespace?)` | angela_JALI 가 아닌 씬이거나 레퍼런스 네임스페이스 — `namespace="angela:"` |
| `Expected 22 columns per line` | txt 가 추론 결과가 아님 |
| 소리가 안 남 / 입이 늦거나 빠름 | 타임슬라이더 `Audio` 에 `visemenet_audio` 지정, `Playback speed = Real-time` |
| 입이 거의 안 움직이거나 엉뚱함 | wav 규격 확인(§5). 48kHz · float 가 가장 흔한 원인 |
| `ModuleNotFoundError: tensorflow` | `.venv\Scripts\python` 으로 실행했는지 확인(§1) |
| 씬을 열 때 읽기 오류 경고 | mental ray 노드 — 무시 |

---

## 7. 확인 기록 (2026-10-19, 이 PC)

| 단계 | 결과 |
|------|------|
| §1 환경 | Python 3.11.9 venv, `tensorflow-cpu` 2.15.1 — `visemenet_frozen.pb` 가 TF2 에서 **원본 코드 수정 없이** 로드됨 |
| §2 추론 | `visemenet_intro` (1452, 22) 3.7초 · `coffee_xxxx` (364, 22) 1.6초. 원본 저자의 참조 출력과 비교 — Jaw/Lip 평균 차이 0.005, 비짐 활성 구간 대부분 겹침(예: MBP 490 / 458 프레임 중 435 겹침) |
| §3 Maya | mayapy 2024 로 angela_JALI.ma 에 적용 — 23개 어트리뷰트 349키, 재생 중 턱 회전 1.9° ~ 6.6°, 재실행 시 키 수 그대로(섞이지 않음), 사운드 노드 1프레임 |
| 미확인 | **Maya GUI 에서 소리와 함께 재생해 눈으로 본 것은 아직 아니다**(타임슬라이더 연결은 GUI 전용 코드) |
