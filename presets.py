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

PRESETS = [
    Preset("Deep Work (Gamma)", BINAURAL, 200.0, 40.0, "Sustained, long-duration focus"),
    Preset("The Espresso Shot (Beta)", ISOCHRONIC, 250.0, 20.0, "5-minute rapid wake-up / fog clearing"),
    Preset("Pre-Performance (Alpha)", ISOCHRONIC, 200.0, 12.0, "Quick pattern interrupt for anxiety"),
    Preset("Deep Sleep (Theta)", BINAURAL, 160.0, 6.0, "Smooth wind-down, non-jarring"),
    Preset("Meditation (Alpha)", BINAURAL, 180.0, 10.0, "Relaxed alertness"),
]
