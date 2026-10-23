# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# STT Converter - Convert 진행 팝업 (게이지 창). VisemeNet Converter 의 progress_dialog 와 같은 구조 - 단계 · 예상 시간만 다르다.
#
# Convert 를 누른 순간 뜨고 작업이 끝나는 순간 100% 로 채워진 뒤 닫힌다. 공용 위젯 JUN_mod_progress_qt_v01
# (vendor/Framework) 의 단계 가중치 · 스타일을 그대로 쓰되,
#   1) 변환은 QThread 워커에서 돌고 이 창은 워커 시그널로만 움직인다 -> processEvents() 없이 값만 반영(_draw 재정의).
#   2) 파일 하나의 추론은 끊어 보고할 수 없다 -> 단계마다 예상 소요(초)를 두고 타이머로 다음 경계까지
#      부드럽게 다가가되 넘지 않게 채운다. 실제 보고(단계 시작 · 파일 시작)가 오면 그 자리로 맞춘다.
#
# 단계(key)  check -> load(모델이 아직 없을 때만) -> convert
# 예상 소요는 docs/0130 §11 M0-6 실측: CPU int8 로드 2 ~ 3 s(첫 실행은 다운로드 포함 수 분), 파일당 고정 약 5 s +
# 음성 길이 x 0.3 (CPU). GPU 는 훨씬 빠르지만 게이지는 경계를 넘지 않으므로 빨리 끝나면 바로 맞춘다.
# 모든 UI 문자열은 영어.

import math
import time

from Framework.qt.qt import *
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01


LABELS = {
    "check": "Checking files",
    "load": "Loading model",
    "convert": "Transcribing",
}

EST_CHECK_BASE, EST_CHECK_PER_FILE = 0.3, 0.1
EST_LOAD = 4.0
EST_CONVERT_BASE, EST_CONVERT_PER_SEC = 5.0, 0.3        # 파일 하나 = BASE + 음성 길이(초) x PER_SEC (CPU int8 실측)

TICK_MS = 50
DONE_HOLD_MS = 500
NEAR_END = 0.92


def _ease(elapsed, estimate):
    """단계(또는 파일) 안의 상대 진행 0 ~ 1. 예상 시간까지 선형으로 NEAR_END, 그 뒤는 1 에 점근."""
    estimate = max(float(estimate), 0.05)
    if elapsed <= estimate:
        return NEAR_END * elapsed / estimate
    return NEAR_END + (1.0 - NEAR_END) * (1.0 - math.exp(-(elapsed - estimate) / estimate))


