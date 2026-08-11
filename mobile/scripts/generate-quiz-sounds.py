"""Synthesise the three quiz sounds.

The tones are generated rather than downloaded so the assets are ours, carry no
licence, and can be retuned by editing numbers instead of hunting for a new file.

Each is a short additive-synthesis bell: a fundamental plus a couple of quiet
partials, under an exponential decay with a few milliseconds of fade at each end
so nothing clicks. Run from the mobile directory:

    python scripts/generate-quiz-sounds.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44_100
AMPLITUDE = 0.62
FADE_SECONDS = 0.005
PARTIALS = ((1.0, 1.0), (2.0, 0.16), (3.0, 0.06))

OUTPUT_DIRECTORY = Path(__file__).resolve().parent.parent / "assets" / "sounds"

Note = tuple[float, float, float, float]

CORRECT: tuple[Note, ...] = (
    (1046.50, 0.00, 0.20, 0.85),
    (1318.51, 0.08, 0.34, 1.00),
)

WRONG: tuple[Note, ...] = (
    (329.63, 0.00, 0.20, 0.75),
    (246.94, 0.10, 0.30, 0.70),
)

FINISHED: tuple[Note, ...] = (
    (523.25, 0.00, 0.30, 0.70),
    (659.25, 0.10, 0.30, 0.75),
    (783.99, 0.20, 0.32, 0.80),
    (1046.50, 0.30, 0.55, 1.00),
)


def render(notes: tuple[Note, ...]) -> list[float]:
    length = max(start + duration for _, start, duration, _ in notes)
    samples = [0.0] * int(length * SAMPLE_RATE)

    for frequency, start, duration, level in notes:
        offset = int(start * SAMPLE_RATE)
        count = int(duration * SAMPLE_RATE)
        for index in range(count):
            if offset + index >= len(samples):
                break
            seconds = index / SAMPLE_RATE
            decay = math.exp(-4.2 * seconds / duration)
            value = sum(
                weight * math.sin(2 * math.pi * frequency * ratio * seconds)
                for ratio, weight in PARTIALS
            )
            samples[offset + index] += value * decay * level

    return normalise(samples)


def normalise(samples: list[float]) -> list[float]:
    peak = max((abs(sample) for sample in samples), default=0.0)
    if peak == 0.0:
        return samples

    scale = AMPLITUDE / peak
    fade = int(FADE_SECONDS * SAMPLE_RATE)
    total = len(samples)

    faded = []
    for index, sample in enumerate(samples):
        envelope = min(1.0, index / fade, (total - index) / fade) if fade else 1.0
        faded.append(sample * scale * envelope)
    return faded


def write(name: str, samples: list[float]) -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIRECTORY / name
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(
            b"".join(
                struct.pack("<h", int(max(-1.0, min(1.0, sample)) * 32_767)) for sample in samples
            )
        )
    print(f"{path.name}: {path.stat().st_size / 1024:.1f} KB")


def main() -> None:
    write("correct.wav", render(CORRECT))
    write("wrong.wav", render(WRONG))
    write("finished.wav", render(FINISHED))


if __name__ == "__main__":
    main()
