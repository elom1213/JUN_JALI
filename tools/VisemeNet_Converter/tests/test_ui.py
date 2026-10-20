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
    wait_worker(win)
    log = win.log_view.toPlainText()
    check("48k stops the batch with E03", "E03 sample rate 48000 Hz" in log and "Nothing was converted" in log)
    check("no output written", not os.path.isdir(out_dir) or not os.listdir(out_dir))
    check("buttons enabled again", win.btn_convert.isEnabled() and not win.btn_stop.isEnabled())

    # 2) 정상 변환
    win.on_clear()
    win._add_paths([coffee, os.path.join(work, "한글 폴더")])
    win.log_view.clear()
    win.on_convert()
    wait_worker(win)
    log = win.log_view.toPlainText()
    check("2 files converted", "[DONE] 2 converted" in log)
    check("korean path ok", os.path.isfile(os.path.join(out_dir, "한글_ok.txt")))
    check("json written", os.path.isfile(os.path.join(out_dir, "coffee_xxxx.visemenet.json")))
    check("progress done", win.progress.format().startswith("Done"))

    # 3) 다시 Convert -> 이미 있음 E09
    win.log_view.clear()
    win.on_convert()
    wait_worker(win)
    check("existing -> E09", "E09 output exists" in win.log_view.toPlainText())

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
