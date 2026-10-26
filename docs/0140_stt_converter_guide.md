# 설치 · STT Converter 사용 안내 — 음성(wav) → 대본(.lab)

> **작성** 2026-10-23 · 대상: `setup_stt.bat` · `Run_STT_Converter.bat` · `tools/STT_Converter` **v01.00** · `tools/STT_Converter/cli.py`
> · 설계 · 조사 · 실측은 [0130 계획서](0130_stt_converter_plan.md), 만든 대본을 쓰는 쪽은 [0080 대본 보정 사용법](0080_transcript_correction_usage.md) · [0050 §6](0050_converter_guide.md)
> · 마야 쪽 대량 파이프라인 `Maya_Python/JUN_All/docs/plans/A00560_JaliBatch_plan.md` P4 가 `cli.py` 를 부른다.

**무엇을 하나**: 잡음 없는 **한국어 · 일본어 · 영어** 음성 wav 를 여러 개 넣으면, 로컬 딥러닝 모델(faster-whisper `large-v3-turbo`)이
받아써서 **그 언어의 대본 `<이름>.lab`** 을 wav 옆에 만든다. 이 대본이 VisemeNet Converter **Correct 모드**의 입력이다 —
지금까지 사람이 손으로 받아쓰던 것([0080 §③](0080_transcript_correction_usage.md))을 대신한다. 인터넷 없이 돈다(모델은 설치 때 한 번 받는다).

```
 ┌ 한 번만 ──────────────────────────────────────────────┐
 │ ① setup_stt.bat   (Python 3.11 확보 → .venv_stt → 모델 1.6 GB → 자가 검사) │
 └───────────────────────────────────────────────────────┘
 ② Run_STT_Converter.bat → wav 넣기 · Language 고르기 · Convert
        ↓
    <이름>.lab  (+ <이름>.stt.json)        ← wav 옆에
        ↓
 ③ VisemeNet Converter: Correct with transcript (MFA)  →  <이름>.txt (22열) + .phones.json  →  Maya A00540
```

---

## 1. 설치 — `setup_stt.bat` 더블클릭

Windows 10 · 11 공용. 관리자 권한 불필요. **인터넷 필요**(패키지 약 1.5 GB + 모델 1.6 GB). VisemeNet 의 `.venv` · MFA 와는 **따로** 설치되고 섞이지 않는다(계획 D9).
GPU 는 선택 — NVIDIA GPU 가 있으면 CUDA 로, 없으면 CPU 로 돈다(§7 속도). CUDA 런타임은 pip 로 함께 받으므로 시스템에 CUDA 를 깔 필요가 없다.

