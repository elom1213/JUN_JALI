# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - 메인 창 (docs/0130_stt_converter_plan.md §5-1). VisemeNet Converter 메인 창과 같은 배치.
#
# wav 목록(공용 TSL) + Language / Engine / Model / Device / Beam / VAD / Kana + 출력 폴더 · 확장자 · 기존 파일 정책 ·
# .stt.json + Check Files / Convert / Stop + 진행 막대 + 로그. 변환은 QThread 워커에서 돈다(창이 멈추지 않게).
# faster-whisper 는 첫 Convert 때 워커 안에서 불러온다. Convert 를 누르면 진행 팝업(progress_dialog)이 뜬다.
# 규칙(D13): 시작 전에 전부 검사하고 하나라도 실패하면 아무것도 변환하지 않는다. 변환 중 파일 하나의 실패는 그 파일만
# 건너뛴다(결과가 서로 독립). 모든 UI 문자열 · 로그는 영어.
# 장치: device.choose() 가 고른다. 강제 CPU(JUN_STT_FORCE_CPU · data/force_cpu.flag)면 Device 콤보를 CPU 로 잠근다 -
# 개발 PC 는 CUDA 기동에서 강제 종료되므로(§6 경고) 이 창에서도 CUDA 를 건드리지 않는다.

import os

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt, JUN_mod_log_qt, JUN_mod_menuBar_qt
from Framework.core import file_opener

from ..config.version import APP_NAME, VERSION, LAST_UPDATE
from ..config.app_meta import icon_path
from ..core import converter, device, job, settings
from ..core.engines import ENGINES, FW_MODEL_CHOICES, LANGUAGES, TranscribeOptions, make_engine
from .progress_dialog import ConvertProgressDialog


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
GUIDE_PATH = os.path.join(REPO_ROOT, "docs", "0140_stt_converter_guide.md")
MODELS_DIR = os.path.join(REPO_ROOT, "models")

VAD_MODES = (("Auto (off for clips under {0:.0f} s)".format(converter.VAD_AUTO_MIN_SECONDS), "auto"),
             ("On", True), ("Off", False))
EXT_CHOICES = ((".lab (recommended)", ".lab"), (".txt", ".txt"))


class ConvertWorker(QThread):
    """사전 검사 + 일괄 변환. 결과는 시그널로만 UI 에 알린다."""

    log = Signal(str, str)                  # level, message
    progress = Signal(int, int, str)        # done, total, name
    planned = Signal(bool, list)            # 사전 검사 뒤: 모델 로드 필요, 파일별 음성 길이(초)
    phase = Signal(str)                     # "check" / "load" / "convert"
    finished_batch = Signal(int, str)       # written count, stop reason ("" = 정상 종료)

    def __init__(self, engine, fallback_factory, wavs, language, out_dir, ext, existing, write_json,
                 options, norm_cfg, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.fallback_factory = fallback_factory
        self.wavs = wavs
        self.language = language
        self.out_dir = out_dir
        self.ext = ext
        self.existing = existing
        self.write_json = write_json
        self.options = options
        self.norm_cfg = norm_cfg
        self._stop = False

    def request_stop(self):
        self._stop = True

    def run(self):
        try:
            self.phase.emit("check")
            jobs, problems = job.preflight(self.wavs, self.language, self.out_dir, self.ext, self.existing,
                                           type(self.engine))
            if problems:
                for wav, code, message in problems:
                    self.log.emit("ERROR", "{0}  {1} {2}".format(os.path.basename(wav) or "Output", code, message))
                self.finished_batch.emit(0, "{0} file(s) failed the check. Nothing was converted."
                                         .format(len(problems)))
                return
            todo = [j for j in jobs if not j.skipped]
            self.planned.emit(not self.engine.loaded and bool(todo),
                              [float(j.info.seconds) for j in todo])
            if todo and not self.engine.loaded:
                self.phase.emit("load")
            written, stopped = converter.run_batch(
                self.engine, jobs, self.options, self.norm_cfg, self.write_json, self.existing,
                "{0} {1}".format(APP_NAME, VERSION),
                log=lambda level, msg: self.log.emit(level, msg),
                progress=self._on_progress,
                should_stop=lambda: self._stop, fallback_factory=self.fallback_factory)
            if stopped:
                self.finished_batch.emit(len(written), "Stopped: {0}. Files already written: {1}"
                                         .format(stopped, len(written)))
            else:
                self.finished_batch.emit(len(written), "")
        except Exception as e:                          # 예상 못 한 오류도 창을 죽이지 않는다
            self.log.emit("ERROR", "unexpected error: {0!r}".format(e))
            self.finished_batch.emit(0, "Stopped: unexpected error")

    def _on_progress(self, done, total, name):
        if done == 0:
            self.phase.emit("convert")
        self.progress.emit(done, total, name)


class UserDictDialog(QDialog):
    """사용자 사전 편집 - 한 줄에 `토큰 = 치환` (data/user_dict_<lang>.json). 영문은 대소문자 구분 없음."""

    def __init__(self, language, parent=None):
        super().__init__(parent)
        self.language = language
        self.setWindowTitle("User Dictionary - {0}".format(language))
        self.resize(460, 380)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("One entry per line:  token = replacement\n"
                                "The token is replaced before the transcript is written (W23 tokens belong here).\n"
                                "Example:  KWI = 케이더블유아이      파이토님 = 파에톤 님"))
        self.edit = QPlainTextEdit()
        self.edit.setPlainText("\n".join("{0} = {1}".format(k, v)
                                         for k, v in sorted(settings.load_user_dict(language).items())))
        layout.addWidget(self.edit, 1)
        self.lb_path = QLabel(settings.user_dict_path(language))
        self.lb_path.setWordWrap(True)
        layout.addWidget(self.lb_path)
        row = QHBoxLayout()
        row.addStretch(1)
        btn_ok = QPushButton("Save")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        layout.addLayout(row)

    def mapping(self):
        out = {}
        for line in self.edit.toPlainText().splitlines():
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k:
                out[k] = v
        return out


class MainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("{0} v{1}".format(APP_NAME, VERSION))
        if icon_path(".png"):
            self.setWindowIcon(QIcon(icon_path(".ico") or icon_path(".png")))
        self.resize(660, 880)
        self.setAcceptDrops(True)

        self._prefs = settings.load()
        self._engine = None
        self._engine_key = None
        self._worker = None
        self._popup = None
        self._forced_cpu = device.force_cpu_reason()

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
        tools_menu = self.menu_bar.addMenu("Tools")
        tools_menu.addAction("User Dictionary...", self.on_user_dict)
        tools_menu.addAction("Open Models Folder", self.on_open_models)
        tools_menu.addSeparator()
        self.act_force_cpu = tools_menu.addAction("Never use CUDA on this PC", self.on_toggle_force_cpu)
        self.act_force_cpu.setCheckable(True)
        self.act_force_cpu.setToolTip("Writes data/force_cpu.flag - the converter never touches the GPU driver.")
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Open Guide", self.on_open_guide)
        help_menu.addAction("About", self.on_about)
        layout.setMenuBar(self.menu_bar)

        # --- 입력 wav 목록
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
            title="WAV (drag & drop .wav files or folders here)", show_select=False, show_add=False, show_del=True,
            show_up=True, show_down=True, show_sort=True, show_order=False,
            attach_uuids=False, list_min_height=140, log_callback=self._log_plain)
        self.tsl.add_button("Clear", self.on_clear)
        self.tsl.list_widget.itemSelectionChanged.connect(self._on_select_wav)
        in_layout.addWidget(self.tsl)
        layout.addWidget(in_box, 3)

        # --- 인식 옵션
        opt_box = QGroupBox("Recognition")
        opt_layout = QVBoxLayout(opt_box)
        row = QHBoxLayout()
        row.addWidget(QLabel("Language"))
        self.cmb_lang = QComboBox()
        for lang in LANGUAGES:
            self.cmb_lang.addItem(lang)
        self.cmb_lang.setToolTip("Language of the speech. It is forced - every file in the batch is transcribed "
                                 "in this language (W20 if the model detects another one).")
        row.addWidget(self.cmb_lang)
        row.addSpacing(12)
        row.addWidget(QLabel("Engine"))
        self.cmb_engine = QComboBox()
        for name, cls in ENGINES.items():
            self.cmb_engine.addItem(name if cls.available() else "{0} (not installed)".format(name), name)
            if not cls.available():
                idx = self.cmb_engine.count() - 1
                self.cmb_engine.model().item(idx).setEnabled(False)
        row.addWidget(self.cmb_engine)
        row.addSpacing(12)
        row.addWidget(QLabel("Model"))
        self.cmb_model = QComboBox()
        for label, key in FW_MODEL_CHOICES:
            self.cmb_model.addItem(label, key)
        self.cmb_model.setToolTip("faster-whisper model. large-v3-turbo: all three languages, fast. "
                                  "Models are downloaded once into models\\ (setup_stt.bat --model NAME).")
        self.cmb_model.currentIndexChanged.connect(self._update_model_ui)
        row.addWidget(self.cmb_model, 1)
        opt_layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Custom model"))
        self.le_model = QLineEdit()
        self.le_model.setPlaceholderText("Hugging Face repo (user/model) or a local CTranslate2 folder")
        row.addWidget(self.le_model, 1)
        opt_layout.addLayout(row)
        self._custom_model_widgets = [self.le_model]

        row = QHBoxLayout()
        row.addWidget(QLabel("Device"))
        self.cmb_device = QComboBox()
        for label, key in device.DEVICE_CHOICES:
            self.cmb_device.addItem(label, key)
        self.cmb_device.setToolTip("Auto: CUDA float16 when an NVIDIA GPU is found, else CPU int8 (W21).")
        row.addWidget(self.cmb_device)
        row.addSpacing(12)
        row.addWidget(QLabel("Beam"))
        self.sb_beam = QSpinBox()
        self.sb_beam.setRange(1, 10)
        self.sb_beam.setToolTip("Beam size. 5 = accuracy first (default), 1 = fastest.")
        row.addWidget(self.sb_beam)
        row.addSpacing(12)
        row.addWidget(QLabel("VAD"))
        self.cmb_vad = QComboBox()
        for label, key in VAD_MODES:
            self.cmb_vad.addItem(label, key)
        self.cmb_vad.setToolTip("Voice activity detection removes leading / trailing silence (prevents hallucinated "
                                "words), but it cut the first word of short clips in tests - Auto turns it off for "
                                "clips shorter than {0:.0f} s.".format(converter.VAD_AUTO_MIN_SECONDS))
        row.addWidget(self.cmb_vad, 1)
        opt_layout.addLayout(row)

        row = QHBoxLayout()
        self.cb_normalize = QCheckBox("Normalize text for MFA (numbers -> words, user dictionary)")
        self.cb_normalize.setToolTip("Recommended. The raw recognized text is kept in <name>.stt.json.")
        self.cb_kana = QCheckBox("Kana output (Japanese)")
        self.cb_kana.setToolTip("Japanese only: write everything in kana (for MFA dictionaries that misread kanji).")
        row.addWidget(self.cb_normalize)
        row.addWidget(self.cb_kana)
        row.addStretch(1)
        opt_layout.addLayout(row)
        self.lb_device = QLabel("")
        self.lb_device.setWordWrap(True)
        opt_layout.addWidget(self.lb_device)
        layout.addWidget(opt_box)

        # --- 출력
        out_box = QGroupBox("Output")
        out_layout = QVBoxLayout(out_box)
        row = QHBoxLayout()
        row.addWidget(QLabel("Folder"))
        self.le_out = QLineEdit()
        self.le_out.setPlaceholderText("Empty = next to each WAV file (where the VisemeNet Converter looks)")
        row.addWidget(self.le_out, 1)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.on_browse_out)
        btn_open = QPushButton("Open")
        btn_open.clicked.connect(self.on_open_out)
        row.addWidget(btn_browse)
        row.addWidget(btn_open)
        out_layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel("Extension"))
        self.cmb_ext = QComboBox()
        for label, key in EXT_CHOICES:
            self.cmb_ext.addItem(label, key)
        self.cmb_ext.setToolTip(".lab is what the VisemeNet Converter reads first. .txt shares its name with the "
                                "VisemeNet 22-column result (W26).")
        row.addWidget(self.cmb_ext)
        row.addSpacing(12)
        row.addWidget(QLabel("Existing"))
        self.cmb_existing = QComboBox()
        for label, key in job.EXISTING_MODES:
            self.cmb_existing.addItem(label, key)
        self.cmb_existing.setToolTip("What to do when <name>.lab already exists. Skip protects hand-written transcripts.")
        row.addWidget(self.cmb_existing, 1)
        out_layout.addLayout(row)
        row = QHBoxLayout()
        self.cb_json = QCheckBox("Write <name>.stt.json (raw text, segments, word times, confidence)")
        row.addWidget(self.cb_json)
        row.addStretch(1)
        out_layout.addLayout(row)
        layout.addWidget(out_box)

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
        self.log_view.setMinimumHeight(160)
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_box, 2)

        self._option_widgets = [self.cmb_lang, self.cmb_engine, self.cmb_model, self.le_model, self.cmb_device,
                                self.sb_beam, self.cmb_vad, self.cb_normalize, self.cb_kana, self.le_out,
                                self.cmb_ext, self.cmb_existing, self.cb_json]

    # ------------------------------------------------------------------ 설정

    def _set_combo_data(self, combo, value, default_index=0):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(default_index)

    def _restore(self):
        p = self._prefs
        files = [f for f in p.get("wav_files", []) if os.path.isfile(f)]
        self.tsl.set_items(files)
        self.cmb_lang.setCurrentIndex(max(self.cmb_lang.findText(p.get("language", "Korean")), 0))
        self._set_combo_data(self.cmb_engine, p.get("engine", "faster-whisper"))
        self._set_combo_data(self.cmb_model, p.get("model", "large-v3-turbo"))
        self.le_model.setText(p.get("custom_model", ""))
        self._set_combo_data(self.cmb_device, p.get("device", "auto"))
        self.sb_beam.setValue(int(p.get("beam_size", 5)))
        self._set_combo_data(self.cmb_vad, p.get("vad", "auto"))
        self.cb_normalize.setChecked(bool(p.get("normalize", True)))
        self.cb_kana.setChecked(bool(p.get("kana", False)))
        self.le_out.setText(p.get("output_dir", ""))
        self._set_combo_data(self.cmb_ext, p.get("ext", ".lab"))
        self._set_combo_data(self.cmb_existing, p.get("existing", "skip"))
        self.cb_json.setChecked(bool(p.get("write_json", True)))
        self._update_model_ui()
        self._update_device_ui()
        self._log("INFO", "{0} v{1} ready. Add WAV files, pick the language, press Convert.".format(APP_NAME, VERSION))
        if not ENGINES["faster-whisper"].available():
            self._log("ERROR", "E40 faster-whisper is not installed in this environment - run setup_stt.bat.")

    def _save(self):
        self._prefs.update({
            "wav_files": self.tsl.get_all_items(),
            "language": self.cmb_lang.currentText(),
            "engine": self.cmb_engine.currentData(),
            "model": self.cmb_model.currentData(),
            "custom_model": self.le_model.text().strip(),
            "device": self.cmb_device.currentData(),
            "beam_size": self.sb_beam.value(),
            "vad": self.cmb_vad.currentData(),
            "normalize": self.cb_normalize.isChecked(),
            "kana": self.cb_kana.isChecked(),
            "output_dir": self.le_out.text().strip(),
            "ext": self.cmb_ext.currentData(),
            "existing": self.cmb_existing.currentData(),
            "write_json": self.cb_json.isChecked(),
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

    # ------------------------------------------------------------------ 옵션 표시

    def _update_model_ui(self, *args):
        custom = self.cmb_model.currentData() == ""
        for w in self._custom_model_widgets:
            w.setEnabled(custom)

    def _update_device_ui(self):
        self._forced_cpu = device.force_cpu_reason()
        self.act_force_cpu.setChecked(bool(self._forced_cpu))
        if self._forced_cpu:
            self._set_combo_data(self.cmb_device, "cpu:int8")
            self.cmb_device.setEnabled(False)
            self.lb_device.setText("Device: CPU int8 - CUDA is disabled on this PC ({0}). "
                                   "Tools > Never use CUDA on this PC to change.".format(self._forced_cpu))
        else:
            self.cmb_device.setEnabled(self._worker is None)
            self.lb_device.setText("Device is chosen when Convert is pressed (GPU is detected then, not at start-up).")

    def _model_name(self):
        key = self.cmb_model.currentData()
        return self.le_model.text().strip() if key == "" else key

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
        """목록에서 하나를 고르면 그 파일의 규격과 기존 대본 유무를 로그에 보여 준다."""
        items = self.tsl.selected_items()
        if len(items) != 1:
            return
        wav = items[0]
        try:
            info = job.read_wav_info(wav)
            self._log("INFO", "{0}  {1}".format(os.path.basename(wav), info.summary()))
        except ValueError as e:
            self._log("WARN", "{0}  E42 cannot read audio: {1}".format(os.path.basename(wav), e))
        out_path, _json = job.output_paths(wav, self.le_out.text().strip(), self.cmb_ext.currentData())
        if os.path.isfile(out_path):
            self._log("INFO", "{0}  transcript exists: {1} ({2})".format(
                os.path.basename(wav), os.path.basename(out_path), self.cmb_existing.currentText()))

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

    # ------------------------------------------------------------------ Tools

    def on_user_dict(self, *args):
        lang = self.cmb_lang.currentText()
        dlg = UserDictDialog(lang, self)
        if dlg.exec() == QDialog.Accepted:
            mapping = dlg.mapping()
            if settings.save_user_dict(lang, mapping):
                self._log("OK", "User dictionary ({0}): {1} entr{2} saved.".format(
                    lang, len(mapping), "y" if len(mapping) == 1 else "ies"))
            else:
                self._log("ERROR", "Could not write {0}".format(settings.user_dict_path(lang)))

    def on_open_models(self, *args):
        try:
            file_opener.open_path(MODELS_DIR)
        except (OSError, ValueError):
            self._log("WARN", "Models folder does not exist yet: {0} (run setup_stt.bat)".format(MODELS_DIR))

    def on_toggle_force_cpu(self, *args):
        enabled = self.act_force_cpu.isChecked()
        if not device.set_force_cpu_flag(enabled):
            self._log("ERROR", "Could not write {0}".format(device.FORCE_CPU_FLAG))
        device.detect(refresh=True)
        self._engine = None                             # 다음 Convert 때 장치를 다시 고른다
        self._update_device_ui()
        self._log("INFO", "CUDA on this PC: {0}.".format("disabled (data/force_cpu.flag)" if enabled else "allowed"))

    # ------------------------------------------------------------------ 실행

    def _inputs(self):
        wavs = self.tsl.get_all_items()
        if not wavs:
            self._log("ERROR", "No WAV files in the list.")
            return None
        if self.cmb_model.currentData() == "" and not self.le_model.text().strip():
            self._log("ERROR", "Custom model: type a Hugging Face repo or a local folder, or pick a model.")
            return None
        return wavs

    def _options(self):
        return TranscribeOptions(beam_size=self.sb_beam.value(), vad=self.cmb_vad.currentData())

    def _norm_cfg(self):
        lang = self.cmb_lang.currentText()
        return converter.NormalizeConfig(enabled=self.cb_normalize.isChecked(),
                                         user_dict=settings.load_user_dict(lang), kana=self.cb_kana.isChecked())

    def on_check(self, *args):
        wavs = self._inputs()
        if not wavs:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            jobs, problems = job.preflight(wavs, self.cmb_lang.currentText(), self.le_out.text().strip(),
                                           self.cmb_ext.currentData(), self.cmb_existing.currentData(),
                                           ENGINES[self.cmb_engine.currentData()])
        finally:
            QApplication.restoreOverrideCursor()
        total_sec = 0.0
        for j in jobs:
            self._log("OK", "{0}  {1}{2}".format(j.name, j.info.summary(), "  -> skip" if j.skipped else ""))
            for code, message in j.warnings:
                self._log("WARN", "{0}  {1} {2}".format(j.name, code, message))
            if not j.skipped:
                total_sec += j.info.seconds
        for wav, code, message in problems:
            self._log("ERROR", "{0}  {1} {2}".format(os.path.basename(wav) or "Output", code, message))
        if problems:
            self._log("ERROR", "{0} of {1} file(s) would stop the conversion.".format(len(problems), len(wavs)))
        else:
            todo = sum(1 for j in jobs if not j.skipped)
            self._log("DONE", "All {0} file(s) passed the check - {1} to transcribe ({2:.0f} s of audio), "
                              "{3} skipped. Device: {4}".format(
                len(jobs), todo, total_sec, len(jobs) - todo, device.detect().summary()))

    def _make_engine(self):
        name = self.cmb_engine.currentData()
        model = self._model_name()
        dev, compute, note = device.choose(self.cmb_device.currentData())
        if note:
            self._log("WARN", "W21 {0}".format(note))
        key = (name, model, dev, compute)
        if self._engine is None or self._engine_key != key:
            self._engine = make_engine(name, model, dev, compute, MODELS_DIR)
            self._engine_key = key
        fallback = (lambda: make_engine(name, model, "cpu", "int8", MODELS_DIR)) if dev == "cuda" else None
        return self._engine, fallback

    def on_convert(self, *args):
        wavs = self._inputs()
        if not wavs:
            return
        self._save()
        try:
            engine, fallback = self._make_engine()
        except Exception as e:
            self._log("ERROR", "E40 {0!r}".format(e))
            return
        self._log("INFO", "Device: {0}".format(device.detect().summary()))
        self._worker = ConvertWorker(engine, fallback, wavs, self.cmb_lang.currentText(),
                                     self.le_out.text().strip(), self.cmb_ext.currentData(),
                                     self.cmb_existing.currentData(), self.cb_json.isChecked(),
                                     self._options(), self._norm_cfg(), parent=self)
        self._worker.log.connect(self._log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_batch.connect(self._on_finished)
        self._set_running(True)
        self._log("INFO", "Transcribing {0} file(s) in {1} with {2}...".format(
            len(wavs), self.cmb_lang.currentText(), engine.describe()))
        self._show_popup(len(wavs), engine.loaded)
        self._worker.start()

    def on_stop(self, *args):
        if self._worker is not None and not self._worker._stop:
            self._worker.request_stop()
            self.btn_stop.setEnabled(False)
            self._log("WARN", "Stop requested - finishing the current file.")

    def _show_popup(self, n_files, model_loaded):
        """Convert 진행 팝업 - 워커 시그널이 단계 · 파일 진행을 넣고, 끝나면 _on_finished 가 닫는다."""
        self._popup = ConvertProgressDialog(self, n_files, model_loaded)
        self._popup.stop_requested.connect(self.on_stop)
        self._worker.planned.connect(self._popup.plan)
        self._worker.phase.connect(self._popup.begin)
        self._worker.progress.connect(self._popup.file_progress)
        self._popup.start()

    def _on_progress(self, done, total, name):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(done)
        self.progress.setFormat("{0} / {1}  {2}".format(done, total, name) if name else "{0} / {1}".format(done, total))

    def _on_finished(self, written, reason):
        if self._popup is not None:
            self._popup.close_popup(not reason)
            self._popup = None
        self._set_running(False)
        if reason:
            self._log("ERROR", reason)
            self.progress.setFormat("Stopped")
        else:
            out = self.le_out.text().strip() or "(next to each WAV)"
            self._log("DONE", "{0} transcript(s) written. Output folder: {1}".format(written, out))
            self.progress.setFormat("Done - {0} file(s)".format(written))
        self._worker = None
        self._update_device_ui()

    def _set_running(self, running):
        for w in [self.btn_check, self.btn_convert, self.tsl] + self._option_widgets:
            w.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        if running:
            self.progress.setRange(0, 0)            # 모델 로드 중엔 바쁨 표시
            self.progress.setFormat("Working...")
        else:
            self._update_model_ui()
            self._update_device_ui()

    # ------------------------------------------------------------------ Help

    def on_open_guide(self, *args):
        try:
            file_opener.open_path(GUIDE_PATH)
        except (OSError, ValueError):
            self._log("WARN", "Guide not found: {0}".format(GUIDE_PATH))

    def on_about(self, *args):
        QMessageBox.information(self, "About", (
            "{0} v{1}\nUpdate date: {2}\n\n"
            "Transcribes WAV files (English / Korean / Japanese) into transcripts\n"
            "(<name>.lab) for the VisemeNet Converter Correct mode (MFA).\n\n"
            "Engine: faster-whisper large-v3-turbo (CTranslate2), local, CPU or NVIDIA GPU.\n"
            "The text is normalized for the aligner (numbers -> words, user dictionary);\n"
            "the raw text and word timings are kept in <name>.stt.json.\n\n"
            "Every file is checked first - if one fails, nothing is converted.\n"
            "A file that fails while converting is skipped; the reason is in the Log.\n\n"
            "Written by Ji Hun Park.").format(APP_NAME, VERSION, LAST_UPDATE))
