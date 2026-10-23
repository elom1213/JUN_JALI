# 음성 → 대본 변환기 (STT Converter) — 툴 제작 계획서

> **작성** 2026-10-23 · 상태: **계획 (코드 전, 실측 M0 전)** · 대상: Windows 10 · 11, 로컬 GPU / CPU 폴백 — **대상 PC 두 종류**(§1-0): 개발 PC(RTX 5070 12 GB) 와
> 사용자가 지정한 **기준 사양 PC(Ryzen 9 3900X · RTX A2000 12 GB · RAM 32 GB 이상)**. 두 PC 모두에서 동작해야 완료다.
> **PC 에 Python 3.14 만 설치돼 있어도 동작해야 한다**(사용자 지정, 2026-10-23) — §1-0 Python 행 · 결정 **D14**.
> **요청**: 잡음 없는 **한국어 · 일본어 · 영어** 음성 wav 여러 개를 **그 언어의 텍스트 파일**로 변환하는 변환기. 딥러닝 모델 가능, **로컬에서** 돌아야 한다.
> 예시 입력: `JUN_JALI_Voice/0060_Vivian_voice/src_kr` · `src_jp` · `src_en`(wav + 손으로 쓴 대본 — 이 손 대본이 지금 변환기가 자동으로 만들어야 할 정답 예시다).
> 선행 문서: [0060 대본 + MFA 계획](0060_transcript_mfa_plan.md) · [0080 대본 보정 사용법](0080_transcript_correction_usage.md)(대본 규칙 §③) · [0030 툴 계획](0030_tool_plan.md)(변환기 뼈대 · bat 설치 방식).
> 관련 계획: `Maya_Python/JUN_All/docs/plans/A00560_JaliBatch_plan.md` P4(wav 폴더에서 변환까지 한 번에) — 이 툴이 그 앞 단계다.

---

## 0. 왜 필요한가 — 파이프라인에서의 자리

```
wav (44.1 kHz 16-bit)        ┌──────────────────────────────┐
     │                        │  ★ 이 계획: STT Converter      │
     ├──────────────────────▶ │  wav → <이름>.lab (대본, UTF-8) │  ← 지금은 사람이 손으로 쓴다 (src_*/ *.txt)
     │                        └──────────────────────────────┘
     ▼
VisemeNet Converter  Correct 모드  =  wav + 대본 → MFA 정렬(음소 구간) → 비짐 보정 → <이름>.txt(22열) · .phones.json
     ▼
A00540 JaliLipSync / A00560 JaliBatch  →  JALI 리그 키 · 클립 .mb
```

- 대본은 VisemeNet 보정의 **입력**이다. 지금은 wav 마다 사람이 받아쓰는데, 수십 개 이상이 되면 가장 느린 단계가 된다.
- 대본은 **"실제로 말한 그대로"** 여야 한다([0080 §③](0080_transcript_correction_usage.md)) — 원고가 아니라 **녹음을 받아쓴 것**. STT 가 바로 이 일을 한다.
  대본에 없는 말 · 빠진 말이 있으면 MFA 가 그 주변을 틀리게 맞춘다(실측: 6 초 불일치 → 모음 하나 2.3 초). 그래서 **정확도가 속도보다 중요**하다.
- 세 언어의 **인식 결과가 MFA 사전 · 분절기에 맞는 표기**여야 한다 — 숫자 · 기호는 읽는 대로, 일본어는 공백 없이, 한국어는 띄어쓰기 유지(§4).

---

## 1-0. 대상 PC 사양 — 둘 다에서 돌아야 한다

