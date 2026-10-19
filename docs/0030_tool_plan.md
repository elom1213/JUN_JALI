# 툴 제작 계획서 — 환경 설치 · 변환기 · Maya 키 툴 · ARKit 매칭

> **작성** 2026-10-19 · 이 문서만 보고 아래 네 작업을 끝낼 수 있게 썼다.
> 선행 문서: [0010 진단](0010_visemenet_feasibility.md) · [0020 사용법](0020_usage_example_maya.md) · [0040 ARKit 매칭](0040_jali_arkit_mapping.md)

---

## 0. 요청과 산출물

| # | 요청 | 산출물 | 저장소 |
|---|------|--------|--------|
| **T1** | 추론 환경을 만드는 파일. **더블클릭**으로 실행, Windows 10 · 11 | `setup_env.bat` | JUN_JALI |
| **T2** | wav → txt **스탠드얼론 툴**. wav 목록 TSL + 저장 경로 UI. 문제가 생기면 **변환을 멈추고 이유를 로그로**. 더블클릭으로 열림 | `Run_VisemeNet_Converter.bat` + `tools/VisemeNet_Converter/` | JUN_JALI |
| **T3** | 마야 리그에 키를 거는 **Maya 툴**. **드래그&드롭 → 셸프 설치**. txt · wav 를 고르는 UI | `A00540_JaliLipSync` | **Maya_Python** (권장, §1 결정 D1) |
| **T4** | JALI 음소 ↔ ARKit 52 매칭 관계 | **완료** — [0040](0040_jali_arkit_mapping.md) (실측 기반) | JUN_JALI |

`JUN_All` 의 공용 코드(`Framework`)를 쓴다 — TSL(`JUN_mod_tsl_qt_v01`), 로그(`JUN_mod_log_qt_v01`), 테마(`ThemeManager`),
탐색기 열기(`file_opener.open_path`), 메뉴 바(`JUN_mod_menuBar_qt_v01`).

---

## 1. 설계 결정 (권장안 — §8 에서 확인받을 것)

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| **D1** | Maya 툴 위치 | **`Maya_Python/JUN_All/tools/A00540_JaliLipSync`** | 마야 툴의 표준 자리(드래그&드롭 · 셸프 · 릴리즈 빌더 · 문서 체계가 다 거기 있다). TensorFlow 가 필요 없고 **txt · wav 만 읽으므로** JUN_JALI 와 코드로 묶일 필요가 없다. 라우팅 규칙("마야 파이썬 툴 → Maya_Python")과도 맞는다 |
| **D2** | 스탠드얼론이 Framework 를 얻는 법 | **복사본(vendor)** — `JUN_JALI/vendor/Framework/` | JUN_JALI 는 별도 공개 저장소다. JUN_All 경로를 참조하면 다른 PC 에서 Maya_Python 이 같은 자리에 없을 때 안 뜬다. Framework 전체가 816KB 라 통째로 복사해도 가볍다. 출처 커밋을 `vendor/FRAMEWORK_SOURCE.txt` 에 남긴다 |
| **D3** | 오류 정책 | **사전 검사(preflight) → 하나라도 실패면 아무것도 변환하지 않고 중단** + 변환 중 오류도 즉시 중단 | 요청("변환을 중단하고 이유를 로그로"). 사전 검사를 두면 10개 중 7번째에서 멈춰 절반만 바뀐 상태가 덜 생긴다 |
| **D4** | 44.1kHz 가 아닌 파일 | **오류로 중단**(자동 변환 안 함) | 요청 그대로. 자동 리샘플은 옵션으로 나중에(§8 Q3) |
| **D5** | 실행 파일 형태 | **`.bat` + 저장소 안 `.venv`** (PyInstaller exe 안 만듦) | TensorFlow 를 exe 로 묶으면 수백 MB 에 빌드 문제가 많다. `.venv` 는 1.6GB(이 PC 실측) |
| **D6** | 파이썬 버전 | **3.11 고정** (3.9 / 3.10 허용) | `tensorflow-cpu` 2.15.1 이 3.9~3.11 만 지원. 이 조합만 실측했다 |

---

## 2. 최종 폴더 구조

