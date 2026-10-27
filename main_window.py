"""PySide6 user interface for NeuralTone."""
from __future__ import annotations

import math
import time

import numpy as np
from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QRadioButton, QSlider, QVBoxLayout,
    QWidget,
)

from presets import CUSTOM, PRESETS
from tone_generator import BINAURAL, ISOCHRONIC, ToneGenerator

BASE_RANGE = (100.0, 1000.0)
BEAT_RANGE = (1.0, 50.0)
SLIDER_SCALE = 10  # slider ints are tenths of a Hz

STYLE = """
QWidget { background: #14161a; color: #d8dce3; font-size: 13px; }
QLabel#title { font-size: 20px; font-weight: 600; color: #ffffff; }
QLabel#hint, QLabel#useCase { color: #7f8896; }
QComboBox, QDoubleSpinBox { background: #1e2127; border: 1px solid #2c313a;
    border-radius: 6px; padding: 5px 8px; }
QComboBox QAbstractItemView { background: #1e2127; selection-background-color: #2f6df6; }
QRadioButton { spacing: 8px; padding: 4px 2px; }
QPushButton#play { background: #2f6df6; color: white; font-size: 18px;
    font-weight: 600; border: none; border-radius: 10px; padding: 14px; }
QPushButton#play:hover { background: #4a80f8; }
QPushButton#play:checked { background: #c24141; }
QPushButton#play:checked:hover { background: #d35555; }
QSlider::groove:horizontal { height: 6px; background: #2c313a; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #2f6df6; border-radius: 3px; }
QSlider::handle:horizontal { background: #ffffff; width: 16px; height: 16px;
    margin: -5px 0; border-radius: 8px; }
"""


