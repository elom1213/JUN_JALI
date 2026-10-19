# 설치 · VisemeNet Converter 사용 안내

> **작성** 2026-10-19 · 대상: `setup_env.bat` · `Run_VisemeNet_Converter.bat` · `tools/VisemeNet_Converter` v01.00
> · 마야 쪽은 `Maya_Python/JUN_All/docs/A00540_JaliLipSync.md` · 계획 [0030](0030_tool_plan.md)

```
① setup_env.bat (한 번)  →  ② Run_VisemeNet_Converter.bat  →  wav 목록 · 출력 폴더 · Convert
                                                              ↓
                                       <이름>.txt + <이름>.visemenet.json
                                                              ↓
                              ③ Maya: JALI LipSync 셸프 버튼 (A00540) → 리그에 키
```

---

## 1. 설치 — `setup_env.bat` 더블클릭

Windows 10 · 11 공용. 관리자 권한 불필요. 인터넷이 필요하다(패키지 약 1.6 GB).
모델 런타임 **TensorFlow 2.15 는 64bit Python 3.9 ~ 3.11 에서만 돈다** — PC 에 Python 3.12 ~ 3.14 만 있으면
setup 이 **이 폴더 전용 Python 3.11** 을 받아 쓴다(2026-10-20, 아래).

| 단계 | 화면 | 하는 일 |
|------|------|--------|
| 1/5 | `found: py -3.11 (Python 3.11)` | 64bit Python 3.9~3.11 을 찾는다: `py -3.11` · `-3.10` · `-3.9` → PATH 의 `python` → 이 폴더의 `.python\`. **후보를 실제로 실행해 출력한 버전으로 판단한다**(종료 코드는 믿지 않는다) |
| (없을 때) | `Found Python 3.14 (not supported).` + `Download the private Python 3.11 now [Y,N]?` | Y = python.org 의 Python 3.11.9 NuGet 패키지(약 17 MB)를 받아 **SHA-256 을 확인**하고 `.python\` 에 푼다 |
| 2/5 | `created .venv` / `reusing the existing .venv` | 저장소 안 `.venv` 를 만들거나 재사용. 만든 뒤 **실제로 생겼는지 확인**하고, 깨진 `.venv` 는 다시 만든다 |
| 3/5 | `packages OK` | `requirements.txt` 설치 (TensorFlow CPU 2.15.1 · PySide6 · scipy …) |
| 4/5 | `[OK] model coffee_xxxx.wav -> (364, 22)` | 모델을 불러와 예시 음성을 실제로 변환해 본다 |

`SETUP OK` 가 나오면 끝. 자세한 출력은 `setup_env.log`.

- **다시 실행해도 안전하다** — 이미 있으면 재사용(이 PC 에서 8~25초). `.venv` 를 새로 만들려면 명령창에서 `setup_env.bat --force`.
  `--yes` = 전용 Python 을 묻지 않고 받는다, `--nopause` = 끝에 멈추지 않는다(스크립트용).

### Python 3.14 만 있는 PC (Windows 10 보고, 2026-10-20)

예전 setup 은 이렇게 실패했다:

```
[ERROR] No runtime installed that matches 3.11. Try running "py install 3.11".
      found: py -3.11  (Python )          <- 3.11 이 없는데 찾았다고 판단
      created .venv                        <- 만들지 못했는데 넘어감