```
JUN_JALI/
├─ setup_env.bat                      T1  더블클릭 → .venv 설치 + 자가 검사
├─ Run_VisemeNet_Converter.bat        T2  더블클릭 → 변환기 창
├─ requirements.txt                   (+ PySide6 추가)
├─ inference.py · postprocess.py · visemenet_frozen.pb · saved_params/ · test_audio/   (원본, 손대지 않음)
├─ vendor/
│  ├─ Framework/                      JUN_All/Framework 복사본 (D2)
│  └─ FRAMEWORK_SOURCE.txt            출처 저장소 · 커밋 · 날짜
├─ tools/
│  ├─ __init__.py
│  ├─ selftest.py                     T1 마지막 단계 (coffee_xxxx.wav → (364, 22) 확인)
│  ├─ sync_framework.py               D2 복사 스크립트 (재실행 = 갱신)
│  └─ VisemeNet_Converter/            T2
│     ├─ __init__.py
│     ├─ launch.py
│     ├─ app/config/{version.py, app_meta.py}
│     ├─ app/core/{wav_check.py, converter.py, output_writer.py, settings.py}
│     ├─ app/ui/main_window.py
│     ├─ data/settings.json           (gitignore)
│     └─ icon/{VisemeNet_Converter.svg, .png, .ico}
├─ examples/maya_apply_visemenet.py   (이미 있음 — T3 가 대체)
└─ docs/ 0010 · 0020 · 0030(이 문서) · 0040 · 0050_converter_guide.md(T2 사용 안내, 새로)

Maya_Python/JUN_All/
├─ tools/A00540_JaliLipSync/          T3
│  ├─ __init__.py · launch.py · __dragDrop_A00540.py
│  ├─ app/config/version.py
│  ├─ app/core/{lipsync_data.py, mapping.py, keyer.py, sound.py, rig_scan.py}
│  ├─ app/mappings/angela_jali_visemenet.json
│  ├─ app/ui/main_window.py
│  └─ icon/A00540_JaliLipSync.{svg,png}
└─ docs/A00540_JaliLipSync.md
```

---

## 3. T1 — `setup_env.bat` (추론 환경 설치)

### 3.1 동작 순서

| 단계 | 하는 일 | 실패하면 (화면 + `setup_env.log`) |
|------|--------|----------------------------------|
| 0 | `chcp 65001` · `cd /d "%~dp0"` (어디서 더블클릭해도 저장소 루트) | — |
| 1 | **파이썬 찾기**: `py -3.11` → `py -3.10` → `py -3.9` → `python`(PATH). 각각 `-c "import sys; print(sys.version_info[:2])"` 로 **실제 버전 확인** | 없음 → §3.2 |
| 2 | `.venv\Scripts\python.exe` 가 있고 버전이 맞으면 재사용, 아니면 `.venv` 삭제 후 `-m venv .venv` | venv 실패 → 메시지 + 종료 |
| 3 | `python -m pip install --upgrade pip` | 네트워크 오류 안내 |
| 4 | `pip install -r requirements.txt` (전체 출력은 로그에, 화면엔 진행 줄만) | 로그 마지막 20줄을 화면에 + 흔한 원인 3개 안내(§3.3) |
| 5 | **임포트 검사**: `import tensorflow, PySide6, scipy, numpy, python_speech_features` | `DLL load failed` → VC++ 재배포 패키지 안내 |
| 6 | **자가 검사** `tools\selftest.py`: 모델 로드 + `test_audio\coffee_xxxx.wav` 추론 → `(364, 22)` · 값이 유한 | 실패 메시지 그대로 |
| 7 | `SETUP OK` + "이제 `Run_VisemeNet_Converter.bat` 를 더블클릭" + `pause` | — |

- **다시 실행해도 안전**(멱등). 이미 설치돼 있으면 4단계는 빠르게 끝난다. 인자 `--force` 면 `.venv` 를 새로 만든다.
- 관리자 권한 불필요. 모든 출력은 `setup_env.log`(gitignore)에도 남긴다.
- 메시지는 영어(툴 UI 규칙). 예: `[ERROR] Python 3.9-3.11 not found.`

### 3.2 파이썬이 없을 때

