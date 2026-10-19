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

**빠른 시작**: ① `setup_env.bat` 더블클릭(한 번) → ② `Run_VisemeNet_Converter.bat` 더블클릭 → wav 넣고 `Convert`
→ ③ 마야에서 `Maya_Python/JUN_All/tools/A00540_JaliLipSync/__dragDrop_A00540.py` 를 드롭해 셸프 툴로 리그에 키.

포크에서 더한 것: `setup_env.bat` · `Run_VisemeNet_Converter.bat` · `tools/VisemeNet_Converter/`(스탠드얼론 변환기) · `tools/selftest.py` ·
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
