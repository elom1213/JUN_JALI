# 설치 · VisemeNet Converter 사용 안내

> **작성** 2026-10-19 · **갱신** 2026-10-22 (v01.02 Windows 10 · Python 3.14 — §1 · §6.1 · §6.7) · 대상: `setup_env.bat` · `Run_VisemeNet_Converter.bat` ·
> `setup_mfa.bat` · `tools/VisemeNet_Converter` v01.01
> · 마야 쪽은 `Maya_Python/JUN_All/docs/A00540_JaliLipSync.md` · 계획 [0030](0030_tool_plan.md) · 대본 보정 계획 [0060](0060_transcript_mfa_plan.md)

```
① setup_env.bat (한 번)  →  ② Run_VisemeNet_Converter.bat  →  wav 목록 · 출력 폴더 · Convert
   (+ setup_mfa.bat — 대본 보정을 쓸 때만, 한 번)                 ↓
                                       <이름>.txt + <이름>.visemenet.json (+ <이름>.phones.json)
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
   - `Transcript (optional)` — `Audio only` (기본) / `Correct with transcript (MFA)` (§6)
4. **`Check Files`** — 변환 없이 검사만. **`Convert`** — 검사 → 변환. `Stop` 은 지금 파일이 끝나면 멈춘다.

설정 · 목록은 창을 닫을 때 저장되어 다음에 그대로 열린다(`tools/VisemeNet_Converter/data/settings.json`).

### 결과 파일

| 파일 | 내용 |
|------|------|
| `<이름>.txt` | 한 줄 = 10ms, 22개 값 (`Jaw Lip` + 비짐 20). 원본 README 와 같은 형식 |
| `<이름>.visemenet.json` | 원본 WAV 경로 · 길이 · 열 이름 · fps · 줄 수 · 추론 모드 (Correct 모드면 `correction` 도) |
| `<이름>.phones.json` | Correct 모드에서만 — MFA 단어 · 음소 구간 (§6.4) |

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
| **E34** | `output would overwrite the transcript` | 출력 폴더를 비워 둬서 결과 `<이름>.txt` 가 **같은 이름의 대본**을 덮게 됐다 → 출력 폴더를 정하거나 대본을 `.lab` 으로 |
| E30 ~ E33 | (Correct 모드) | §6.5 |

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
| `app/core/converter.py` | `Engine`(모델 1회 로드, 결정적 모드), `preflight()`(E09~E11 · E30~E32 · E34), `run_batch()`(E20~E24, Stop, 정렬 · 보정), `expected_rows()` |
| `app/core/aligner.py` | MFA 찾기(`mfa_path.local.txt`) · 대본 찾기 · 한 번에 정렬(`mfa align`, G2P) · TextGrid 읽기 — E30~E33 |
| `app/core/viseme_merge.py` | 안 B 보정(`correct()`) · IPA 매핑(`PhoneMap`) — 순수 numpy |
| `saved_params/ipa_to_jali.json` | MFA 음소(IPA) → JALI 비짐 가중치 |
| `app/core/output_writer.py` | txt(np.savetxt) · json · phones.json, 임시 파일 → 이름 바꾸기 |
| `app/ui/main_window.py` | 창 + `ConvertWorker`(QThread) |
| `tools/selftest.py` | 설치 마지막 검사 |
| `tools/sync_framework.py` | `vendor/Framework` 를 `Maya_Python/JUN_All/Framework` 에서 다시 복사 (출처 커밋 `vendor/FRAMEWORK_SOURCE.txt`) |

**시험** (`.venv\Scripts\python` 으로):

```
tools\VisemeNet_Converter\tests\make_bad_wavs.py <작업폴더>   검사 규칙 13개 (나쁜 wav 를 만들어 코드 확인)
tools\VisemeNet_Converter\tests\test_core.py     <작업폴더>   일괄 변환 17개 (사전검사 중단 · 결정성 · Stop · E09/E11/E20/E21)
tools\VisemeNet_Converter\tests\test_ui.py       <작업폴더>   오프스크린 UI 16개 (실제 Convert 경로 · 한글 경로 · Correct 모드 · 설정 복원)
tools\VisemeNet_Converter\tests\test_merge.py    <작업폴더>   보정 · 매핑 · TextGrid · 대본 찾기 · MFA 실행 환경 격리 41개 (MFA 없이 합성 데이터, 사전 음소 전수 검사)
tools\VisemeNet_Converter\tests\test_align.py    <작업폴더>   Correct 모드 통합 16개 (실제 MFA — setup_mfa.bat 뒤)
```

앞의 셋은 같은 작업 폴더를 순서대로(`make_bad_wavs` 가 만든 파일을 뒤가 쓴다). `test_merge` · `test_align` 은 따로.

**확인 기록 (2026-10-20, Python 3.14 대응)**: 저장소 사본을 짧은 경로에 두고, 가짜 `py`(3.9~3.11 = 보고와 같은 오류 출력 + 종료 코드 0, 기본 = 3.14)와
가짜 `python`(3.14)만 PATH 에 둔 채 `setup_env.bat --yes` → 3.14 감지 · 전용 Python 받기(SHA-256) · venv · 패키지 · 자가 검사 `SETUP OK`(87초, pip 캐시 있음),
`.python\` 를 지우고 다시 → 다시 받아 `SETUP OK`, 재실행은 재사용. 그 `.venv` 로 변환기 검사 · UI 시험 통과. 이 PC 의 실제 3.11 로도 `SETUP OK`.
실제 Windows 10 + Python 3.14 PC 에서의 확인은 사용자 몫.

**확인 기록 (2026-10-22, v01.02)**: 오염된 `PYTHONHOME` · `PYTHONPATH` · `CONDA_*` 까지 넣은 전체 모사 — §6.7.

**확인 기록 (2026-10-19, Windows 11)**: 위 시험 전부 통과 · `.venv` 없는 상태에서 `setup_env.bat` → `SETUP OK` 84초(pip 캐시 있음) ·
재실행 8초 · PATH 에 파이썬이 없을 때 안내 후 종료 · `Run_VisemeNet_Converter.bat` → 시작 오류 없이 이벤트 루프 진입.
**미확인**: 실제 화면에 뜬 창(내 셸에서는 보이지 않는 세션), winget 자동 설치, Windows 10.

---

## 6. 대본 보정 — Correct 모드 (v01.01)

음성만으로는 입 모양이 덜 나오는 문제(특히 **p · b · m 에서 입술이 안 닫힘**)를, 같은 발화의 **대본**으로 고친다.
대본을 Montreal Forced Aligner(MFA)로 음성에 맞춰 **음소마다 시작 · 끝 시간**을 얻고, 그 구간에서 비짐을 보정한다.
설계와 이유는 [0060](0060_transcript_mfa_plan.md) 안 B.

### 6.1 설치 — `setup_mfa.bat` (한 번, 선택)

MFA 는 추론 `.venv` 와 **섞지 않고** 따로 설치한다. 인터넷 필요, 약 **6.5 GB**, 처음 5 ~ 15분.

```
setup_mfa.bat                     질문에 답한다 (Enter = 기본 폴더 <저장소>\.mfa)
setup_mfa.bat D:\tools\mfa        폴더를 인자로
setup_mfa.bat --yes --nopause     묻지 않고 기본 폴더 (스크립트용)
setup_mfa.bat --force             환경만 다시 만든다 (Miniforge · 모델은 유지)
```

| 단계 | 하는 일 |
|------|--------|
| 1/5 | 설치 폴더 결정 — 인자 → 질문 → Enter = 기본값(`<저장소>\.mfa`, 이미 설치했다면 그 폴더). **공백 · 한글이 없고 80자 이하인 로컬 경로만** 받는다(conda · Kaldi 가 실패한다 — 한글 사용자 이름 아래 `C:\Users\홍길동\...` 도 안 된다. 80자: Windows 10 기본은 전체 경로 260자 제한이고, 설치 안 가장 깊은 파일이 폴더 아래 약 175자다). 여유 공간 10 GB 미만이면 중단 |
| 2/5 | **Miniforge 26.7.2-0** 을 받아 **SHA-256 확인** 후 조용히 설치 — "just me", **PATH · 레지스트리 · 바로가기 변경 없음** |
| 3/5 | MFA 환경 — 저장소의 **`mfa_env.lock.txt` 가 있으면 그 정확한 버전으로**(다른 PC 도 같은 환경), 없으면 고정 목록(`montreal-forced-aligner=3.4.3 python=3.11 sudachipy sudachidict-core`). 한국어 토크나이저 `python-mecab-ko` 는 pip(`requirements_mfa.txt`, 버전 고정) |
| 4/5 | 모델 — 음향 모델 · 사전 `english_mfa` · `korean_mfa` · `japanese_mfa` + G2P(사전에 없는 단어의 발음) `english_us_mfa` · `korean_mfa` · `japanese_mfa` |
| 5/5 | 자가 검사 — `test_audio\coffee_xxxx.wav` 를 실제로 정렬. 처음 설치면 `mfa_env.lock.txt` 를 만든다 |

`MFA SETUP OK` 가 나오면 끝. 선택한 폴더는 `mfa_path.local.txt` (gitignore) 에 저장되고 변환기가 읽는다. 로그 `setup_mfa.log`.

**PC 의 다른 Python · conda 와 격리** — `setup_env.bat` · `setup_mfa.bat` · `Run_VisemeNet_Converter.bat` 은 시작할 때 `PYTHONHOME` · `PYTHONPATH` · `PYTHONSTARTUP` 을 비우고 `PYTHONNOUSERSITE=1` 로 둔다(`setup_mfa` 는 `CONDA_PREFIX` 등 conda 변수도). 변환기가 MFA 를 부를 때도 같다. PC 에 Python 3.14 를 가리키는 `PYTHONHOME` / `PYTHONPATH` 가 걸려 있으면 이 툴의 3.11 파이썬(추론 `.venv` · 전용 `.python` · MFA)이 3.14 의 표준 라이브러리를 읽어 **첫 `import numpy` 에서 죽는다**(`warnings` → `_py_warnings.py`: `AttributeError: 'sys.flags' object has no attribute 'context_aware_warnings'` — 2026-10-22 실측, §6.7).

설치 폴더 구조 — **폴더 하나만 지우면 제거된다**:

```
<폴더>\miniforge\   conda 본체
<폴더>\env\         MFA 환경 (mfa.exe)
<폴더>\models\      MFA_ROOT_DIR - 모델 · 사전 · MFA 임시 파일 (기본 Documents\MFA 대신)
```

**다른 PC**: 저장소를 받고 `setup_mfa.bat` 더블클릭 → 폴더를 고른다. `mfa_env.lock.txt` · `requirements_mfa.txt` 가 버전을 고정하므로
이 PC 와 같은 환경이 된다.

| 실패 메시지 | 해결 |
|------------|------|
| `the folder path must not contain spaces or non-ASCII characters` | `C:\mfa` 처럼 공백 · 한글 없는 경로 |
| `the folder path is N characters - at most 80` | `C:\mfa` 처럼 짧은 경로 (저장소가 깊은 폴더에 있으면 기본값 `<저장소>\.mfa` 도 걸린다) |
| `only N GB free` | 다른 드라이브(`D:\mfa`) |
| `Miniforge download failed` | 인터넷 · 프록시 확인 |
| `Could not create the MFA environment` | 로그 끝 15줄이 나온다. `CondaHTTPError` · `SSL` 이면 네트워크 · 프록시 |
| `could not download the ... model` | 네트워크. 다시 실행하면 받은 것은 건너뛴다 |

### 6.2 대본 준비

- WAV 와 **같은 폴더 · 같은 이름**: `<이름>.lab` (권장) 또는 `<이름>.txt`. 둘 다 있으면 `.lab`.
- **UTF-8**. 실제로 말한 단어만 — 숫자 · 기호는 읽는 대로(`2018` → `twenty eighteen`), 무대 지시 · 화자 이름 빼기.
  **말하지 않은 단어가 있거나 철자가 다르면 그 주변 정렬이 틀어진다** (§6.6).
- 대본이 없는 WAV 는 그대로 **오디오만으로** 변환한다 (멈추지 않는다).
- `.txt` 대본을 쓰면 결과 `<이름>.txt` 와 이름이 같다 → **출력 폴더를 꼭 정한다** (비워 두면 E34 로 멈춘다 — 대본을 덮지 않게).

### 6.3 사용

`Transcript (optional)` 상자:

| 항목 | 내용 |
|------|------|
| `Mode` | `Audio only` / **`Correct with transcript (MFA)`** |
| `Language` | `English` / `Korean` / `Japanese` — 음성 · 대본의 언어 |
| `MFA folder` | 비우면 `setup_mfa.bat` 이 고른 폴더. 아래 줄에 찾은 위치(또는 `not found`) |

`Check Files` 는 파일마다 `transcript: <이름>.txt` / `none (audio only)` 를 보여 준다. `Convert` 는 대본 있는 파일을 **한 번에** MFA 로
정렬한 뒤(이 PC: 2개 26초 — MFA 시작 비용이 대부분) 하나씩 추론 · 보정한다. 로그의 `(…, corrected, …)` / `(…, audio only, …)` 로 구분.

### 6.4 보정 규칙 (안 B)

열 0 ~ 1 (**Jaw · Lip 은 그대로**), 열 2 ~ 21 (비짐 20개) 만 바꾼다. 음소는 `saved_params/ipa_to_jali.json` 으로 비짐에 매핑한다
(IPA — 세 언어 공용, 사전의 음소 영어 92 · 한국어 104 · 일본어 84 개를 전부 덮는다).

| 구간 | 처리 |
|------|------|
| 음소 구간 | 그 음소의 비짐에 **최솟값 보장** — 기본 0.6, **입술(MBP · FV) 0.8**. 이미 더 크면 그대로 |
| 같은 구간의 다른 비짐 | × 0.5 |
| 무음 | 비짐 전부 × 0.2 |
| 경계 | 앞뒤 3행(30 ms) 선형 램프 |
| `spn`(사전 · G2P 모두 실패한 단어), `h` 같은 중립 음소, `ʋ`(영어 사전이 w · v 양쪽에 씀) | **VisemeNet 값 그대로** |
| 일본어 `ɴ`(ん) | 뒤 자음을 따른다 (m 앞 → MBP), 끝이면 GK |

`<이름>.phones.json` — `words` · `phones` 를 `[시작초, 끝초, 라벨]` 로. `.visemenet.json` 의 `correction` — 언어 · 대본 · MFA 버전 · 보정 음소 수 ·
매핑에 없던 음소 · 보정값.

### 6.5 코드

| 코드 | 로그 | 할 일 |
|------|------|------|
| E30 | `MFA not found` | `setup_mfa.bat` 실행, 또는 `MFA folder` 지정 |
| E31 | `MFA model missing for <언어>` | `setup_mfa.bat` 다시 실행 (빠진 모델만 받는다) |
| E32 | `transcript is empty` / `not UTF-8` | 대본을 UTF-8 로 저장 (메모장: 다른 이름으로 저장 → 인코딩 UTF-8) |
| E33 | `MFA align failed` / `did not finish` | MFA 자체가 실패 — 로그의 `detail` |
| E34 | `output would overwrite the transcript` | §6.2 |
| W10 | `alignment failed - audio only` | 그 파일만 오디오로. 대본이 음성과 맞는지 확인 |
| W11 | `N word(s) not in the dictionary` | 그 단어 구간은 VisemeNet 값 그대로 |
| W13 | `phones not in ipa_to_jali.json` | 그 음소 구간은 그대로. 표에 추가할 후보 |

### 6.6 확인 기록 (2026-10-20, 영어 예시 2개 · angela 리그)

- **Windows 10 + Python 3.14 모사** (§6.7): 통과.
- **재현성**: 같은 PC 의 다른 폴더(`C:\jun_mfa_test`)에 `mfa_env.lock.txt` 로 새로 설치 → `MFA SETUP OK`, 패키지 230개가 잠금 파일과 **완전히 같다**, 한국어 토크나이저 · 자가 검사 정렬 통과. 실제 다른 PC 는 미확인.
- MFA 경계는 10 ms 격자 — 100fps 행과 그대로 맞물린다.
- 사전에 없는 `VizimNet` → G2P 가 `vʲ ɪ z ɪ m n ɛ t` 로 만들어 정렬.
- `visemenet_intro` 입술 음소 21개 — angela 의 `CNT_PHONEMES.MBP` · `FFF` 컨트롤이 **8 이상(0 ~ 10) 된 수: 오디오만 10 → 보정 21**
  (평균 5.4 → 8.4). `coffee_xxxx` 의 `f` 는 0 → 8. 비교 장면: `out/m2/angela_JALI_<이름>_{audio,correct}.ma` (gitignore).
- 대본 `visemenet_intro.txt` 의 `cures` 는 `c ʊ ə z` 로 정렬됐다 — 실제 발화가 *curves* 라면 v 가 빠진다(대본 확인 필요).
- **눈으로 보는 확인(입술이 실제로 자연스럽게 닫히는가)은 아직** — 위 장면을 열어 재생해 볼 것. 보정값(0.6 · 0.8 · ×0.5)은 초안이다.

### 6.7 확인 기록 (2026-10-22, Windows 10 + Python 3.14 PC 모사, v01.02)

실제 Windows 10 PC 는 없어 이 PC(Windows 11)에서 **보고된 환경을 그대로 흉내 내어** 돌렸다.

- PATH 에 **Python 3.14.9 만**(python.org NuGet 패키지, 시스템에 설치하지 않고 임시 폴더에 푼 것) + 가짜 `py` 런처 — `py -3.11` · `-3.10` · `-3.9` 는
  보고와 같은 문구 `No runtime installed that matches 3.11. Try running "py install 3.11".` 를 내고 **종료 코드 0**, 그 외는 3.14 를 실행.
  이 PC 의 실제 Python 3.11 과 `py.exe` 는 PATH 에서 뺐다.
- 오염 변수: `PYTHONHOME` = 3.14 폴더, `PYTHONPATH` = 3.14 의 `Lib`, `PYTHONSTARTUP` = 없는 파일, `CONDA_PREFIX` · `CONDA_EXE` = 없는 경로,
  `CONDA_DEFAULT_ENV=other`, `CONDA_SHLVL=1`.

| 단계 | 결과 |
|------|------|
| 음성 대조 — 오염 변수를 **지우지 않고** `.venv` · `.python` · MFA 의 Python 3.11 을 실행 | 셋 다 시작은 되지만 3.14 의 `Lib` 를 읽는다(`os.__file__` 이 3.14 쪽). 첫 `import numpy` 에서 `warnings` → `_py_warnings.py` 의 `sys.flags.context_aware_warnings` 로 `AttributeError` — 자가 검사 · 변환기 · MFA 전부 못 돈다. `PYTHONHOME` 만, `PYTHONPATH` 만 걸어도 같다 |
| `setup_env.bat --yes --nopause` (오염된 채 호출) | `.bat` 가 변수를 비우므로 3.14 는 "not supported" 로 지나치고 `.python\` 의 3.11 → `.venv` 재사용 → 패키지 OK → 자가 검사 `(364, 22)` → **`SETUP OK`** |
| `setup_mfa.bat <95자 경로> --nopause` | 설치 전에 `[ERROR] the folder path is 95 characters - at most 80 (Windows 260-character path limit), e.g. C:\mfa` 로 중단, 종료 코드 1 |
| `Run_VisemeNet_Converter.bat` 의 사전 점검 줄(변수를 비운 뒤 `.venv` 로 `import PySide6`) | OK, `startup_error.log` 없음. 창을 띄우는 실행 자체는 10-20 에 같은 조건으로 종료 코드 0 확인 |
| 변환기 시험 5종 — `.bat` 처럼 Python 변수만 비우고 `CONDA_*` 오염은 남긴 채 `.venv` 로 | `make_bad_wavs` 13 · `test_core` 17 · `test_ui` 16 · `test_merge` 41 · `test_align` 16(실제 MFA 정렬) 전부 `RESULT OK` |

- `test_merge` 의 새 항목 2개: `aligner.MfaInstall.environ()` 이 `PYTHONHOME` · `PYTHONPATH` · `CONDA_DEFAULT_ENV` 를 빼고 `PYTHONNOUSERSITE=1` · `MFA_ROOT_DIR` 를 넣는지.
- **미확인**: 실제 Windows 10 PC, 실제 Python 설치 관리자의 `py`(가짜로 대신했다), 화면에 뜬 창. 그 PC 에서 문제가 나면
  `setup_env.log` · `setup_mfa.log` · `tools\VisemeNet_Converter\data\startup_error.log` 를 보내 달라.