1. `winget` 이 있으면(Win10 1809+ · Win11 기본) `Install Python 3.11 now with winget? [Y/N]` → Y 면
   `winget install -e --id Python.Python.3.11 --scope user` 후 1단계를 다시 한다 (**자동 설치를 허용할지 §8 Q7**).
2. 없거나 N → `https://www.python.org/downloads/release/python-3119/` 를 안내하고 "**Add python.exe to PATH** 체크" 를 강조, 종료.
3. **함정**: `python` 이 `...\WindowsApps\python.exe`(스토어 바로가기)면 실행 시 스토어가 열린다 → 경로에 `WindowsApps` 가 있으면 건너뛴다.

### 3.3 흔한 설치 실패와 안내 문구

| 증상 | 원인 | 안내 |
|------|------|------|
| `No matching distribution found for tensorflow-cpu==2.15.1` | 파이썬 3.12+ 또는 32bit | 1단계 버전 확인으로 막는다 |
| `DLL load failed while importing _pywrap_tensorflow_internal` | VC++ 2015-2022 재배포 패키지 없음 | `https://aka.ms/vs/17/release/vc_redist.x64.exe` |
| `OSError: [Errno 2] No such file or directory` (긴 경로) | 260자 제한 | 저장소를 짧은 경로로 옮기거나 LongPathsEnabled (관리자) |
| SSL / timeout | 회사망 · 프록시 | `pip --proxy` 안내 |

### 3.4 `requirements.txt` 변경

```
tensorflow-cpu==2.15.1
numpy==1.26.4
scipy==1.17.1
python_speech_features==0.6
PySide6==<설치 시 확인한 버전으로 고정>
```

### 3.5 완료 조건

- [ ] 이 PC: `.venv` 를 지운 상태에서 더블클릭 → `SETUP OK` (시간 기록)
- [ ] 두 번째 실행이 1분 안에 끝남(재사용)
- [ ] 파이썬 3.12 만 있는 상황 흉내(`py -3.11` 실패) → 안내 후 종료
- [ ] **Windows 10 PC 에서 1회**(§8 Q8)

---

## 4. T2 — VisemeNet Converter (스탠드얼론)

### 4.1 실행

`Run_VisemeNet_Converter.bat`:

```bat
@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo [ERROR] Environment not found. Run setup_env.bat first.
    pause & exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "tools\VisemeNet_Converter\launch.py"
```

- `pythonw` 라 콘솔 창이 남지 않는다. **대신 시작 중 예외가 화면에 안 보이므로** `launch.py` 는 시작 코드를
  `try` 로 감싸 `QMessageBox.critical` + `tools/VisemeNet_Converter/data/startup_error.log` 에 남긴다.
- `launch.py` 의 `sys.path`: 저장소 루트(→ `inference`, `postprocess`, `tools.*`) + `vendor/`(→ `Framework`).
  import 는 `from tools.VisemeNet_Converter.app.ui.main_window import MainWindow` (bare `app` 금지 — 다른 툴과 충돌).
- 작업표시줄 아이콘: `SetCurrentProcessExplicitAppUserModelID("JUN.JALI.VisemeNetConverter")` 를 `QApplication()` **전에**,
  `icon/*.ico` 는 SVG 에서 크기별로 직접 렌더(가이드 `Maya_Python/JUN_All/docs/taskbar_icon_guide.md`).
- 테마: `ThemeManager.load_theme_dev(app, "dark")` (다른 스탠드얼론 툴과 같음).

### 4.2 화면

