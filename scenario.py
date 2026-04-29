"""
Shared simulation parameters for main.py.

Time base
---------
``hours_per_timestep`` is how many **real hours** one simulation **step** represents.
Example: ``hours_per_timestep = 1.0`` → one step = one hour, so one real day = 24 steps.

``infectious_period_days`` (preset dict or manual block below) is converted to
``DiseaseModel.recovery_time`` in steps by:

    recovery_time_steps ≈ infectious_period_days * (24 / hours_per_timestep)

Movement (same clock)
---------------------
Coordinates are **abstract grid units** (not meters unless you say so in your report).
``movement_units_per_hour`` is how far an agent tends to move along that grid in **one
simulated hour**. Each step advances the clock by ``hours_per_timestep`` hours, so per
step agents move ``movement_units_per_hour * hours_per_timestep`` units—keeping travel
speed consistent when you change how long a step represents.

Disease
-------
Set ``disease_preset`` to a name from ``disease_presets.py``, or ``None`` and use the
manual fields (including ``infectious_period_days`` and ``contact_radius``).
"""

from disease import DiseaseModel
from disease_presets import build_disease, recovery_timesteps_from_infectious_days

# Core scenario: world, population
num_agents = 500
# How many agents start as Infected (creation order: north→south→east→west). Use >1 if a single seed often recovers before transmitting.
initial_infected_count = 5
vaccination_fraction = 0.1
bedridden = True
width = 500
height = 500
timesteps = 10000

# --- Clock (preset + manual) ---
# Real hours represented by one simulation timestep (e.g. 1.0 → one step = one hour).
hours_per_timestep = 1.0

# Grid units per simulated hour of movement (abstract; tune with width/height and contact_radius).
movement_units_per_hour = 5.0

# --- Disease ---
# Named preset: "flu" | "covid19" | "strep" (see disease_presets.py). Set to None for manual.
disease_preset = "covid19"

# Manual disease (only when disease_preset is None)
infectious_period_days = 10.0
transmission_prob = 0.5
vaccination_efficacy = 0.5
contact_radius = 3.0

# Live viewer only (playback speed; does not change the model)
live_interval_ms = 40
live_steps_per_frame = 4


def movement_step_size() -> float:
    """Grid units moved per simulation step (speed × hours represented by that step)."""
    return movement_units_per_hour * hours_per_timestep


def make_disease() -> DiseaseModel:
    if disease_preset:
        return build_disease(disease_preset, hours_per_timestep=hours_per_timestep)
    recovery_time = recovery_timesteps_from_infectious_days(
        infectious_period_days, hours_per_timestep
    )
    return DiseaseModel(
        transmission_prob,
        recovery_time,
        vaccination_efficacy=vaccination_efficacy,
        contact_radius=contact_radius,
    )