| | 개발 PC (이 PC) | **기준 사양 PC (사용자 지정, 2026-10-23)** | 계획에 주는 뜻 |
|---|---|---|---|
| CPU | — | AMD Ryzen 9 3900X (12코어 24스레드, Zen 2, **AVX2 · AVX-512 없음**) | CPU 폴백(int8) 은 CTranslate2 AVX2 경로 — 문제 없음. 24 스레드라 CPU 폴백도 실용 범위(turbo 모델 기준 실시간의 1 ~ 2배 예상, M0-8 실측) |
| GPU | NVIDIA GeForce RTX 5070 **12 GB** (Blackwell, sm_120, 드라이버 610) | NVIDIA **RTX A2000 12 GB** (Ampere **GA106, sm_86**, 3,328 CUDA 코어, 70 W, 메모리 288 GB/s) | **VRAM 이 둘 다 12 GB** → 모델 · compute_type 선택은 같다. A2000 은 Ampere 라 **int8 · float16 · bf16 모두 정식 지원**, Blackwell 호환 문제(§3-3) 가 없다. 연산 성능은 5070 의 약 1/4 ~ 1/3 → 변환 시간 기준은 **A2000 으로 잡는다** |
| RAM | — | 32 GB 이상 | 모델 로드(CPU 측 가중치 복사) · PyAV 디코드에 충분. CPU 폴백에서 large-v3 fp32 도 8 GB 안쪽 |
| 드라이버 | GeForce | RTX(구 Quadro) 드라이버 — CUDA 12.x 런타임 DLL 은 pip 로 가져오므로 **드라이버는 CUDA 12 이상을 지원하는 R525+ 면 된다** | `setup_stt.bat` 자가 검사가 `nvidia-smi` 드라이버 버전 · CUDA 버전을 로그에 적는다 |
| **Python** | 3.11 (시스템) + JUN_JALI `.python\` 없음 | **Python 3.14 만 설치된 PC 도 지원해야 한다**(사용자 지정, 2026-10-23). 새 Python 설치 관리자(`py` 가 3.14 만 알고, 없는 버전을 요청해도 **종료 코드 0**) 가정 | 툴은 **PC 의 Python 에 의존하지 않는다** — `setup_stt.bat` 가 `setup_env.bat` 와 같은 방식으로 **전용 Python 3.11.9**(python.org NuGet 패키지, SHA-256 검사, 약 17 MB)를 저장소 `.python\` 에 받아 `.venv_stt` 를 만든다(**D14**). 3.14 네이티브 설치는 보조 경로(§3-3 Python 행) |
| **OS** | Windows 11 Pro | **Windows 10 도 지원해야 한다**(사용자 지정, 2026-10-23) — 64-bit 21H2 이상 가정 | Python 3.11 · PySide6 6.12(Qt 6.8+, Win10 1809+) · CUDA 12.8 런타임 · CTranslate2 · PyTorch cu128 모두 Win10 64-bit 지원. **이 저장소가 Win10 PC 에서 이미 겪은 함정을 그대로 적용**: ① 새 Python 설치 관리자의 `py -3.11` 이 3.11 없이도 종료 코드 0 → 후보를 **실행해 출력으로** 판단 ② 사용자 이름이 한글이면 260자 경로 한계 · cp949 콘솔 → 설치 폴더 80자 제한 · `chcp 65001` ③ `PYTHONHOME` · `PYTHONPATH` · `CONDA_*` 격리(VisemeNet Converter v01.02 와 동일). 자가 검사 로그 첫머리에 `ver`(OS 빌드) 를 적어 Win10 · 11 을 구분한다 |

- **Windows 10 에서 조심할 것(추가)**: ⑤ Win10 기본 콘솔은 UTF-8 이 아니다 → bat 의 `chcp 65001` + Python 쪽 `PYTHONUTF8=1`, 로그 파일은 UTF-8 로 ⑥ 긴 경로 지원(`LongPathsEnabled`) 이 꺼져 있는 PC 가 많다 → Hugging Face 캐시(`models/`) 는 저장소 루트처럼 **짧은 경로**에, 모델 폴더 이름도 짧게(`snapshots/<hash>` 깊이 주의) ⑦ Windows 10 은 2025-10 이후 MS 일반 지원이 끝났지만 NVIDIA 드라이버 · CUDA 12.8 은 지원 중 — 드라이버가 오래된 PC 가 있을 수 있어 setup 이 **최소 드라이버 버전을 검사해 안내**한다 ⑧ 마지막 확인은 **실제 Win10 PC 에서**(M0-8 을 Win10 + A2000 PC 로 묶어서 하는 것이 가장 좋다, Q8).
- **설계 영향**: ① 기본 compute_type 은 두 GPU 공통으로 **float16**(A2000 에선 `int8_float16` 도 안전하므로 VRAM 여유가 필요할 때 옵션) ② Qwen3-ASR-1.7B bf16(≈ 4 GB 추정) 도 12 GB 안에 든다 — 다만 A2000 은 bf16 연산이 느리므로 Qwen 엔진은 A2000 에서 시간을 따로 잰다 ③ 진행 팝업의 예상 시간 가중치는 **A2000 실측값**으로(5070 은 더 빨라 일찍 끝날 뿐) ④ 기준 PC 에서 돌릴 수 없는 의존성(FlashAttention 소스 빌드 · vLLM) 은 **쓰지 않는다**.

## 1. 설계 결정 (권장안 — §10 질문에서 확인)

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| **D1** | 저장소 · 위치 | **`JUN_JALI/tools/STT_Converter/`** + `Run_STT_Converter.bat` + `setup_stt.bat` (VisemeNet Converter 와 나란히) | 대본은 MFA 보정의 입력이라 JALI 툴의 한 단계다. 사용자 용어 "JALI 툴 = JUN_JALI". 마야가 필요 없고 GPU 런타임(수 GB)이 필요하므로 Maya_Python 에 둘 이유가 없다. 공용 위젯은 `vendor/Framework`(이미 있음) |
| **D2** | 1차 엔진 | **faster-whisper + `large-v3-turbo`** (CTranslate2, Hugging Face `mobiuslabsgmbh/faster-whisper-large-v3-turbo`) | 세 언어를 한 모델이 받는다 · Windows pip 설치가 가장 단순(PyAV 동봉, ffmpeg 불필요) · `language=` 강제 · `word_timestamps` · VAD 내장 · int8/float16 로 VRAM 2 ~ 4 GB. 커뮤니티 벤치에서 일본어 CER 5 ~ 7 %, 한국어 CER 4 ~ 6 %(읽기 음성) |
| **D3** | 2차 엔진 (교체 가능) | **Qwen3-ASR-1.7B**(Apache 2.0, 2026-01 공개, 한 · 일 · 영 포함 30 언어) 를 **같은 인터페이스**로 끼울 수 있게 엔진 추상화(`engines/base.py`) | 한국어(KsponSpeech 9.6 vs Whisper 13.8 CER)에서 Whisper 보다 낫고 일본어는 데이터셋에 따라 엇갈린다(§3). **PyTorch cu128 + Blackwell** 조합을 실측해야 하므로 1차에 묶지 않는다 |
| **D4** | 언어 | **파일마다 `Language` 를 사람이 정한다**(폴더 단위 기본값 + 자동 감지는 보조) — `English` / `Korean` / `Japanese` | VisemeNet Converter 도 "한 번의 변환에 한 언어" 다. 자동 감지는 짧은 클립(1.5 초짜리가 있다)에서 틀리기 쉽다. 감지 결과가 선택과 다르면 **W20** 경고 |
| **D5** | 출력 파일 | **`<이름>.lab`** 기본(UTF-8, BOM 없음, 끝 줄바꿈 1개) · 옵션 `.txt` · 보조 `<이름>.stt.json`(세그먼트 · 단어 시각 · 확신도 · 엔진 · 모델 · 정규화 전 원문) | VisemeNet Converter 는 `.lab` 우선이고 `.txt` 는 결과 22열 txt 와 이름이 겹쳐 E34 를 낸다([0060 §10](0060_transcript_mfa_plan.md)). json 은 검수 · 재현용 |
| **D6** | 덮어쓰기 | **기본 Skip**(대본이 이미 있으면 건너뜀) / Overwrite / Overwrite with backup(`<이름>.lab.bak`) | 손으로 고친 대본을 자동 결과가 덮으면 안 된다 — `src_*` 의 손 대본이 바로 그 경우 |
| **D7** | 텍스트 정규화 | **언어별 후처리**(§4)를 거친 결과를 `.lab` 에 쓰고, 원문은 json 에 보존. 정규화는 **MFA 정렬용**이지 번역용 · 자막용이 아니다 | 숫자 `1등` 은 MFA 사전에 없다 → `일등`. 일본어 공백 제거는 VisemeNet Converter 가 이미 하므로 여기서는 **공백을 남겨 사람이 읽기 좋게** 두고 넘긴다(중복 처리 안 함) |
| **D8** | 입력 wav | 44.1 kHz 16-bit 모노를 **그대로 받는다**(Whisper 는 내부에서 16 kHz 로 리샘플). 스테레오 · 다른 샘플레이트도 **받는다**(VisemeNet 과 달리 E 가 아니라 INFO) | STT 는 리샘플에 둔감하다. 다만 결과 대본은 VisemeNet 에 들어가므로 wav 자체는 바꾸지 않는다 |
| **D9** | 환경 | **별도 `.venv_stt`**(Python 3.11, `requirements_stt.txt`) — VisemeNet `.venv`(tensorflow-cpu) · MFA conda 와 섞지 않는다 | CTranslate2 · torch 가 numpy · protobuf 버전을 끌어 TensorFlow 2.15 와 충돌할 수 있다. 0060 D 와 같은 원칙("MFA 는 따로") |
| **D10** | GPU 없을 때 · 기준 사양 | 자동 **CPU int8 폴백** + 로그에 알린다(`turbo` 모델은 CPU 에서도 실시간의 수 배). **성능 기준은 RTX A2000 PC(§1-0)** 로 잡고, 그 PC 에서 돌지 않는 의존성은 넣지 않는다 | 사용자 지정 기준 사양(Ryzen 9 3900X · A2000 12 GB · 32 GB) 과 GPU 없는 노트북 양쪽에서 돌아야 한다 |
| **D11** | 실행 형태 | `.bat` + `.venv_stt`(exe 안 만듦) — VisemeNet Converter 와 같다 | 모델 · CUDA 라이브러리가 수 GB 라 PyInstaller 로 묶을 수 없다 |
| **D12** | 헤드리스 | `tools/STT_Converter/cli.py`(폴더 · 언어 · 출력 옵션 → 종료 코드) 를 UI 와 **같은 코어**로 | A00560 P4 가 호출한다. UI 는 코어의 껍데기 |
| **D13** | 오류 정책 | VisemeNet Converter 와 **같은 사전 검사 → 하나라도 실패면 변환 0**(E40 ~ E49), 변환 중 파일 하나 실패는 **그 파일만 W** 로 넘기고 계속 | 변환 결과는 독립적(파일 하나가 다른 파일에 영향 없음) 이라 중단할 이유가 없다. 사전 검사는 환경 · 경로 문제를 미리 잡는 용도 |
| **D14** | **Python 공급 — PC 에 3.14 만 있을 때** | **`setup_stt.bat` 가 PC 의 Python 을 쓰지 않고 전용 Python 3.11.9 를 `.python\` 에 받아 `.venv_stt` 를 만든다**(`setup_env.bat` 의 `:probe` · `:download_python` 루틴을 그대로 가져옴). 순서: ① `.python\python.exe` 가 이미 있으면(VisemeNet `setup_env.bat` 이 받아 둔 것) **그걸 공유** ② 없으면 `py -3.11` · PATH 의 python 을 **실행해 출력(`JUNPY 3 11 64`)으로** 판단 ③ 둘 다 없으면 전용 3.11.9 다운로드(`--yes` 로 무확인). **PC 의 3.14 는 후보에 넣지 않는다**(기본) — `--use-system-python` 옵션으로만 시도 | 2026-10-20 Win10 · Python 3.14 PC 에서 **이미 검증된 방식**이다(VisemeNet 변환기). 3.11 은 faster-whisper · CTranslate2 · PySide6 · PyTorch cu128 · `qwen-asr` 가 모두 지원하고 **이 조합만 실측한다**. 3.14 네이티브는 휠은 대부분 있지만(§3-3) 검증 조합이 하나 더 늘고, PyTorch 는 2.15 부터 CUDA 12.x 휠을 끊어 Blackwell/Ampere 공통 cu128 조합을 3.14 에서 오래 유지하기 어렵다. 전용 Python 은 시스템을 건드리지 않고(`.python\` 폴더 삭제 = 제거) 두 PC · 두 OS 에서 같은 바이너리를 쓰게 한다 |

---

## 2. 최종 폴더 구조

```
JUN_JALI/
├─ .python/                             (.gitignore) 전용 Python 3.11.9 — setup_env.bat · setup_stt.bat 이 공유 (D14)
├─ .venv_stt/                           (.gitignore) STT 전용 가상환경 — .python\ 또는 PC 의 3.11 로 만든다
├─ setup_stt.bat                        T1  더블클릭 → Python 3.11 확보(D14) → .venv_stt + faster-whisper + 모델 받기 + 자가 검사
├─ Run_STT_Converter.bat                T2  더블클릭 → 변환기 창 (Run_VisemeNet_Converter.bat 와 같은 꼴)
├─ requirements_stt.txt                 고정 버전 (실측 뒤 적는다 — §6 M0)
├─ requirements_stt_qwen.txt            (선택) Qwen3-ASR 엔진 추가 설치
├─ models/                              .gitignore — 받은 모델 캐시 (HF_HOME 을 여기로)
├─ tools/
│  └─ STT_Converter/                    T2
│     ├─ __init__.py · launch.py
│     ├─ cli.py                         T4  헤드리스 (A00560 P4 가 부른다)
│     ├─ app/config/{version.py, app_meta.py}
│     ├─ app/core/
│     │  ├─ engines/
│     │  │  ├─ base.py                  Engine 인터페이스: load() · transcribe(wav, language) → Result(segments, words, lang, prob)
│     │  │  ├─ faster_whisper_engine.py 1차 (D2)
│     │  │  └─ qwen3_asr_engine.py      2차 (D3, 선택 설치 — import 실패면 콤보에서 비활성)
│     │  ├─ normalize/
│     │  │  ├─ base.py                  공통: 따옴표 · 말줄임표 · 전각 기호 통일, 줄바꿈 → 공백
│     │  │  ├─ english.py               숫자 → 단어(num2words en), 약어 · 통화 · 서수
│     │  │  ├─ korean.py                숫자 → 한자어 수사 / 고유어 수사(단위명사 규칙표), 영문 약어 → 한글 읽기표(사용자 사전)
│     │  │  └─ japanese.py              숫자 → かな/漢数字(num2words ja), 영문 → カタカナ 사용자 사전, 공백 처리
│     │  ├─ device.py                   GPU 감지(CUDA · VRAM) → compute_type 자동(float16 / int8_float16 / CPU int8)
│     │  ├─ job.py                      Job(wav, language, out_path) · 사전 검사 E40 ~ E49
│     │  ├─ converter.py                run_batch(jobs, engine, log, progress) · Skip/Overwrite/backup
│     │  ├─ output_writer.py            .lab / .txt / .stt.json
│     │  └─ settings.py                 마지막 폴더 · 언어 · 엔진 · 모델 · 옵션 (data/settings.json)
│     ├─ app/ui/
│     │  ├─ main_window.py              TSL(wav 목록) + Language/Engine/Model 콤보 + Output + Check / Convert + 로그 (공용 위젯)
│     │  ├─ progress_dialog.py          VisemeNet Converter 의 것을 그대로
│     │  └─ review_dialog.py            T3  (선택) 결과 대본을 wav 와 함께 듣고 고치는 간단 편집창
│     ├─ data/                          settings.json · startup_error.log · user_dict_{ko,ja,en}.json
│     ├─ icon/
│     └─ tests/                         test_normalize.py · test_core.py · test_ui.py · test_engine_smoke.py(모델 있을 때만)
└─ docs/0130_stt_converter_plan.md      이 문서 → 완료 후 0140 사용법 문서
```

`vendor/Framework` 의 TSL(`JUN_mod_tsl_qt_v01`) · 로그(`JUN_mod_log_qt_v01`) · 테마 · 메뉴 바 · 진행 팝업을 그대로 쓴다.

---

## 3. 모델 · 라이브러리 조사 (2026-10-23 기준)

### 3-1. 후보 요약 — 세 언어를 한 모델로

| 모델 | 공개 · 라이선스 | 한 · 일 · 영 | 크기 / VRAM | Windows 로컬 | 비고 |
|------|----------------|--------------|-------------|--------------|------|
| **Whisper large-v3-turbo** (OpenAI) via **faster-whisper** | 2024-10 · MIT | ✅ 99 언어 | 809 M · fp16 ≈ 2 GB, int8 ≈ 1 GB(가중치) + 작업 메모리 | ✅ pip, CUDA 12 DLL 만 | **1차 권장**. 디코더 4층으로 large-v3 보다 4 ~ 6배 빠르고 정확도 거의 같음(혼합 벤치 WER 7.75 vs 7.4) |
| Whisper large-v3 (원본 크기) | 2023-11 · MIT | ✅ | 1.55 B · fp16 ≈ 3 GB | ✅ | turbo 가 틀리는 파일만 **재시도용** |
| **Qwen3-ASR-1.7B / 0.6B** (Alibaba Qwen) | **2026-01-29** · Apache 2.0 | ✅ 30 언어(ko · ja 명시) | 1.7 B · bf16 ≈ 4 GB (실측 필요) | ⚠ PyTorch cu128 필요(Blackwell), FlashAttention 은 선택 | **2차**. 한국어 Kspon CER 9.6 (Whisper-v3 13.8), FLEURS-ja 5.5 (6.1) 로 우세, Reazon-ja 26 (15) 로 열세. 짝 모델 **Qwen3-ForcedAligner-0.6B**(ko · ja · en 타임스탬프, 5 분까지) |
| SenseVoice-Small (FunAudioLLM / FunASR) | 2024-07 · MIT(코드) | ✅ zh · yue · en · ja · ko | 234 M | ✅ ONNX / libtorch / GGUF | 속도 최강(비자기회귀 CTC). 정확도는 Whisper 가 한국어(5.6 vs 8.3 CER) · 일본어(10.3 vs 12.0) 에서 앞섰다는 벤치 → **속도 전용 보조** |
| Voxtral Mini Transcribe V2 (Mistral) | 2026-02 · 13 언어(ko · ja 포함) | ✅ | 4 B | ⚠ 오픈 가중치는 Realtime 모델만 확인됨, 배치 모델 공개 여부 미확인 | 후보에서 **보류** — 가중치 · 라이선스 확인 뒤 |
| NVIDIA Parakeet / Canary (NeMo) | Parakeet-tdt-0.6b-v3 25 유럽어 · Canary 4 언어 | ❌ ko · ja 없음(zh 변종만) | — | NeMo 는 Windows 설치가 어렵다 | 영어 전용으로는 최상위(Open ASR 6.34 WER) 지만 **세 언어 조건에 안 맞아 제외** |

### 3-2. 언어별 전문 모델 (한 언어가 계속 틀릴 때 교체)

| 언어 | 모델 | 공개 · 라이선스 | 정확도 (자기 보고) | 비고 |
|------|------|----------------|---------------------|------|
| 한국어 | **BuzzASR/korean** (Whisper large-v3 한국어 미세조정) | 2026-09 · MIT, EMNLP 2026 Findings | FLEURS+CV25 CER **4.61** (제로샷 v3 5.72), WER 13.74 | Whisper 구조라 `ct2-transformers-converter` 로 CT2 변환 → **faster-whisper 엔진에 그대로** 끼울 수 있다(변환 실측 필요) |
| 한국어 | TeamUNIVA/qwen3_asr_1.7b_ko_beta | Qwen3-ASR 한국어 미세조정 | 한국어 종합 CER 5.37 (기본 6.86) · Kspon · Zeroth · clova_call 포함 | Qwen 엔진(D3) 에 모델 이름만 바꿔 끼움 |
| 한국어 | kresnik/wav2vec2-large-xlsr-korean | CTC | Zeroth WER 4.74 / CER 1.78 (읽기 음성, 쉬운 벤치) | 구두점 · 띄어쓰기 없음 → MFA 입력으로는 오히려 무난하나 대화체에서 약함 |
| 일본어 | **kotoba-tech/kotoba-whisper-v2.0** (+ `-faster` CT2 판) | 2024-10 · Apache 2.0 | CER CV8 9.2 / JSUT 8.4 / Reazon 11.6 — large-v3 는 8.5 / 7.1 / 14.9 | large-v3 보다 6.3 배 빠르지만 **ReazonSpeech 도메인 밖에서는 v3 가 더 정확** → 속도 보조. v2.2 는 화자 분리 · 구두점 파이프라인 추가 |
| 일본어 | reazonspeech-nemo-v2 | NeMo | CV8 9.1 / JSUT 7.4 / Reazon 11.2 | NeMo 의존 → Windows 에서 **보류** |
| 일본어 | litagin/anime-whisper | Whisper 미세조정(게임 대사) | 게임 대사 5종 평균 CER 16.5(v3) 대비 개선 보고 | **캐릭터 연기 음성**(Vivian 같은) 에서 시험 가치 있음 |
| 영어 | distil-large-v3.5 · Parakeet-tdt-0.6b-v3 | MIT / CC-BY | Parakeet Open ASR 6.34 WER (Whisper turbo 7.83) | 영어만 쓰는 배치가 많아지면 faster-whisper 콤보에 `distil-large-v3.5` 추가(이미 `_MODELS` 에 있음) |

### 3-3. 런타임 · 라이브러리

| 항목 | 내용 | 주의 — 개발 PC(RTX 5070 · Blackwell sm_120) / 기준 PC(RTX A2000 · Ampere sm_86) |
|------|------|-----------------------------------------------|
| **Python 버전** | 툴 고정 **3.11**(D14). 참고 — 3.14 네이티브 휠 현황(2026-10): CTranslate2 4.8.1 분류자에 3.14 포함(Windows 휠은 "지원 버전 전부" 라는 유지자 답변, 파일명 미확인) · PySide6 **6.11.0(2026-03) 부터** 3.14 지원(6.10 은 `<3.14`) · PyTorch 는 3.9 ~ 3.14 지원이나 **2.15 부터 CUDA 12.x 휠 중단** · `qwen-asr` ≥ 3.9 · num2words · soundfile 은 순수/범용 휠 | 3.14 로 깔 수는 있어 보이지만 **실측 조합을 하나로** 유지하기 위해 기본은 전용 3.11. `--use-system-python` 으로 3.14 를 시도할 때는 `pip download --only-binary=:all: --python-version 3.14 --platform win_amd64` 로 휠 존재를 먼저 검사해 **휠이 없으면 전용 3.11 로 되돌아간다**(소스 빌드는 절대 하지 않음 — 기준 PC 에 컴파일러가 없다) |
| **faster-whisper** (SYSTRAN) | Python ≥ 3.9 · `pip install faster-whisper` · PyAV 동봉(ffmpeg 불필요) · `WhisperModel(name, device, compute_type)` · `transcribe(language=, beam_size=, word_timestamps=, vad_filter=, initial_prompt=, condition_on_previous_text=)` · `BatchedInferencePipeline` | 모델 이름 `large-v3-turbo` = `turbo` → `mobiuslabsgmbh/faster-whisper-large-v3-turbo` |
| **CTranslate2** | 4.6.3 (2026-01) CUDA 12.8 지원 · cuDNN 선택 사항으로 · **4.6.2 가 sm120 에서 INT8 비활성**, 4.7.0 이 INT8 텐서코어 패딩 수정(#1982) · 최신 4.8.3 (2026-10-13) | 5070: RTX 50 에서 int8 → `CUBLAS_STATUS_NOT_SUPPORTED` 보고가 있었다(수정 전 버전). **M0 에서 `float16` 과 `int8_float16` 둘 다 실측**, 실패하면 float16 고정. **A2000(Ampere) 은 CTranslate2 가 오래 지원한 세대라 int8 · float16 모두 문제 없음** — 기준 PC 쪽 리스크는 성능만 |
| CUDA DLL (Windows) | faster-whisper README 는 Windows 에 pip 경로를 주지 않는다 → ① `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*` 뒤 `os.add_dll_directory` 로 등록(코드에서) 또는 ② Purfview `whisper-standalone-win` 의 libs zip | ①을 기본으로 시험, `device.py` 가 DLL 폴더를 등록 |
| **PyTorch** (Qwen 엔진용) | Blackwell 은 **cu128 이상 빌드**만. `pip install torch --index-url https://download.pytorch.org/whl/cu128` — 같은 cu128 휠이 Ampere(sm_86) 도 포함하므로 **두 PC 에 하나의 requirements** 로 간다 | 5070: 설치 후 `torch.cuda.get_arch_list()` 에 `sm_120` 이 있는지 확인(M0-4). 스테이블 2.7.1+cu128 에서 sm_120 경고 보고 있음 → 안 되면 nightly. A2000: 문제 없음, bf16 은 Ampere 부터 지원되나 A2000 은 텐서코어가 적어 **느리다** → Qwen 1.7B 시간 실측(M0-8) |
| **qwen-asr** (PyPI 0.0.6, 2026-01-30) | Python ≥ 3.9(권장 3.12) · `Qwen3ASRModel.from_pretrained(..., dtype=bf16, device_map="cuda:0")` · `transcribe(audio, language="Korean")` · `forced_aligner=` 로 타임스탬프 | 3.11 로 깔리는지 M0-4 에서 확인 |
| **num2words** | `lang='ko'` · `'ja'` · `'en'` 지원 | 한국어는 **한자어 수사만**("일등" OK, "한 개" 류 고유어는 단위명사 규칙표로 보완 §4) |
| whisper.cpp (ggml-org) | v1.9.5 (2026-10-06) · Windows CUDA 바이너리는 릴리스마다 자산이 다름 | Python 없이 돌리는 **대안 경로**로만 기록 — 이 툴은 Python 코어가 필요하므로 채택 안 함 |
| Purfview **Faster-Whisper-XXL** | 모든 라이브러리 동봉 exe(r245.x) | 설치 없이 **사람이 바로 확인**해 볼 때 유용. Blackwell 지원 여부 미확인 |
| WhisperX · stable-ts | 단어 타임스탬프(wav2vec2 언어별 정렬 모델) | 정렬은 **MFA 가 담당**하므로 쓰지 않는다. 한국어 · 일본어 정렬 모델 의존이 불확실 |