```
┌ VisemeNet Converter v01.00 ─────────────────────────────────┐
│ File  Help                                                   │
│ ┌ Input WAV Files ─────────────────────────────────────────┐ │
│ │ [Add Files...] [Add Folder...]                            │ │
│ │ ┌──────────────────────────────────────┐  [Up]  [Down]   │ │
│ │ │ D:\voice\line01_en.wav               │  [Del] [Clear]  │ │
│ │ │ D:\voice\line01_ko.wav               │  [Sort]         │ │
│ │ └──────────────────────────────────────┘  Number: 2      │ │
│ │ (wav 를 목록에 끌어다 놓아도 추가)                          │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌ Output ───────────────────────────────────────────────────┐ │
│ │ Folder [D:\voice\visemes__________] [Browse...] [Open]    │ │
│ │ [x] Write .json info file   [ ] Overwrite existing        │ │
│ │ Max length (sec) [120]                                    │ │
│ └───────────────────────────────────────────────────────────┘ │
│ [ Check Files ]                     [ Convert ]   ([ Stop ])  │
│ [██████████░░░░░░░░] 1 / 2  line01_en.wav                    │
│ ┌ Log ───────────────────────────── [Expand][Clear][Copy] ─┐ │
│ │ [OK]   line01_en.wav  44100 Hz · int16 · 2 ch · 3.99 s    │ │
│ │ [ERR]  line01_ko.wav  sample rate 48000 Hz - need 44100   │ │
│ │ [STOP] 1 file failed the check. Nothing was converted.    │ │
│ └───────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

- 목록 = `JUN_mod_tsl_qt_v01(title="Input WAV Files", show_select=False, show_add=False, attach_uuids=False, ...)`
  (씬 노드가 아니므로 UUID 끄기, 마야 버튼 숨김). 위에 `Add Files...` / `Add Folder...` 버튼, 목록에 `.wav` 드롭 허용.
  같은 파일 두 번 추가는 무시.
- 출력 폴더 = `QLineEdit` + `Browse...` + `Open`(`file_opener.open_path`). 비우면 **각 wav 와 같은 폴더**.
- 마지막 목록 · 폴더 · 옵션은 `data/settings.json` 에 저장 → 다음 실행 때 복원.
- 로그 = `JUN_mod_log_qt_v01` (레벨 색: `[OK]` `[WARN]` `[ERR]` `[STOP]`).
- 변환은 **`QThread` 워커**에서 — 창이 멈추지 않는다. TensorFlow import(~5초) 와 모델 로드는 첫 `Convert` 때 한 번만.
  `Stop` 은 지금 파일이 끝나면 멈춘다(추론 한 건은 중간에 끊을 수 없다).

### 4.3 검사 규칙 (`app/core/wav_check.py`) ⭐

`check_wav(path, max_seconds) -> WavInfo | raise WavError(code, message)`. `Check Files` 와 `Convert` 의 사전 검사가 같은 함수를 쓴다.

| 코드 | 검사 | 결과 | 로그 문구 (영어) |
|------|------|------|-----------------|
| E01 | 파일 없음 | 중단 | `file not found` |
| E02 | `scipy.io.wavfile.read` 실패 (mp3 를 이름만 바꾼 것, ADPCM 압축 등) | 중단 | `cannot read as PCM WAV: <원인>` |
| E03 | **샘플레이트 ≠ 44100** | 중단 | `sample rate 48000 Hz - VisemeNet needs 44100 Hz (re-export the file at 44.1 kHz)` |
| E04 | **dtype ≠ int16** (float32 · 24/32bit = int32 · 8bit = uint8) | 중단 | `sample format float32 - need 16-bit integer PCM` |
| E05 | 채널 > 2 | 중단 | `3 channels - need mono or stereo` |
| E06 | 길이 < 0.5초 | 중단 | `too short (0.21 s)` |
| E07 | 길이 > Max length | 중단 | `too long (185.0 s > 120 s) - split the file` |
| E08 | 무음 (최대 진폭 0) | 중단 | `silent audio` |
| E09 | 출력 파일이 있고 Overwrite 꺼짐 | 중단 | `output exists: <path> (turn on Overwrite)` |
| E10 | 출력 폴더를 만들 수 없음 / 쓰기 불가 | 중단 | `cannot write to <folder>` |
| E11 | 같은 이름 wav 가 다른 폴더에 둘 → 출력 이름 충돌 | 중단 | `two files would write the same output: <name>.txt` |
| W01 | 스테레오 | 계속 | `stereo - only the left channel is used` |
| W02 | 클리핑 (±32767 근처 샘플 > 0.1%) | 계속 | `clipping detected (0.8 % of samples)` |

**변환 중 오류 (`app/core/converter.py`)** — 하나라도 나면 **남은 파일을 처리하지 않고** 멈춘다.

| 코드 | 상황 | 로그 |
|------|------|------|
| E20 | 모델 · `saved_params` 파일 없음 | `model file missing: visemenet_frozen.pb` |
| E21 | TensorFlow 예외 | `inference failed: <예외 첫 줄>` (전문은 `[DETAIL]` 로) |
| E22 | 출력에 NaN · inf | `model output has NaN` |
| E23 | 출력 모양 ≠ (≈길이×100, 22) | `unexpected output shape (n, m)` |
| E24 | 파일 쓰기 실패 | `cannot write <path>: <원인>` |

- 끝 로그: 성공 `[DONE] 5 converted in 12.3 s → <folder>` / 중단 `[STOP] stopped at 3 / 5 (line03_ko.wav): <이유>. Files already written: 2`.
- **경고 소음 걸러내기**: `python_speech_features` 의 `frame length (1103) is greater than FFT size (512)` 와
  scipy `WavFileWarning`(메타데이터 청크)은 **정상**(학습 때도 같았다) → 오류로 세지 않고 첫 파일에서 한 번만 `[INFO]` 로.
  TensorFlow 로그는 `TF_CPP_MIN_LOG_LEVEL=2`.

### 4.4 원본 코드 사용법 (수정 없이)

`inference.py` 는 기본 인자가 **현재 폴더 기준 상대경로**(`./saved_params/...`)다. 변환기는 절대경로를 넘긴다.

```python
reg = VisemeRegressor(pb_filepath=os.path.join(ROOT, "visemenet_frozen.pb"))
out = reg.predict_outputs(
    wav_file_path=wav,
    mean_std_csv_path=os.path.join(ROOT, "saved_params", "wav_mean_std.csv"),
    close_face_txt_path=os.path.join(ROOT, "saved_params", "maya_close_face.txt"))
