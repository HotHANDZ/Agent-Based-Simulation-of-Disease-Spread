"""
Agent-based SIR-style disease simulation on a 2D rectangle.

Significant pieces:
- Agents move; pairwise proximity drives transmission (see Simulation.step).
- Vaccination is a static trait at birth; efficacy scales per-contact infection risk.
- Optional "bedridden" policy sends infected agents home until recovery (Agent.move).
- run() writes CSV + JSON under outputs/ for reproducibility; plot() saves run_plot.png there.
- run_live() opens an animated 2D scatter of agents (S/I/R colors) stepping the model in real time.
"""
import random
import csv
import os
import json
from datetime import datetime
import time
from agent import Agent

class Simulation:
    """
    Holds the world (width x height), all Agent instances, and the DiseaseModel parameters.

    Each timestep: move all agents, apply infection by proximity, advance recovery timers,
    then append S/I/R counts for plotting and logging.
    """
    #Construct the simulation with variable agent amounts, variable width and height of border, and a self value
    def __init__(
        self,
        num_agents,
        width,
        height,
        disease,
        vaccination_fraction=0.2,
        bedridden=False,
        movement_step_size=5.0,
        initial_infected_count=1,
    ):
        
        #Set the number of agents equal to input value
        self.num_agents = num_agents
        
        #Set the boundary of the simulation
        self.width = width
        self.height = height
        
        #Create an array for the agents (Will be used to set initial spawnpoints and house the agents)
        self.agents = []
        
        #Use the DiseaseModel class [Inside disease.py] for reference on infection
        self.disease = disease
        
        # When True, infected agents go home and stay there until they recover.
        self.bedridden = bedridden

        # Grid units moved per epidemiological timestep (see scenario.movement_step_size).
        self.movement_step_size = float(movement_step_size)

        if initial_infected_count < 0:
            raise ValueError("initial_infected_count must be >= 0")
        if initial_infected_count > num_agents:
            raise ValueError(
                f"initial_infected_count ({initial_infected_count}) cannot exceed num_agents ({num_agents})"
            )
        self.initial_infected_count = int(initial_infected_count)
        
        #Set initial time at 0 - used as reference for agents to recover and for data gethering
        self.time = 0
        self.run_started_at = None


        # Initialize agents homes on the border edges.
        # Spawn distribution:
        # - 1/4 on the north edge (y = 0)
        # - 1/4 on the south edge (y = height)
        # - 1/4 on the east edge  (x = width)
        # - 1/4 on the west edge  (x = 0)
        # If num_agents is not divisible by 4, the remainder is distributed in this order:
        # north, south, east, west.
        # Vaccination status is deterministic so you can control it from `main.py`.
        vaccinated_count = int(num_agents * vaccination_fraction)

        base = num_agents // 4
        remainder = num_agents % 4
        edge_counts = [base, base, base, base]  # [north, south, east, west]
        for k in range(remainder):
            edge_counts[k] += 1

        north_count, south_count, east_count, west_count = edge_counts

        # Add agents in the order: north, south, east, west.
        # Use evenly spaced positions along each edge to avoid homes stacking.
        idx = 0

        def add_agent(home_x, home_y):
            nonlocal idx
            vaccinated = idx < vaccinated_count
            # Agents keep a home on the border, but start at random interior positions.
            spawn_x = random.uniform(0, width)
            spawn_y = random.uniform(0, height)
            self.agents.append(Agent(spawn_x, spawn_y, vaccinated=vaccinated, home_x=home_x, home_y=home_y))
            idx += 1

        # north edge: y = 0, x spans the width (excluding corners)
        for i in range(north_count):
            x = ((i + 1) / (north_count + 1)) * width
            add_agent(x, 0)

        # south edge: y = height, x spans the width (excluding corners)
        for i in range(south_count):
            x = ((i + 1) / (south_count + 1)) * width
            add_agent(x, height)

        # east edge: x = width, y spans the height (excluding corners)
        for i in range(east_count):
            y = ((i + 1) / (east_count + 1)) * height
            add_agent(width, y)

        # west edge: x = 0, y spans the height (excluding corners)
        for i in range(west_count):
            y = ((i + 1) / (west_count + 1)) * height
            add_agent(0, y)


        # Initial infections: first ``initial_infected_count`` agents in creation order
        # (north→south→east→west home assignment), same bedridden policy as later infections.
        for i in range(self.initial_infected_count):
            self.agents[i].infect(bedridden=self.bedridden)

        # One list entry per simulated timestep (filled in record_data after each step).
        self.susceptible_counts = []
        self.infected_counts = []
        self.recovered_counts = []

    def step(self):
        # 1) Movement (home ↔ random interior destination, or straight home if bedridden-infected).
        for agent in self.agents:
            agent.move(self.width, self.height, step_size=self.movement_step_size)

        # 2) Transmission: for every infected–susceptible pair within infection_radius,
        # roll once per timestep against (possibly vaccination-adjusted) transmission probability.
        # NOTE: nested loops over all agents → O(N²) per step when many are infected; fine for small N.
        infection_radius = float(getattr(self.disease, "contact_radius", 3.0))

        for agent in self.agents:
            
            #Check if the current agent is considered infected
            if agent.state == "Infected":
                
                #Check all other agents for susceptibility
                for other in self.agents:
                    if other.state == "Susceptible":
                        
                        if agent.distance(other) < infection_radius:
                            # Vaccination: susceptibles who are vaccinated take scaled risk (DiseaseModel.vaccination_efficacy).
                            effective_prob = self.disease.transmission_probability
                            if other.vaccinated:
                                efficacy = getattr(self.disease, "vaccination_efficacy", 0.0)
                                risk_multiplier = max(0.0, min(1.0, 1.0 - efficacy))
                                effective_prob = effective_prob * risk_multiplier

                            #Reference the probability of infection against random number rolled.
                            if random.random() < effective_prob:
                                other.infect(bedridden=self.bedridden)


        # 3) Recovery: infected agents count up timesteps until recovery_time, then become Recovered.
        for agent in self.agents:
            
            #Check if agent is considered infected, and if so, increment agent time by 1
            if agent.state == "Infected":
                agent.time_infected += 1
                
                #If agent time == time necessary for recovery, recover the agent
                if agent.time_infected >= self.disease.recovery_time:
                    agent.recover()


        self.record_data()
        self.time += 1

    def record_data(self):
        
        #Get the sum of every agent of type Susceptible, Infected and Recovered
        s = sum(1 for a in self.agents if a.state == "Susceptible")
        i = sum(1 for a in self.agents if a.state == "Infected")
        r = sum(1 for a in self.agents if a.state == "Recovered")

        #Change values depending on current counts
        self.susceptible_counts.append(s)
        self.infected_counts.append(i)
        self.recovered_counts.append(r)
        
    def _format_param_for_filename(self, value):
        if isinstance(value, float):
            # Avoid dots in filenames while keeping values readable.
            return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "p")
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _build_default_run_paths(self, steps):
        # Human-readable run folder name encodes key parameters (for organization / batch runs).
        real_start = datetime.now()
        run_stamp = real_start.strftime("%Y%m%dT%H%M%S")

        run_label = (
            f"run_{run_stamp}"
            f"_agents-{self.num_agents}"
            f"_size-{self.width}x{self.height}"
            f"_steps-{steps}"
            f"_tp-{self._format_param_for_filename(self.disease.transmission_probability)}"
            f"_rt-{self._format_param_for_filename(self.disease.recovery_time)}"
            f"_vf-{self._format_param_for_filename(sum(1 for a in self.agents if getattr(a, 'vaccinated', False)) / self.num_agents if self.num_agents else 0.0)}"
            f"_bedridden-{self._format_param_for_filename(self.bedridden)}"
        )
        run_dir = os.path.join("outputs", run_label)
        csv_path = os.path.join(run_dir, f"{run_label}_timeseries.csv")
        metadata_json_path = os.path.join(run_dir, f"{run_label}_metadata.json")
        return run_label, run_dir, csv_path, metadata_json_path, real_start

    def _collect_static_run_metadata(self, steps, log_interval, real_start):
        vaccinated = sum(1 for a in self.agents if getattr(a, "vaccinated", False))
        vaccination_fraction = (vaccinated / self.num_agents) if self.num_agents else 0.0
        return {
            "dataset_schema_version": "1.0",
            "run_real_start_time_iso8601": real_start.isoformat(timespec="seconds"),
            "simulation_parameters": {
                "num_agents_count": self.num_agents,
                "space_width_units": self.width,
                "space_height_units": self.height,
                "planned_timesteps_count": steps,
                "log_interval_timesteps": log_interval,
                "bedridden_policy_enabled": self.bedridden,
                "transmission_probability_fraction": self.disease.transmission_probability,
                "recovery_time_timesteps": self.disease.recovery_time,
                "vaccinated_agents_count": vaccinated,
                "vaccinated_fraction": vaccination_fraction,
                "initial_infected_agents_count": self.initial_infected_count,
            },
            "units": {
                "simulation_timestep_step": "step",
                "real_elapsed_seconds_s": "s",
                "susceptible_agents_count": "agents",
                "infected_agents_count": "agents",
                "recovered_agents_count": "agents",
                "vaccinated_agents_count": "agents",
                "transmission_probability_fraction": "fraction",
                "vaccination_efficacy_fraction": "fraction",
                "vaccinated_fraction": "fraction",
                "effective_transmission_probability_fraction": "fraction",
                "transmission_probability_reduction_fraction": "fraction",
                "entity_count_agents": "agents",
                "initial_infected_agents_count": "agents",
            },
        }

    def _collect_run_metrics(self):
        # Counts correspond to the last recorded step (after `step()` runs).
        susceptible = self.susceptible_counts[-1]
        infected = self.infected_counts[-1]
        recovered = self.recovered_counts[-1]
        vaccinated = sum(1 for a in self.agents if getattr(a, "vaccinated", False))

        vaccination_efficacy = getattr(self.disease, "vaccination_efficacy", 0.0)
        vaccinated_fraction = (vaccinated / self.num_agents) if self.num_agents else 0.0

        # Our infection model scales transmission probability by:
        # - 1.0 for unvaccinated susceptibles
        # - (1 - vaccination_efficacy) for vaccinated susceptibles
        # So the expected (weighted) effective transmission probability is:
        #   base * [(1-v) * 1 + v * (1 - e)] = base * (1 - v * e)
        base_transmission_probability = self.disease.transmission_probability
        effective_transmission_probability = base_transmission_probability * (1.0 - vaccinated_fraction * vaccination_efficacy)
        effective_transmission_probability = max(0.0, min(base_transmission_probability, effective_transmission_probability))
        transmission_probability_reduction = base_transmission_probability - effective_transmission_probability

        elapsed_seconds = ""
        runtime_mm_ss = ""
        if hasattr(self, "_run_start_perf_counter"):
            elapsed_seconds_value = max(0.0, time.perf_counter() - self._run_start_perf_counter)
            elapsed_seconds = round(elapsed_seconds_value, 3)
            minutes = int(elapsed_seconds_value // 60)
            seconds = int(elapsed_seconds_value % 60)
            runtime_mm_ss = f"{minutes:02d}:{seconds:02d}"

        return {
            "real_time_iso8601": datetime.now().isoformat(timespec="seconds"),
            "simulation_timestep_step": self.time,
            "susceptible_agents_count": susceptible,
            "infected_agents_count": infected,
            "recovered_agents_count": recovered,
            "vaccinated_agents_count": vaccinated,
            "transmission_probability_fraction": base_transmission_probability,
            "vaccination_efficacy_fraction": vaccination_efficacy,
            "vaccinated_fraction": vaccinated_fraction,
            "effective_transmission_probability_fraction": effective_transmission_probability,
            "transmission_probability_reduction_fraction": transmission_probability_reduction,
            "entity_count_agents": self.num_agents,
            "real_elapsed_seconds_s": elapsed_seconds,
            "runtime_mm_ss": runtime_mm_ss,
        }

    def _write_run_log_csv(self, path, rows):
        fieldnames = [
            "real_time_iso8601",
            "simulation_timestep_step",
            "susceptible_agents_count",
            "infected_agents_count",
            "recovered_agents_count",
            "vaccinated_agents_count",
            "transmission_probability_fraction",
            "vaccination_efficacy_fraction",
            "vaccinated_fraction",
            "effective_transmission_probability_fraction",
            "transmission_probability_reduction_fraction",
            "entity_count_agents",
            "real_elapsed_seconds_s",
            "runtime_mm_ss",
        ]

        # Ensure output directory exists (if user gave a nested path)
        parent = os.path.dirname(os.path.abspath(path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def _write_metadata_json(self, path, metadata):
        parent = os.path.dirname(os.path.abspath(path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def run(self, steps, log_interval=1000, output_csv_path=None, output_metadata_path=None):
        """
        Run for `steps` timesteps.

        S/I/R lists get one sample every step (for plot()). The CSV rows are subsampled:
        only every log_interval-th timestep (plus whatever you configure) via _collect_run_metrics.
        Writes *_timeseries.csv and *_metadata.json under outputs/<run_label>/.
        """
        run_label, run_dir, default_csv_path, default_metadata_path, real_start = self._build_default_run_paths(steps)
        if output_csv_path is None:
            output_csv_path = default_csv_path
        if output_metadata_path is None:
            output_metadata_path = default_metadata_path

        # Console sanity check: confirms Python picked up the same numbers as your saved main.py.
        print(f"[run] num_agents={self.num_agents}, steps={steps}, log_interval={log_interval}")

        # Track total runtime and set real-time start stamp.
        self._run_start_perf_counter = time.perf_counter()
        self.run_started_at = real_start.isoformat(timespec="seconds")

        run_rows = []

        for t in range(steps):
            self.step()

            if log_interval and (self.time % log_interval == 0):
                run_rows.append(self._collect_run_metrics())

        # Write portable run artifacts with documented fields/units.
        self._write_run_log_csv(output_csv_path, run_rows)
        total_elapsed_seconds = max(0.0, time.perf_counter() - self._run_start_perf_counter)
        metadata = self._collect_static_run_metadata(steps, log_interval, real_start)
        metadata.update(
            {
                "run_label": run_label,
                "output_directory": run_dir,
                "output_files": {
                    "timeseries_csv": output_csv_path,
                    "metadata_json": output_metadata_path,
                },
                "run_real_end_time_iso8601": datetime.now().isoformat(timespec="seconds"),
                "run_real_elapsed_seconds_s": round(total_elapsed_seconds, 3),
                "logged_rows_count": len(run_rows),
            }
        )
        self._write_metadata_json(output_metadata_path, metadata)
        self.last_run_log_path = output_csv_path
        self.last_run_metadata_path = output_metadata_path

    def plot(self):
        """SIR line chart; saves run_plot.png next to the last CSV. plt.show() blocks until the window closes."""
        import matplotlib.pyplot as plt
        print(
            f"[plot] num_agents={self.num_agents}, time_points={len(self.susceptible_counts)}"
        )

        vaccinated = sum(1 for a in self.agents if getattr(a, "vaccinated", False))
        vaccinated_fraction = (vaccinated / self.num_agents) if self.num_agents else 0.0

        transmission_probability = self.disease.transmission_probability
        recovery_time = self.disease.recovery_time

        fig, ax = plt.subplots()
        ax.plot(self.susceptible_counts, label="Susceptible")
        ax.plot(self.infected_counts, label="Infected")
        ax.plot(self.recovered_counts, label="Recovered")

        ax.set_xlabel("Time Steps")
        ax.set_ylabel("Number of Agents")
        ax.set_ylim(0, self.num_agents)  # Helps prevent misleading tick labels.
        if self.num_agents:
            ax.set_yticks([0, self.num_agents])

        ax.set_title(
            f"SIR (agents={self.num_agents}, vacc_frac={vaccinated_fraction:.3f}, tp={transmission_probability:.4f}, rt={recovery_time})"
        )
        ax.legend()
        fig.tight_layout()

        if getattr(self, "last_run_log_path", None):
            run_dir = os.path.dirname(os.path.abspath(self.last_run_log_path))
            save_png_path = os.path.join(run_dir, "run_plot.png")
        else:
            fig_dir = os.path.join("outputs", "figures")
            os.makedirs(fig_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            save_png_path = os.path.join(fig_dir, f"sir_plot_{stamp}.png")
        fig.savefig(save_png_path, dpi=150)
        print(f"[plot] saved {save_png_path}")

        plt.show()
        return fig

    def _build_live_funcanimation(self, steps, interval_ms, steps_per_frame, title_prefix):
        """Shared setup for ``run_live`` and ``save_live_animation`` (non-interactive GIF)."""
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation

        if steps <= 0:
            raise ValueError("steps must be positive")
        steps_per_frame = max(1, int(steps_per_frame))

        state_to_color = {
            "Susceptible": "#3366cc",
            "Infected": "#e03333",
            "Recovered": "#2d8f2d",
        }

        def colors_array():
            return np.array([state_to_color.get(a.state, "#888888") for a in self.agents])

        fig, ax = plt.subplots(figsize=(9, 9))
        ax.set_xlim(0, self.width)
        ax.set_ylim(0, self.height)
        ax.set_aspect("equal")
        ax.set_xlabel("x")
        ax.set_ylabel("y")

        xy = np.array([[a.x, a.y] for a in self.agents], dtype=float)
        sc = ax.scatter(
            xy[:, 0],
            xy[:, 1],
            c=colors_array(),
            s=max(6, min(36, 8000 // max(1, self.num_agents))),
            linewidths=0,
            alpha=0.9,
            zorder=5,
        )
        ax.set_title(f"{title_prefix}  step 0/{steps}")

        n_frames = 1 + (steps + steps_per_frame - 1) // steps_per_frame

        def update(frame):
            if frame > 0:
                for _ in range(steps_per_frame):
                    if self.time >= steps:
                        break
                    self.step()
            xy2 = np.array([[a.x, a.y] for a in self.agents], dtype=float)
            sc.set_offsets(xy2)
            sc.set_facecolors(colors_array())
            s = sum(1 for a in self.agents if a.state == "Susceptible")
            i = sum(1 for a in self.agents if a.state == "Infected")
            r = sum(1 for a in self.agents if a.state == "Recovered")
            ax.set_title(f"{title_prefix}  step {self.time}/{steps}  S={s}  I={i}  R={r}")
            return (sc,)

        anim = FuncAnimation(
            fig,
            update,
            frames=n_frames,
            interval=interval_ms,
            blit=False,
            repeat=False,
        )
        return fig, anim

    def run_live(self, steps, interval_ms=50, steps_per_frame=1, title_prefix="Live ABM"):
        """
        Show agents moving on a 2D plot while the simulation runs.

        Each frame advances the model by up to ``steps_per_frame`` calls to ``step()`` (after the
        first frame, which shows the initial state at t=0). Useful for demos and qualitative
        checks that movement and proximity-based spread look reasonable; quantitative validation
        should still use time series, parameter sweeps, and comparisons to data/expectations.

        Requires matplotlib (and numpy, already used for coordinate arrays).

        Parameters
        ----------
        steps : int
            Total number of timesteps to simulate (same meaning as ``run(steps)``).
        interval_ms : int
            Delay between animation frames in milliseconds.
        steps_per_frame : int
            Simulation steps per frame; increase for faster playback when N is large.
        title_prefix : str
            Short label for the window title line.
        """
        import matplotlib.pyplot as plt

        fig, anim = self._build_live_funcanimation(
            steps, interval_ms, steps_per_frame, title_prefix
        )
        fig.tight_layout()
        plt.show()
        return anim

    def save_live_animation(self, path, steps, fps=12, steps_per_frame=4, title_prefix="Live ABM"):
        """
        Write the same 2D agent animation as ``run_live`` to a GIF file (no on-screen window).

        Call this in a fresh process or before any other pyplot use if you require a non-GUI
        backend; this method sets matplotlib to ``Agg`` before importing pyplot.

        Requires Pillow (``pip install pillow``) for the GIF writer.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, anim = self._build_live_funcanimation(
            steps, 1000 // max(1, int(fps)), steps_per_frame, title_prefix
        )
        fig.tight_layout()
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        anim.save(path, writer="pillow", fps=max(1, int(fps)))
        plt.close(fig)
        return path