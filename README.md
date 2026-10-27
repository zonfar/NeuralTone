# NeuralTone

A standalone Windows app that generates pure binaural and isochronic tones in real time (sine waves only, no noise or pre-rendered audio).

- **Binaural** – left = base frequency, right = base + beat (headphones required)
- **Isochronic** – mono carrier gated by a 50% duty square pulse with ~7 ms edge smoothing
- 50 ms fade on play/stop and mode switches, presets, manual tuning, slowed-down scope

Stack: Python, PySide6, numpy, sounddevice.

## Run

```
pip install -r requirements.txt
python main.py
```

## Build a single .exe

Run `build.bat` → `dist\NeuralTone.exe`. To use a custom icon, place your own `icon.ico` in the project folder first (otherwise one is generated).
