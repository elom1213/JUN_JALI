# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 실행 장치 선택 (docs/0130_stt_converter_plan.md D10 · §1-0 · §3-3)
#
# 1) Windows: pip 로 받은 nvidia-cublas-cu12 / nvidia-cudnn-cu12 의 DLL 폴더를 ctranslate2 import **전에** 등록한다
#    (faster-whisper README 는 Windows 에 pip 경로를 주지 않지만 같은 DLL 이다 - M0-1 실측).
# 2) CUDA 장치 수 · 지원 compute type 을 ctranslate2 에 묻고, 요청(Auto / CUDA float16 / CUDA int8 / CPU int8)에
#    맞는 (device, compute_type) 을 고른다. GPU 가 없거나 초기화에 실패하면 CPU int8 로 폴백하고 그 사실을 돌려준다(W21).
# 3) nvidia-smi 가 있으면 GPU 이름 · VRAM 을 로그용으로 읽는다 (없어도 동작).
# 4) 강제 CPU (2026-10-23): 개발 PC 는 CUDA 프로세스 기동 중 강제 종료가 반복된다(docs/0130 §6 경고 · §11 크래시 기록).
#    환경 변수 JUN_STT_FORCE_CPU=1 또는 data/force_cpu.flag 파일이 있으면 CUDA 를 **전혀 건드리지 않고**(DLL 등록 ·
#    장치 수 조회도 안 함) 어떤 요청이든 CPU int8 로 간다. UI · CLI · 엔진 모두 이 모듈을 거친다.

import os
import subprocess

from . import settings

FORCE_CPU_ENV = "JUN_STT_FORCE_CPU"
FORCE_CPU_FLAG = os.path.join(settings.DATA_DIR, "force_cpu.flag")

DEVICE_CHOICES = (
    ("Auto (CUDA if available, else CPU)", "auto"),
    ("CUDA float16", "cuda:float16"),
    ("CUDA int8_float16", "cuda:int8_float16"),
    ("CPU int8", "cpu:int8"),
)


def force_cpu_reason():
    """CPU 강제 사유 문자열 - 비어 있으면 강제 아님."""
    if os.environ.get(FORCE_CPU_ENV, "").strip() not in ("", "0"):
        return "environment variable {0}={1}".format(FORCE_CPU_ENV, os.environ.get(FORCE_CPU_ENV).strip())
    if os.path.isfile(FORCE_CPU_FLAG):
        return "flag file {0}".format(FORCE_CPU_FLAG)
    return ""


def set_force_cpu_flag(enabled, note=""):
    """data/force_cpu.flag 를 만들거나 지운다 (UI 의 'Never use CUDA on this PC' 체크). Returns 성공 여부."""
    try:
        if enabled:
            os.makedirs(os.path.dirname(FORCE_CPU_FLAG), exist_ok=True)
            with open(FORCE_CPU_FLAG, "w", encoding="utf-8") as f:
                f.write((note or "CUDA disabled on this PC - delete this file to allow CUDA again") + "\n")
        elif os.path.isfile(FORCE_CPU_FLAG):
            os.remove(FORCE_CPU_FLAG)
        return True
    except OSError:
        return False


class DeviceInfo(object):
    def __init__(self):
        self.forced_cpu = ""                 # 비어 있지 않으면 CUDA 를 건드리지 않은 이유
        self.dll_dirs = []
        self.cuda_devices = 0
        self.cuda_compute_types = []
        self.cpu_compute_types = []
        self.gpu_name = ""
        self.gpu_vram_mb = 0
        self.driver = ""
        self.error = ""

    def summary(self):
        if self.forced_cpu:
            return "CPU forced ({0}) - CUDA not touched".format(self.forced_cpu)
        if self.cuda_devices:
            gpu = self.gpu_name or "CUDA device"
            vram = " ({0} MB)".format(self.gpu_vram_mb) if self.gpu_vram_mb else ""
            return "GPU: {0}{1}, driver {2}, compute types {3}".format(
                gpu, vram, self.driver or "?", ", ".join(self.cuda_compute_types))
        return "no CUDA device - CPU only ({0})".format(self.error or "ctranslate2 found 0 devices")


def add_nvidia_dlls():
    """pip nvidia-* 패키지의 bin 폴더를 DLL 탐색 경로에 더한다. Returns 등록한 폴더 목록."""
    added = []
    if os.name != "nt":
        return added
    try:
        import nvidia
    except ImportError:
        return added
    for base in list(getattr(nvidia, "__path__", [])):
        for sub in ("cublas", "cudnn", "cuda_nvrtc"):
            d = os.path.join(base, sub, "bin")
            if os.path.isdir(d) and d not in added:
                try:
                    os.add_dll_directory(d)
                except (OSError, AttributeError):
                    pass
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                added.append(d)
    return added


def _nvidia_smi():
    """(name, vram_mb, driver) - 실패면 ("", 0, "")."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=5, creationflags=0x08000000)
        line = (out.stdout or "").strip().splitlines()
        if not line:
            return "", 0, ""
        parts = [p.strip() for p in line[0].split(",")]
        vram = int(parts[1].split()[0]) if len(parts) > 1 and parts[1].split() and parts[1].split()[0].isdigit() else 0
        return parts[0], vram, (parts[2] if len(parts) > 2 else "")
    except (OSError, ValueError, subprocess.SubprocessError):
        return "", 0, ""


_cached = None


def detect(refresh=False):
    """장치 정보 (한 번만 묻고 캐시)."""
    global _cached
    if _cached is not None and not refresh:
        return _cached
    info = DeviceInfo()
    info.forced_cpu = force_cpu_reason()
    if info.forced_cpu:                          # CUDA 를 전혀 건드리지 않는다 (DLL 등록 · 장치 조회 생략)
        try:
            import ctranslate2
            info.cpu_compute_types = sorted(ctranslate2.get_supported_compute_types("cpu"))
        except Exception as e:
            info.error = "{0!r}".format(e)
        _cached = info
        return info
    info.dll_dirs = add_nvidia_dlls()
    try:
        import ctranslate2
        info.cuda_devices = ctranslate2.get_cuda_device_count()
        info.cpu_compute_types = sorted(ctranslate2.get_supported_compute_types("cpu"))
        if info.cuda_devices:
            info.cuda_compute_types = sorted(ctranslate2.get_supported_compute_types("cuda"))
    except Exception as e:                       # DLL 누락 · 드라이버 문제 - CPU 로 간다
        info.error = "{0!r}".format(e)
    if info.cuda_devices:
        info.gpu_name, info.gpu_vram_mb, info.driver = _nvidia_smi()
    _cached = info
    return info


def choose(preference="auto"):
    """요청 -> (device, compute_type, note). note 는 폴백했을 때만 채워진다 (UI 가 W21 로 올린다)."""
    info = detect()
    if info.forced_cpu:
        return "cpu", "int8", ("" if preference in ("auto", "cpu:int8") else
                               "CPU forced ({0}) - CUDA was not used".format(info.forced_cpu))
    if preference in ("auto", "cuda:float16", "cuda:int8_float16"):
        if info.cuda_devices:
            want = "float16" if preference in ("auto", "cuda:float16") else "int8_float16"
            if want in info.cuda_compute_types or not info.cuda_compute_types:
                return "cuda", want, ""
            return "cuda", "float16", "{0} is not supported on this GPU - using float16".format(want)
        if preference == "auto":
            return "cpu", "int8", ""
        return "cpu", "int8", "no CUDA device ({0}) - falling back to CPU int8 (slow)".format(
            info.error or "none found")
    return "cpu", "int8", ""
