# -*- coding: utf-8 -*-
# STT Converter - 오프스크린 UI 시험 (실제 버튼 경로: Check Files · Convert -> 워커 -> 팝업 -> 로그). 모델 없이 fake_engine.
# 사용: .venv_stt\Scripts\python.exe tools\STT_Converter\tests\test_ui.py <작업 폴더>
import os
import shutil
import sys
import wave

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for p in (ROOT, os.path.join(ROOT, "vendor")):
    sys.path.insert(0, p)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Framework.qt.qt import QApplication, QEventLoop, QTimer, QProgressBar   # noqa: E402
from Framework.themes.theme_manager import ThemeManager                       # noqa: E402
from tools.STT_Converter.app.core import device, settings                     # noqa: E402
from tools.STT_Converter.app.ui import main_window as mw                      # noqa: E402
from fake_engine import FakeEngine                                             # noqa: E402

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


def wait_worker(win, timeout_ms=60000):
    loop = QEventLoop()
    win._worker.finished_batch.connect(lambda *a: QTimer.singleShot(0, loop.quit))
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


def wait_ms(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class PopupWatch(object):
    def __init__(self, win):
        self.dlg = win._popup
        self.values = []
        self.phases = []
        self.visible_during = self.dlg is not None and self.dlg.isVisible()
        self.timer = QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self._sample)
        self._sample()
        self.timer.start()

    def _sample(self):
        try:
            self.values.append(self.dlg.bar.value())
            text = self.dlg.lbl_phase.text()
            if not self.phases or self.phases[-1] != text:
                self.phases.append(text)
        except RuntimeError:
            self.timer.stop()

    def stop(self):
        self.timer.stop()
        self._sample()
        self.monotonic = all(b >= a for a, b in zip(self.values, self.values[1:]))
        self.final = self.values[-1] if self.values else -1


