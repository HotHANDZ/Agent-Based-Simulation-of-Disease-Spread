# Agent-based SIR simulation of infectious disease spread

Discrete-time **agent-based model (ABM)** on a 2D rectangle: agents commute between homes on the boundary and random interior targets, may infect one another when within a Euclidean **contact radius**, and recover after a fixed infectious period (in simulation steps). The implementation matches a standard **Susceptible–Infected–Recovered (SIR)** compartment story at the population level, with explicit space and movement.

**Repository:** [github.com/HotHANDZ/Agent-Based-Simulation-of-Disease-Spread](https://github.com/HotHANDZ/Agent-Based-Simulation-of-Disease-Spread)

## Features

- Core classes: `Agent` (movement, health state, commute state machine), `DiseaseModel` (transmission probability, recovery time, contact radius, vaccine scaling), `Simulation` (population, timestep loop, outputs, plots, live view).
- Fixed timestep order: move all agents, then pairwise transmission attempts, then infection timers and recovery, then S/I/R counts.
- Transmission: Bernoulli trial per at-risk pair per step; distance must be strictly less than the disease contact radius.
- Vaccination: static trait; vaccinated susceptibles use per-contact probability scaled by `(1 − r)` against the base transmission probability.
- Bedridden (stay-home-when-sick): optional; infected agents steer toward home until recovered (`scenario.bedridden`).
- Disease presets in `disease_presets.py` (`flu`, `covid19`, `strep`) or manual fields in `scenario.py`.
- Artifacts under `outputs/`: time series CSV, run metadata JSON, SIR plot PNG; batch mode adds aggregated tables, KPI JSON, and summary PNG.

## Requirements

- Python 3.10 or newer
- Packages listed in `requirements.txt` (NumPy, Matplotlib; Pillow for GIF export via `save_live_animation`).

## Setup

```bash
cd TermProject
python -m venv venv
```

Activate the virtual environment:

- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **Windows (cmd):** `.\venv\Scripts\activate.bat`
- **macOS / Linux:** `source venv/bin/activate`

Install packages:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

Edit **`scenario.py`** — it is the single place for experiment knobs:

| Area | Examples |
|------|-----------|
| Population & space | `num_agents`, `width`, `height`, `initial_infected_count` |
| Clock | `timesteps`, `hours_per_timestep` (links steps to “real” hours/days in plots and batch) |
| Movement | `movement_distance_per_step` or `movement_units_per_hour` + `hours_per_timestep` |
| Policy | `population_vaccinated_fraction` (0–1), `bedridden` |
| Disease | `disease_preset` (`None` for manual) or manual `transmission_prob`, `infectious_period_days`, `contact_radius`, `vaccine_transmission_risk_reduction_fraction` |
| Live view | `live_interval_ms`, `live_steps_per_frame` |

`scenario.make_disease()` returns a `DiseaseModel` used by `main.py` and `run_batch.py`.

## Running

**Interactive run** (2D animation; after you close the window, artifacts are written, then the SIR plot opens):

```bash
python main.py
```

**Headless run** (no animation; writes outputs then plots):

```bash
python main.py --no-live
```

**Batch / Monte Carlo** (many independent replications using the same `scenario.py` settings; writes under `outputs/batch_<timestamp>/`):

```bash
python run_batch.py
python run_batch.py --iterations 30 --steps 500 --output-dir outputs
```

Arguments: `--iterations` (default 20), `--steps` (default `scenario.timesteps`), `--output-dir` (default `outputs`).

## Outputs

- **Single run:** timestamped folder under `outputs/` with `*_timeseries.csv`, `*_metadata.json`, and `run_plot.png` (and paths logged to the console).
- **Batch:** `batch_results.csv`, `batch_iteration_summary.csv`, `batch_summary.json`, `batch_summary.png`.

The `outputs/` directory is gitignored.

## Project layout

| File | Role |
|------|------|
| `scenario.py` | All tunable parameters; `make_disease()`, `movement_step_size()` |
| `main.py` | CLI entry: `--no-live` or default live + `write_run_artifacts` + `plot()` |
| `run_batch.py` | Batch runner; aggregates CSV/JSON/PNG |
| `simulation.py` | `Simulation`: loop, logging, matplotlib plot and animation |
| `agent.py` | `Agent`: position, SIR state, commute / bedridden movement |
| `disease.py` | `DiseaseModel` parameters |
| `disease_presets.py` | Named presets and day→step helpers |

## Notes

- Pairwise contact checks are **O(N²)** per step — suitable for modest population sizes (e.g., hundreds), not city-scale N.
- Preset parameters are **illustrative** for coursework exploration, not calibrated to real outbreaks.
- For GIF export, call `Simulation.save_live_animation(...)` from your own script; that path uses Matplotlib’s **Pillow** writer (install `pillow`).

## License / academic use

Course term project; treat licensing as unspecified unless you add a `LICENSE` file.
