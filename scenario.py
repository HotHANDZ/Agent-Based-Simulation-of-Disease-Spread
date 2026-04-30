# SHARED CONSTANTS FOR WORLD, POPULATION, CLOCK, DISEASE, AND LIVE VIEWER TUNING.
"""ALL TUNABLE PARAMETERS FOR MAIN.PY AND RUN_BATCH.PY LIVE HERE."""

from disease import DiseaseModel
from disease_presets import build_disease, recovery_timesteps_from_infectious_days

# POPULATION AND SPACE (ABSTRACT GRID UNITS).
num_agents = 500
initial_infected_count = 5
vaccination_fraction = 0
bedridden = True
width = 500
height = 500
timesteps = 700

# CLOCK: ONE SIM STEP = hours_per_timestep REAL HOURS.
hours_per_timestep = 1.0
# SPEED IN GRID UNITS PER SIMULATED HOUR (USED ONLY IF movement_distance_per_step IS None BELOW).
movement_units_per_hour = 5.0
# GRID UNITS EACH AGENT MOVES PER SIMULATION STEP TOWARD ITS TARGET. SET A NUMBER HERE TO USE IT DIRECTLY.
# IF None, USE movement_units_per_hour * hours_per_timestep INSTEAD.
movement_distance_per_step = None

# SET TO A PRESET NAME (E.G. "flu") OR NONE TO USE MANUAL BLOCK BELOW.
disease_preset = None

# MANUAL DISEASE WHEN disease_preset IS NONE (recovery_time DERIVED FROM infectious_period_days).
infectious_period_days = 10.0
transmission_prob = .4
vaccination_efficacy = 0.5
contact_radius = 3

# MATPLOTLIB ANIMATION ONLY (DOES NOT CHANGE EPIDEMIOLOGY).
live_interval_ms = 40
live_steps_per_frame = 4


def movement_step_size() -> float:
    # GRID UNITS MOVED PER EPIDEMIOLOGICAL TIMESTEP (EXPLICIT OR FROM HOURLY SPEED).
    if movement_distance_per_step is not None:
        return float(movement_distance_per_step)
    return movement_units_per_hour * hours_per_timestep


def _preset_name_or_none():
    # NORMALIZE disease_preset: EMPTY OR "none" STRING -> USE MANUAL PARAMETERS.
    p = disease_preset
    if p is None:
        return None
    if isinstance(p, str):
        s = p.strip()
        if not s or s.lower() in ("none", "null"):
            return None
        return s
    return str(p)


def make_disease() -> DiseaseModel:
    preset = _preset_name_or_none()
    if preset:
        return build_disease(preset, hours_per_timestep=hours_per_timestep)
    recovery_time = recovery_timesteps_from_infectious_days(
        infectious_period_days, hours_per_timestep
    )
    return DiseaseModel(
        transmission_prob,
        recovery_time,
        vaccination_efficacy=vaccination_efficacy,
        contact_radius=contact_radius,
    )
