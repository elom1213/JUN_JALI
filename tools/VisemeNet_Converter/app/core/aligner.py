# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-20
# VisemeNet Converter - Montreal Forced Aligner(MFA) 호출 + TextGrid 읽기 (UI 비의존)
#
# docs/0060_transcript_mfa_plan.md §3. MFA 는 setup_mfa.bat 이 따로 설치한다(추론 .venv 와 섞지 않는다).
# 설치 위치는 저장소의 mfa_path.local.txt (setup_mfa.bat 이 씀) 또는 변환기 설정의 MFA 폴더.
#   <folder>\env\Scripts\mfa.exe    MFA
#   <folder>\models\                MFA_ROOT_DIR (모델 · 사전 · MFA 임시 파일)
#
# 정렬 한 번에 MFA 시작 비용(수십 초)이 들어서, 일괄 변환은 파일을 한 말뭉치(corpus)로 묶어 **한 번에** 정렬한다.
# 입력 wav 는 모노 16-bit 사본을 임시 폴더에 만들어 넘긴다 - 원본은 건드리지 않는다.

import os
import re
import shutil
import subprocess
import tempfile
import time

import numpy as np


PATH_FILE = "mfa_path.local.txt"
LANGUAGES = {
    # UI 이름: (MFA 음향 모델, 사전, G2P 모델 - 사전에 없는 단어의 발음을 만든다)
    "English": ("english_mfa", "english_mfa", "english_us_mfa"),
    "Korean": ("korean_mfa", "korean_mfa", "korean_mfa"),
    "Japanese": ("japanese_mfa", "japanese_mfa", "japanese_mfa"),
}
TRANSCRIPT_EXTS = (".lab", ".txt")
ALIGN_TIMEOUT_SEC = 1800


class AlignError(Exception):
    """정렬 전 · 정렬 중 문제. code 는 E30 ~ E33 (멈춤)."""

    def __init__(self, code, message, detail=None):
        super().__init__("{0} {1}".format(code, message))
        self.code = code
        self.message = message
        self.detail = detail


# ------------------------------------------------------------------ 설치 찾기

class MfaInstall(object):
    def __init__(self, folder):
        self.folder = os.path.abspath(folder)
        self.env = os.path.join(self.folder, "env")
        self.models = os.path.join(self.folder, "models")
        self.exe = os.path.join(self.env, "Scripts", "mfa.exe")

    @property
    def ok(self):
        return os.path.isfile(self.exe)

    def environ(self):
        """conda activate 와 같은 PATH (Library\\bin 의 DLL) + MFA_ROOT_DIR."""
        env = dict(os.environ)
        extra = [self.env, os.path.join(self.env, "Library", "mingw-w64", "bin"),
                 os.path.join(self.env, "Library", "usr", "bin"), os.path.join(self.env, "Library", "bin"),
                 os.path.join(self.env, "Scripts"), os.path.join(self.env, "bin")]
        env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "")])
        env["CONDA_PREFIX"] = self.env
        env["MFA_ROOT_DIR"] = self.models
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONNOUSERSITE"] = "1"                   # %APPDATA%\Python\Python311 의 패키지가 섞이지 않게
        # 추론 .venv · PC 의 다른 파이썬(예: PYTHONPATH 를 건 3.14) · 다른 conda 설정이 MFA 로 새지 않게
        for key in ("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
                    "CONDA_SHLVL", "CONDA_EXE", "CONDA_PYTHON_EXE", "_CE_CONDA", "_CE_M"):
            env.pop(key, None)
        return env


def find_install(repo_root, folder=""):
    """folder(설정값) -> mfa_path.local.txt 순으로 찾는다. 없으면 None."""
    candidates = []
    if folder:
        candidates.append(folder)
    path_file = os.path.join(repo_root, PATH_FILE)
    if os.path.isfile(path_file):
        try:
            with open(path_file, "r", encoding="utf-8-sig", errors="replace") as f:
                line = f.readline().strip()
            if line:
                candidates.append(line)
        except OSError:
            pass
    candidates.append(os.path.join(repo_root, ".mfa"))
    for c in candidates:
        inst = MfaInstall(c)
        if inst.ok:
            return inst
    return None