### 3-4. 선택 근거 요약

1. **turbo 하나로 세 언어를 먼저 맞춘다.** 설치가 가장 단순하고 외부 벤치가 가장 많다. 한국어 · 일본어 모두 CER 한 자리(읽기 음성 기준).
2. **Qwen3-ASR 은 엔진 교체 1순위**로 설계에 자리를 비워 둔다. 한국어에서 Whisper 보다 분명히 낫다는 결과가 둘(Kspon · FLEURS-ko) 있고 Apache 2.0 이다. 다만 PyTorch + Blackwell 실측과 VRAM 측정이 끝나야 넣는다.
3. 언어별 미세조정 모델(BuzzASR/korean · kotoba-whisper) 은 **Whisper 구조라 1차 엔진에 모델 이름만 바꿔 끼울 수 있다** — 콤보 항목으로 열어 두고 Vivian 음성으로 비교한다(M3).

---

## 4. 텍스트 정규화 — MFA 가 받을 수 있는 대본으로

STT 결과는 자막용 표기(숫자 · 기호 · 영문 약어)다. MFA 사전은 **발음대로 쓴 단어**만 안다(없는 단어는 G2P 폴백 — 숫자 · 기호는 G2P 도 못 읽는다).

| 언어 | 규칙 | 예 (STT 결과 → .lab) | 근거 · 주의 |
|------|------|----------------------|-------------|
| 공통 | 줄바꿈 → 공백, 연속 공백 1개, 전각 기호 → 반각, 따옴표 · 괄호 · 말줄임표 제거(문장부호 `. , ? !` 는 남김 — MFA 가 무시) | `"오늘…"` → `오늘` | MFA 는 구두점을 지우고 단어만 본다 |
| 영어 | 숫자 → 단어(`num2words`), `%` → percent, `$5` → five dollars, 서수 `1st` → first, 약어는 사용자 사전(`UE` → U E) | `2018` → `twenty eighteen`(연도 규칙) | [0080 §③](0080_transcript_correction_usage.md) 의 예시 그대로 |
| 한국어 | 숫자 → 수사. **단위명사 규칙표**로 고유어/한자어 선택(`1등` → 일등, `3개` → 세 개, `10시` → 열 시, `2026년` → 이천이십육 년), 영문자 → 한글 읽기 사용자 사전(`KWI` → 케이더블유아이), 띄어쓰기 **유지**(korean_mfa 는 mecab 으로 다시 분절) | `1등이 될 거예요` → `일등이 될 거예요` | Whisper 한국어는 숫자를 아라비아로 쓰는 경향 — 예시 `src_kr` 에도 `1등` 이 있다 |
| 일본어 | 숫자 → 漢数字 또는 かな(`num2words ja` → 사용자 선택, 기본 かな), 영문 → カタカナ 사용자 사전, **공백은 남긴다**(제거는 VisemeNet Converter 가 한다, v01.04) | `3時` → さんじ | 한자 읽기 오류는 MFA(Sudachi) 쪽 리스크([0060 Q4](0060_transcript_mfa_plan.md)) → 옵션 `Kana output`(pykakasi 로 전부 かな) 를 둔다 |