```

`_load_graph` 가 텐서 이름을 `print` 하므로(pythonw 에선 안 보임) 그대로 둔다. 원본 버그 수정(진단 문서 §4)은 **이 계획 범위 밖** —
출력이 바뀌기 때문이다(나중에 별도 버전으로).

### 4.5 출력 형식 (`app/core/output_writer.py`)

| 파일 | 내용 |
|------|------|
| `<wav 이름>.txt` | **원본과 똑같이** `np.savetxt(path, out, '%.4f')` — 0020 문서 · examples 스크립트와 호환 |
| `<wav 이름>.visemenet.json` (옵션, 기본 켬) | 아래 |

```json
{
  "format": "jun_jali.visemenet/1",
  "source_wav": "D:/voice/line01_ko.wav",
  "wav": {"sample_rate": 44100, "channels": 2, "seconds": 3.99},
  "fps": 100,
  "rows": 364,
  "columns": ["Jaw","Lip","Ah","Aa","Eh","Ee","Ih","Oh","Uh","U","Eu","Schwa","R","S","ShChZh","Th","JY","LNTD","GK","MBP","FV","W"],
  "model": "visemenet_frozen.pb",
  "converter": "VisemeNet Converter 01.00",
  "created": "2026-10-20T10:00:00"
}
```

쓰기는 **임시 파일에 쓰고 이름 바꾸기**(중간에 멈춰도 반쯤 쓴 txt 가 남지 않게).
T3 는 이 json 이 있으면 wav 경로와 fps 를 자동으로 채운다.

### 4.6 검증 (완료 조건)

`tools/VisemeNet_Converter/tests/make_bad_wavs.py` 가 scipy 로 시험용 wav 를 만든다:
48kHz int16 · 44.1kHz float32 · 44.1kHz int32(24bit 흉내) · 3채널 · 0.2초 · 무음 · 깨진 바이트 · **한글 경로** · 클리핑.

- [ ] 각 시험 파일이 §4.3 의 **정확한 코드**로 걸린다 (헤드리스 스크립트로 `check_wav` 직접 호출)
- [ ] 정상 파일 + 나쁜 파일 섞은 목록 → 사전 검사에서 멈추고 **아무 txt 도 안 생긴다**
- [ ] `visemenet_intro.wav` 결과가 0020 문서의 `out/visemenet_intro.txt` 와 **같은 값**(np.allclose)
- [ ] 변환 중 창이 멈추지 않는다, `Stop` 동작
- [ ] 오프스크린 UI 테스트(`QT_QPA_PLATFORM=offscreen`) — 목록 채우기 · 설정 저장/복원
- [ ] 사용자 GUI 확인 (더블클릭 → 변환 → 로그)

---

## 5. T3 — `A00540_JaliLipSync` (Maya, 드래그&드롭 셸프)

구조는 in-Maya PySide 툴(아키텍처 B)을 따른다 — 복제 기준 `A00008_base_QT_maya` / 최근 예 `A00340_SelectionTool`.

### 5.1 설치 · 실행

- `__dragDrop_A00540.py` 를 뷰포트로 드롭 → 현재 셸프에 버튼. 이름은 툴마다 고유해야 하고 끝에서
  `sys.modules.pop(__name__, None)` (CLAUDE.md §3 의 드롭 파일 규칙). 셸프 명령은 `tools.A00540_JaliLipSync.run(True)`.
- 셸프 아이콘 32px (`icon/`, 공통 배경 틀 `#2d2d30` / `#4a4a4f`, rx 6).
- `launch.py` 는 릴리즈 배치도 구분하는 공통 프리앰블(`JUN_All/docs/Release_Layout.md`).

