"""Train the Tier A models on synthetic data and write them out as configuration.

Ghana surveillance line-lists were not available to us, so the training set is
generated from a documented latent process rather than observed cases. The
process is deliberately smooth where the rules are stepped: the model learns how
risk rises between published thresholds, which is the thing a step function
cannot express. It is not a substitute for the rules and cannot overturn them.

Swapping in real case data is a training run, not a rewrite: replace
`synthetic_samples` with a reader over the real line-list and run this again.

Run: python -m scripts.train_tier_a
"""

import random
from collections.abc import Callable, Sequence
from math import exp
from pathlib import Path

from climahealth.domain.models import HealthCondition, SignalName

TRAINING_SEED = 20260804
SAMPLE_COUNT = 6000
HOLDOUT_FRACTION = 0.25
LEARNING_RATE = 0.35
EPOCHS = 400

MODEL_PACKAGE = Path(__file__).resolve().parent.parent / "climahealth" / "domain" / "model"
OUTPUT_PATH = MODEL_PACKAGE / "trained.py"

SignalRange = tuple[float, float]


class ConditionSpec:
    def __init__(
        self,
        condition: HealthCondition,
        signals: dict[SignalName, SignalRange],
        latent: Callable[[dict[SignalName, float]], float],
    ) -> None:
        self.condition = condition
        self.signals = signals
        self.latent = latent


def logistic(value: float) -> float:
    return 1.0 / (1.0 + exp(-max(min(value, 60.0), -60.0)))


