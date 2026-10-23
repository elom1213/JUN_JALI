# -*- coding: utf-8 -*-
# STT Converter - 코어 시험 (헤드리스, 모델 없음 - fake_engine). 사전 검사 · 일괄 변환 · 경고 코드 · 기존 파일 정책 ·
# VAD 자동 · CPU 폴백 · 중단. 사용: .venv_stt\Scripts\python.exe tools\STT_Converter\tests\test_core.py <작업 폴더>
import json
import os
import shutil
import sys
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools.STT_Converter.app.core import converter, job, output_writer          # noqa: E402
from tools.STT_Converter.app.core.engines import EngineError, TranscribeOptions  # noqa: E402
from fake_engine import FakeEngine                                               # noqa: E402

results = []


def check(name, cond):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def make_wav(path, seconds, rate=44100):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))


def main(work):
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    short = os.path.join(work, "clip_short.wav")        # 1.5 s -> VAD auto = off
    long_ = os.path.join(work, "clip_long.wav")         # 12 s  -> VAD auto = on
    num = os.path.join(work, "clip_num.wav")
    ja = os.path.join(work, "clip_ja.wav")
    empty = os.path.join(work, "clip_empty.wav")
    rep = os.path.join(work, "clip_rep.wav")
    fail = os.path.join(work, "clip_fail.wav")
    zero = os.path.join(work, "zero.wav")
    for p, s in ((short, 1.5), (long_, 12.0), (num, 2.0), (ja, 2.0), (empty, 1.5), (rep, 3.0), (fail, 2.0)):
        make_wav(p, s)
    with open(zero, "wb") as f:
        f.write(b"RIFF")
    logs = []
    log = lambda lv, m: logs.append((lv, m))   # noqa: E731

    # ---------------------------------------------------------------- 사전 검사
    jobs, problems = job.preflight([short, zero, os.path.join(work, "missing.wav"), short], "Korean", "", ".lab",
                                   "skip", FakeEngine)
    codes = [p[1] for p in problems]
    check("preflight: broken + missing wav -> E42 x2, duplicates removed", codes == ["E42", "E42"] and len(jobs) == 1)
    jobs, problems = job.preflight([short], "Korean", "", ".doc", "skip", FakeEngine)
    check("preflight: unknown extension -> E43", [p[1] for p in problems] == ["E43"])
    out_dir = os.path.join(work, "out")
    jobs, problems = job.preflight([short, long_], "Korean", out_dir, ".lab", "skip", FakeEngine)
    check("preflight: output folder created and writable", not problems and os.path.isdir(out_dir)
          and jobs[0].out_path == os.path.join(out_dir, "clip_short.lab")
          and jobs[0].json_path == os.path.join(out_dir, "clip_short.stt.json"))
    jobs, problems = job.preflight([short], "Korean", "", ".txt", "skip", FakeEngine)
    check("preflight: .txt -> W26", [w[0] for w in jobs[0].warnings] == ["W26"])

    # ---------------------------------------------------------------- 변환 (VAD auto · 정규화 · 경고 · json)
    jobs, problems = job.preflight([short, long_, num, ja, empty, rep, fail], "Korean", out_dir, ".lab", "skip",
                                   FakeEngine)
    FakeEngine.calls = []
    engine = FakeEngine("fake-model", "cpu", "int8")
    written, reason = converter.run_batch(engine, jobs, TranscribeOptions(vad="auto"),
                                          converter.NormalizeConfig(user_dict={"KWI": "케이더블유아이"}),
                                          log=log)
    check("batch: no stop reason", reason == "")
    check("batch: 5 transcripts written (empty + fail skipped)", len(written) == 5)
    vad_by = {c[0]: c[2] for c in FakeEngine.calls}
    check("vad auto: off for 1.5 s, on for 12 s", vad_by["clip_short.wav"] is False and vad_by["clip_long.wav"] is True)
    lab = open(os.path.join(out_dir, "clip_short.lab"), "rb").read()
    check("lab: UTF-8 without BOM, one trailing newline", lab == "안녕하세요 테스트입니다\n".encode("utf-8"))
    num_lab = open(os.path.join(out_dir, "clip_num.lab"), encoding="utf-8").read()
    check("normalize: 1등 -> 일등, user dict KWI", num_lab == "일등이 될 거예요 케이더블유아이\n")
    j = json.load(open(os.path.join(out_dir, "clip_num.stt.json"), encoding="utf-8"))
    check("json: raw text kept, replaced list, engine/device, segments with words",
          j["raw_text"] == "1등이 될 거예요 KWI" and j["text"] == "일등이 될 거예요 케이더블유아이"
          and sorted(r[0] for r in j["replaced"]) == ["1등", "KWI"] and j["engine"] == "fake" and j["device"] == "cpu"
          and j["segments"][0]["words"][0][2] == "1등이" and j["options"]["vad"] is False)
    msgs = [m for _lv, m in logs]
    check("W20 detected language differs", any("W20" in m and "clip_ja" in m for m in msgs))
    check("W22 empty result: json only, no lab", any("W22" in m for m in msgs)
          and not os.path.isfile(os.path.join(out_dir, "clip_empty.lab"))
          and os.path.isfile(os.path.join(out_dir, "clip_empty.stt.json")))
    check("W24 repeated n-gram / compression ratio", any("W24" in m and "clip_rep" in m for m in msgs))
    check("E45 one file fails -> skipped, batch continues", any("E45" in m and "skipped" in m for m in msgs)
          and os.path.isfile(os.path.join(out_dir, "clip_rep.lab")))
    check("VAD off logged for short clips", any("VAD off" in m and "clip_short" in m for m in msgs))

    # ---------------------------------------------------------------- 기존 파일 정책
    logs[:] = []
    jobs, _ = job.preflight([short], "Korean", out_dir, ".lab", "skip", FakeEngine)
    check("existing skip: job.skipped + W25", jobs[0].skipped and jobs[0].warnings[0][0] == "W25")
    written, reason = converter.run_batch(engine, jobs, log=log)
    check("existing skip: nothing written, W25 logged", written == [] and any("W25" in m for _l, m in logs))
    with open(os.path.join(out_dir, "clip_short.lab"), "w", encoding="utf-8") as f:
        f.write("hand written\n")
    jobs, _ = job.preflight([short], "Korean", out_dir, ".lab", "backup", FakeEngine)
    written, reason = converter.run_batch(engine, jobs, existing="backup", log=log)
    check("existing backup: .bak holds the old text, new lab written",
          open(os.path.join(out_dir, "clip_short.lab.bak"), encoding="utf-8").read() == "hand written\n"
          and open(os.path.join(out_dir, "clip_short.lab"), encoding="utf-8").read() == "안녕하세요 테스트입니다\n")
    jobs, _ = job.preflight([short], "Korean", out_dir, ".lab", "overwrite", FakeEngine)
    check("existing overwrite: W27 warning, not skipped", not jobs[0].skipped and jobs[0].warnings[0][0] == "W27")

    # ---------------------------------------------------------------- CPU 폴백 (E44 -> W21) · 중단
    logs[:] = []
    jobs, _ = job.preflight([short, long_], "Korean", os.path.join(work, "out2"), ".lab", "skip", FakeEngine)
    cuda_engine = FakeEngine("fake-model", "cuda", "float16")
    written, reason = converter.run_batch(cuda_engine, jobs, log=log,
                                          fallback_factory=lambda: FakeEngine("fake-model", "cpu", "int8"))
    check("E44 on CUDA -> W21 fallback to CPU, batch completes", reason == "" and len(written) == 2
          and any("W21" in m for _l, m in logs))
    jobs, _ = job.preflight([short, long_], "Korean", os.path.join(work, "out3"), ".lab", "skip", FakeEngine)
    written, reason = converter.run_batch(cuda_engine, jobs, log=log)
    check("E44 without fallback -> stopped, nothing written", reason.startswith("Stopped: E44") and written == [])
    jobs, _ = job.preflight([short, long_], "Korean", os.path.join(work, "out4"), ".lab", "skip", FakeEngine)
    n = {"calls": 0}

    def stop_after_first():
        n["calls"] += 1
        return n["calls"] > 1
    written, reason = converter.run_batch(engine, jobs, log=log, should_stop=stop_after_first)
    check("stop after the first file", reason == "stopped by user" and len(written) == 1)

    # ---------------------------------------------------------------- 출력 경로 · 쓰기
    out_path, json_path = job.output_paths(r"C:\x\y\name.wav", "", ".txt")
    check("output_paths next to wav", out_path == os.path.join(r"C:\x\y", "name.txt")
          and json_path == os.path.join(r"C:\x\y", "name.stt.json"))
    p = os.path.join(work, "t.lab")
    output_writer.write_transcript(p, "a\n\n")
    check("write_transcript trims extra newlines", open(p, "rb").read() == b"a\n")

    n_fail = results.count(False)
    print("\n{0} checks, {1} failed".format(len(results), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("TEMP", "."), "stt_test_core")))