### 5.2 화면

```
┌ JALI LipSync v01.00 ────────────────────────── [Pin] ┐
│ File  Help                                            │
│ ┌ Data ──────────────────────────────────────────────┐ │
│ │ Viseme TXT [D:\voice\visemes\line01_ko.txt] [...]  │ │
│ │ Audio WAV  [D:\voice\line01_ko.wav        ] [...]  │ │
│ │ 364 rows · 3.64 s @100fps · json: found            │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌ Target ────────────────────────────────────────────┐ │
│ │ Rig       [angela: (CNT_PHONEMES found) ▼] [Refresh]│ │
│ │ Mapping   [angela_jali_visemenet ▼]                 │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌ Options ───────────────────────────────────────────┐ │
│ │ Start frame [1]   Viseme scale [10.0]               │ │
│ │ JaLi  (•) From data  ( ) Fixed  Jaw [9.0] Lip [9.0] │ │
│ │ [x] Attach audio   [x] Set playback range           │ │
│ └────────────────────────────────────────────────────┘ │
│ [ Apply ]   [ Remove Keys ]   [ Select Controls ]      │
│ Log                                                    │
└────────────────────────────────────────────────────────┘
```

- **TXT 를 고르면** 같은 폴더의 `<이름>.visemenet.json` 을 찾아 WAV 경로를 채운다. json 이 없으면 txt 와 같은 이름의 `.wav` 를
  txt 폴더 → 상위 폴더 순으로 찾는다. 못 찾으면 비워 두고 `[WARN]`. 마지막 폴더는 기억한다(`optionVar`).
- **Rig 콤보** = 씬에서 `*CNT_PHONEMES` 를 찾아 네임스페이스별로 나열(`rig_scan.py`). 레퍼런스 리그도 된다.
- **JaLi `Fixed`** = `CNT_JaLi` 에 키를 걸지 않고 고정값만 둔다 — 비짐 타이밍은 데이터, 말투는 사람이 정한다(0020 §4).
- `Apply` = 그 구간 기존 키 지우고 → 키 → 오디오 → 재생 범위. **Undo 한 번**(`undo_chunk`).
  `Remove Keys` = 매핑의 어트리뷰트 키를 구간에서 지우기. `Select Controls` = 매핑 컨트롤 선택.
- 진행 팝업은 길 때만(`JUN_mod_progress_qt_v01`) — 349 프레임 × 23 어트리뷰트가 0.2초(실측)라 2분짜리도 수 초.

### 5.3 코어 (`app/core`, UI 비의존)

| 파일 | 함수 | 하는 일 |
|------|------|--------|
| `lipsync_data.py` | `load(txt_path) -> LipsyncData` | txt 읽기(22열 검사) + json 있으면 fps · columns · source_wav 확인 |
| `mapping.py` | `load_mapping(name)`, `list_mappings()` | `app/mappings/*.json` |
| `keyer.py` | `apply(data, mapping, namespace, start, scale, jali_fixed=None, progress=None)` | 씬 fps 로 샘플 → 키. `examples/maya_apply_visemenet.py` 를 옮긴다 |
| `keyer.py` | `remove(mapping, namespace, start, end)` | 키 삭제 |
| `sound.py` | `attach(wav, start)` | `cmds.sound` + GUI 면 타임슬라이더 연결 |
| `rig_scan.py` | `find_rigs() -> [namespace]` | `CNT_PHONEMES` 가 있는 네임스페이스 |

