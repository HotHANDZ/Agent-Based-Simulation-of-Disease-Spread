# NAMED DiseaseModel BUILDS; RECOVERY STEPS USE scenario.hours_per_timestep.
"""PRESET FLU / COVID19 / STREP AND HELPERS TO CONVERT INFECTIOUS DAYS TO STEPS."""

from __future__ import annotations

from disease import DiseaseModel

# STATIC TABLES: LABELS ARE FOR DISPLAY ONLY; NUMBERS ARE TOY CALIBRATION.
_PRESETS: dict[str, dict] = {
    "flu": {
        "label": "Seasonal influenza (illustrative; typical ~5–7 d infectious window in simple models)",
        "infectious_period_days": 5.5,
        "transmission_probability": 0.18,
        "contact_radius": 3.0,
        "vaccination_efficacy": 0.5,
    },
    "covid19": {
        "label": "SARS-CoV-2–style (simplified: longer window, much higher per-contact spread + wider reach vs flu in this toy grid)",
        "infectious_period_days": 10.0,
        # COVID PRESET: HIGHER P AND RADIUS THAN FLU SO OUTBREAKS DOMINATE FLU IN THIS TOY MODEL.
        "transmission_probability": 0.4,
        "contact_radius": 6.0,
        "vaccination_efficacy": 0.55,
    },
    "strep": {
        "label": "Group A strep pharyngitis analogy (bacterial; no vaccine in preset; shorter window, closer contact)",
        "infectious_period_days": 4.0,
        "transmission_probability": 0.01,
        "contact_radius": 2.5,
        "vaccination_efficacy": 0.0,
    },
}

# USER CAN TYPE ALIASES; WE MAP TO CANONICAL PRESET KEYS.
_ALIASES = {
    "covid": "covid19",
    "coronavirus": "covid19",
    "influenza": "flu",
    "strep_throat": "strep",
    "streptococcus": "strep",
}


def preset_names() -> list[str]:
    return sorted(_PRESETS.keys())


def recovery_timesteps_from_infectious_days(
    infectious_period_days: float, hours_per_timestep: float
) -> int:
    # DAYS * (24 H / HOURS_PER_STEP) -> INTEGER STEP COUNT, AT LEAST 1.
    if infectious_period_days <= 0:
        raise ValueError("infectious_period_days must be positive")
    if hours_per_timestep <= 0:
        raise ValueError("hours_per_timestep must be positive")
    steps_per_day = 24.0 / hours_per_timestep
    return max(1, round(infectious_period_days * steps_per_day))


def build_disease(preset: str, hours_per_timestep: float) -> DiseaseModel:
    key = _ALIASES.get(preset.strip().lower(), preset.strip().lower())
    if key not in _PRESETS:
        raise ValueError(
            f"Unknown disease preset {preset!r}. Choose one of: {', '.join(preset_names())}"
        )
    if hours_per_timestep <= 0:
        raise ValueError("hours_per_timestep must be positive")

    p = _PRESETS[key]
    recovery_timesteps = recovery_timesteps_from_infectious_days(
        p["infectious_period_days"], hours_per_timestep
    )

    return DiseaseModel(
        p["transmission_probability"],
        recovery_timesteps,
        vaccination_efficacy=p["vaccination_efficacy"],
        contact_radius=p["contact_radius"],
    )


def preset_summary(preset: str) -> str:
    # ONE-LINE LABEL FOR LOGGING; FALL BACK TO RAW STRING IF UNKNOWN.
    key = _ALIASES.get(preset.strip().lower(), preset.strip().lower())
    if key not in _PRESETS:
        return preset
    return _PRESETS[key]["label"]