The system cannot find the path specified.
```

**원인** — 새 Python 설치 관리자(Python 3.14 와 함께 오는 `py`)는 3.11 이 없을 때 `py -3.11 ...` 이 오류를 출력하고도 **성공 코드(0)** 로
끝났다(보고 로그 기준). 예전 setup 은 종료 코드만 봤다. 지금은 후보마다 `import sys; print('JUNPY', 버전, 64bit)` 를 실행해 **출력을 읽고**,
venv 는 `python.exe` 가 실제로 생겼는지 본다.

**전용 Python (`.python\`)**
- python.org 가 배포하는 **설치 프로그램 없는 Python 3.11.9**(NuGet 패키지)를 이 폴더에만 푼다. 시스템에 설치하지 않고(레지스트리 · PATH ·
  `py` 런처 변경 없음) 기존 Python 3.14 도 그대로다. 지우려면 `.python\` · `.venv\` 폴더만 지우면 된다.
- 받은 파일은 SHA-256 `9283876d…3c67` 과 맞아야 푼다(다르면 중단). 다운로드 · 해시 · 압축 풀기는 PowerShell 모듈 없이 .NET 만 쓴다
  (Windows 10 기본 PowerShell 5.1 에서 `Get-FileHash` 등이 안 보이는 환경이 있었다).
- 패키지의 `Lib\site-packages\`(미리 든 pip · setuptools)는 풀지 않는다 — 경로가 가장 깊어 긴 폴더에서 260자 제한에 걸리고,
  venv 는 `Lib\ensurepip` 로 pip 를 따로 설치한다.
- **폴더를 옮기면** `.venv` 가 옛 경로를 가리켜 깨진다 → `Run_VisemeNet_Converter.bat` 가 실행 전에 확인하고
  `Double-click setup_env.bat again` 을 띄운다. 그때 `setup_env.bat --force`.

| 실패 메시지 | 해결 |
|------------|------|
| `Python 3.9 - 3.11 (64-bit) is required.` | 다시 실행해 `Y`(전용 Python 받기), 또는 Python 3.11 64bit 설치 |
| `Download / extract failed` | 인터넷 · 회사 프록시 확인, 또는 폴더 경로가 너무 길다 → `C:\JUN_JALI` 처럼 짧은 곳으로 |
| `Hint: this Python version is not supported` | (예전 판) 3.12 이상으로 venv 를 만든 경우 — 지금 판으로 `--force` |
| `DLL load failed ...` + VC++ 링크 | Microsoft Visual C++ 재배포 패키지(x64) 설치 (TensorFlow 가 쓴다) |
| `Hint: Windows 260-character path limit` | 저장소를 `C:\JUN_JALI` 처럼 짧은 경로로 옮기기 |
| `Hint: network / proxy problem` | 인터넷 · 회사 프록시 확인 |

---

## 2. 변환 — `Run_VisemeNet_Converter.bat` 더블클릭

콘솔 없이 창만 뜬다. 첫 `Convert` 때 모델을 불러오느라 몇 초 걸린다.

1. **WAV 넣기** — `Add Files...` / `Add Folder...`, 또는 탐색기에서 **창으로 끌어다 놓기**. 같은 파일은 한 번만 들어간다.
   목록에서 하나를 누르면 로그에 규격이 나온다(`44100 Hz · int16 · 2 ch · 3.99 s`). `Up` / `Down` / `Del` / `Sort` / `Clear`.
2. **출력 폴더** — `Browse...`. **비우면 각 WAV 옆에** 쓴다. `Open` 은 탐색기로 연다.
3. 옵션
   - `Write .visemenet.json info file` (기본 켬) — 마야 툴이 WAV 를 자동으로 찾는 데 쓴다
   - `Overwrite existing` (기본 끔) — 끄면 이미 있는 결과 때문에 멈춘다(E09)
   - `Max length (sec)` (기본 120) — 파일 하나를 통째로 처리하므로 아주 긴 파일은 나눌 것
   - `Inference` — **`Deterministic (recommended)`** / `Original - random dropout` (§4)
4. **`Check Files`** — 변환 없이 검사만. **`Convert`** — 검사 → 변환. `Stop` 은 지금 파일이 끝나면 멈춘다.

설정 · 목록은 창을 닫을 때 저장되어 다음에 그대로 열린다(`tools/VisemeNet_Converter/data/settings.json`).

### 결과 파일

| 파일 | 내용 |
|------|------|
| `<이름>.txt` | 한 줄 = 10ms, 22개 값 (`Jaw Lip` + 비짐 20). 원본 README 와 같은 형식 |
| `<이름>.visemenet.json` | 원본 WAV 경로 · 길이 · 열 이름 · fps · 줄 수 · 추론 모드 |

---

## 3. 멈추는 경우 — 로그 읽는 법

**시작 전에 목록 전체를 검사하고, 하나라도 걸리면 아무것도 변환하지 않는다.** 변환 중 오류가 나도 그 자리에서 멈춘다
(이미 끝난 파일은 남는다 — 로그 마지막 줄에 몇 개인지 나온다).

| 코드 | 로그 | 할 일 |
|------|------|------|
| E01 | `file not found` | 파일이 옮겨졌거나 지워졌다 |
| E02 | `cannot read as PCM WAV (...)` | mp3 를 이름만 바꾼 파일 · 압축 WAV · 깨진 파일 → PCM WAV 로 다시 내보내기 |
| **E03** | `sample rate 48000 Hz - VisemeNet needs 44100 Hz` | **44.1kHz 로 다시 내보내기** (Audacity: Project Rate 44100) |
| **E04** | `sample format 32-bit float - need 16-bit integer PCM` | **16-bit PCM** 으로 다시 내보내기 |
| E05 | `3 channels - need mono or stereo` | 모노 · 스테레오로 |
| E06 / E07 | `too short` / `too long` | 0.5초 이상 · Max length 이하로 |
| E08 | `silent audio` | 소리가 없는 파일 |
| E09 | `output exists` | `Overwrite existing` 켜기 또는 다른 출력 폴더 |
| E10 | `cannot write to ...` | 출력 폴더 권한 |
| E11 | `two files would write the same output` | 다른 폴더의 같은 이름 WAV — 이름을 바꾸거나 따로 변환 |
| E20 | `model file missing` | 저장소가 불완전 — 다시 받기 |
| E21 ~ E24 | `inference failed` · `NaN` · `unexpected output` · `cannot write` | 로그의 `detail` 줄을 확인 |

**경고(멈추지 않음)**: `W01 stereo - only the left channel is used`(모델은 왼쪽 채널만 쓴다) · `W02 clipping detected`.
`'frame will be truncated' ... is normal at 44.1 kHz` 는 정상 안내다(모델이 그렇게 학습됐다).

---

## 4. 알아 둘 것 — 원본 모델의 두 가지 성질 (실측)

### 4.1 원본은 돌릴 때마다 결과가 다르다 → 기본은 결정적 모드

원본 `model.py` 는 `net2` LSTM 7개에 `DropoutWrapper(output_keep_prob=0.5)` 를 **상수로** 넣었다
(입력으로 받는 dropout 값은 `net1` 에만 걸린다). 그래서 **추론 때도 dropout 이 돌아** 같은 WAV 도 매번 결과가 다르다
(같은 파일 두 번 — 최대 차 0.64). 원본 저자의 참조 출력도 그런 무작위 결과 하나다.

변환기는 기본으로 **그 상수를 1.0 으로 바꿔 불러온다**(`inference.py` 는 손대지 않고, 불러온 그래프만).
inverted dropout 이라 이것이 곧 dropout 의 기댓값 추론이다.

| 비교 (`visemenet_intro.wav`) | 결과 |
|------------------------------|------|
| 결정적 모드 두 번 | **완전히 같다** |
| 무작위 실행끼리 | 평균 차 0.010 |
| 결정적 vs 무작위 20번 평균 | 평균 차 0.014 · 비짐이 켜지는 구간 패턴은 거의 같다 |
| Jaw / Lip 평균 | 결정적 0.29 / 0.30 · 무작위 0.32 / 0.38 — 결정적 쪽이 조금 작다 |

원본과 똑같이 하고 싶으면 `Inference = Original - random dropout`. json 의 `inference_mode` 에 남는다.

### 4.2 출력은 음성 끝 0.32초가 빠진다 (시작은 맞다)

`net2` 가 앞에 0 을 32줄 채운 뒤 64줄 창으로 훑기 때문에 **줄 수가 32 줄어든다** — 줄 i 는 여전히 음성 i × 10ms 다.

| 음성 | 길이 | 출력 |
|------|------|------|
| `coffee_xxxx.wav` | 3.99 s | 364줄 = 3.64 s |
| `visemenet_intro.wav` | 14.86 s | 1452줄 = 14.52 s |

→ 마야에서 **소리와 입은 처음부터 맞고**, 마지막 0.32초는 마지막 키 값이 유지된다(대개 말끝의 무음 구간).
줄 수 공식은 `converter.expected_rows()` — 다르면 E23 으로 멈춘다.

---

## 5. 개발자용

| 파일 | 역할 |
|------|------|
| `tools/VisemeNet_Converter/launch.py` | 진입점. `sys.path` = 저장소 루트 + `vendor/`. 시작 오류는 메시지 창 + `data/startup_error.log` |
| `app/core/wav_check.py` | `check_wav()` — E01~E08, W01~W02 |
| `app/core/converter.py` | `Engine`(모델 1회 로드, 결정적 모드), `preflight()`(E09~E11), `run_batch()`(E20~E24, Stop), `expected_rows()` |
| `app/core/output_writer.py` | txt(np.savetxt) · json, 임시 파일 → 이름 바꾸기 |
| `app/ui/main_window.py` | 창 + `ConvertWorker`(QThread) |
| `tools/selftest.py` | 설치 마지막 검사 |
| `tools/sync_framework.py` | `vendor/Framework` 를 `Maya_Python/JUN_All/Framework` 에서 다시 복사 (출처 커밋 `vendor/FRAMEWORK_SOURCE.txt`) |

**시험** (`.venv\Scripts\python` 으로):

```
tools\VisemeNet_Converter\tests\make_bad_wavs.py <작업폴더>   검사 규칙 13개 (나쁜 wav 를 만들어 코드 확인)
tools\VisemeNet_Converter\tests\test_core.py     <작업폴더>   일괄 변환 17개 (사전검사 중단 · 결정성 · Stop · E09/E11/E20/E21)
tools\VisemeNet_Converter\tests\test_ui.py       <작업폴더>   오프스크린 UI 12개 (실제 Convert 경로 · 한글 경로 · 설정 복원)
```

**확인 기록 (2026-10-20, Python 3.14 대응)**: 저장소 사본을 짧은 경로에 두고, 가짜 `py`(3.9~3.11 = 보고와 같은 오류 출력 + 종료 코드 0, 기본 = 3.14)와
가짜 `python`(3.14)만 PATH 에 둔 채 `setup_env.bat --yes` → 3.14 감지 · 전용 Python 받기(SHA-256) · venv · 패키지 · 자가 검사 `SETUP OK`(87초, pip 캐시 있음),
`.python\` 를 지우고 다시 → 다시 받아 `SETUP OK`, 재실행은 재사용. 그 `.venv` 로 변환기 검사 · UI 시험 통과. 이 PC 의 실제 3.11 로도 `SETUP OK`.
실제 Windows 10 + Python 3.14 PC 에서의 확인은 사용자 몫.

**확인 기록 (2026-10-19, Windows 11)**: 위 시험 전부 통과 · `.venv` 없는 상태에서 `setup_env.bat` → `SETUP OK` 84초(pip 캐시 있음) ·
재실행 8초 · PATH 에 파이썬이 없을 때 안내 후 종료 · `Run_VisemeNet_Converter.bat` → 시작 오류 없이 이벤트 루프 진입.
**미확인**: 실제 화면에 뜬 창(내 셸에서는 보이지 않는 세션), winget 자동 설치, Windows 10.