**Maya 쪽 검사** (멈추고 `[ERR]`): txt 열 ≠ 22 · 숫자 아님 · 0줄 / json 의 columns 가 매핑과 다름 / 매핑 어트리뷰트가 리그에 없음(전부 나열) /
어트리뷰트가 잠김 · 다른 노드에 연결됨. **경고만**: wav 길이와 txt 길이가 0.1초 넘게 차이 / 씬 fps 가 24 · 25 · 30 이 아님.

### 5.4 매핑 json (`app/mappings/angela_jali_visemenet.json`)

```json
{
  "name": "angela_jali_visemenet",
  "description": "VisemeNet 22 columns -> angela_JALI.ma (same as the original maya_animation.py)",
  "model_columns": ["Jaw","Lip","Ah","Aa","Eh","Ee","Ih","Oh","Uh","U","Eu","Schwa","R","S","ShChZh","Th","JY","LNTD","GK","MBP","FV","W"],
  "clamp": [0.0, 1.0],
  "targets": [
    {"attr": "CNT_JaLi.translateX", "from": ["Jaw"], "scale": 10, "role": "jali"},
    {"attr": "CNT_JaLi.translateY", "from": ["Lip"], "scale": 10, "role": "jali"},
    {"attr": "CNT_PHONEMES.OHH",    "from": ["Oh", "Uh"], "combine": "max", "scale": 10},
    "... 0020 문서 §3 표의 나머지 20개 ..."
  ]
}
```

- `role: "jali"` 는 `JaLi = Fixed` 일 때 키 대신 고정값을 넣는 대상.
- 옵션 `Viseme scale` 은 `role` 이 없는 대상의 `scale` 을 덮어쓴다.
- **새 리그 · ARKit 아바타 = json 하나 추가**(코드 수정 없음). ARKit 판은 0040 §3 표를 `targets` 로 옮기면 된다(§7 T4-b).

### 5.5 검증 (완료 조건)

- [ ] mayapy: angela 열기 → `apply` → 23개 어트리뷰트 키 · 재생 범위 · 사운드 노드 (0020 §7 과 같은 숫자)
- [ ] 리그를 **레퍼런스**로 불러온 씬에서 네임스페이스 감지 · 적용
- [ ] 다시 Apply → 키 수 그대로 · Undo 한 번으로 원상태
- [ ] `JaLi = Fixed` → `CNT_JaLi` 에 키 없음, 값 고정
- [ ] 22열 아닌 txt · 어트리뷰트 없는 리그 → `[ERR]`, 씬 변화 없음
- [ ] 오프스크린 UI: TXT 고르면 WAV 자동 채움(json 있음 / 없음)
- [ ] 드롭 설치 · 셸프 버튼 · 아이콘 — **마야 GUI 에서 사용자 확인**
- [ ] 문서 `docs/A00540_JaliLipSync.md`, WORKLOG, README 툴 수 · 최근 작업, 포트폴리오(페이셜 축) 갱신

---

## 6. 작업 순서

| 순서 | 작업 | 끝났다는 기준 | 커밋 · 푸시 |
|------|------|--------------|------------|
| 1 | §8 답 받기 | D1~D6 확정 | — |
| 2 | `vendor/Framework` 복사 + `tools/sync_framework.py` | `python -c "from Framework.qt import JUN_mod_tsl_qt"` 가 `.venv` 에서 됨 | JUN_JALI |
| 3 | T1 `setup_env.bat` + `tools/selftest.py` + requirements(PySide6) | §3.5 | JUN_JALI |
| 4 | T2 코어(`wav_check` · `converter` · `output_writer`) + 시험 wav | §4.6 앞 3개 | JUN_JALI |
| 5 | T2 UI + 런처 bat + 아이콘 + `docs/0050_converter_guide.md` | §4.6 나머지 | JUN_JALI |
| 6 | T3 코어 + 매핑 json | §5.5 앞 5개 | Maya_Python |
| 7 | T3 UI + 드롭 설치 + 아이콘 + 문서 | §5.5 나머지 | Maya_Python |
| 8 | 0020 문서를 툴 기준으로 갱신(스크립트 붙여넣기 → 셸프 툴) | — | JUN_JALI |
| 9 | (선택) T4-b ARKit 매핑 json + 아바타 대조 | §8 Q9 답에 따라 | 둘 중 해당 |