class ConvertProgressDialog(JUN_mod_progress_qt_v01):
    """Convert 진행 팝업. 워커 시그널(plan / begin / file_progress) 과 메인 창(close_popup) 이 움직인다."""

    stop_requested = Signal()

    def __init__(self, parent, n_files, model_loaded, per_sec=EST_CONVERT_PER_SEC, base=EST_CONVERT_BASE):
        self._n_files = int(n_files)
        self._per_sec = float(per_sec)
        self._base = float(base)
        self._file_seconds = [1.0] * self._n_files
        self._keys = []
        self._est = {}
        self._set_plan(not model_loaded, self._file_seconds)
        super().__init__(parent, title="Convert", message=LABELS["check"], phases=self._phase_list(),
                         cancellable=True)
        self.btn_cancel.setText("Stop")
        self.btn_cancel.setToolTip("Stops after the current file (one file cannot be interrupted).")
        self.lbl_detail.setText("{0} file(s)".format(self._n_files))

        self._anchor = 0.0
        self._target = 0.0
        self._estimate = 1.0
        self._t_anchor = time.time()
        self._finished = False
        self._timer = QTimer(self)
        self._timer.setInterval(TICK_MS)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------ 단계 계획

    def _set_plan(self, load_needed, file_seconds):
        self._file_seconds = [max(float(s), 0.0) for s in file_seconds] or [1.0] * self._n_files
        n = len(self._file_seconds)
        self._est = {"check": EST_CHECK_BASE + EST_CHECK_PER_FILE * n}
        self._keys = ["check"]
        if load_needed:
            self._keys.append("load")
            self._est["load"] = EST_LOAD
        self._keys.append("convert")
        self._est["convert"] = sum(self._file_estimate(i) for i in range(n))

    def _phase_list(self):
        return [(LABELS[k], self._est[k]) for k in self._keys]

    def _file_estimate(self, i):
        return self._base + self._per_sec * self._file_seconds[i]

    def plan(self, load_needed, file_seconds):
        """워커가 사전 검사를 마친 뒤: 모델 로드가 필요한지, 파일별 음성 길이(초). 검사 단계는 끝난 것으로 채운다."""
        self._set_plan(bool(load_needed), list(file_seconds))
        self.set_phases(self._phase_list())
        self.begin_phase(index=0)
        base, span = self._window()
        self._hold(base + span, base + span, 0.0)

    def begin(self, key):
        if key not in self._keys or self._finished:
            return
        self.begin_phase(index=self._keys.index(key))
        base, span = self._window()
        self._hold(base, base + span, self._est.get(key, 1.0))
        if key == "convert":
            self.lbl_detail.setText("{0} file(s)".format(len(self._file_seconds)))

    def file_progress(self, done, total, name):
        """run_batch 의 progress(done, total, name) - convert 단계 안에서 파일 done 번째가 시작됐다."""
        if self._finished or "convert" not in self._keys:
            return
        if self._index != self._keys.index("convert"):
            self.begin("convert")
        base, span = self._window()
        weights = [self._file_estimate(i) for i in range(len(self._file_seconds))]
        if len(weights) != int(total) or sum(weights) <= 0.0:
            weights = [1.0] * max(int(total), 1)
        whole = float(sum(weights))
        done = max(0, min(int(done), len(weights)))
        start = sum(weights[:done]) / whole
        end = sum(weights[:done + 1]) / whole if done < len(weights) else 1.0
        self._hold(base + span * start, base + span * end, weights[done] if done < len(weights) else 0.0)
        if name:
            self.lbl_detail.setText("{0} / {1}  {2}".format(done + 1, total, name) if done < total
                                    else "{0} / {1}".format(done, total))
        else:
            self.lbl_detail.setText("{0} / {1}".format(done, total))

    # ------------------------------------------------------------------ 게이지

    def _hold(self, anchor, target, estimate):
        self._anchor = max(0.0, min(1.0, anchor))
        self._target = max(self._anchor, min(1.0, target))
        self._estimate = max(float(estimate), 0.0)
        self._t_anchor = time.time()
        self.set_fraction(self._anchor, force=True)

    def _tick(self):
        if self._finished or self._target <= self._anchor:
            return
        local = _ease(time.time() - self._t_anchor, self._estimate) if self._estimate > 0.0 else 1.0
        self.set_fraction(self._anchor + (self._target - self._anchor) * local)

    def _draw(self, force=False):
        percent = int(round(self._fraction * 100.0))
        if percent != self._percent:
            self._percent = percent
            self.bar.setValue(percent)
        self.lbl_time.setText("{0:.1f}s".format(time.time() - self._t0))

    # ------------------------------------------------------------------ 수명

    def start(self):
        super().start()
        self._hold(0.0, self._window()[1], self._est.get("check", 0.5))
        self._timer.start()
        return self

    def close_popup(self, success):
        """작업 종료. 성공이면 100% 를 잠깐 보여 주고 닫고, 멈춤 · 오류면 바로 닫는다(가짜 100% 를 만들지 않는다)."""
        if self._finished:
            return
        self._finished = True
        self._timer.stop()
        if success:
            self._fraction = 1.0
            self._percent = 100
            self.bar.setValue(100)
            self.lbl_phase.setText("Done")
            self.lbl_time.setText("{0:.1f}s".format(time.time() - self._t0))
            self.btn_cancel.setEnabled(False)
            QTimer.singleShot(DONE_HOLD_MS, self._close_now)
        else:
            self._close_now()

    def _close_now(self):
        self.close()
        self.deleteLater()

    def finish(self):
        self.close_popup(True)

    def _on_cancel(self):
        if self._finished:
            return
        self._cancelled = True
        self.btn_cancel.setEnabled(False)
        self.lbl_detail.setText("Stop requested - finishing the current file...")
        self.stop_requested.emit()