def check_models(inst, language):
    """언어 모델 · 사전이 내려받아져 있는지. 없으면 AlignError(E31)."""
    acoustic, dictionary, g2p = LANGUAGES[language]
    pm = os.path.join(inst.models, "pretrained_models")
    a = os.path.join(pm, "acoustic", acoustic + ".zip")
    d = os.path.join(pm, "dictionary", dictionary + ".dict")
    g = os.path.join(pm, "g2p", g2p + ".zip")
    missing = [p for p in (a, d, g) if not os.path.isfile(p)]
    if missing:
        raise AlignError("E31", "MFA model missing for {0} - run setup_mfa.bat again".format(language),
                         detail=", ".join(missing))


# ------------------------------------------------------------------ 대본

def transcript_path(wav_path):
    """wav 옆의 대본 - <이름>.lab 우선, 없으면 <이름>.txt (VisemeNet 결과 txt 는 제외). 없으면 None."""
    stem = os.path.splitext(wav_path)[0]
    for ext in TRANSCRIPT_EXTS:
        p = stem + ext
        if os.path.isfile(p) and not looks_like_viseme_txt(p):
            return p
    return None


def looks_like_viseme_txt(path):
    """VisemeNet 결과(<이름>.txt, 숫자 22열)인가 - 같은 이름의 대본과 구분한다."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            first = f.readline().split()
    except OSError:
        return False
    if len(first) < 2:
        return False
    try:
        [float(x) for x in first]
        return True
    except ValueError:
        return False


def read_transcript(path):
    """UTF-8 (BOM 허용) 대본 -> 한 줄 문자열. 비었거나 못 읽으면 AlignError(E32)."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            text = f.read()
    except UnicodeDecodeError:
        raise AlignError("E32", "transcript is not UTF-8: {0}".format(os.path.basename(path)))
    except OSError as e:
        raise AlignError("E32", "cannot read transcript {0}: {1}".format(os.path.basename(path), e.strerror))
    text = " ".join(text.split())
    if not text:
        raise AlignError("E32", "transcript is empty: {0}".format(os.path.basename(path)))
    return text


# ------------------------------------------------------------------ 정렬

class AlignResult(object):
    def __init__(self, key, textgrid_path):
        self.key = key
        self.textgrid_path = textgrid_path
        self.tiers = parse_textgrid(textgrid_path) if textgrid_path else {}

    @property
    def ok(self):
        return bool(self.tiers.get("phones"))

    @property
    def phones(self):
        return self.tiers.get("phones", [])

    @property
    def words(self):
        return self.tiers.get("words", [])


