from climahealth.domain.models import ClimateFeatures, DistrictContext, SignalName

SIGNAL_LABELS: dict[SignalName, str] = {
    SignalName.RAINFALL_7D_MM: "7-day rainfall",
    SignalName.RAINFALL_14D_MM: "14-day rainfall",
    SignalName.CONSECUTIVE_DRY_DAYS: "consecutive dry days",
    SignalName.HUMIDITY_MEAN_PERCENT: "average humidity",
    SignalName.TEMPERATURE_MEAN_C: "average temperature",
    SignalName.TEMPERATURE_MAX_C: "peak temperature",
    SignalName.DUST_CONCENTRATION_UG_M3: "dust concentration",
    SignalName.PARTICULATE_MATTER_10_UG_M3: "PM10",
    SignalName.POOR_SANITATION_INDEX: "sanitation deficit",
    SignalName.UNSAFE_WATER_RATIO: "unsafe water access",
    SignalName.STAGNANT_WATER_INDEX: "stagnant water presence",
}

SIGNAL_UNITS: dict[SignalName, str] = {
    SignalName.RAINFALL_7D_MM: " mm",
    SignalName.RAINFALL_14D_MM: " mm",
    SignalName.CONSECUTIVE_DRY_DAYS: " days",
    SignalName.HUMIDITY_MEAN_PERCENT: "%",
    SignalName.TEMPERATURE_MEAN_C: " C",
    SignalName.TEMPERATURE_MAX_C: " C",
    SignalName.DUST_CONCENTRATION_UG_M3: " ug/m3",
    SignalName.PARTICULATE_MATTER_10_UG_M3: " ug/m3",
    SignalName.POOR_SANITATION_INDEX: "",
    SignalName.UNSAFE_WATER_RATIO: "",
    SignalName.STAGNANT_WATER_INDEX: "",
}


def resolve_signal(
    signal: SignalName,
    features: ClimateFeatures,
    context: DistrictContext,
) -> float | None:
    match signal:
        case SignalName.RAINFALL_7D_MM:
            return features.rainfall_7d_mm
        case SignalName.RAINFALL_14D_MM:
            return features.rainfall_14d_mm
        case SignalName.CONSECUTIVE_DRY_DAYS:
            return float(features.consecutive_dry_days)
        case SignalName.HUMIDITY_MEAN_PERCENT:
            return features.humidity_mean_percent
        case SignalName.TEMPERATURE_MEAN_C:
            return features.temperature_mean_c
        case SignalName.TEMPERATURE_MAX_C:
            return features.temperature_max_c
        case SignalName.DUST_CONCENTRATION_UG_M3:
            return features.dust_concentration_ug_m3
        case SignalName.PARTICULATE_MATTER_10_UG_M3:
            return features.particulate_matter_10_ug_m3
        case SignalName.POOR_SANITATION_INDEX:
            return context.poor_sanitation_index
        case SignalName.UNSAFE_WATER_RATIO:
            return context.unsafe_water_ratio
        case SignalName.STAGNANT_WATER_INDEX:
            return context.stagnant_water_index


def describe_signal(signal: SignalName, value: float) -> str:
    return f"{SIGNAL_LABELS[signal]} {round(value, 1):g}{SIGNAL_UNITS[signal]}"


def describe_threshold(signal: SignalName, threshold: float) -> str:
    return f"{threshold:g}{SIGNAL_UNITS[signal]}"
