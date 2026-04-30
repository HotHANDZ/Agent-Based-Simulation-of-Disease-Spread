# RUN SEVERAL HEADLESS SIMULATIONS IN A ROW USING scenario CONSTANTS.
"""LOOP PRESET DISEASES PLUS ONE MANUAL DiseaseModel FROM SCENARIO."""

from __future__ import annotations

from disease import DiseaseModel
from disease_presets import build_disease, recovery_timesteps_from_infectious_days
from simulation import Simulation
import scenario

# (LABEL FOR PRINT, PRESET NAME OR None FOR MANUAL BLOCK).
CONFIGS: list[tuple[str, str | None]] = [
    ("covid19", "covid19"),
    ("flu", "flu"),
    ("strep", "strep"),
    ("manual", None),
]


def manual_disease_from_scenario() -> DiseaseModel:
    # SAME RECOVERY MAPPING AS scenario.make_disease() BUT WITHOUT PRESET BRANCH.
    rt = recovery_timesteps_from_infectious_days(
        scenario.infectious_period_days, scenario.hours_per_timestep
    )
    return DiseaseModel(
        scenario.transmission_prob,
        rt,
        vaccination_efficacy=scenario.vaccination_efficacy,
        contact_radius=scenario.contact_radius,
    )


def run_one(label: str, preset: str | None) -> None:
    if preset is None:
        disease = manual_disease_from_scenario()
    else:
        disease = build_disease(preset, hours_per_timestep=scenario.hours_per_timestep)

    sim = Simulation(
        scenario.num_agents,
        scenario.width,
        scenario.height,
        disease,
        vaccination_fraction=scenario.vaccination_fraction,
        bedridden=scenario.bedridden,
        movement_step_size=scenario.movement_step_size(),
        initial_infected_count=scenario.initial_infected_count,
    )
    steps = scenario.timesteps
    # MATCH main.py SUBSAMPLING FOR CSV ROWS.
    log_interval = max(1, min(1000, steps // 50))
    sim.run(steps, log_interval=log_interval)
    sim.plot()
    print(f"Done: {label}")


if __name__ == "__main__":
    for label, preset in CONFIGS:
        run_one(label, preset)