class ScopeWidget(QWidget):
    """Slow-motion visualisation of the beat/pulse envelope.

    The real rate (up to 50 Hz) would be a flicker hazard on screen, so the
    waveform scrolls at ~1 cycle per second regardless of the target frequency;
    the number of cycles drawn still reflects the target frequency visually.
    """

    CARRIER_CYCLES = 8      # visual carrier cycles per beat cycle
    VIEW_CYCLES = 3
    SCROLL_HZ = 0.5

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(150)
        self.mode = BINAURAL
        self.beat = 10.0
        self.active = False
        self._t0 = time.monotonic()
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(33)

    def set_state(self, mode: str, beat: float, active: bool) -> None:
        self.mode, self.beat, self.active = mode, beat, active

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.setBrush(QColor("#0d0f12"))
        p.setPen(QPen(QColor("#2c313a"), 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 8, 8)
        mid = h / 2
        p.setPen(QPen(QColor("#22262d"), 1))
        p.drawLine(0, int(mid), w, int(mid))

        x = np.linspace(0.0, self.VIEW_CYCLES, max(w, 2))
        shift = (time.monotonic() - self._t0) * self.SCROLL_HZ if self.active else 0.0
        x = x + shift
        c = self.CARRIER_CYCLES
        if self.mode == BINAURAL:
            y = 0.5 * (np.sin(2 * np.pi * c * x) + np.sin(2 * np.pi * (c + 1) * x))
        else:
            frac = x % 1.0
            edge = 0.04
            gate = np.clip(frac / edge, 0, 1) - np.clip((frac - 0.5) / edge, 0, 1)
            y = np.sin(2 * np.pi * c * x) * gate
        color = QColor("#4a9cff" if self.mode == BINAURAL else "#ffb347")
        if not self.active:
            color.setAlpha(110)
        amp = h * 0.4
        poly = QPolygonF([QPointF(i, mid - v * amp) for i, v in enumerate(y)])
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color, 2))
        p.drawPolyline(poly)

        p.setPen(QColor("#7f8896"))
        p.drawText(10, 18, f"{self.beat:.1f} Hz  (slowed for display)")
        p.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuralTone")
        self.setMinimumWidth(480)
        self.gen = ToneGenerator()
        self._loading = False

        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(14)

        title = QLabel("NeuralTone")
        title.setObjectName("title")
        lay.addWidget(title)

        # --- presets & controls
        self.preset_box = QComboBox()
        self.preset_box.addItems([p.name for p in PRESETS] + [CUSTOM])
        self.preset_box.setCurrentText(PRESETS[0].name)
        self.use_case = QLabel()
        self.use_case.setObjectName("useCase")
        lay.addWidget(self.preset_box)
        lay.addWidget(self.use_case)

        self.rb_bin = QRadioButton("Binaural (Headphones Required)")
        self.rb_iso = QRadioButton("Isochronic (Speakers/Headphones)")
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_bin)
        self.mode_group.addButton(self.rb_iso)
        mode_row = QVBoxLayout()
        mode_row.setSpacing(2)
        mode_row.addWidget(self.rb_bin)
        mode_row.addWidget(self.rb_iso)
        lay.addLayout(mode_row)

        self.play_btn = QPushButton("Play")
        self.play_btn.setObjectName("play")
        self.play_btn.setCheckable(True)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.play_btn)

        vol_row = QHBoxLayout()
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(50)
        self.vol_label = QLabel("50%")
        self.vol_label.setMinimumWidth(40)
        vol_row.addWidget(QLabel("Volume"))
        vol_row.addWidget(self.vol_slider, 1)
        vol_row.addWidget(self.vol_label)
        lay.addLayout(vol_row)

        # --- parameters
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        self.base_label = QLabel("Base Frequency (Carrier)")
        self.base_spin, self.base_slider = self._param_row(grid, 0, self.base_label, BASE_RANGE)
        self.beat_label = QLabel()
        self.beat_spin, self.beat_slider = self._param_row(grid, 1, self.beat_label, BEAT_RANGE)
        lay.addLayout(grid)

        # --- visual
        self.scope = ScopeWidget()
        lay.addWidget(self.scope, 1)
        hint = QLabel("Use headphones for binaural beats. Keep volume comfortable.")
        hint.setObjectName("hint")
        lay.addWidget(hint)

        # --- signals
        self.preset_box.currentTextChanged.connect(self._on_preset)
        self.mode_group.buttonToggled.connect(self._on_mode)
        self.play_btn.toggled.connect(self._on_play)
        self.vol_slider.valueChanged.connect(self._on_volume)
        for spin, slider in ((self.base_spin, self.base_slider), (self.beat_spin, self.beat_slider)):
            spin.valueChanged.connect(lambda v, s=slider: self._sync_slider(s, v))
            spin.valueChanged.connect(self._on_manual_edit)
            slider.valueChanged.connect(lambda v, sp=spin: self._sync_spin(sp, v))

        self._on_preset(PRESETS[0].name)
        self._on_volume(50)

    # ------------------------------------------------------------- helpers
    def _param_row(self, grid, row, label, rng):
        spin = QDoubleSpinBox()
        spin.setRange(*rng)
        spin.setDecimals(1)
        spin.setSingleStep(0.5)
        spin.setSuffix(" Hz")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(rng[0] * SLIDER_SCALE), int(rng[1] * SLIDER_SCALE))
        grid.addWidget(label, row * 2, 0, 1, 2)
        grid.addWidget(slider, row * 2 + 1, 0, 1, 2)
        grid.addWidget(spin, row * 2 + 1, 2)
        return spin, slider

    @staticmethod
    def _sync_slider(slider, value):
        slider.blockSignals(True)
        slider.setValue(round(value * SLIDER_SCALE))
        slider.blockSignals(False)

    @staticmethod
    def _sync_spin(spin, ivalue):
        spin.setValue(ivalue / SLIDER_SCALE)  # triggers valueChanged -> edit

    @property
    def mode(self) -> str:
        return BINAURAL if self.rb_bin.isChecked() else ISOCHRONIC

    def _apply_to_engine(self) -> None:
        self.gen.set_mode(self.mode)
        self.gen.set_base_frequency(self.base_spin.value())
        self.gen.set_beat_frequency(self.beat_spin.value())
        self.scope.set_state(self.mode, self.beat_spin.value(), self.play_btn.isChecked())

    def _update_labels(self) -> None:
        self.beat_label.setText(
            "Beat Frequency (Target Brainwave)" if self.mode == BINAURAL
            else "Pulse Frequency (Target Brainwave)"
        )

    # ------------------------------------------------------------ handlers
    def _on_preset(self, name: str) -> None:
        preset = next((p for p in PRESETS if p.name == name), None)
        if preset is None:
            self.use_case.setText("Manual settings")
            return
        self._loading = True
        (self.rb_bin if preset.mode == BINAURAL else self.rb_iso).setChecked(True)
        self.base_spin.setValue(preset.base)
        self.beat_spin.setValue(preset.target)
        self.use_case.setText(preset.use_case)
        self._loading = False
        self._update_labels()
        self._apply_to_engine()

    def _on_manual_edit(self, _value=None) -> None:
        if not self._loading and self.preset_box.currentText() != CUSTOM:
            self.preset_box.blockSignals(True)
            self.preset_box.setCurrentText(CUSTOM)
            self.preset_box.blockSignals(False)
            self.use_case.setText("Manual settings")
        self._apply_to_engine()

    def _on_mode(self, _button, checked: bool) -> None:
        if not checked:
            return
        self._update_labels()
        if not self._loading and self.preset_box.currentText() != CUSTOM:
            self._on_manual_edit()
        self._apply_to_engine()  # engine fades out, switches, fades back in

    def _on_volume(self, value: int) -> None:
        self.vol_label.setText(f"{value}%")
        self.gen.set_volume(value / 100.0)

    def _on_play(self, checked: bool) -> None:
        if checked:
            self._apply_to_engine()
            try:
                self.gen.start()
            except Exception as exc:  # no device, device busy, etc.
                self.play_btn.blockSignals(True)
                self.play_btn.setChecked(False)
                self.play_btn.blockSignals(False)
                QMessageBox.critical(self, "Audio error", f"Could not open audio output:\n{exc}")
                return
            self.play_btn.setText("Stop")
        else:
            self.gen.stop()
            QTimer.singleShot(150, self.gen.close_if_idle)
            self.play_btn.setText("Play")
        self.scope.set_state(self.mode, self.beat_spin.value(), checked)

    def closeEvent(self, event) -> None:
        self.gen.shutdown()
        super().closeEvent(event)
