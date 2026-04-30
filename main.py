# ENTRY POINT: SET PARAMETERS IN SCENARIO.PY; RUN WITH OR WITHOUT LIVE ANIMATION.
"""CONFIGURE SCENARIO.PY THEN RUN THIS MODULE."""
import argparse

from simulation import Simulation
import scenario


def main() -> None:
    # PARSE --NO-LIVE FOR HEADLESS RUN (CSV/JSON WRITTEN INSIDE run()).
    parser = argparse.ArgumentParser(description="Agent-based disease simulation (see scenario.py).")
    parser.add_argument(
        "--no-live",
        action="store_true",
        help="Skip the 2D animation; run the model with run() and save outputs/ then plot.",
    )
    args = parser.parse_args()

    # BUILD DISEASE FROM PRESET OR MANUAL FIELDS IN SCENARIO.
    disease = scenario.make_disease()
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

    # SUBSAMPLE INTERVAL FOR CSV ROWS (CAPPED SO FILES STAY REASONABLE).
    _log = max(1, min(1000, scenario.timesteps // 50))

    if args.no_live:
        sim.run(scenario.timesteps, log_interval=_log)
    else:
        # LIVE MODE: ANIMATION ONLY UNTIL WINDOW CLOSES; NO FILES YET.
        sim.run_live(
            scenario.timesteps,
            interval_ms=scenario.live_interval_ms,
            steps_per_frame=scenario.live_steps_per_frame,
        )
        # RUN_LIVE DOES NOT WRITE CSV/JSON; DUMP ARTIFACTS AFTER THE WINDOW CLOSES.
        sim.write_run_artifacts(scenario.timesteps, log_interval=_log)

    sim.plot()


if __name__ == "__main__":
    main()