| 단계 | 화면 | 하는 일 |
|------|------|--------|
| 1/6 | `found: ...\.python\python.exe  (Python 3.11)` | 64bit Python 3.9 ~ 3.11 을 찾는다. **순서**: ① 이 폴더의 `.python\`(VisemeNet `setup_env.bat` 이 받아 둔 전용 Python 이면 **그대로 공유**) → ② `py -3.11` · `-3.10` · `-3.9` → ③ PATH 의 `python`. 후보를 **실제로 실행해 출력으로** 판단한다(종료 코드는 믿지 않는다 — [0050 §1](0050_converter_guide.md) 의 Python 3.14 PC 사례) |
| (없을 때) | `Found Python 3.14 (not supported ...)` + `Download the private Python 3.11 now [Y,N]?` | Y = python.org 의 Python 3.11.9 NuGet 패키지(약 17 MB)를 받아 SHA-256 확인 뒤 `.python\` 에 푼다. 시스템에 설치하지 않고 PC 의 Python 3.14 도 그대로다 |
| 2/6 | `created .venv_stt` / `reusing the existing .venv_stt` | 저장소 안 `.venv_stt`. 만든 뒤 실제로 도는지 확인하고, 깨진 것은 다시 만든다 |
| 3/6 | `packages OK` | `requirements_stt.txt`(고정 버전: faster-whisper 1.2.1 · CTranslate2 4.8.3 · PySide6 6.12 · nvidia cuBLAS · cuDNN …) |
| 4/6 | `[OK] model 'large-v3-turbo' -> ...  (1.62 GB, N s)` | 모델을 `models\hub\` 에 미리 받는다(처음 한 번). 이미 있으면 바로 지나간다 |
| 5/6 | `[OK] transcribe coffee_xxxx.wav (4.0 s audio) -> "This coffee sucks!"  in 5.8 s` | **CPU 로** 모델을 올려 `test_audio\coffee_xxxx.wav` 를 실제로 받아쓴다. `coffee` 가 나와야 통과. GPU 는 설치 단계에서 건드리지 않는다(드라이버 문제로 설치가 멈추지 않게) |
| 6/6 | `SETUP OK` | 끝. 로그 `setup_stt.log` 첫머리에 OS 빌드 · GPU · 드라이버 · 어느 Python 을 썼는지 적힌다 — 다른 PC 에서 문제가 나면 이 파일을 보내 달라 |

**다시 실행해도 안전하다** — 있는 것은 재사용한다(이 PC 에서 약 30 초). 명령창 옵션:

| 옵션 | 뜻 |
|------|-----|
| `--force` | `.venv_stt` 를 지우고 다시 만든다. **폴더를 옮겼거나**, 실행 중 `source code string cannot contain null bytes` · `DLL load failed` 같은 오류가 나면 이것 |
| `--yes` | 전용 Python 을 묻지 않고 받는다 (스크립트용) |
| `--nopause` | 끝에 멈추지 않는다 |
| `--no-system-python` | PC 의 Python 을 후보에서 빼고 `.python\` 만 쓴다(없으면 받는다) — Python 3.14 PC 모사용(계획 M0-9) |
| `--use-system-python` | PC 의 Python 3.12 ~ 3.14 도 후보에 넣는다 (**미검증** — 휠이 없으면 pip 에서 멈춘다) |
| `--offline` | 모델 다운로드를 건너뛴다. 인터넷 없는 PC 는 다른 PC 의 `models\` 폴더를 통째로 복사해 두고 이 옵션 |
| `--model NAME` | 기본 모델에 더해 하나 더 받는다 — `large-v3` · `distil-large-v3.5` · `kotoba-tech/kotoba-whisper-v2.0-faster` … |
| `--qwen` | 2차 엔진(Qwen3-ASR) 설치 — `requirements_stt_qwen.txt` 가 저장소에 생긴 뒤에만 동작(지금은 건너뛴다) |

| 실패 메시지 | 해결 |
|------------|------|
| `Python 3.9 - 3.11 (64-bit) is required.` | 다시 실행해 `Y`(전용 Python 받기), 또는 Python 3.11 64bit 설치. 다운로드가 막힌 PC 는 다른 PC 의 `.python\` 폴더를 복사해 두면 그걸 쓴다 |
| `Download / extract failed` | 인터넷 · 회사 프록시, 또는 폴더 경로가 너무 길다 → `C:\JUN_JALI` 처럼 짧은 곳으로 |
| `Could not create .venv_stt` | `setup_stt.log` 끝 확인. 대개 경로 길이 · 권한 |
| `Package installation failed` + `No matching distribution` | 그 Python 에 휠이 없다 — `--use-system-python` 을 빼고 3.11 로 |
| `Model download failed` | 인터넷. 또는 `models\` 를 복사해 오고 `--offline` |
| `[ERROR] model test failed ... E41` | `models\hub` 에 모델이 없다 — 인터넷을 연결하고 `--offline` 없이 다시 |
| `import failed: DLL load failed` | Microsoft Visual C++ 재배포 패키지(x64) 설치 (`https://aka.ms/vs/17/release/vc_redist.x64.exe`) |
| `source code string cannot contain null bytes` | 설치 도중 PC 가 꺼져 `.venv_stt` 의 파일이 비었다(2026-10-23 실제 사례, §9) → `setup_stt.bat --force` |

**PC 의 다른 Python · conda 와 격리** — VisemeNet 쪽과 같다([0050 §6.1](0050_converter_guide.md)): `setup_stt.bat` · `Run_STT_Converter.bat` 은 시작할 때
`PYTHONHOME` · `PYTHONPATH` · `PYTHONSTARTUP` 을 비우고 `PYTHONNOUSERSITE=1` · `PYTHONUTF8=1` 로 둔다. 모델 캐시는 `HF_HOME=<저장소>\models` 로 고정한다(PC 의 `~\.cache\huggingface` 를 쓰지 않는다).

