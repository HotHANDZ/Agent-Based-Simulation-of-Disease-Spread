"""
Named disease presets for rough, classroom-style storytelling.

This model is SIR-like with immediate infection on contact (no latent/exposed class), spatial
mixing, and abstract timesteps. Presets do **not** reproduce published R0 or generation times;
they give **order-of-magnitude** infectious duration and relative transmissibility / “reach”
you can justify in prose using real disease biology.

**How to calibrate time:** Set ``hours_per_timestep`` in ``scenario.py`` (real hours per
simulation step). Preset and manual ``infectious_period_days`` both convert to
``recovery_time`` steps the same way.

Example: ``infectious_period_days = 10``, ``hours_per_timestep = 1`` (one step = one hour) →
``recovery_time ≈ 10 * 24 = 240`` steps.
"""

from __future__ import annotations

from disease import DiseaseModel

# Ballpark infectious windows (single compartment), transmission tuned relative to each other,
# contact_radius = qualitative “how far apart a contact can still count” on your grid.
_PRESETS: dict[str, dict] = {
    "flu": {
        "label": "Seasonal influenza (illustrative; typical ~5–7 d infectious window in simple models)",
        "infectious_period_days": 5.5,
        "transmission_probability": 0.045,
        "contact_radius": 3.0,
        "vaccination_efficacy": 0.5,
    },
    "covid19": {
        "label": "SARS-CoV-2–style (simplified: longer window, much higher per-contact spread + wider reach vs flu in this toy grid)",
        "infectious_period_days": 10.0,
        # Tuned so COVID clearly out-infects flu here: more attempts succeed when pairs overlap,
        # and radius is larger (aerosol / crowding analogy in abstract grid units).
        "transmission_probability": 0.14,
        "contact_radius": 6.0,
        "vaccination_efficacy": 0.55,
    },
    "strep": {
        "label": "Group A strep pharyngitis analogy (bacterial; no vaccine in preset; shorter window, closer contact)",
        "infectious_period_days": 4.0,
        "transmission_probability": 0.028,
        "contact_radius": 2.5,
        "vaccination_efficacy": 0.0,
    },
}

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
    """
    Convert a real-world infectious window (days) into ``recovery_time`` simulation steps.

    One timestep represents ``hours_per_timestep`` real hours, so each day is ``24 /
    hours_per_timestep`` steps.
    """
    if infectious_period_days <= 0:
        raise ValueError("infectious_period_days must be positive")
    if hours_per_timestep <= 0:
        raise ValueError("hours_per_timestep must be positive")
    steps_per_day = 24.0 / hours_per_timestep
    return max(1, round(infectious_period_days * steps_per_day))


def build_disease(preset: str, hours_per_timestep: float) -> DiseaseModel:
    """
    Build a ``DiseaseModel`` from a named preset.

    Parameters
    ----------
    preset:
        One of ``flu``, ``covid19``, ``strep`` (aliases: ``covid``, ``influenza``, …).
    hours_per_timestep:
        Real-world hours represented by one simulation timestep (must be > 0).
    """
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
    """Human-readable one-line description for logs or reports."""
    key = _ALIASES.get(preset.strip().lower(), preset.strip().lower())
    if key not in _PRESETS:
        return preset
    return _PRESETS[key]["label"]
