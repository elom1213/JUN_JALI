# -*- coding: utf-8 -*-
# VisemeNet Converter - 오프스크린 UI 시험 (실제 버튼 경로: Convert -> 워커 -> 로그)
# 사용: .venv\Scripts\python tools\VisemeNet_Converter\tests\test_ui.py <작업 폴더(make_bad_wavs 결과)>
import os
import shutil
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for p in (ROOT, os.path.join(ROOT, "vendor")):
    sys.path.insert(0, p)

from Framework.qt.qt import QApplication, QEventLoop, QTimer           # noqa: E402
from Framework.qt.qt import QProgressBar                                # noqa: E402
from Framework.themes.theme_manager import ThemeManager                 # noqa: E402
from tools.VisemeNet_Converter.app.core import settings                 # noqa: E402
from tools.VisemeNet_Converter.app.ui import main_window as mw          # noqa: E402

results = []


def check(name, cond):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name)


def wait_worker(win, timeout_ms=180000):
    loop = QEventLoop()
    win._worker.finished_batch.connect(lambda *a: QTimer.singleShot(0, loop.quit))
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


def wait_ms(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class PopupWatch(object):
    """변환 중 팝업이 떠 있고 게이지가 단조 증가하는지, 끝나면 100% 뒤 닫히는지 본다."""

    def __init__(self, win):
        self.dlg = win._popup
        self.values = []
        self.phases = []
        self.visible_during = self.dlg is not None and self.dlg.isVisible()
        self.timer = QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self._sample)
        self._sample()                      # 검사 단계는 20 ms 보다 짧을 수 있다 - 지금 라벨부터 담는다
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
        self._sample()                      # 끝난 직후 상태(Done · 100 %)
        self.monotonic = all(b >= a for a, b in zip(self.values, self.values[1:]))
        self.final = self.values[-1] if self.values else -1


def main(work):
    settings._PATH = os.path.join(work, "ui_settings.json")       # 실제 설정 파일을 건드리지 않게
    app = QApplication.instance() or QApplication(sys.argv)
    ThemeManager.load_theme_dev(app, "dark")
    win = mw.MainWindow()
    win.show()
    check("window title", win.windowTitle().startswith("VisemeNet Converter v"))

    out_dir = os.path.join(work, "ui_out")
    shutil.rmtree(out_dir, ignore_errors=True)
    coffee = os.path.join(ROOT, "test_audio", "coffee_xxxx.wav")

    # 1) 나쁜 파일이 섞이면 멈추고 아무것도 안 쓴다
    win._add_paths([coffee, os.path.join(work, "rate_48k.wav"), os.path.join(work, "readme.txt")])
    check("list has 2 wavs (txt skipped)", win.tsl.count() == 2)
    win.le_out.setText(out_dir)
    win.on_convert()
    watch = PopupWatch(win)
    wait_worker(win)
    watch.stop()
    log = win.log_view.toPlainText()
    check("48k stops the batch with E03", "E03 sample rate 48000 Hz" in log and "Nothing was converted" in log)
    check("popup shown during the failed check", watch.visible_during)
    check("popup closed at once on failure (no fake 100 %)", win._popup is None and watch.final < 100)
    check("no output written", not os.path.isdir(out_dir) or not os.listdir(out_dir))
    check("buttons enabled again", win.btn_convert.isEnabled() and not win.btn_stop.isEnabled())

    # 2) 정상 변환
    win.on_clear()
    win._add_paths([coffee, os.path.join(work, "한글 폴더")])
    win.log_view.clear()
    win.on_convert()
    watch = PopupWatch(win)
    dlg = win._popup
    check("popup is a modal gauge window", watch.visible_during and dlg.isModal()
          and isinstance(dlg.bar, QProgressBar) and dlg.btn_cancel.text() == "Stop")
    wait_ms(300)
    early = dlg.bar.value()
    wait_worker(win)
    watch.stop()
    log = win.log_view.toPlainText()
    check("2 files converted", "[DONE] 2 converted" in log)
    check("popup gauge fills up (0 -> 100, never goes back)", watch.monotonic and watch.final == 100
          and 0 <= early < 100)
    print("      popup phases:", watch.phases)
    check("popup phases: check -> load -> convert -> done",
          watch.phases == ["Checking files", "Loading model", "Converting", "Done"])
    check("popup still at 100 % right after the batch", win._popup is None and dlg.isVisible()
          and dlg.bar.value() == 100)
    wait_ms(800)
    try:
        closed = not dlg.isVisible()
    except RuntimeError:
        closed = True
    check("popup closes after showing 100 %", closed)
    check("korean path ok", os.path.isfile(os.path.join(out_dir, "한글_ok.txt")))
    check("json written", os.path.isfile(os.path.join(out_dir, "coffee_xxxx.visemenet.json")))
    check("progress done", win.progress.format().startswith("Done"))

    # 3) 다시 Convert -> 이미 있음 E09
    win.log_view.clear()
    win.on_convert()
    wait_worker(win)
    check("existing -> E09", "E09 output exists" in win.log_view.toPlainText())
    check("popup closed after E09", win._popup is None)

    # 3b) 팝업의 Stop = 메인 창 Stop (모델은 이미 있으니 Loading model 단계는 없다)
    win.log_view.clear()
    win.cb_overwrite.setChecked(True)
    win.on_convert()
    watch = PopupWatch(win)
    popup = win._popup
    win._worker.progress.connect(lambda d, t, n: popup.btn_cancel.click() if d == 0 else None)
    wait_worker(win)
    watch.stop()
    log = win.log_view.toPlainText()
    check("popup Stop = main Stop: stops after the current file", "Stop requested" in log
          and "stopped by user before" in log and "Files already written: 1" in log)
    print("      popup phases:", watch.phases)
    check("popup closed on stop, no Loading model phase", win._popup is None
          and "Loading model" not in watch.phases and watch.phases[:2] == ["Checking files", "Converting"])
    win.cb_overwrite.setChecked(False)

    # 4) Check Files 버튼
    win.log_view.clear()
    win.cb_overwrite.setChecked(True)
    win.on_check()
    check("check passes with overwrite", "[DONE] All 2 file(s) passed the check." in win.log_view.toPlainText())

    # 5) Correct 모드 (대본 + MFA) - setup_mfa.bat 을 실행한 PC 에서만
    has_mfa = mw.aligner.find_install(ROOT) is not None
    check("transcript widgets off in Audio only mode", not win.cmb_lang.isEnabled())
    win.cmb_align.setCurrentIndex(1)
    check("transcript widgets on in Correct mode", win.cmb_lang.isEnabled() and win.le_mfa.isEnabled())
    if has_mfa:
        win.on_clear()
        win._add_paths([coffee])
        win.log_view.clear()
        win.on_convert()
        wait_worker(win, 600000)
        log = win.log_view.toPlainText()
        check("correct mode: aligned and corrected", "MFA align: 1 file(s)" in log and "corrected" in log)
        check("correct mode: phones.json written", os.path.isfile(os.path.join(out_dir, "coffee_xxxx.phones.json")))
    else:
        print("SKIP correct-mode conversion (MFA not installed - run setup_mfa.bat)")

    # 6) 설정 저장 / 복원
    n_items = win.tsl.count()
    win.close()
    win2 = mw.MainWindow()
    check("settings restored", win2.tsl.count() == n_items and win2.le_out.text() == out_dir
          and win2.cb_overwrite.isChecked() and win2.cmb_align.currentIndex() == 1)
    win2.close()

    print("RESULT", "OK" if all(results) else "{0} FAILED".format(results.count(False)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
