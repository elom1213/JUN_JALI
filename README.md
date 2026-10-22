# JUN_JALI — VisemeNet 포크 `[JUN]`

> [`junhwanjang/visemenet-inference`](https://github.com/junhwanjang/visemenet-inference) (`c20ec78`) 포크.
> 목표: 같은 의미 · 다른 언어 음성으로 **JALI 리그 립싱크**를 자동 생성 (Maya → Unreal).

| 문서 | 내용 |
|------|------|
| [docs/0010_visemenet_feasibility.md](docs/0010_visemenet_feasibility.md) | 진단 — 가능 여부, 필요 조건, 수정 계획 |
| [docs/0020_usage_example_maya.md](docs/0020_usage_example_maya.md) | **사용법** — 예시 wav → 추론 → Maya JALI 리그(angela_JALI.ma) 키 |
| [docs/0030_tool_plan.md](docs/0030_tool_plan.md) | 툴 제작 계획 — 환경 설치 bat · wav→txt 변환기 · Maya 키 툴(A00540) |
| [docs/0040_jali_arkit_mapping.md](docs/0040_jali_arkit_mapping.md) | JALI 음소 ↔ ARKit 52 블렌드셰이프 매칭 (리그 실측 기반) |
| [docs/0050_converter_guide.md](docs/0050_converter_guide.md) | **설치 · 변환기 사용법** — `setup_env.bat` · `Run_VisemeNet_Converter.bat`, 오류 코드, 원본 모델의 무작위성 · 끝 0.32초 |
| [docs/0060_transcript_mfa_plan.md](docs/0060_transcript_mfa_plan.md) | 개선 계획 — 대본 + Montreal Forced Aligner 로 비짐 보정 · 하이브리드 생성 (영 · 한 · 일) |
| [docs/0070_advancedskeleton_lipsync_research.md](docs/0070_advancedskeleton_lipsync_research.md) | 조사 — AdvancedSkeleton 의 Audio2Face (NVIDIA → ARKit 52 리타깃) · Auto lipsync (MFA 1.1) 동작 과정과 0060 계획에 주는 의미 |
| [docs/0080_transcript_correction_usage.md](docs/0080_transcript_correction_usage.md) | **사용법 — 대본으로 립싱크 보정** (v01.01): `setup_mfa.bat` → 대본 준비 → 변환기 Correct 모드 → Maya |
| [docs/0090_jali_slider_ctl_plan.md](docs/0090_jali_slider_ctl_plan.md) | 제작 계획 — JALI 슬라이더 컨트롤러 리그 (`02_Cage_JALI/A0020`): angela 어트리뷰트 1:1 슬라이더 · `output_min/max` 리맵 · 더미 입력/출력 노드 |
| [docs/0100_jali_dummy_out_attrs_guide.md](docs/0100_jali_dummy_out_attrs_guide.md) | **안내 — `DUMMY_OUT_PHONEMES` · `DUMMY_OUT_COARTIC` 어트리뷰트가 만드는 얼굴 표현** (angela 실측: 턱 각도 · 입술 근육 · 혀, 동시조음 채널의 뜻과 같이 쓰는 예) |
| [docs/0100_mh_arkit_dummy_plan.md](docs/0100_mh_arkit_dummy_plan.md) | 제작 계획 — 메타휴먼 페이셜 ↔ ARKit 52 ↔ JALI 더미 노드 에셋 (`07_MH_sample_02/0010_sample_0040`): `dmy_in`/`dmy_out`(ARKit 52) · `dmy_in_jali` 매핑표, Epic ARKit 포즈 실측, 쓰이는 컨트롤러 68개 색 구분 (확인 질문 Q1~Q8) |
| [docs/0110_jali_mh_dummy_plan.md](docs/0110_jali_mh_dummy_plan.md) | 매칭표 · 제작 계획 — JALI 음소 ↔ 메타휴먼 페이셜 더미 노드 (`0010_sample_0050`): `dmy_in_jali/phonemes/coartic`(A0020 `DUMMY_OUT_*` 와 이름 · 단위 동일), ARKit 경유 합성표 + 혀 · 입술 깨물기 · 턱 비례 동시조음 직접 매핑 제안 (확인 질문 Q1~Q8) |

**빠른 시작**: ① `setup_env.bat` 더블클릭(한 번 — PC 에 Python 3.12 ~ 3.14 만 있으면 이 폴더 전용 Python 3.11 을 받아 쓴다) → ② `Run_VisemeNet_Converter.bat` 더블클릭 → wav 넣고 `Convert`
→ ③ 마야에서 `Maya_Python/JUN_All/tools/A00540_JaliLipSync/__dragDrop_A00540.py` 를 드롭해 셸프 툴로 리그에 키.

**대본 보정 (선택, v01.01)**: `setup_mfa.bat` 더블클릭(한 번 — 설치 폴더를 고른다, 약 6.5 GB) → 변환기 `Transcript` 를 `Correct with transcript (MFA)` 로,
WAV 옆에 같은 이름의 대본(`.lab` / `.txt`, UTF-8) — 음소 구간으로 비짐을 보정한다 ([0080 사용법](docs/0080_transcript_correction_usage.md) · [0050 §6](docs/0050_converter_guide.md)).

포크에서 더한 것: `setup_env.bat` · `setup_mfa.bat`(+ `mfa_env.lock.txt` · `requirements_mfa.txt`) · `Run_VisemeNet_Converter.bat` · `tools/VisemeNet_Converter/`(스탠드얼론 변환기) · `saved_params/ipa_to_jali.json` · `tools/selftest.py` ·
`vendor/Framework/`(Maya_Python 공용 위젯 복사본) · `requirements.txt` · `examples/maya_apply_visemenet.py` · `docs/`.
원본 코드(`inference.py` · `postprocess.py` · `visemenet_frozen.pb`)는 손대지 않았다 — 결정적 모드는 불러온 그래프만 바꾼다.
라이선스 주의: 원본 VisemeNet 은 GPLv3 또는 상용(UMass) — 진단 문서 §4.

---

## 원본 README

# visemenet-inference
- Inference Demo of ["VisemeNet-tensorflow"](https://github.com/yzhou359/VisemeNet_tensorflow) 
    * VisemeNet is an audio-driven animator centric speech animation driving a JALI or standard FACS-based face-rigging from input audio. 
    * The original repo is outdated and difficult to setup the environment for testing the pretrained model. This code is to provide a super-clean inference module based on the original author's repo.

## Model Inference
[Colab Demo](https://colab.research.google.com/drive/1dS4chsaFdC1D3vBaIaqIhBNaGSzXtzAc?usp=sharing)

- This code provides the simple and clean inference code without any needless ones
- It's compatible with TF 2.0 Version

### Requirements
* Tensorflow 2.x
* numpy
* scipy
* python_speech_features

### How to run inference
```python
import numpy as np
from inference import VisemeRegressor

pb_filepath = "./visemenet_frozen.pb"
wav_file_path = "./test_audio.wav"
out_txt_path = "./maya_viseme_outputs.txt"

viseme_regressor = VisemeRegressor(pb_filepath=pb_filepath)

viseme_outputs = viseme_regressor.predict_outputs(wav_file_path=wav_file_path)

np.savetxt(out_txt_path, viseme_outputs, '%.4f')
```

## How to freeze graph
- This repo does not need bazel-build for "freeze-graph" function
- Thanks to https://github.com/lighttransport/VisemeNet-infer for giving some examples.

### Requirements
* Python 3.6.x using ["pyenv"](https://github.com/pyenv/pyenv)
* Tensorflow 1.1.0

1. Setup the envs and packages
```shell
# Install Virtualenv using pyenv
pyenv install 3.6.5
pyenv virtualenv 3.6.5 visemenet-freeze
pyenv activate visemenet-freeze
```
```shell
# Install packages
pip install tensorflow==1.1.0
```

2. Clone the repo
```shell
# Clone Visemenet repo and the pretrained model
git clone https://github.com/yzhou359/VisemeNet_tensorflow.git
curl -L https://www.dropbox.com/sh/7nbqgwv0zz8pbk9/AAAghy76GVYDLqPKdANcyDuba?dl=0 > pretrained_model.zip
unzip prtrained_model.zip -d VisemeNet_tensorflow/data/ckpt/pretrain_biwi/
```

3. Freeze Graph and Save as pb
```shell
# Freeze Graph
python freeze_graph.py
```
