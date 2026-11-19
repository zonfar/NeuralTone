from dataclasses import dataclass

from tone_generator import BINAURAL, ISOCHRONIC


@dataclass(frozen=True)
class Preset:
    name: str
    mode: str
    base: float
    target: float
    use_case: str


CUSTOM = "Custom"

# Band associations follow the commonly cited EEG ranges: delta 0.5-4 Hz,
# theta 4-8, alpha 8-12, SMR 12-15, beta 13-30, gamma 30+. Research on
# entrainment is mixed and effects vary by person; treat these as starting
# points, not treatments. The lowest delta is clamped to the app's 1 Hz minimum.
BINAURAL_PRESETS = [
    Preset("Deep Work (Gamma)", BINAURAL, 200.0, 40.0, "Sustained, long-duration focus (40 Hz gamma)"),
    Preset("Study (Low Beta)", BINAURAL, 220.0, 15.0, "Active learning and reading (low beta)"),
    Preset("Calm Focus (SMR)", BINAURAL, 220.0, 13.5, "Relaxed attention, steady concentration (SMR)"),
    Preset("Meditation (Alpha)", BINAURAL, 180.0, 10.0, "Relaxed alertness"),
    Preset("Schumann Grounding", BINAURAL, 200.0, 7.83, "Earth's fundamental resonance, calm and grounded (alpha/theta edge)"),
    Preset("Creative Drift (Theta)", BINAURAL, 180.0, 5.5, "Daydreaming and idea generation (theta)"),
    Preset("Deep Sleep (Theta)", BINAURAL, 160.0, 6.0, "Smooth wind-down, non-jarring"),
    Preset("Delta Sleep", BINAURAL, 150.0, 2.0, "Deep, dreamless sleep (delta)"),
]

ISOCHRONIC_PRESETS = [
    Preset("Gamma Focus Pulse", ISOCHRONIC, 250.0, 40.0, "Intense concentration, 40 Hz gamma"),
    Preset("The Espresso Shot (Beta)", ISOCHRONIC, 250.0, 20.0, "5-minute rapid wake-up / fog clearing"),
    Preset("Calm Focus (SMR)", ISOCHRONIC, 220.0, 13.5, "Relaxed attention, steady concentration (SMR)"),
    Preset("Pre-Performance (Alpha)", ISOCHRONIC, 200.0, 12.0, "Quick pattern interrupt for anxiety"),
    Preset("Alpha Relax", ISOCHRONIC, 200.0, 10.0, "Unwinding after work, light relaxation"),
    Preset("Schumann Grounding", ISOCHRONIC, 200.0, 7.83, "Earth's fundamental resonance, calm and grounded (alpha/theta edge)"),
    Preset("Creative Drift (Theta)", ISOCHRONIC, 200.0, 5.5, "Daydreaming and idea generation (theta)"),
    Preset("Delta Sleep", ISOCHRONIC, 150.0, 2.0, "Deep, dreamless sleep (delta)"),
]

PRESETS = BINAURAL_PRESETS + ISOCHRONIC_PRESETS