def align(inst, language, items, log=None, keep_dir=None):
    """여러 (key, wav, transcript_text) 를 한 번에 정렬한다.

    Returns:
        {key: AlignResult} - 정렬에 실패한 파일은 AlignResult.ok 가 False (멈추지 않는다 - W10 으로 처리).
    Raises:
        AlignError(E33) - MFA 자체가 실행되지 않을 때.
    """
    from scipy.io import wavfile

    acoustic, dictionary, g2p = LANGUAGES[language]
    work = tempfile.mkdtemp(prefix="jun_jali_mfa_")
    corpus = os.path.join(work, "corpus")
    out_dir = os.path.join(work, "aligned")
    os.makedirs(corpus)
    names = {}
    try:
        for i, (key, wav, text) in enumerate(items):
            name = "utt{0:03d}".format(i)               # ASCII 이름 - 한글 경로 · 같은 이름 문제를 피한다
            names[key] = name
            rate, data = wavfile.read(wav)              # wav_check 가 이미 16-bit PCM 임을 확인했다
            mono = data.reshape(len(data), -1).mean(axis=1).round().astype(np.int16)
            wavfile.write(os.path.join(corpus, name + ".wav"), rate, mono)
            with open(os.path.join(corpus, name + ".lab"), "w", encoding="utf-8") as f:
                f.write(text + "\n")

        g2p_path = os.path.join(inst.models, "pretrained_models", "g2p", g2p + ".zip")
        cmd = [inst.exe, "align", corpus, dictionary, acoustic, out_dir,
               "--clean", "--single_speaker", "--final_clean", "--overwrite", "--g2p_model_path", g2p_path]
        if log:
            log("INFO", "MFA align: {0} file(s), {1} ({2} / {3})".format(len(items), language, acoustic, dictionary))
        t = time.time()
        proc = _run(inst, cmd)
        if log:
            log("INFO", "MFA finished in {0:.1f} s".format(time.time() - t))
        results = {}
        for key, name in names.items():
            tg = os.path.join(out_dir, name + ".TextGrid")
            results[key] = AlignResult(key, tg if os.path.isfile(tg) else None)
        if proc.returncode != 0 and not any(r.ok for r in results.values()):
            raise AlignError("E33", "MFA align failed (exit code {0})".format(proc.returncode),
                             detail=_tail(proc.stdout, 12))
        return results
    finally:
        if keep_dir:
            shutil.rmtree(keep_dir, ignore_errors=True)
            shutil.copytree(work, keep_dir)
        shutil.rmtree(work, ignore_errors=True)


def version(inst):
    proc = _run(inst, [inst.exe, "version"], timeout=120)
    return (proc.stdout or "").strip().splitlines()[-1] if proc.returncode == 0 and proc.stdout else ""


def _run(inst, cmd, timeout=ALIGN_TIMEOUT_SEC):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        return subprocess.run(cmd, env=inst.environ(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace",
                              timeout=timeout, creationflags=flags)
    except FileNotFoundError:
        raise AlignError("E30", "MFA not found - set the MFA folder in Settings or run setup_mfa.bat")
    except subprocess.TimeoutExpired:
        raise AlignError("E33", "MFA did not finish in {0} s".format(timeout))


def _tail(text, n):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return "\n".join(lines[-n:])


# ------------------------------------------------------------------ TextGrid

_ITEM_RE = re.compile(r'^\s*(xmin|xmax|text|name|class)\s*=\s*(.*?)\s*$')


def parse_textgrid(path):
    """Praat TextGrid (long text format - MFA 기본 출력) -> {tier 이름: [(start, end, label)]}.

    짧은 형식(short)도 읽는다: 숫자 · 문자열 토큰을 순서대로 해석한다.
    """
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    if "item [" in text or "intervals [" in text:
        return _parse_long(text)
    return _parse_short(text)


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1].replace('""', '"')
    return s


def _parse_long(text):
    tiers = {}
    current = None
    interval = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("item ["):
            current = None
            continue
        if stripped.startswith("intervals ["):
            interval = {}
            continue
        m = _ITEM_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if key == "name":
            current = tiers.setdefault(_unquote(value), [])
            interval = None
        elif current is not None and interval is not None:
            if key in ("xmin", "xmax"):
                interval[key] = float(value)
            elif key == "text":
                interval["text"] = _unquote(value)
                if "xmin" in interval and "xmax" in interval:
                    current.append((interval["xmin"], interval["xmax"], interval["text"]))
                interval = None
    return tiers


def _parse_short(text):
    tokens = re.findall(r'"(?:[^"]|"")*"|[-+0-9.eE]+', text)
    vals = [_unquote(t) if t.startswith('"') else t for t in tokens]
    tiers = {}
    i = 0
    # "ooTextFile" "TextGrid" xmin xmax <exists> n_tiers
    while i < len(vals) and vals[i] != "IntervalTier":
        i += 1
    while i < len(vals):
        if vals[i] != "IntervalTier":
            i += 1
            continue
        name = vals[i + 1]
        n = int(float(vals[i + 4]))
        i += 5
        items = []
        for _ in range(n):
            items.append((float(vals[i]), float(vals[i + 1]), vals[i + 2]))
            i += 3
        tiers[name] = items
    return tiers