- 사용자 사전 `data/user_dict_{ko,ja,en}.json` = `{"KWI": "케이더블유아이"}` 꼴, UI 에서 편집(간단 표).
- 정규화 전 원문은 `.stt.json` 의 `raw_text` 에 그대로 — 사람이 검수할 때는 원문이 읽기 쉽다.

---

## 5. 변환기 동작

### 5-1. UI (VisemeNet Converter 와 같은 배치)

```
┌ STT Converter v01.00 ───────────────────────────────────────────────┐
│ WAV files                                   [Add Files] [Add Folder] │
│ ┌──────────────────────────────────────────┐ [Remove] [Clear]        │
│ │ 0010_vivian_kr.wav       (35.9 s)        │                        │
│ │ 0020_vivian_jp.wav       (45.8 s)        │                        │
│ └──────────────────────────────────────────┘                        │
│ Language [Korean ▼]   Engine [faster-whisper ▼]  Model [large-v3-turbo ▼] │
│ Device   [Auto: CUDA float16 ▼]   Beam [5]   □ Kana output (ja)       │
│ Output   [ (next to WAV) ............ ] [Browse] [Open]  Ext [.lab ▼] │
│ Existing [Skip ▼]   □ Write .stt.json   □ Review after convert        │
│                                   [Check Files]  [Convert]           │
│ ── Log ─────────────────────────────────────────────────────────────  │
│ [INFO] device: NVIDIA GeForce RTX 5070 (12 GB) - float16             │
│ [OK] 0010_vivian_kr.wav -> 0010_vivian_kr.lab  (6 segments, 12.3 s)  │
└──────────────────────────────────────────────────────────────────────┘
```