def main(work):
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    settings._PATH = os.path.join(work, "ui_settings.json")
    settings.DATA_DIR = work                                     # 사용자 사전도 작업 폴더에
    mw.make_engine = lambda name, model, dev, compute, cache="": FakeEngine(model, dev, compute, cache)
    FakeEngine.delay = 0.3                                   # 팝업 단계가 20 ms 샘플링에 잡히게
    short = os.path.join(work, "clip_short.wav")
    long_ = os.path.join(work, "한글 폴더", "clip_long.wav")
    os.makedirs(os.path.dirname(long_))
    make_wav(short, 1.5)
    make_wav(long_, 12.0)
    with open(os.path.join(work, "zero.wav"), "wb") as f:
        f.write(b"RIFF")

    app = QApplication.instance() or QApplication(sys.argv)
    ThemeManager.load_theme_dev(app, "dark")
    win = mw.MainWindow()
    win.show()
    check("window title", win.windowTitle().startswith("STT Converter v"))
    forced = bool(device.force_cpu_reason())
    check("device combo locked to CPU when CUDA is disabled on this PC",
          win.cmb_device.isEnabled() == (not forced) and (not forced or win.cmb_device.currentData() == "cpu:int8"))
    out_dir = os.path.join(work, "ui_out")

    # 1) 나쁜 파일이 섞이면 멈추고 아무것도 안 쓴다
    win._add_paths([short, os.path.join(work, "zero.wav"), os.path.join(work, "readme.txt")])
    check("list has 2 wavs (txt skipped)", win.tsl.count() == 2)
    win.le_out.setText(out_dir)
    win.cmb_lang.setCurrentIndex(win.cmb_lang.findText("Korean"))
    win.on_check()
    log = win.log_view.toPlainText()
    check("Check Files reports E42 and would stop", "E42" in log and "would stop the conversion" in log)
    win.log_view.clear()
    win.on_convert()
    watch = PopupWatch(win)
    wait_worker(win)
    watch.stop()
    log = win.log_view.toPlainText()
    check("Convert with a broken wav: E42, nothing converted", "E42" in log and "Nothing was converted" in log)
    check("popup closed at once on failure (no fake 100 %)", win._popup is None and watch.final < 100)
    check("no output written", not os.path.isdir(out_dir) or not os.listdir(out_dir))
    check("buttons enabled again", win.btn_convert.isEnabled() and not win.btn_stop.isEnabled())

    # 2) 정상 변환 (짧은 클립 + 한글 폴더의 긴 클립)
    win.on_clear()
    win._add_paths([short, os.path.dirname(long_)])
    win.log_view.clear()
    FakeEngine.calls = []
    win.on_convert()
    watch = PopupWatch(win)
    dlg = win._popup
    check("popup is a modal gauge window", watch.visible_during and dlg.isModal()
          and isinstance(dlg.bar, QProgressBar) and dlg.btn_cancel.text() == "Stop")
    wait_worker(win)
    watch.stop()
    log = win.log_view.toPlainText()
    check("2 transcripts written", "[DONE] 2 transcript(s) written" in log)
    check("lab files in the output folder", os.path.isfile(os.path.join(out_dir, "clip_short.lab"))
          and os.path.isfile(os.path.join(out_dir, "clip_long.lab"))
          and os.path.isfile(os.path.join(out_dir, "clip_long.stt.json")))
    check("VAD auto: off for the short clip, on for the long one",
          {c[0]: c[2] for c in FakeEngine.calls} == {"clip_short.wav": False, "clip_long.wav": True})
    check("popup gauge fills up (never goes back), ends at 100", watch.monotonic and watch.final == 100)
    print("      popup phases:", watch.phases)
    check("popup phases: check -> load -> transcribe -> done",
          watch.phases == ["Checking files", "Loading model", "Transcribing", "Done"])
    wait_ms(800)
    try:
        closed = not dlg.isVisible()
    except RuntimeError:
        closed = True
    check("popup closes after showing 100 %", closed)
    check("progress bar says Done", win.progress.format().startswith("Done"))

    # 3) 다시 Convert -> 기존 대본은 Skip (W25), 아무것도 안 씀
    win.log_view.clear()
    win.on_convert()
    wait_worker(win)
    log = win.log_view.toPlainText()
    check("existing -> W25 skipped, 0 written", "W25" in log and "[DONE] 0 transcript(s) written" in log)
    check("popup closed", win._popup is None)

    # 3b) Overwrite + 팝업 Stop = 첫 파일 뒤 중단 (모델은 이미 있으니 Loading model 단계 없음)
    win.log_view.clear()
    win._set_combo_data(win.cmb_existing, "overwrite")
    win.on_convert()
    watch = PopupWatch(win)
    popup = win._popup
    win._worker.progress.connect(lambda d, t, n: popup.btn_cancel.click() if d == 0 else None)
    wait_worker(win)
    watch.stop()
    log = win.log_view.toPlainText()
    check("popup Stop = main Stop: stops after the current file", "Stop requested" in log
          and "stopped by user" in log and "Files already written: 1" in log)
    print("      popup phases:", watch.phases)
    check("no Loading model phase on the second run", "Loading model" not in watch.phases
          and watch.phases[:2] == ["Checking files", "Transcribing"])
    win._set_combo_data(win.cmb_existing, "skip")

    # 4) 사용자 사전 다이얼로그 -> 저장 -> 정규화에 반영
    dlg = mw.UserDictDialog("Korean", win)
    dlg.edit.setPlainText("KWI = 케이더블유아이\nbad line\n  = empty key")
    check("user dict parse", dlg.mapping() == {"KWI": "케이더블유아이"})
    settings.save_user_dict("Korean", dlg.mapping())
    check("user dict saved under DATA_DIR", settings.load_user_dict("Korean") == {"KWI": "케이더블유아이"}
          and os.path.isfile(os.path.join(work, "user_dict_ko.json")))

    # 5) 설정 저장 / 복원
    n_items = win.tsl.count()
    win.cmb_lang.setCurrentIndex(win.cmb_lang.findText("Japanese"))
    win.cb_kana.setChecked(True)
    win.close()
    win2 = mw.MainWindow()
    check("settings restored", win2.tsl.count() == n_items and win2.le_out.text() == out_dir
          and win2.cmb_lang.currentText() == "Japanese" and win2.cb_kana.isChecked())
    win2.close()

    n_fail = results.count(False)
    print("\n{0} checks, {1} failed".format(len(results), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("TEMP", "."), "stt_test_ui")))
