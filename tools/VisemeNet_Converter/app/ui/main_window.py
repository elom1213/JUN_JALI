# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-20
# VisemeNet Converter - 메인 창 (docs/0030_tool_plan.md §4.2)
#
# wav 목록(공용 TSL) + 출력 폴더 + 옵션 + 대본 보정(Correct 모드, MFA) + Check Files / Convert / Stop + 진행 막대 + 로그.
# 변환은 QThread 워커에서 돈다(창이 멈추지 않게). TensorFlow 는 첫 Convert 때 워커 안에서 불러온다.
# 규칙: 시작 전에 전부 검사하고 하나라도 실패하면 아무것도 변환하지 않는다. 변환 중 오류도 즉시 멈춘다.
# 모든 UI 문자열 · 로그는 영어.

import os

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt, JUN_mod_log_qt, JUN_mod_menuBar_qt
from Framework.core import file_opener

from ..config.version import APP_NAME, VERSION, LAST_UPDATE
from ..config.app_meta import icon_path
from ..core import aligner, converter, settings
from ..core.wav_check import check_wav, WavError, DEFAULT_MAX_SECONDS


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
GUIDE_PATH = os.path.join(REPO_ROOT, "docs", "0050_converter_guide.md")

MODES = [("Deterministic (recommended)", True), ("Original - random dropout", False)]
ALIGN_MODES = [("Audio only", "audio"), ("Correct with transcript (MFA)", "correct")]


class ConvertWorker(QThread):
    """사전 검사 + 일괄 변환. 결과는 시그널로만 UI 에 알린다."""

    log = Signal(str, str)                  # level, message
    progress = Signal(int, int, str)        # done, total, name
    finished_batch = Signal(int, str)       # written count, stop reason ("" = 정상 종료)

    def __init__(self, engine, wavs, out_dir, overwrite, max_seconds, write_json, align_cfg=None, parent=None):
        super().__init__(parent)
        self.align_cfg = align_cfg
        self.engine = engine
        self.wavs = wavs
        self.out_dir = out_dir
        self.overwrite = overwrite
        self.max_seconds = max_seconds
        self.write_json = write_json
        self._stop = False

    def request_stop(self):
        self._stop = True

    def run(self):
        try:
            jobs, problems = converter.preflight(
                self.wavs, self.out_dir, self.overwrite, self.max_seconds, self.write_json, self.align_cfg,
                REPO_ROOT)
            if problems:
                for wav, code, message in problems:
                    self.log.emit("ERROR", "{0}  {1} {2}".format(os.path.basename(wav) or "Output", code, message))
                self.finished_batch.emit(0, "{0} file(s) failed the check. Nothing was converted."
                                         .format(len(problems)))
                return
            for job in jobs:
                for code, message in job.info.warnings:
                    self.log.emit("WARN", "{0}  {1} {2}".format(os.path.basename(job.wav_path), code, message))

            if not self.engine.loaded:
                self.log.emit("INFO", "Loading model (first run takes a few seconds)...")
                self.engine.load()

            written, stopped = converter.run_batch(
                self.engine, jobs, self.write_json, "{0} {1}".format(APP_NAME, VERSION),
                log=lambda level, msg: self.log.emit(level, msg),
                progress=lambda done, total, name: self.progress.emit(done, total, name),
                should_stop=lambda: self._stop, align_cfg=self.align_cfg)
            if stopped:
                self.finished_batch.emit(len(written), "Stopped: {0}. Files already written: {1}"
                                         .format(stopped, len(written)))
            else:
                self.finished_batch.emit(len(written), "")
        except converter.ConvertError as e:
            self.log.emit("ERROR", "{0} {1}".format(e.code, e.message))
            if e.detail:
                self.log.emit("INFO", "detail: {0}".format(e.detail))
            self.finished_batch.emit(0, "Stopped: {0} {1}".format(e.code, e.message))
        except Exception as e:                          # 예상 못 한 오류도 창을 죽이지 않는다
            self.log.emit("ERROR", "unexpected error: {0!r}".format(e))
            self.finished_batch.emit(0, "Stopped: unexpected error")


class MainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("{0} v{1}".format(APP_NAME, VERSION))
        if icon_path(".png"):
            self.setWindowIcon(QIcon(icon_path(".ico") or icon_path(".png")))
        self.resize(640, 860)
        self.setAcceptDrops(True)

        self._prefs = settings.load()
        self._engine = None
        self._worker = None

        self._build_ui()
        self._restore()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt.JUN_mod_menuBar_qt_v01(tool_file=__file__)
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction("Add Files...", self.on_add_files)
        file_menu.addAction("Add Folder...", self.on_add_folder)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Open Guide", self.on_open_guide)
        help_menu.addAction("About", self.on_about)
        layout.setMenuBar(self.menu_bar)

        # --- 입력 wav 목록 (씬 노드가 아니므로 마야 버튼 · UUID 끔)
        in_box = QGroupBox("Input WAV Files")
        in_layout = QVBoxLayout(in_box)
        add_row = QHBoxLayout()
        btn_files = QPushButton("Add Files...")
        btn_files.clicked.connect(self.on_add_files)
        btn_folder = QPushButton("Add Folder...")
        btn_folder.clicked.connect(self.on_add_folder)
        add_row.addWidget(btn_files)
        add_row.addWidget(btn_folder)
        add_row.addStretch(1)
        in_layout.addLayout(add_row)

        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="WAV (drag & drop .wav files here)", show_select=False, show_add=False, show_del=True,
            show_up=True, show_down=True, show_sort=True, show_order=False,
            attach_uuids=False, list_min_height=160, log_callback=self._log_plain)
        self.tsl.add_button("Clear", self.on_clear)
        self.tsl.list_widget.itemSelectionChanged.connect(self._on_select_wav)
        in_layout.addWidget(self.tsl)
        layout.addWidget(in_box, 3)

        # --- 출력
        out_box = QGroupBox("Output")
        out_layout = QVBoxLayout(out_box)
        row = QHBoxLayout()
        row.addWidget(QLabel("Folder"))
        self.le_out = QLineEdit()
        self.le_out.setPlaceholderText("Empty = next to each WAV file")
        row.addWidget(self.le_out, 1)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.on_browse_out)
        btn_open = QPushButton("Open")
        btn_open.clicked.connect(self.on_open_out)
        row.addWidget(btn_browse)
        row.addWidget(btn_open)
        out_layout.addLayout(row)

        opt = QHBoxLayout()
        self.cb_json = QCheckBox("Write .visemenet.json info file")
        self.cb_json.setToolTip("Columns, fps and the source WAV path - JALI LipSync (Maya) uses it "
                                "to find the audio automatically.")
        self.cb_overwrite = QCheckBox("Overwrite existing")
        opt.addWidget(self.cb_json)
        opt.addWidget(self.cb_overwrite)
        opt.addStretch(1)
        out_layout.addLayout(opt)

        opt2 = QHBoxLayout()
        opt2.addWidget(QLabel("Max length (sec)"))
        self.sb_max = QSpinBox()
        self.sb_max.setRange(5, 3600)
        self.sb_max.setToolTip("Longer files stop the check (E07). The whole file is processed at once, "
                               "so very long files need a lot of memory.")
        opt2.addWidget(self.sb_max)
        opt2.addSpacing(16)
        opt2.addWidget(QLabel("Inference"))
        self.cmb_mode = QComboBox()
        for label, _det in MODES:
            self.cmb_mode.addItem(label)
        self.cmb_mode.setToolTip(
            "Deterministic: the model's built-in dropout is turned off, so the same WAV always gives "
            "the same result.\nOriginal: exactly as published - results change a little on every run.")
        opt2.addWidget(self.cmb_mode)
        opt2.addStretch(1)
        out_layout.addLayout(opt2)
        layout.addWidget(out_box)

        # --- 대본 보정 (docs/0060 안 B) - wav 옆의 <이름>.lab / .txt 를 MFA 로 정렬해 비짐을 보정
        tr_box = QGroupBox("Transcript (optional)")
        tr_layout = QVBoxLayout(tr_box)
        row = QHBoxLayout()
        row.addWidget(QLabel("Mode"))
        self.cmb_align = QComboBox()
        for label, _key in ALIGN_MODES:
            self.cmb_align.addItem(label)
        self.cmb_align.setToolTip(
            "Correct: a transcript next to each WAV (<name>.lab, or <name>.txt, UTF-8) is aligned with\n"
            "Montreal Forced Aligner and the viseme curves are corrected phone by phone\n"
            "(lips close on p / b / m, f / v ...). Jaw and Lip stay as VisemeNet made them.\n"
            "WAV files without a transcript are converted from the audio only.")
        self.cmb_align.currentIndexChanged.connect(self._update_align_ui)
        row.addWidget(self.cmb_align)
        row.addSpacing(16)
        row.addWidget(QLabel("Language"))
        self.cmb_lang = QComboBox()
        for lang in aligner.LANGUAGES:
            self.cmb_lang.addItem(lang)
        self.cmb_lang.setToolTip("Language of the speech and the transcript (MFA acoustic model + dictionary).")
        row.addWidget(self.cmb_lang)
        row.addStretch(1)
        tr_layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel("MFA folder"))
        self.le_mfa = QLineEdit()
        self.le_mfa.setPlaceholderText("Empty = the folder chosen in setup_mfa.bat")
        self.le_mfa.editingFinished.connect(self._update_align_ui)
        row.addWidget(self.le_mfa, 1)
        btn_mfa = QPushButton("Browse...")
        btn_mfa.clicked.connect(self.on_browse_mfa)
        row.addWidget(btn_mfa)
        tr_layout.addLayout(row)
        self.lb_mfa = QLabel("")
        tr_layout.addWidget(self.lb_mfa)
        self._align_widgets = [self.cmb_lang, self.le_mfa, btn_mfa, self.lb_mfa]
        layout.addWidget(tr_box)

        # --- 실행
        run_row = QHBoxLayout()
        self.btn_check = QPushButton("Check Files")
        self.btn_check.clicked.connect(self.on_check)
        self.btn_convert = QPushButton("Convert")
        self.btn_convert.setMinimumHeight(32)
        self.btn_convert.clicked.connect(self.on_convert)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setToolTip("Stops after the current file (one file cannot be interrupted).")
        self.btn_stop.clicked.connect(self.on_stop)
        run_row.addWidget(self.btn_check)
        run_row.addStretch(1)
        run_row.addWidget(self.btn_convert, 2)
        run_row.addWidget(self.btn_stop)
        layout.addLayout(run_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setFormat("Idle")
        layout.addWidget(self.progress)

        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        self.log_view = JUN_mod_log_qt.JUN_mod_log_qt_v01()
        self.log_view.setMinimumHeight(180)
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_box, 2)

    # ------------------------------------------------------------------ 설정

    def _restore(self):
        p = self._prefs
        files = [f for f in p.get("wav_files", []) if os.path.isfile(f)]
        self.tsl.set_items(files)
        self.le_out.setText(p.get("output_dir", ""))
        self.cb_json.setChecked(bool(p.get("write_json", True)))
        self.cb_overwrite.setChecked(bool(p.get("overwrite", False)))
        self.sb_max.setValue(int(p.get("max_seconds", DEFAULT_MAX_SECONDS)))
        self.cmb_mode.setCurrentIndex(0)
        keys = [k for _l, k in ALIGN_MODES]
        self.cmb_align.setCurrentIndex(keys.index(p.get("align_mode")) if p.get("align_mode") in keys else 0)
        self.cmb_lang.setCurrentIndex(max(self.cmb_lang.findText(p.get("language", "English")), 0))
        self.le_mfa.setText(p.get("mfa_folder", ""))
        self._update_align_ui()
        self._log("INFO", "{0} v{1} ready. Add WAV files (44.1 kHz, 16-bit PCM).".format(APP_NAME, VERSION))

    def _save(self):
        self._prefs.update({
            "wav_files": self.tsl.get_all_items(),
            "output_dir": self.le_out.text().strip(),
            "write_json": self.cb_json.isChecked(),
            "overwrite": self.cb_overwrite.isChecked(),
            "max_seconds": self.sb_max.value(),
            "align_mode": ALIGN_MODES[self.cmb_align.currentIndex()][1],
            "language": self.cmb_lang.currentText(),
            "mfa_folder": self.le_mfa.text().strip(),
        })
        settings.save(self._prefs)

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._log("WARN", "Converting - press Stop and wait for the current file to finish.")
            event.ignore()
            return
        self._save()
        super().closeEvent(event)

    # ------------------------------------------------------------------ 로그

    def _log(self, level, message):
        self.log_view.appendPlainText("[{0}] {1}".format(level, message))

    def _log_plain(self, message):
        self.log_view.appendPlainText(message)

    # ------------------------------------------------------------------ 입력

    def _add_paths(self, paths):
        wavs, skipped = [], 0
        for p in paths:
            if os.path.isdir(p):
                for name in sorted(os.listdir(p)):
                    if name.lower().endswith(".wav"):
                        wavs.append(os.path.normpath(os.path.join(p, name)))
            elif p.lower().endswith(".wav"):
                wavs.append(os.path.normpath(p))
            else:
                skipped += 1
        before = self.tsl.count()
        self.tsl.append_unique(wavs)
        added = self.tsl.count() - before
        self._log("INFO", "Added {0} WAV file(s){1}.".format(
            added, ", skipped {0} non-WAV".format(skipped) if skipped else ""))

    def on_add_files(self, *args):
        files, _ = QFileDialog.getOpenFileNames(self, "Add WAV Files", self._prefs.get("last_dir", ""),
                                                "WAV files (*.wav);;All files (*.*)")
        if files:
            self._prefs["last_dir"] = os.path.dirname(files[0])
            self._add_paths(files)

    def on_add_folder(self, *args):
        folder = QFileDialog.getExistingDirectory(self, "Add WAV Folder", self._prefs.get("last_dir", ""))
        if folder:
            self._prefs["last_dir"] = folder
            self._add_paths([folder])

    def on_clear(self, *args):
        self.tsl.clear()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self._add_paths(paths)
            event.acceptProposedAction()

    def _on_select_wav(self):
        """목록에서 하나를 고르면 그 파일의 규격을 로그에 보여 준다."""
        items = self.tsl.selected_items()
        if len(items) != 1:
            return
        try:
            info = check_wav(items[0], self.sb_max.value())
            self._log("INFO", "{0}  {1}".format(os.path.basename(items[0]), info.summary()))
        except WavError as e:
            self._log("WARN", "{0}  {1} {2}".format(os.path.basename(items[0]), e.code, e.message))
        if self._correct_mode():
            tr = aligner.transcript_path(items[0])
            self._log("INFO", "{0}  transcript: {1}".format(
                os.path.basename(items[0]), os.path.basename(tr) if tr else "none (audio only)"))

    # ------------------------------------------------------------------ 출력

    def on_browse_out(self, *args):
        folder = QFileDialog.getExistingDirectory(self, "Output Folder", self.le_out.text() or
                                                  self._prefs.get("last_dir", ""))
        if folder:
            self.le_out.setText(os.path.normpath(folder))

    def on_open_out(self, *args):
        folder = self.le_out.text().strip()
        if not folder:
            items = self.tsl.get_all_items()
            folder = os.path.dirname(items[0]) if items else ""
        try:
            file_opener.open_path(folder)
        except (OSError, ValueError):
            self._log("WARN", "Folder does not exist yet: {0}".format(folder or "(none)"))

    # ------------------------------------------------------------------ 대본 보정

    def _correct_mode(self):
        return ALIGN_MODES[self.cmb_align.currentIndex()][1] == "correct"

    def _align_cfg(self):
        if not self._correct_mode():
            return None
        return converter.AlignConfig(self.cmb_lang.currentText(), self.le_mfa.text().strip())

    def _update_align_ui(self, *args):
        on = self._correct_mode()
        for w in self._align_widgets:
            w.setEnabled(on)
        inst = aligner.find_install(REPO_ROOT, self.le_mfa.text().strip())
        if inst is None:
            self.lb_mfa.setText("MFA: not found - run setup_mfa.bat (once) or set the folder")
        else:
            self.lb_mfa.setText("MFA: {0}".format(inst.folder))

    def on_browse_mfa(self, *args):
        folder = QFileDialog.getExistingDirectory(self, "MFA Folder (chosen in setup_mfa.bat)",
                                                  self.le_mfa.text() or REPO_ROOT)
        if folder:
            self.le_mfa.setText(os.path.normpath(folder))
            self._update_align_ui()

    # ------------------------------------------------------------------ 실행

    def _inputs(self):
        wavs = self.tsl.get_all_items()
        if not wavs:
            self._log("ERROR", "No WAV files in the list.")
            return None
        return wavs

    def on_check(self, *args):
        wavs = self._inputs()
        if not wavs:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            jobs, problems = converter.preflight(wavs, self.le_out.text().strip(), self.cb_overwrite.isChecked(),
                                                 self.sb_max.value(), self.cb_json.isChecked(),
                                                 self._align_cfg(), REPO_ROOT)
        finally:
            QApplication.restoreOverrideCursor()
        for job in jobs:
            self._log("OK", "{0}  {1}".format(os.path.basename(job.wav_path), job.info.summary()))
            for code, message in job.info.warnings:
                self._log("WARN", "{0}  {1} {2}".format(os.path.basename(job.wav_path), code, message))
            if self._correct_mode():
                self._log("INFO", "{0}  transcript: {1}".format(
                    os.path.basename(job.wav_path),
                    os.path.basename(job.transcript_path) if job.transcript_path else "none (audio only)"))
        for wav, code, message in problems:
            self._log("ERROR", "{0}  {1} {2}".format(os.path.basename(wav) or "Output", code, message))
        if problems:
            self._log("ERROR", "{0} of {1} file(s) would stop the conversion.".format(len(problems), len(wavs)))
        else:
            self._log("DONE", "All {0} file(s) passed the check.".format(len(jobs)))

    def on_convert(self, *args):
        wavs = self._inputs()
        if not wavs:
            return
        deterministic = MODES[self.cmb_mode.currentIndex()][1]
        if self._engine is None or self._engine.deterministic != deterministic:
            self._engine = converter.Engine(REPO_ROOT, deterministic=deterministic)
        self._save()

        self._worker = ConvertWorker(self._engine, wavs, self.le_out.text().strip(),
                                     self.cb_overwrite.isChecked(), self.sb_max.value(),
                                     self.cb_json.isChecked(), self._align_cfg(), parent=self)
        self._worker.log.connect(self._log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_batch.connect(self._on_finished)
        self._set_running(True)
        self._log("INFO", "Converting {0} file(s)...".format(len(wavs)))
        self._worker.start()

    def on_stop(self, *args):
        if self._worker is not None:
            self._worker.request_stop()
            self.btn_stop.setEnabled(False)
            self._log("WARN", "Stop requested - finishing the current file.")

    def _on_progress(self, done, total, name):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(done)
        self.progress.setFormat("{0} / {1}  {2}".format(done, total, name) if name else "{0} / {1}".format(done, total))

    def _on_finished(self, written, reason):
        self._set_running(False)
        if reason:
            self._log("ERROR", reason)
            self.progress.setFormat("Stopped")
        else:
            out = self.le_out.text().strip() or "(next to each WAV)"
            self._log("DONE", "Output folder: {0}".format(out))
            self.progress.setFormat("Done - {0} file(s)".format(written))
        self._worker = None

    def _set_running(self, running):
        for w in (self.btn_check, self.btn_convert, self.tsl, self.le_out, self.cb_json,
                  self.cb_overwrite, self.sb_max, self.cmb_mode, self.cmb_align):
            w.setEnabled(not running)
        for w in self._align_widgets:
            w.setEnabled(not running and self._correct_mode())
        self.btn_stop.setEnabled(running)
        if running:
            self.progress.setRange(0, 0)            # 모델 로드 중엔 바쁨 표시
            self.progress.setFormat("Working...")

    # ------------------------------------------------------------------ Help

    def on_open_guide(self, *args):
        try:
            file_opener.open_path(GUIDE_PATH)
        except (OSError, ValueError):
            self._log("WARN", "Guide not found: {0}".format(GUIDE_PATH))

    def on_about(self, *args):
        QMessageBox.information(self, "About", (
            "{0} v{1}\nUpdate date: {2}\n\n"
            "Converts 44.1 kHz / 16-bit WAV files to VisemeNet viseme curves\n"
            "(<name>.txt, 100 fps x 22 columns: Jaw, Lip + 20 visemes).\n\n"
            "Correct mode: a transcript next to each WAV is aligned with Montreal\n"
            "Forced Aligner and the visemes are corrected phone by phone.\n\n"
            "Every file is checked first - if one fails, nothing is converted.\n"
            "An error while converting stops the batch; the reason is in the Log.\n\n"
            "Model: VisemeNet (Zhou et al. 2018), fork JUN_JALI.\n"
            "Written by Ji Hun Park.").format(APP_NAME, VERSION, LAST_UPDATE))