- **Check Files**: 변환 없이 사전 검사 + 기존 대본 유무 + 추정 시간.
- **Convert**: 모델 로드(처음 한 번, 수 초 ~ 수십 초) → 파일마다 변환 → 정규화 → 쓰기. 진행 팝업은 VisemeNet Converter 의 것(Stop = 현재 파일 뒤 중단).
- **Review** (T3, 선택): 변환 뒤 wav 재생 + 세그먼트별 텍스트 편집 → 저장. 1차에서는 "탐색기에서 열기" 로 대체 가능(§10 Q4).

### 5-2. 추론 옵션 (기본값)

| 옵션 | 기본 | 이유 |
|------|------|------|
| `language` | UI 선택(강제) | D4. 자동 감지 결과는 `detected_language` · 확률로 json 에 기록, 다르면 W20 |
| `beam_size` | 5 | 정확도 우선(요청). 속도가 문제면 1 |
| `vad_filter` | **True**, `min_silence_duration_ms=500` | 앞뒤 무음(예시 kr 은 4.5 초 무음으로 시작)에서 **환각**(없는 말 생성)을 막는다 |
| `condition_on_previous_text` | **False** | 반복 환각 방지. 클립이 짧아 문맥 이득이 없다 |
| `word_timestamps` | True | json 에만 — 검수 · 나중에 MFA 실패 구간 비교용 |
| `initial_prompt` | 언어별 짧은 문장(선택) | 한국어 띄어쓰기 · 일본어 구두점 스타일을 유도. 효과는 M3 에서 판단 |
| `compute_type` | CUDA: float16 (int8_float16 은 실측 뒤) · CPU: int8 | §3-3 Blackwell 주의 |
| `temperature` | 0 → 실패 시 (0.2, 0.4) 폴백 | faster-whisper 기본 폴백 유지 |

### 5-3. 오류 · 경고 코드 (VisemeNet Converter 번호와 겹치지 않게 E40 ~, W20 ~)

| 코드 | 뜻 | 처리 |
|------|-----|------|
| E40 | 환경 없음(`.venv_stt` · faster-whisper import 실패) | 시작 때 메시지 박스 → `setup_stt.bat` |
| E41 | 모델 캐시 없음 + 오프라인 | 사전 검사 중단, `setup_stt.bat --model` 안내 |
| E42 | wav 를 못 읽음(손상 · 0 초) | 그 파일 사전 검사 실패 → 전체 중단(D13) |
| E43 | 출력 폴더 쓰기 불가 | 중단 |
| E44 | CUDA 초기화 실패(DLL · 드라이버) | **중단하지 않고** CPU 폴백 + W21 |
| W20 | 감지 언어 ≠ 선택 언어 | 결과는 쓰되 로그에 확률과 함께 |
| W21 | CPU 폴백 | 시간이 오래 걸림을 알림 |
| W22 | 빈 결과(음성 없음으로 판정) | `.lab` 안 씀, json 만 |
| W23 | 정규화에서 처리 못 한 토큰(숫자 · 기호 · 영문자가 남음) | 토큰과 위치를 로그에 — 사용자 사전에 추가하라는 뜻 |
| W24 | 반복 · 환각 의심(같은 n-gram 3회 이상 · `no_speech_prob` 높음 · 압축비 2.4 초과) | 로그 + json `suspect` 플래그 |
| W25 | 기존 대본 있어 Skip | — |

