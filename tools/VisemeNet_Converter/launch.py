# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# VisemeNet Converter - 실행 진입점 (Run_VisemeNet_Converter.bat 이 .venv 의 pythonw 로 부른다)
#
# sys.path : 저장소 루트(inference · postprocess · tools.*) + vendor/(Framework 복사본).
# import 는 tools.VisemeNet_Converter.app... 로 - bare `app` 은 다른 툴과 sys.modules 에서 충돌한다.
# pythonw 는 콘솔이 없어 시작 중 예외가 보이지 않는다 -> 메시지 창 + data/startup_error.log 로 남긴다.

import os
import sys
import traceback

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))
VENDOR = os.path.join(REPO_ROOT, "vendor")

for _path in (REPO_ROOT, VENDOR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def _startup_error(text):
    log_path = os.path.join(TOOL_ROOT, "data", "startup_error.log")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass
    try:
        from Framework.qt.qt import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "VisemeNet Converter - startup error",
                             "The converter could not start.\n\n{0}\n\nDetails: {1}".format(
                                 text.strip().splitlines()[-1], log_path))
    except Exception:
        sys.stderr.write(text) if sys.stderr else None


def _set_windows_app_id(app_id):
    """작업표시줄이 python 아이콘 대신 이 앱 아이콘을 쓰게 (QApplication 전에)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def main():
    from tools.VisemeNet_Converter.app.config.app_meta import APP_USER_MODEL_ID, icon_path
    _set_windows_app_id(APP_USER_MODEL_ID)

    from Framework.qt.qt import QApplication, QIcon
    from Framework.themes.theme_manager import ThemeManager
    from tools.VisemeNet_Converter.app.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    if icon_path(".ico"):
        app.setWindowIcon(QIcon(icon_path(".ico")))
    ThemeManager.load_theme_dev(app, "dark")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        _startup_error(traceback.format_exc())
        sys.exit(1)
