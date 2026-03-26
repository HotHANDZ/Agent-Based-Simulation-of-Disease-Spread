import random
import csv
import os
import json
from datetime import datetime
import time
from agent import Agent

class Simulation:
    
    #Construct the simulation with variable agent amounts, variable width and height of border, and a self value
    def __init__(self, num_agents, width, height, disease, vaccination_fraction=0.2, bedridden=False):
        
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


        #Set a single agent to be infected
        self.agents[0].infect(bedridden=self.bedridden)



        #DEUBG/ INFO GATHERING -------------------------------
        self.susceptible_counts = []
        self.infected_counts = []
        self.recovered_counts = []
        #-----------------------------------------------------



    def step(self):
        # Move agents
        for agent in self.agents:
            agent.move(self.width, self.height)


        #MAIN MODEL FOR SIMULATION
        #Enclosed in the lines is the heart of the SIR model -----------------------------------------------------------

        #Infect an agent logic
        for agent in self.agents:
            
            #Check if the current agent is considered infected
            if agent.state == "Infected":
                
                #Check all other agents for susceptibility
                for other in self.agents:
                    if other.state == "Susceptible":
                        
                        #If the agent is susceptible, verify the distance between the infected and susceptible agent is less than 2
                        if agent.distance(other) < 3:
                            # Vaccinated agents have reduced infection risk.
                            effective_prob = self.disease.transmission_probability
                            if other.vaccinated:
                                efficacy = getattr(self.disease, "vaccination_efficacy", 0.0)
                                risk_multiplier = max(0.0, min(1.0, 1.0 - efficacy))
                                effective_prob = effective_prob * risk_multiplier

                            #Reference the probability of infection against random number rolled.
                            if random.random() < effective_prob:
                                other.infect(bedridden=self.bedridden)


        #Logic for agent recovery
        
        #Check every agent in the agent array
        for agent in self.agents:
            
            #Check if agent is considered infected, and if so, increment agent time by 1
            if agent.state == "Infected":
                agent.time_infected += 1
                
                #If agent time == time necessary for recovery, recover the agent
                if agent.time_infected >= self.disease.recovery_time:
                    agent.recover()


        #----------------------------------------------------------------------------------------------------------------

        #DEBUG / COLLECT STATS
        self.record_data()

        #Increment time by 1
        self.time += 1



    #Define a function for number of agents of each type 
    def record_data(self):
        
        #Get the sum of every agent of type Susceptible, Infected and Recovered
        s = sum(1 for a in self.agents if a.state == "Susceptible")
        i = sum(1 for a in self.agents if a.state == "Infected")
        r = sum(1 for a in self.agents if a.state == "Recovered")

        #Change values depending on current counts
        self.susceptible_counts.append(s)
        self.infected_counts.append(i)
        self.recovered_counts.append(r)
        
    #Itterate through "time" as per the number defined by "time steps" in Main
    def _format_param_for_filename(self, value):
        if isinstance(value, float):
            # Avoid dots in filenames while keeping values readable.
            return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "p")
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _build_default_run_paths(self, steps):
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
        Run the simulation and collect metrics every `log_interval` timesteps.

        By default this writes:
        - a CSV time-series dataset
        - a JSON metadata file
        into a systematically named run folder under `outputs/`.
        """
        run_label, run_dir, default_csv_path, default_metadata_path, real_start = self._build_default_run_paths(steps)
        if output_csv_path is None:
            output_csv_path = default_csv_path
        if output_metadata_path is None:
            output_metadata_path = default_metadata_path

        print(f"[run] num_agents={self.num_agents}, steps={steps}, log_interval={log_interval}")

        # Track total runtime and set real-time start stamp.
        self._run_start_perf_counter = time.perf_counter()
        self.run_started_at = real_start.isoformat(timespec="seconds")

        run_rows = []

        for t in range(steps):
            self.step()

            # Record metrics at every 1000 timesteps (and any other interval requested)
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

    # Plot points on a 2D chart and save into the latest run folder.
    def plot(self):
        import matplotlib.pyplot as plt
        # Diagnostic: confirm the plotted values match the run settings.
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

        # Save into the same run folder by default.
        if hasattr(self, "last_run_log_path") and self.last_run_log_path:
            run_dir = os.path.dirname(os.path.abspath(self.last_run_log_path))
            save_png_path = os.path.join(run_dir, "run_plot.png")
            fig.savefig(save_png_path, dpi=150)

        plt.show()
        return fig