**PC 에 남는 것**: `.venv_stt\` · `.python\` · `models\` · `tools\STT_Converter\data\`(설정 · 사용자 사전) · `setup_stt.log` — 전부 저장소 폴더 안(gitignore). 지우려면 폴더만 지운다.

---

## 2. 변환 — `Run_STT_Converter.bat` 더블클릭

설치가 끝나면 같은 폴더에 아이콘이 붙은 바로가기 **`STT Converter.lnk`** 가 생긴다 — 이걸 눌러도 같다(`.bat` 은 자체 아이콘을 못 가져서 바로가기로 보인다. 폴더를 옮겼으면 `make_shortcuts.bat` 을 다시 실행).

콘솔 없이 창만 뜬다. 실행 전에 `.venv_stt` 가 도는지 확인하고, 안 되면 `Double-click setup_stt.bat again` 을 띄운다(폴더를 옮긴 경우 → `--force`).
시작 중 오류는 메시지 창 + `tools\STT_Converter\data\startup_error.log`.

```
┌ STT Converter v01.00 ───────────────────────────────────────────────────┐
│ File  Tools  Help                                                        │
├ Input WAV Files ─────────────────────────────────────────────────────────┤
│ [Add Files...] [Add Folder...]                                           │
│  D:\voice\src_kr\0010_vivian_kr.wav                      [Del][Up][Down] │
│  D:\voice\src_kr\0020_vivian_kr.wav                      [Sort][Clear]   │
├ Recognition ─────────────────────────────────────────────────────────────┤
│ Language [Korean ▼]  Engine [faster-whisper ▼]  Model [large-v3-turbo (recommended) ▼] │
│ Custom model [                                              ] (Custom 일 때만) │
│ Device [Auto (CUDA if available, else CPU) ▼]  Beam [5]  VAD [Auto (off for clips under 10 s) ▼] │
│ [x] Normalize text for MFA (numbers -> words, user dictionary)  [ ] Kana output (Japanese) │
│ Device is chosen when Convert is pressed (GPU is detected then, not at start-up). │
├ Output ──────────────────────────────────────────────────────────────────┤
│ Folder [                                   ] [Browse...] [Open]   ← 비우면 wav 옆 │
│ Extension [.lab (recommended) ▼]   Existing [Skip (keep the existing transcript) ▼] │
│ [x] Write <name>.stt.json (raw text, segments, word times, confidence)    │
├──────────────────────────────────────────────────────────────────────────┤
│ [Check Files]                       [        Convert        ]   [Stop]   │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░  2 / 3  0020_vivian_kr.wav       │
├ Log ─────────────────────────────────────────────────────────────────────┤
│ [INFO] Device: CPU forced (flag file ...\data\force_cpu.flag) - CUDA not touched │
│ [OK] 0010_vivian_kr.wav -> 0010_vivian_kr.lab  (6 segment(s), 35.9 s audio, 6.8 s)  파에톤 님… │
└──────────────────────────────────────────────────────────────────────────┘
```

1. **WAV 넣기** — `Add Files...` / `Add Folder...`(폴더 바로 아래 `.wav`, 하위 폴더는 안 본다), 또는 탐색기에서 **창으로 끌어다 놓기**(파일 · 폴더).
   같은 파일은 한 번만 들어간다. 목록에서 하나를 누르면 로그에 규격(`44100 Hz, 1 ch, 35.9 s PCM_16`)과 **이미 대본이 있는지** 나온다.
   샘플레이트 · 채널 · 비트 수는 가리지 않는다(모델이 내부에서 16 kHz 로 바꾼다 — VisemeNet 의 E03 · E04 와 달리 멈추지 않는다). wav 자체는 바꾸지 않는다.
2. **Language** — **한 번의 변환에 한 언어**(`English` / `Korean` / `Japanese`). 자동 감지에 맡기지 않고 **강제**한다 — 1.5 초짜리 짧은 클립은 감지가 자주 틀린다.
   언어가 섞인 목록은 나눠서 변환한다. 모델이 다른 언어로 판단하면 `W20` 으로 알려 준다(결과는 쓴다).
3. **Model** — 기본 `large-v3-turbo`(세 언어 공용, 빠름). 틀린 말이 많으면 `large-v3`(느리지만 조금 더 정확), 일본어만이면 `kotoba-whisper-v2.0`, 영어만이면 `distil-large-v3.5`.
   `Custom...` 은 Hugging Face repo 이름(`user/model`) 또는 CTranslate2 로 변환한 로컬 폴더. 목록에 없는 모델은 **첫 Convert 때 받는다**(인터넷 필요, 수 분) — 미리 받으려면 `setup_stt.bat --model NAME`.
4. **Device** — `Auto` 면 NVIDIA GPU 가 있을 때 `CUDA float16`, 없으면 `CPU int8`(로그에 `W21`). GPU 는 **Convert 를 누를 때** 찾는다(창을 띄울 때는 건드리지 않는다).
   `CUDA int8_float16` 은 Ampere(A2000) 에서 더 빠를 수 있는 옵션 — RTX 50(Blackwell) 에서는 미검증. CUDA 초기화가 실패하면(E44) 멈추지 않고 CPU 로 폴백한다.
   **이 PC 에서는 CUDA 를 쓰지 말아야 한다면** `Tools > Never use CUDA on this PC` 를 켠다 — `data\force_cpu.flag` 가 생기고 Device 가 `CPU int8` 로 잠긴다(GPU 드라이버를 전혀 부르지 않는다). 환경 변수 `JUN_STT_FORCE_CPU=1` 도 같다. 개발 PC 가 그 경우다([0130 §6](0130_stt_converter_plan.md)).
5. **Beam** 5 = 정확도 우선(기본). 1 로 내리면 빠르지만 틀린 말이 는다. **VAD** `Auto` = 10 초 이상 파일만 앞뒤 무음을 잘라 낸다(없는 말을 지어내는 환각 방지). 짧은 클립은 끈다 — 실측에서 VAD 가 3.7 초 · 4.9 초 클립의 **첫 단어를 잘라 먹었다**(§7). `On` · `Off` 로 고정할 수도 있다.
6. **Normalize text for MFA** (기본 켬) — 숫자 · 기호를 읽는 대로 풀고 사용자 사전을 적용한다(§3). 끄면 모델이 낸 글 그대로 `.lab` 에 쓴다. `Kana output` 은 일본어만 — 전부 かな 로(§3 주의).
7. **Output** — `Folder` 를 **비우면 각 wav 옆**에 쓴다(VisemeNet Converter 가 대본을 찾는 자리). `Extension` 은 `.lab` 권장 — `.txt` 는 VisemeNet 결과 22열 `.txt` 와 이름이 같아 헷갈린다(`W26`, [0050 §3 E34](0050_converter_guide.md)).
   **Existing** — 대본이 이미 있으면 기본 **Skip**(손으로 고친 대본을 자동 결과가 덮지 않게, `W25`) / `Overwrite` / `Overwrite with backup`(`<이름>.lab.bak`).
8. **`Check Files`** — 변환 없이 검사만: 파일마다 규격 · 건너뛸지 · 경고, 마지막에 받아쓸 파일 수와 음성 총 길이, 장치.
   **`Convert`** — 검사 → (첫 번째만) 모델 로드 → 파일마다 받아쓰기 → 정규화 → 쓰기. **하나라도 검사에 걸리면 아무것도 변환하지 않는다**(E 코드). 변환 중 파일 하나가 실패하면 **그 파일만 건너뛰고 계속**한다(결과가 서로 독립이라). `Stop` 은 지금 파일이 끝나면 멈춘다.
   `Convert` 를 누르면 **진행 팝업**이 떠서 `Checking files` → `Loading model`(첫 변환만) → `Transcribing`(`n / 전체 파일명`) → `Done` 100 % 뒤 닫힌다. 단계 · 파일 폭은 예상 시간(CPU 기준: 파일당 5 초 + 음성 길이 × 0.3)에 맞춰 차오르고 경계를 넘지 않는다. 팝업의 `Stop` 은 창의 `Stop` 과 같다. 실패 · Stop 이면 100 % 를 만들지 않고 바로 닫힌다.

설정 · 목록은 창을 닫을 때 저장되어 다음에 그대로 열린다(`tools\STT_Converter\data\settings.json`). 변환 중에는 창을 닫을 수 없다(Stop 먼저).

메뉴: `File`(Add Files · Add Folder · Exit) · `Tools`(**User Dictionary...** §3 · Open Models Folder · Never use CUDA on this PC) · `Help`(Open Guide = 이 문서 · About).

### 결과 파일

| 파일 | 내용 |
|------|------|
| `<이름>.lab` | 대본 **한 줄**. UTF-8(BOM 없음), 끝 줄바꿈 1개. 정규화를 거친 글(§3). VisemeNet Converter Correct 모드가 그대로 읽는다 |
| `<이름>.stt.json` | 검수 · 재현용(옵션, 기본 켬). `raw_text`(모델이 낸 원문) · `text`(.lab 내용) · `replaced`(정규화가 바꾼 토큰) · `unresolved`(W23 토큰) · `suspects`(W24 구간) · `warnings` · `segments`(구간마다 시작 · 끝 · 글 · 단어별 `[시작, 끝, 단어, 확신도]` · `avg_logprob` · `no_speech_prob` · `compression_ratio`) · `detected_language` + 확률 · 엔진 · 모델 · 장치 · 옵션 · 걸린 시간 |
| `<이름>.lab.bak` | `Overwrite with backup` 일 때 이전 대본 |

빈 결과(말이 없다고 판정, `W22`)는 `.lab` 을 쓰지 않고 json 만 남긴다.

---

## 3. 대본은 이렇게 나온다 — 정규화 · 사용자 사전

STT 모델은 **자막 표기**(숫자 · 기호 · 영문 약어)로 쓴다. MFA 사전은 **발음대로 쓴 단어**만 알고 숫자 · 기호는 읽지 못하므로, `.lab` 에 쓰기 전에 언어별로 고친다([0080 §③](0080_transcript_correction_usage.md) 의 "읽는 대로" 규칙을 자동화한 것). 원문은 `.stt.json` 의 `raw_text` 에 그대로 남는다.

| 언어 | 규칙 | 예 (모델 출력 → .lab) |
|------|------|-----------------------|
| 공통 | 전각 → 반각(NFKC), 따옴표 · 괄호 · 말줄임표 · 대시 제거, 줄바꿈 → 공백, 연속 공백 1개. **문장부호 `. , ? !` 는 남긴다**(MFA 가 무시한다, 사람이 읽기 좋다) | `"오늘…"` → `오늘` |
| 영어 | 숫자 → 단어(연도 `2018` → `twenty eighteen`, `2005` → `two thousand five`), 서수 `1st` → `first`, `50%` → `fifty percent`, `$5` → `five dollars`, 시각 `3:30` → `three thirty`, 소수 `3.5` → `three point five`. 대문자 2 ~ 5 글자 약어(`UE` · `KWI`)는 **그대로 두고 W23** 으로 알린다(철자대로 `U E` 로 풀거나 사전에) | `We present 2 methods.` → `We present two methods.` |
| 한국어 | 숫자 → 수사. 뒤의 **단위명사**로 고유어 / 한자어를 고른다 — `1등` → `일등`, `3개` → `세개`, `10시` → `열시`, `2026년` → `이천이십육년`, `1,000` → `천`, `3.5` → `삼 점 오`. 단위 없는 숫자 · 모르는 단위는 한자어. 수사와 단위는 숫자 표기처럼 붙여 쓴다(mecab 이 분절한다). **띄어쓰기는 유지**(korean_mfa 가 다시 분절). 로마자 토큰은 W23 | `1등이 될 거예요` → `일등이 될 거예요` |
| 일본어 | 숫자 → 漢数字 — `3時` → `三時`, `2026年` → `二千二十六年`, `50%` → `五十パーセント`(읽기는 MFA 의 Sudachi 가 정한다). **공백 · 줄바꿈은 남긴다** — 지우는 것은 VisemeNet Converter 가 MFA 직전에 한다([0080 §③](0080_transcript_correction_usage.md)). 로마자 토큰은 W23(カタカナ 로 사전에) | `3時に会おう` → `三時に会おう` |

- **`Kana output` (일본어)** — 전부 ひらがな 로 바꾼다. 한자 읽기를 MFA 가 틀릴 때 쓴다. **`pykakasi` 패키지가 있을 때만** 동작한다 — 기본 설치에는 들어 있지 않아 지금은 켜도 한자 혼용 그대로 나오고 `W23 (kana output) pykakasi is not installed` 로 알린다. 쓰려면 `.venv_stt\Scripts\python.exe -m pip install pykakasi`.
- **사용자 사전** — `Tools > User Dictionary...`(지금 고른 언어의 사전이 열린다). 한 줄에 `토큰 = 치환`:
  ```
  KWI = 케이더블유아이
  파이토님 = 파에톤 님
  ```
  정규화 때 토큰 단위로(긴 것부터, 영문은 대소문자 무시) 바꾼다. 파일은 `tools\STT_Converter\data\user_dict_{en,ko,ja}.json`(PC 마다 따로 — 다른 PC 로 가져가려면 복사). **로그에 `W23` 으로 남은 토큰이 사전에 넣을 후보다.** 고유명사를 모델이 다르게 받아쓰는 경우(실측: `파에톤 님` → `파이토님` 4회)도 여기서 고친다.

---

## 4. 멈추는 경우 · 경고 — 로그 읽는 법

**시작 전에 목록 전체를 검사하고, 하나라도 걸리면 아무것도 변환하지 않는다**(E40 ~ E43). 변환 중의 실패는 **그 파일만** 건너뛴다(E44 · E45 · 쓰기 실패) — 로그 끝 `[DONE] n transcript(s) written` 으로 몇 개가 됐는지 본다.
번호는 VisemeNet Converter(E01 ~ E34 · W01 ~ W13)와 겹치지 않게 E40 ~ · W20 ~ 다.

| 코드 | 로그 | 할 일 |
|------|------|------|
| **E40** | `engine package is not installed - run setup_stt.bat` | `.venv_stt` 가 없거나 깨졌다 → `setup_stt.bat`(안 되면 `--force`) |
| **E41** | `model load failed ...` + Hugging Face · connection | `models\hub` 에 그 모델이 없고 인터넷도 없다 → 인터넷 연결 후 다시, 또는 `setup_stt.bat --model NAME`, 또는 다른 PC 의 `models\` 복사 |
| E42 | `cannot read audio (...)` / `audio is empty (0.05 s)` | 깨진 wav · 0.1 초 미만 · 이름만 wav 인 mp3 → PCM wav 로 다시 내보내기 |
| E43 | `cannot write to the output folder` / `cannot write output` | 출력 폴더 권한 · 드라이브. (`cannot write output` 은 변환 중 — 그 파일만 건너뜀) |
| E44 | `CUDA is disabled on this PC` / `model load failed ... cuda` | CUDA 초기화 실패 · 금지 → **멈추지 않고** CPU int8 로 다시 올린다(`W21`). CPU 로도 안 되면 중단 |
| E45 | `transcription failed: <파일>` | 그 파일만 건너뜀. `detail:` 줄 확인(메모리 부족이면 Beam 을 줄이거나 CPU) |
| W20 | `detected language 'ja' (p=0.93) differs from the selected Korean` | 결과는 썼지만 **언어 선택이 틀렸을 수 있다** — 들어 보고 맞는 언어로 다시 |
| W21 | `no CUDA device ... falling back to CPU int8 (slow)` / `CPU forced (...)` | 정보. 시간이 더 걸린다(§7) |
| W22 | `no speech recognized - transcript not written` | 말이 없다고 판정. 소리가 아주 작거나 전부 무음 — `VAD Off` 로 한 번 더 |
| **W23** | `unresolved token 'KWI' (latin letters - add to the Korean user dictionary)` / `'3' (digits left)` | 정규화가 못 푼 토큰 → **사용자 사전에 넣고** 다시 변환(§3). 그대로 두면 MFA 가 그 단어를 추측(G2P)한다 |
| W24 | `possible hallucination at 0.0-4.5 s (no_speech_prob 0.82)` / `(compression_ratio 2.6)` / `(repeated '...')` | 환각 · 반복 의심 구간 — `.stt.json` 의 `suspects` 에도 남는다. 그 시각을 들어 보고 `.lab` 을 손으로 고친다 |
| W25 | `transcript exists - skipped (<이름>.lab)` | 기존 대본을 지켰다. 새로 받아쓰려면 `Existing = Overwrite` |
| W26 | `output is .txt - ... .lab is recommended` | `.txt` 를 골랐다 — VisemeNet 결과와 이름이 겹친다 |
| W27 | `transcript exists - will be overwritten` / `backed up to ....bak` | `Overwrite` 모드 안내 |

`[INFO] <파일>  VAD off (clip shorter than 10 s)` 는 정상 안내다.

---

## 5. VisemeNet Converter 로 넘기기

1. `Output Folder` 를 **비워 두고** 변환하면 `.lab` 이 wav 옆에 생긴다 — 그 자리가 VisemeNet Converter 가 대본을 찾는 곳([0080 §③](0080_transcript_correction_usage.md)).
2. VisemeNet Converter 에 **같은 wav** 를 넣고 `Transcript = Correct with transcript (MFA)`, `Language` 를 **여기서 고른 것과 같게**, `Convert`.
3. `Check Files` 에서 `transcript: <이름>.lab` 이 보이면 연결된 것이다.

- `.lab` 을 **열어서 한 번 읽어 보는 것**이 가장 싼 검수다 — 특히 `W20` · `W23` · `W24` 가 난 파일. 대본에 없는 말 · 잘못 받아쓴 말이 있으면 MFA 가 그 주변을 틀리게 맞춘다([0050 §6.5 W12](0050_converter_guide.md)).
- 손으로 쓴 대본이 이미 있는 폴더(`src_*`)에서는 기본 `Skip` 이 그 대본을 지킨다. 자동 결과와 비교하려면 `Output Folder` 를 다른 곳으로.
- 같은 이름의 `.lab` 과 `.txt` 가 둘 다 있으면 VisemeNet Converter 는 `.lab` 을 쓴다.

---

## 6. 헤드리스 — `cli.py` (A00560 JaliBatch 가 부르는 형식)

```
.venv_stt\Scripts\python.exe tools\STT_Converter\cli.py <폴더 | wav ...> --language Korean
    [--out DIR] [--ext .lab|.txt] [--existing skip|overwrite|backup] [--no-json]
    [--engine faster-whisper] [--model large-v3-turbo] [--device auto|cuda:float16|cuda:int8_float16|cpu:int8]
    [--beam 5] [--vad auto|on|off] [--kana] [--no-normalize] [--user-dict FILE.json] [--quiet]