- 커밋은 저장소마다 따로(경로 명시 스테이징). **푸시는 그 턴에 요청이 있을 때만** — JUN_JALI → `origin main`, Maya_Python → `Dnable_repo dev`.
- UI 문자열 · 로그는 영어, 주석 · 독스트링은 한국어.

---

## 7. T4 — ARKit 매칭

- **T4-a (요청 범위, 완료)**: [0040](0040_jali_arkit_mapping.md). angela 리그에서 음소 16개 + 동시조음 6개를 하나씩 올려
  턱 · 근육 · 혀 변화를 **실측**하고, 근육 → FACS → ARKit 로 이었다. 핵심: Jaw 축 = `jawOpen`, Lip 축 = `mouth*`, `MBP` = `mouthClose`+`jawOpen`.
- **T4-b (선택)**: ARKit 52 블렌드셰이프를 가진 아바타에 VisemeNet 결과를 거는 매핑 json + 음소별 렌더 비교로 가중치 조정.
  대상 아바타가 있어야 한다(§8 Q9).

---

## 8. 정해 주거나 제공해야 할 것

| # | 질문 | 권장 / 기본값 | 왜 필요한가 |
|---|------|--------------|------------|
| **Q1** | Maya 툴을 **Maya_Python(A00540)** 에 둘까, JUN_JALI 에 둘까 | Maya_Python | §1 D1 |
| **Q2** | 스탠드얼론의 Framework 를 **복사본(vendor)** 으로 둘까, JUN_All 경로를 참조할까 | 복사본 | 다른 PC 에서 JUN_JALI 만 받아도 돌아가야 하는지 |
| **Q3** | 44.1kHz 가 아닌 파일 — 요청대로 **중단만**? 아니면 "44.1kHz 사본을 만들어 변환" 옵션도? | 중단만 (옵션은 나중) | §1 D4 |
| **Q4** | 오류 시 — **시작 전 전체 검사 후 하나라도 실패면 전부 중단**으로 괜찮은가 | 예 | §1 D3 |
| **Q5** | 최대 길이 기본값 · 출력 덮어쓰기 기본값 | 120초 · 덮어쓰기 끔 | 긴 파일은 메모리 한계 미검증 |
| **Q6** | 지원할 **Maya 버전** | 2024 (2022 · 2023 · 2025 도 필요하면 알려 줄 것) | PySide2/6 · 테스트 범위 |
| **Q7** | 파이썬이 없는 PC 에서 `setup_env.bat` 가 **winget 으로 Python 3.11 을 설치**해도 되나 | 물어보고(Y/N) 설치 | 남의 PC 에 소프트웨어를 까는 일 |
| **Q8** | **Windows 10 테스트 PC** 가 있나 | — | 이 PC 는 Windows 11 뿐. 없으면 Win10 은 "미검증" 으로 남긴다 |
| **Q9** | ARKit 매칭을 **표로만** 둘까, ARKit 아바타에 거는 기능(T4-b)까지 갈까. 간다면 **그 아바타 파일**(블렌드셰이프 이름 포함) | 표만 (완료) | T4-b 는 대상이 있어야 가능 |
| **Q10** | 이 툴들을 **누가 쓰나** — 본인만 / 팀 / 공개 배포 | 본인 + 포트폴리오 | 원본 VisemeNet 은 GPLv3 · 상용 이중 라이선스, 가중치 표기 없음 → 배포 범위에 따라 확인 필요 |
| **Q11** | 툴 이름 — `VisemeNet Converter` / `JALI LipSync` 로 괜찮나 | 그대로 | 창 제목 · 셸프 라벨 · 아이콘 |

> 답이 없으면 **권장 / 기본값**으로 진행한다. Q8 · Q9 · Q10 은 내가 정할 수 없는 정보다.