def ramp(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return min(max((value - low) / (high - low), 0.0), 1.0)


def malaria_latent(sample: dict[SignalName, float]) -> float:
    rain = ramp(sample[SignalName.RAINFALL_7D_MM], 20.0, 160.0)
    humidity = ramp(sample[SignalName.HUMIDITY_MEAN_PERCENT], 50.0, 90.0)
    temperature = sample[SignalName.TEMPERATURE_MEAN_C]
    thermal = ramp(temperature, 18.0, 27.0) * (1 - ramp(temperature, 30.0, 36.0))
    return -3.2 + 3.4 * rain + 2.6 * humidity + 2.4 * thermal


def cholera_latent(sample: dict[SignalName, float]) -> float:
    rain = ramp(sample[SignalName.RAINFALL_7D_MM], 40.0, 220.0)
    sustained = ramp(sample[SignalName.RAINFALL_14D_MM], 60.0, 320.0)
    warmth = ramp(sample[SignalName.TEMPERATURE_MEAN_C], 22.0, 32.0)
    return -3.6 + 3.8 * rain + 2.2 * sustained + 1.4 * warmth


def meningitis_latent(sample: dict[SignalName, float]) -> float:
    dust = ramp(sample[SignalName.DUST_CONCENTRATION_UG_M3], 20.0, 180.0)
    dryness = 1 - ramp(sample[SignalName.HUMIDITY_MEAN_PERCENT], 8.0, 45.0)
    spell = ramp(sample[SignalName.CONSECUTIVE_DRY_DAYS], 5.0, 55.0)
    return -3.4 + 3.2 * dust + 2.8 * dryness + 2.0 * spell


def diarrhoeal_latent(sample: dict[SignalName, float]) -> float:
    rain = ramp(sample[SignalName.RAINFALL_7D_MM], 30.0, 190.0)
    warmth = ramp(sample[SignalName.TEMPERATURE_MEAN_C], 24.0, 34.0)
    return -2.9 + 3.3 * rain + 2.1 * warmth


def respiratory_latent(sample: dict[SignalName, float]) -> float:
    heat = ramp(sample[SignalName.TEMPERATURE_MAX_C], 32.0, 45.0)
    particulate = ramp(sample[SignalName.PARTICULATE_MATTER_10_UG_M3], 30.0, 260.0)
    dryness = 1 - ramp(sample[SignalName.HUMIDITY_MEAN_PERCENT], 10.0, 50.0)
    return -3.3 + 3.0 * heat + 2.9 * particulate + 1.6 * dryness


SPECS: tuple[ConditionSpec, ...] = (
    ConditionSpec(
        HealthCondition.MALARIA,
        {
            SignalName.RAINFALL_7D_MM: (0.0, 260.0),
            SignalName.HUMIDITY_MEAN_PERCENT: (15.0, 100.0),
            SignalName.TEMPERATURE_MEAN_C: (16.0, 38.0),
        },
        malaria_latent,
    ),
    ConditionSpec(
        HealthCondition.CHOLERA,
        {
            SignalName.RAINFALL_7D_MM: (0.0, 300.0),
            SignalName.RAINFALL_14D_MM: (0.0, 420.0),
            SignalName.TEMPERATURE_MEAN_C: (16.0, 38.0),
        },
        cholera_latent,
    ),
    ConditionSpec(
        HealthCondition.MENINGITIS,
        {
            SignalName.DUST_CONCENTRATION_UG_M3: (0.0, 260.0),
            SignalName.HUMIDITY_MEAN_PERCENT: (5.0, 100.0),
            SignalName.CONSECUTIVE_DRY_DAYS: (0.0, 90.0),
        },
        meningitis_latent,
    ),
    ConditionSpec(
        HealthCondition.DIARRHOEAL_DISEASE,
        {
            SignalName.RAINFALL_7D_MM: (0.0, 260.0),
            SignalName.TEMPERATURE_MEAN_C: (16.0, 38.0),
        },
        diarrhoeal_latent,
    ),
    ConditionSpec(
        HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        {
            SignalName.TEMPERATURE_MAX_C: (20.0, 48.0),
            SignalName.PARTICULATE_MATTER_10_UG_M3: (0.0, 320.0),
            SignalName.HUMIDITY_MEAN_PERCENT: (5.0, 100.0),
        },
        respiratory_latent,
    ),
)


def synthetic_samples(
    spec: ConditionSpec, rng: random.Random
) -> list[tuple[dict[SignalName, float], int]]:
    samples = []
    for _ in range(SAMPLE_COUNT):
        reading = {signal: rng.uniform(low, high) for signal, (low, high) in spec.signals.items()}
        probability = logistic(spec.latent(reading))
        samples.append((reading, 1 if rng.random() < probability else 0))
    return samples


def standardisation(
    samples: Sequence[tuple[dict[SignalName, float], int]], signal: SignalName
) -> tuple[float, float]:
    values = [reading[signal] for reading, _ in samples]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return mean, variance**0.5 or 1.0


def train(
    samples: Sequence[tuple[dict[SignalName, float], int]],
    signals: Sequence[SignalName],
    scaling: dict[SignalName, tuple[float, float]],
) -> tuple[float, dict[SignalName, float]]:
    intercept = 0.0
    weights = {signal: 0.0 for signal in signals}

    for _ in range(EPOCHS):
        intercept_gradient = 0.0
        gradients = {signal: 0.0 for signal in signals}

        for reading, label in samples:
            scaled = {
                signal: (reading[signal] - scaling[signal][0]) / scaling[signal][1]
                for signal in signals
            }
            prediction = logistic(
                intercept + sum(weights[signal] * scaled[signal] for signal in signals)
            )
            error = prediction - label
            intercept_gradient += error
            for signal in signals:
                gradients[signal] += error * scaled[signal]

        count = len(samples)
        intercept -= LEARNING_RATE * intercept_gradient / count
        for signal in signals:
            weights[signal] -= LEARNING_RATE * gradients[signal] / count

    return intercept, weights


def accuracy(
    samples: Sequence[tuple[dict[SignalName, float], int]],
    signals: Sequence[SignalName],
    scaling: dict[SignalName, tuple[float, float]],
    intercept: float,
    weights: dict[SignalName, float],
) -> float:
    correct = 0
    for reading, label in samples:
        scaled = {
            signal: (reading[signal] - scaling[signal][0]) / scaling[signal][1]
            for signal in signals
        }
        prediction = logistic(
            intercept + sum(weights[signal] * scaled[signal] for signal in signals)
        )
        correct += int((prediction >= 0.5) == bool(label))
    return correct / len(samples)


def render(models: list[str]) -> str:
    body = ",\n".join(models)
    return (
        '"""Tier A coefficients. Generated by scripts/train_tier_a.py — do not hand-edit.\n\n'
        "Trained on synthetic data from a documented latent process, because Ghana\n"
        "surveillance line-lists were not available. Replacing the training source is a\n"
        'training run, not an engine change.\n"""\n\n'
        "from climahealth.domain.model.logistic import ConditionModel, StandardisedTerm\n"
        "from climahealth.domain.models import HealthCondition, SignalName\n\n"
        f"TRAINED_MODELS: tuple[ConditionModel, ...] = (\n{body},\n)\n\n"
        "CONDITION_MODELS: dict[HealthCondition, ConditionModel] = {\n"
        "    model.condition: model for model in TRAINED_MODELS\n"
        "}\n"
    )


def main() -> None:
    rng = random.Random(TRAINING_SEED)
    rendered = []

    for spec in SPECS:
        samples = synthetic_samples(spec, rng)
        split = int(len(samples) * (1 - HOLDOUT_FRACTION))
        training, holdout = samples[:split], samples[split:]
        signals = list(spec.signals)
        scaling = {signal: standardisation(training, signal) for signal in signals}
        intercept, weights = train(training, signals, scaling)
        score = accuracy(holdout, signals, scaling, intercept, weights)

        terms = "\n".join(
            f"            StandardisedTerm(\n"
            f"                signal=SignalName.{signal.name},\n"
            f"                mean={scaling[signal][0]:.6f},\n"
            f"                scale={scaling[signal][1]:.6f},\n"
            f"                coefficient={weights[signal]:.6f},\n"
            f"            ),"
            for signal in signals
        )
        rendered.append(
            f"    ConditionModel(\n"
            f"        condition=HealthCondition.{spec.condition.name},\n"
            f"        intercept={intercept:.6f},\n"
            f"        terms=(\n{terms}\n        ),\n"
            f'        trained_on="synthetic",\n'
            f"        sample_count={len(training)},\n"
            f"        holdout_accuracy={score:.4f},\n"
            f"    )"
        )
        print(f"{spec.condition.value:26} holdout accuracy {score:.1%}")

    OUTPUT_PATH.write_text(render(rendered))
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