```

- 창과 **같은 코어**(사전 검사 · 정규화 · 쓰기 · 코드)를 쓴다. 폴더는 바로 아래 `.wav` 만.
- 로그는 stdout 에 창과 같은 `[LEVEL] message` 줄. `--quiet` 면 `WARN` · `ERROR` · `DONE` 만.
- **종료 코드**: `0` = 전부 끝남(건너뜀 · 경고 포함) · `1` = 사전 검사 실패(아무것도 안 씀) · 엔진 로드 실패 · 중단 · wav 없음 · `2` = 인자 오류(`--user-dict` 못 읽음 포함).
- `--user-dict` 를 주지 않으면 창과 같은 `data\user_dict_<lang>.json` 을 쓴다. 모델 캐시도 같은 `models\`.
- 환경 격리(`PYTHONHOME` 등)는 bat 이 해 주는 것이라, 직접 부를 때는 호출하는 쪽에서 비운다(A00560 의 `mayapy_runner` 가 한다).

```
$ cli.py D:\voice\src_kr --language Korean --quiet
[WARN] 0010_vivian_kr.wav  W25 transcript exists - skipped (0010_vivian_kr.lab)
[DONE] 2 transcript(s) written, 1 skipped (existing), 3 file(s) total
```

---

## 7. 속도 · 정확도 — 실측 (2026-10-23, 자세한 표는 [0130 §11](0130_stt_converter_plan.md))

| | GPU (RTX 5070, CUDA float16) | CPU (Ryzen 7 7800X3D 16 스레드, int8) |
|---|---|---|
| 모델 로드(캐시 있을 때) | 1.9 s | 2.3 ~ 3.0 s |
| 한국어 35.9 s 음성 | 0.9 s | 6.8 s |
| 일본어 45.8 s | 1.1 s | 12.9 s |
| 영어 29.7 s | 9.0 s (첫 호출, 워밍업 포함) | 6.3 s |
| 호출당 고정 비용 | — | 약 5 s (1.5 초 클립도 5 s) |

- **결과 텍스트는 GPU float16 과 CPU int8 이 글자 단위로 같았다**(KR · EN). CPU 가 느릴 뿐 품질 차이는 없다.
- **정확도**(Vivian 예시, 손 대본 대비 글자 오류율 CER): 영어 **0.33 %**(구두점 · 대소문자뿐) · 한국어 **6.59 %**(전부 고유명사 `파에톤 님` → 사전으로 해결) · 일본어 **11.05 %**(`わたし`/`私`, `辿り着いて`/`たどり着いて` 같은 **표기 차이** — 발음은 같다. 고유명사 `パエトーン` 은 사전).
- 짧은 클립(1.5 ~ 10 초) 은 VAD 를 끄면 CER 0 %, 켜면 첫 단어가 잘렸다(72 % · 13 %) → `VAD Auto` 의 근거.
- 기준 사양 PC(Ryzen 9 3900X · RTX A2000 12 GB) 값은 아직 없다 — 그 PC 에서 돌린 `setup_stt.log` · 변환 로그를 받으면 여기에 적는다(계획 M0-8).

---

## 8. 개발자용

| 파일 | 역할 |
|------|------|
| `setup_stt.bat` | 설치(§1). `setup_env.bat` 의 Python 탐색(`:probe` · `:download_python`)을 그대로 가져옴 — `.python\` 공유 |
| `Run_STT_Converter.bat` | 환경 확인 → `HF_HOME=models` → `pythonw launch.py` |
| `tools/STT_Converter/launch.py` | 진입점. `sys.path` = 저장소 루트 + `vendor/`. 시작 오류 → 메시지 창 + `data/startup_error.log` |
| `cli.py` | 헤드리스(§6) |
| `selftest.py` | 설치 마지막 검사(CPU 고정). `--wav` `--language` `--model` |
| `download_model.py` | 모델 선다운로드(`faster_whisper.utils.download_model` → `models\hub`) |
| `app/config/version.py` · `app_meta.py` | 버전 · 작업표시줄 아이콘 ID(AUMID) · `icon_path()` |
| `tools/STT_Converter/icon/` | `STT_Converter.svg`(원본: 파형 → 대본 줄) · `.png`(256) · `.ico`(16 ~ 256 멀티) — 창 · 작업표시줄 · 바로가기 아이콘 |
| `make_shortcuts.bat` | 탐색기 바로가기 `STT Converter.lnk` · `VisemeNet Converter.lnk`(아이콘 = 각 `icon/*.ico`, 최소화 실행). `setup_*.bat` 끝에서 부른다. 절대 경로라 git 에 넣지 않는다(`/*.lnk`) |
| `app/core/engines/base.py` | `Engine` 인터페이스(`load` · `transcribe` → `TranscribeResult`) · `TranscribeOptions` · `EngineError(code)` · W24 휴리스틱(`suspects`) |
| `app/core/engines/faster_whisper_engine.py` | 1차 엔진. 모델 콤보 목록 `MODEL_CHOICES`. `qwen3_asr_engine.py` 가 생기면 `engines/__init__.py` 가 자동으로 콤보에 넣는다 |
| `app/core/device.py` | nvidia DLL 등록 → CUDA 장치 · compute type 조회 → `choose(preference)`. **강제 CPU**(`JUN_STT_FORCE_CPU` · `data/force_cpu.flag`) 면 CUDA 를 전혀 부르지 않는다 |
| `app/core/job.py` | `Job` · `preflight()` — E40 · E42 · E43, W25 ~ W27, 출력 경로 |
| `app/core/converter.py` | `run_batch()` — 로드(E44 → CPU 폴백) · 파일마다 VAD 결정(`VAD_AUTO_MIN_SECONDS = 10`) · W20 ~ W24 · 쓰기 · Stop |
| `app/core/normalize/{base,english,korean,japanese}.py` | §3 규칙. `normalize(text, language, user_dict, kana)` → `NormalizeResult(text, replaced, unresolved)` |
| `app/core/output_writer.py` | `.lab`(임시 파일 → 이름 바꾸기, `.bak`) · `.stt.json`(`format: jun_jali.stt/1`) |
| `app/core/settings.py` | `data/settings.json` · 사용자 사전 읽기 · 쓰기 |
| `app/ui/main_window.py` | 창 + `ConvertWorker`(QThread) + `UserDictDialog` |
| `app/ui/progress_dialog.py` | 진행 팝업(공용 `JUN_mod_progress_qt_v01`, 예상 시간 기반 보간) |

**시험** (`.venv_stt\Scripts\python.exe` 로, `PYTHONUTF8=1`):

```
tools\STT_Converter\tests\test_normalize.py                 정규화 65개 (§3 표의 예시 전부 · 한국어 수사 · 일본어 漢数字 · 영어 num2words · 사용자 사전)
tools\STT_Converter\tests\test_core.py        <작업폴더>    코어 24개 (가짜 엔진: 사전 검사 중단 · W20 ~ W25 · Skip/Overwrite/backup · VAD 자동 · E44 → CPU 폴백 · Stop · json 내용)
tools\STT_Converter\tests\test_ui.py          <작업폴더>    오프스크린 UI 23개 (실제 버튼 경로 · 진행 팝업 단계 · 단조 증가 · 100 % 뒤 닫힘 · 팝업 Stop · 한글 경로 · 사용자 사전 · 설정 복원)
tools\STT_Converter\tests\test_engine_smoke.py <작업폴더>   실제 모델 8개 — cli.py 로 coffee_xxxx.wav 를 CPU int8 변환 → .lab 에 coffee · W25 · 종료 코드 (models\ 에 모델이 있어야 한다)
tools\STT_Converter\tests\m0_transcribe.py    <wav>         실측 스크립트 — 손 대본이 옆에 있으면 CER / WER (계획 §11)
```

`test_core` · `test_ui` 는 모델 없이 `tests/fake_engine.py` 로 돈다(파일 이름 `*_empty` · `*_ja` · `*_num` · `*_rep` · `*_fail` 이 각 경고 경로).
`test_engine_smoke` 는 `JUN_STT_FORCE_CPU=1` 로 돌려도 된다(개발 PC).

---

## 9. 확인 기록 (2026-10-23, Windows 11 · 개발 PC)

- **개발 PC 는 CPU 로만 확인했다.** 이 PC 는 faster-whisper 의 CUDA 기동 중 강제 종료가 하루 3회 났고 원인은 PC 쪽이다([0130 §11 크래시 기록](0130_stt_converter_plan.md)). `data\force_cpu.flag` 를 두고 작업했다.
  GPU 경로(CUDA float16 로드 · 변환 · W21 폴백)는 크래시 전 M0-1 · M0-3 실측 로그로만 확인됐다.
- `setup_stt.bat` — `.python\`(VisemeNet 이 받아 둔 3.11.9) 공유 → `.venv_stt` → 패키지 → 모델(캐시 재사용) → 자가 검사 → **`SETUP OK`**. `--force --offline` 재구축도 통과.
  **크래시 사례**: `setup_stt.bat --force` 로 패키지를 설치하던 중 PC 가 꺼져, `.venv_stt` 안 파일 285개가 크기는 맞는데 **내용이 전부 0 바이트**로 남았다(NTFS 가 데이터를 쓰기 전에 꺼짐). 증상은 `SyntaxError: source code string cannot contain null bytes`. 저장소 · 모델(1.6 GB) · `.python\` 은 멀쩡했고 `--force --offline` 로 복구했다 → §1 실패표에 올렸다.
- 시험 4종(§8) 전부 통과: 정규화 65 · 코어 24 · UI 23 · 실제 모델 스모크 8.
- 복구 뒤 `setup_stt.bat` 에서 bat 버그 둘을 고쳤다: ① 파일이 LF 줄바꿈이라 cmd 의 `call :label` 복귀 위치가 어긋나 로그 첫머리에 다른 블록의 문장(`SETUP FAILED` · `'-m' is not recognized`)이 찍혔다 → CRLF 로 변환(`.gitattributes` 의 `*.bat eol=crlf` 가 체크아웃 때 보장) ② `else (` 블록 안의 따옴표 없는 `(no NVIDIA driver - CPU mode)` 가 블록을 일찍 닫아 GPU 가 있어도 `GPU: no NVIDIA driver found` 가 함께 찍혔다 → 괄호 제거. 둘 다 설치 결과에는 영향이 없었고 로그만 틀렸다.
- **미확인**: 실제 화면에 뜬 창(내 셸에서는 보이지 않는 세션) · 기준 사양 PC(A2000 · Windows 10, 계획 M0-8) · Python 3.14 만 있는 PC 의 전용 Python 다운로드 경로(M0-9 — `.python\` 이 이미 있어 이 PC 에서는 다운로드가 일어나지 않는다; VisemeNet `setup_env.bat` 의 같은 루틴은 [0050 §5](0050_converter_guide.md) 에서 모사 검증됨) · 예시 3 언어 `.lab` → MFA 정렬 통과(계획 M0-5) · `CUDA int8_float16` · Qwen3-ASR 2차 엔진.

---

## 자주 묻는 것

**인터넷이 꼭 필요한가?** — 설치 때만(패키지 · 모델). 변환은 오프라인이다. 인터넷 없는 PC 는 다른 PC 의 `models\` 를 복사하고 `setup_stt.bat --offline`.

**GPU 가 없는 노트북에서도 되나?** — 된다. `Device = Auto` 가 CPU int8 로 간다(`W21`). 36 초 음성이 7 초쯤(이 PC 기준) — 결과는 GPU 와 같다.

**첫 Convert 가 느리다** — 모델 로드(2 ~ 3 초, 캐시 없으면 다운로드 수 분) + 호출당 고정 5 초(CPU). 파일이 많아도 로드는 한 번이므로 **여러 파일을 한 번에** 넣는 편이 빠르다.

**대본이 틀렸다** — ① `W20` 이면 언어 선택 확인 ② 고유명사 · 약어는 **사용자 사전**(§3) ③ `Model = large-v3` 로 다시 ④ 그래도 틀리면 `.lab` 을 열어 손으로 고친다(원문 · 단어 시각은 `.stt.json`). 대본은 **실제로 말한 그대로**여야 MFA 가 맞는다.

**손으로 쓴 대본을 덮어 버리지 않나?** — 기본 `Existing = Skip` 이라 덮지 않는다(`W25`). 덮을 때도 `Overwrite with backup` 이면 `.lab.bak` 이 남는다.

**일본어 대본에 공백이 있는데 괜찮나?** — 괜찮다. VisemeNet Converter 가 MFA 에 넘기기 직전에 공백 · 줄바꿈을 뺀다(v01.04). 여기서는 사람이 읽기 좋게 남긴다.

**다른 모델을 써 보고 싶다** — `Model` 콤보(한국어 미세조정 모델은 CTranslate2 로 변환해 `Custom` 에 폴더 경로) 또는 `setup_stt.bat --model NAME`. 2차 엔진 Qwen3-ASR 은 계획(0130 D3 · T5)만 있고 아직 없다.

**지우려면?** — `.venv_stt\` · `models\` · `tools\STT_Converter\data\` 를 지운다. `.python\` 은 VisemeNet 변환기도 쓰므로 그쪽도 안 쓸 때만.