---

## 6. 실측 항목 M0 — 코드 전에 확정할 것 (이 PC)

| # | 항목 | 방법 | 통과 기준 |
|---|------|------|-----------|
| **M0-1** | faster-whisper + CUDA DLL(pip `nvidia-*-cu12`) 가 RTX 5070 에서 뜨는가 | 스크래치 venv, `WhisperModel("large-v3-turbo", "cuda", "float16")` 로 `src_en/…_01.wav` | 결과 텍스트 · 로그에 CUDA 오류 없음 |
| **M0-2** | `int8_float16` 이 Blackwell 에서 되는가 | 같은 파일, compute_type 바꿔 | 되면 기본값 후보, `CUBLAS_STATUS_NOT_SUPPORTED` 면 float16 고정 + 문서화 |
| **M0-3** | 세 언어 기본 정확도 | `src_kr` · `src_jp` · `src_en_full` 3개 → 손 대본과 CER 비교(jiwer) | 각 언어 CER < 10 %(연기 음성이라 벤치보다 나쁠 수 있음). 틀린 유형 기록 |
| **M0-4** | Qwen3-ASR 설치 가능성 | 스크래치 venv Python 3.11 + torch cu128 + `qwen-asr`, `torch.cuda.get_arch_list()` 에 `sm_120`, 1.7B bf16 VRAM 측정 | 돌면 D3 2차 엔진 일정 확정, 안 돌면 1차에서 제외하고 사유 기록 |
| **M0-5** | 정규화 → MFA 통과 | M0-3 결과를 정규화해 `.lab` 로 두고 VisemeNet Converter Correct 모드 실행 | E33 · W12 없이 정렬, `.phones.json` 생성. 남는 미처리 토큰(W23) 목록 |
| **M0-6** | 속도 | 세 파일(총 111 초) 변환 시간, 모델 로드 시간 | 로드 < 30 초, 변환 실시간의 1/5 이하(GPU) — 진행 팝업 가중치 산정 |
| **M0-7** | CPU 폴백 | `device="cpu", compute_type="int8"`, 같은 파일 | 결과 동일성 · 시간 기록(다른 PC 안내용) |
| **M0-9** | **Python 3.14 만 있는 상황**에서 `setup_stt.bat` 가 전용 3.11 을 받아 끝까지 가는가 | 이 PC 에서는 3.11 이 있으므로 `setup_stt.bat --no-system-python`(후보 탐색을 건너뛰고 바로 다운로드 경로) 로 **모사**, 가능하면 사용자의 3.14 PC 에서 실제 더블클릭(Q9) | `.python\` 생성 → `.venv_stt` → pip 설치 → 자가 검사(1.5 초 wav 변환) 까지 **질문 한 번(Y) 외 입력 없이** 통과. `setup_env.bat` 이 이미 받아 둔 `.python\` 이 있으면 **다시 받지 않는다**. `PYTHONHOME` · `PYTHONPATH` 가 3.14 를 가리키는 PC 에서도 import 오류 없음(격리 변수 확인) |
| **M0-8** | **기준 사양 PC(Ryzen 9 3900X · RTX A2000 12 GB · 32 GB, 가능하면 Windows 10)** 에서 M0-1 · M0-2 · M0-6 · M0-7 재실행 (+ M0-4 가 통과했으면 Qwen 1.7B 시간 · VRAM) | `setup_stt.bat` 를 그 PC 에서 더블클릭 → 자가 검사 → 같은 3 파일 변환 | 설치 한 번에 성공, **GPU float16 로 3 파일(111 초) 변환 < 60 초**, CPU int8 폴백도 끝까지 돈다, VRAM 피크 < 8 GB. 이 값이 진행 팝업 가중치 · 문서의 "예상 시간" 이 된다. **이 PC 가 없으면 사용자가 로그(`setup_stt.log` · 변환 로그)를 보내 주는 방식으로** |

---

## 7. 작업 순서

| 단계 | 내용 | 완료 조건 |
|------|------|-----------|
| **M0** | §6 실측 7개 — 결과를 이 문서 §11 에 적는다 | 엔진 · compute_type · requirements 고정 |
| **T1** `setup_stt.bat` | `setup_env.bat` 복제 → **Python 3.11 확보(D14: `.python\` 공유 → PC 3.11 탐색 → 전용 3.11.9 다운로드)** → `.venv_stt` · `requirements_stt.txt` · CUDA DLL(pip `nvidia-*-cu12`) · 모델 선다운로드(`huggingface_hub` → `models/`) · 자가 검사(1.5 초 wav 변환) · 옵션 `--yes` `--force` `--nopause` `--no-system-python` `--use-system-python` `--qwen` `--offline` | 더블클릭 한 번으로 끝(3.14 만 있는 PC 는 Y 한 번), 재실행 안전, 로그 `setup_stt.log` 첫머리에 OS 빌드 · GPU · 드라이버 · 어느 Python 을 썼는지 |
| **T2** 코어 + UI | `engines/faster_whisper_engine` · `normalize/*` · `converter` · `output_writer` · `main_window` | `tests/` 통과(정규화 표 케이스 전부, UI 오프스크린), 예시 3 언어 변환 → VisemeNet Converter 통과 |
| **T4** `cli.py` | `python cli.py <folder|wav...> --language Korean --ext lab --existing skip --json` → 종료 코드 0/1, 로그 stdout | A00560 P4 가 그대로 호출 가능 |
| **T3** Review 창(선택) | 세그먼트 표 + 재생 + 저장 | Q4 답에 따라 |
| **T5** Qwen 엔진(선택) | `qwen3_asr_engine.py` + `requirements_stt_qwen.txt` + Model 콤보에 `TeamUNIVA/..._ko_beta` | M0-4 통과했을 때만. 세 언어 CER 비교표를 §11 에 |
| **문서** | `docs/0140_stt_converter_guide.md`(설치 · 사용법 · 오류표) · README 표 · Maya_Python WORKLOG 한 줄 | — |

---

## 8. 리스크

| 리스크 | 영향 | 대비 |
|--------|------|------|
| Blackwell(sm_120) 에서 CTranslate2 int8 · PyTorch 호환 (개발 PC) | 설치가 안 되거나 느림 | M0-1 · 2 · 4 를 코드 전에. float16 고정 · CPU 폴백 |
| **기준 PC(RTX A2000)** 의 연산 성능이 개발 PC 의 1/4 ~ 1/3 | 개발 PC 에서 맞춘 "예상 시간" 이 틀림, Qwen 1.7B 가 체감상 느릴 수 있음 | 시간 기준은 A2000 실측(M0-8). 느리면 콤보 기본을 turbo + `int8_float16` 으로. RTX 드라이버(구 Quadro) 는 CUDA 12 지원 버전인지 setup 이 확인 |
| 기준 PC 에 모델을 받을 네트워크가 없을 수 있음 | 설치 중단 | `models/` 캐시 폴더를 통째로 복사해 쓰는 경로 · `setup_stt.bat --offline` |
| **Windows 10** 고유 — 긴 경로 꺼짐 · cp949 콘솔 · 새 Python 설치 관리자(3.14) 의 `py` 동작 · 오래된 드라이버 | 설치 실패 · 모델 캐시 경로 오류 · 로그 깨짐 | §1-0 ⑤ ~ ⑧. `setup_env.bat` 가 Win10 PC 에서 이미 해결한 방식(실행해서 버전 판단 · 전용 Python 3.11.9 · 80자 경로) 을 `setup_stt.bat` 에 그대로 가져온다 |
| **PC 에 Python 3.14 만 있음**(D14) — `py -3.11` 이 성공한 척(종료 코드 0) · `PYTHONHOME`/`PYTHONPATH` 가 3.14 표준 라이브러리를 가리킴 · NuGet 다운로드가 막힌 네트워크 | 잘못된 Python 으로 venv 를 만들거나 첫 import 에서 죽음 · 다운로드 실패로 설치 중단 | 후보는 **실행해 출력으로** 판단, 격리 변수(VisemeNet v01.02 와 동일), `.python\` 공유로 다운로드 1회. 다운로드가 막히면 **E40 안내에 두 길**: ① `.python\` 폴더를 다른 PC 에서 복사 ② python.org 3.11.9 설치. `.venv_stt` 는 만든 Python 의 절대 경로를 박으므로 **폴더 이동 뒤에는 `--force`** (Run 배치가 `import PySide6` 로 먼저 검사해 안내) |
| **연기 음성**(감탄 · 외침 · 속삭임)은 벤치(읽기 음성)보다 인식률이 낮다 | 대본 오류 → MFA 틀어짐 | beam 5 · VAD · 모델 교체 콤보 · Review 창 · `.stt.json` 의 확신도로 낮은 구간 표시 |
| 짧은 클립(1.5 초) 환각 · 언어 오감지 | 엉뚱한 문장 | 언어 강제(D4) · W24 휴리스틱 · 빈 결과는 W22 |
| 숫자 · 고유명사 표기(`파에톤`, `KWI`) | MFA 사전 밖 → G2P 추측 | 사용자 사전 · W23 로 남는 토큰 보여 주기 |
| 일본어 한자 읽기(MFA 측) | 음소 오류 | `Kana output` 옵션(pykakasi) |
| 모델 다운로드(수 GB) 환경 | 오프라인 PC 설치 실패 | `models/` 캐시를 복사해 쓰는 경로(`HF_HOME`) 문서화, E41 |
| 라이선스 | — | Whisper · faster-whisper · Qwen3-ASR · BuzzASR · kotoba 모두 MIT / Apache 2.0. VisemeNet 쪽 GPLv3 문제와 무관 |

---

## 9. 참고 자료

### 모델
- OpenAI Whisper — https://github.com/openai/whisper (large-v3-turbo 공개 노트 포함, MIT)
- faster-whisper (SYSTRAN, CTranslate2 기반) — https://github.com/SYSTRAN/faster-whisper · 모델 매핑 `faster_whisper/utils.py` · turbo CT2 가중치 https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo
- CTranslate2 릴리스(CUDA 12.8 · sm120 INT8) — https://github.com/OpenNMT/CTranslate2/releases
- **Qwen3-ASR** — https://github.com/QwenLM/Qwen3-ASR · 블로그 https://qwen.ai/blog?id=qwen3asr · 기술 보고서 https://arxiv.org/abs/2601.21337 · HF https://huggingface.co/Qwen/Qwen3-ASR-1.7B · PyPI `qwen-asr` https://pypi.org/project/qwen-asr/
- BuzzASR/korean (Whisper-v3 한국어 미세조정, MIT) — https://huggingface.co/BuzzASR/korean (논문 arXiv:2609.09554)
- TeamUNIVA/qwen3_asr_1.7b_ko_beta — https://huggingface.co/TeamUNIVA/qwen3_asr_1.7b_ko_beta
- kresnik/wav2vec2-large-xlsr-korean — https://huggingface.co/kresnik/wav2vec2-large-xlsr-korean
- kotoba-whisper v2.0 / v2.2 (일본어, Apache 2.0) — https://huggingface.co/kotoba-tech/kotoba-whisper-v2.0 · https://huggingface.co/kotoba-tech/kotoba-whisper-v2.2 · CT2 판 `kotoba-tech/kotoba-whisper-v2.0-faster`
- ReazonSpeech nemo v2 — https://huggingface.co/reazon-research/reazonspeech-nemo-v2
- litagin/anime-whisper(게임 대사 일본어) — https://huggingface.co/litagin/anime-whisper
- SenseVoice (FunAudioLLM) — https://github.com/FunAudioLLM/SenseVoice · FunASR https://github.com/modelscope/FunASR
- NVIDIA Parakeet / Canary(영어 · 유럽어 참고) — https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
- Voxtral (Mistral) — https://mistral.ai/news/voxtral · HF `mistralai` 조직(ko · ja 가 들어간 Transcribe V2 의 오픈 가중치 여부 확인 필요)
- 벤치마크 참고 — Open ASR Leaderboard https://huggingface.co/spaces/hf-audio/open_asr_leaderboard · Whisfusion 논문(ko · ja 표) https://arxiv.org/abs/2508.07048 · 일본어 ASR 비교 https://japanese-asr-readme.static.hf.space/ · Qwen3-ASR vs Whisper FLEURS 30 언어 https://whispernotes.app/blog/qwen3-asr-vs-whisper · 언어별 로컬 모델 표 https://models.handy.computer/languages/ko

### 런타임 · 도구
- PyTorch cu128(Blackwell) — https://pytorch.org/get-started/locally/ · sm_120 논의 https://discuss.pytorch.org/t/pytorch-support-for-sm120/216099 · CUDA 12.x 휠 중단 공지(2.15 부터, Python 3.10 제거) https://dev-discuss.pytorch.org/t/notice-python-3-10-support-is-being-removed-from-pytorch-2-15-2-14-is-the-last-release-with-3-10-wheels/3440
- Python 3.14 호환 참고 — PySide6 6.11 릴리스(3.14 지원 시작) https://www.qt.io/blog/qt-for-python-release-6.11-is-out · CTranslate2 설치 문서 https://opennmt.net/CTranslate2/installation.html · 전용 Python 3.11.9 NuGet 패키지 https://www.nuget.org/api/v2/package/python/3.11.9 (`setup_env.bat` 이 쓰는 것, SHA-256 `9283876d…`)
- whisper.cpp — https://github.com/ggml-org/whisper.cpp (Python 없는 대안) · Purfview Faster-Whisper-XXL(올인원 exe) — https://github.com/Purfview/whisper-standalone-win
- WhisperX — https://github.com/m-bain/whisperX · whisper-timestamped — https://github.com/linto-ai/whisper-timestamped (쓰지 않는 이유 §3-3)
- num2words — https://pypi.org/project/num2words/ · pykakasi(일본어 かな 변환) — https://codeberg.org/miurahr/pykakasi · jiwer(CER/WER) — https://github.com/jitsi/jiwer
- Montreal Forced Aligner 3 — https://montreal-forced-aligner.readthedocs.io/ · 모델 벤치 https://mfa-models.readthedocs.io/en/latest/benchmarks/index.html

### 이 저장소
- 변환기 뼈대 · bat 설치 방식: [0030](0030_tool_plan.md) · `setup_env.bat` · `Run_VisemeNet_Converter.bat` · `tools/VisemeNet_Converter/app/core/{converter,aligner}.py`
- 대본 규칙 · MFA 실측 함정(일본어 공백 · 넓은 beam · W12): [0060 §10](0060_transcript_mfa_plan.md) · [0080 §③](0080_transcript_correction_usage.md)

---

## 10. 확인 질문 (답이 없으면 권장안으로 진행)

| # | 질문 | 권장 | 영향 |
|---|------|------|------|
| **Q1** | 툴 위치 — `JUN_JALI/tools/STT_Converter`(D1) 가 맞나, 아니면 Maya_Python `A005xx` standalone 으로? | JUN_JALI | 폴더 · bat · 문서 번호 |
| **Q2** | 1차 엔진 turbo 로 시작하고 Qwen3-ASR 은 M0-4 결과에 따라 2차로? 아니면 처음부터 둘 다? | turbo 먼저 | T5 일정 |
| **Q3** | 출력 기본 확장자 `.lab`(권장) vs `.txt`(지금 `src_*` 가 쓰는 꼴) | `.lab` | E34 충돌 회피 |
| **Q4** | Review 창(T3) 을 1차에 넣나 | **1차에서는 빼고** 탐색기 열기 + `.stt.json` 확신도만 | 일정 |
| **Q5** | 한국어 숫자 읽기 — 단위명사 규칙표 기본값(고유어 vs 한자어)을 어디까지 다루나 | 자주 쓰는 단위 20개 표 + 나머지는 한자어 + W23 | normalize/korean.py 범위 |
| **Q6** | 일본어 출력 — 한자 혼용(STT 그대로) 기본 vs かな 전용 | 한자 혼용 기본, `Kana output` 옵션 | pykakasi 의존 추가 |
| **Q7** | 테스트 음성 — `0060_Vivian_voice` 3 언어 외에 **대화체 · 짧은 외침** 샘플이 더 있나 | 있으면 M0-3 에 추가 | 정확도 기준값 |
| **Q8** | 기준 사양 PC(A2000) 에 직접 접근할 수 있나, 아니면 사용자가 그 PC 에서 bat 을 돌리고 로그를 전달하나 | 로그 전달 방식도 되게 `setup_stt.bat` 가 환경 요약(GPU · 드라이버 · CUDA · RAM · 자가 검사 시간)을 로그 첫머리에 쓴다 | M0-8 진행 방법 |
| **Q9** | Python 3.14 만 있는 PC — 전용 3.11 다운로드(D14, 권장) 로 가는 데 동의하나, 아니면 3.14 네이티브 설치를 1차 목표로? 그 PC 가 기준 사양(A2000 · Win10) PC 와 같은 PC 인가 | 전용 3.11. 같은 PC 면 M0-8 과 M0-9 를 한 번에 | D14 · M0-9. 3.14 네이티브를 고르면 PySide6 ≥ 6.11 · PyTorch cu128 ≤ 2.14 로 핀이 바뀌고 실측 조합이 둘로 늘어난다 |

---

## 12. 작업 재개 절차 — 컴퓨터가 꺼져도 이 문서만 보고 이어서 한다

**원칙**: 단계 하나가 끝날 때마다 ① 코드 · 문서를 `dev` 브랜치에 **커밋**하고 ② 아래 §12-1 체크리스트의 그 줄을 `[x]` 로 바꿔 **같은 커밋에 넣는다** ③ 실측값은 §11 표에 바로 적는다.
그래서 재개할 때는 `git log` 가 아니라 **이 문서의 체크리스트가 진실**이다(커밋 안 된 작업 트리 변경은 잃은 것으로 본다).

### 12-1. 진행 상태 체크리스트

- [x] 계획서 작성 · README 등록 (2026-10-23, `c044fea` · `6473649`)
- [x] 브랜치 정리: `dev` = `main` fast-forward, 이후 모든 작업은 **`dev`** 에서 (2026-10-23)
- [ ] **M0-1** faster-whisper + CUDA DLL 이 RTX 5070 에서 뜬다 (`.venv_stt`, float16)
- [ ] **M0-2** `int8_float16` 가능 여부
- [ ] **M0-3** 세 언어 CER (src_kr · src_jp · src_en_full vs 손 대본)
- [ ] **M0-5** 정규화 → `.lab` → VisemeNet Converter Correct 모드 통과
- [ ] **M0-6** 속도 · 모델 로드 시간
- [ ] **M0-7** CPU int8 폴백
- [ ] **M0-4** Qwen3-ASR 설치 가능성 (torch cu128 · sm_120) — 선택
- [ ] **T1** `setup_stt.bat` · `requirements_stt.txt` · `Run_STT_Converter.bat` (+ M0-9 모사 `--no-system-python`)
- [ ] **T2-a** `app/core/engines/` (base · faster_whisper_engine) + `device.py`
- [ ] **T2-b** `app/core/normalize/` (base · english · korean · japanese) + `tests/test_normalize.py`
- [ ] **T2-c** `app/core/{job,converter,output_writer,settings}.py` + `tests/test_core.py`
- [ ] **T2-d** `app/ui/main_window.py` (+ progress_dialog 복제) + `launch.py` + `tests/test_ui.py`
- [ ] **T2-e** 예시 3 언어 실제 변환 → `.lab` → MFA 통과 (`tests/test_engine_smoke.py`)
- [ ] **T4** `cli.py` + 종료 코드 · A00560 호출 형식 확정
- [ ] **문서** `docs/0140_stt_converter_guide.md` · README 표 · Maya_Python `JUN_All/docs/WORKLOG.md` 한 줄
- [ ] **T5** Qwen3-ASR 엔진 (M0-4 통과 시) — 선택
- [ ] **M0-8** 기준 PC(A2000 · Win10) 실측 — 사용자 PC, 로그 전달
- [ ] **M0-9** Python 3.14 만 있는 PC 실제 확인 — 사용자 PC

### 12-2. 재개할 때 하는 일 (순서대로)

1. `cd JUN_JALI` → `git status` · `git branch` — **`dev`** 인지, 미커밋 변경이 있는지 본다. 미커밋 변경은 내용을 확인한 뒤 이어 쓰거나 버린다(절반만 된 파일은 보통 버리고 체크리스트의 그 단계를 처음부터).
2. §12-1 에서 **첫 `[ ]` 줄**이 다음 할 일이다. 그 단계의 산출물 위치는 §2 폴더 구조, 통과 기준은 §6(M0) · §7(T) 표.
3. 환경: `.venv_stt\Scripts\python.exe -c "import faster_whisper, ctranslate2; print(ctranslate2.get_cuda_device_count())"` 가 1 이상이면 환경은 살아 있다. 0 이거나 import 실패면 `setup_stt.bat --force`(T1 전이면 §12-3 수동 명령).
4. 모델 캐시: `models\` 에 `models--mobiuslabsgmbh--faster-whisper-large-v3-turbo` 가 있으면 다운로드는 끝난 것(약 1.6 GB). 없으면 첫 변환 때 받는다(`HF_HOME` 을 `models\` 로).
5. 테스트: `.venv_stt\Scripts\python.exe -m pytest tools\STT_Converter\tests -q` (T2 이후). M0 단계면 §12-3 의 스크립트.
6. 끝나면 체크리스트 `[x]` + §11 실측값 + 커밋 — **푸시는 사용자가 그 턴에 요청할 때만**.

### 12-3. T1 전 수동 환경 명령 (M0 용, `setup_stt.bat` 이 이걸 자동화한다)

```bat
cd JUN_JALI
py -3.11 -m venv .venv_stt
.venv_stt\Scripts\python.exe -m pip install -U pip
.venv_stt\Scripts\python.exe -m pip install faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" jiwer num2words soundfile huggingface_hub PySide6==6.12.0
set HF_HOME=%CD%\models
```

M0 스크립트는 `tools/STT_Converter/tests/m0_*.py` 에 두고 커밋한다(실측 재현용). 결과는 §11.

---

## 11. 실측 기록 (M0 — 아직 없음)

| # | 날짜 | 결과 |
|---|------|------|
| M0-1 ~ M0-7 (개발 PC, RTX 5070) | — | 코드 전 실측 뒤 채운다 |
| M0-8 (기준 PC, Ryzen 9 3900X · RTX A2000 12 GB · 32 GB) | — | 〃 — 변환 시간 · VRAM 피크 · CPU 폴백 시간 |
| M0-9 (Python 3.14 만 있는 PC / `--no-system-python` 모사) | — | 〃 — 전용 3.11 다운로드 → 자가 검사 통과 여부 |
