import random
import csv
import os
from datetime import datetime
import time
from agent import Agent

class Simulation:
    
    #Construct the simulation with variable agent amounts, variable width and height of border, and a self value
    def __init__(self, num_agents, width, height, disease, vaccination_fraction=0.2):
        
        #Set the number of agents equal to input value
        self.num_agents = num_agents
        
        #Set the boundary of the simulation
        self.width = width
        self.height = height
        
        #Create an array for the agents (Will be used to set initial spawnpoints and house the agents)
        self.agents = []
        
        #Use the DiseaseModel class [Inside disease.py] for reference on infection
        self.disease = disease
        
        #Set initial time at 0 - used as reference for agents to recover and for data gethering
        self.time = 0


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

        def add_agent(x, y):
            nonlocal idx
            vaccinated = idx < vaccinated_count
            self.agents.append(Agent(x, y, vaccinated=vaccinated))
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
        self.agents[0].infect()



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
                                other.infect()


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
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "timestep": self.time,
            "susceptible": susceptible,
            "infected": infected,
            "recovered": recovered,
            "vaccinated": vaccinated,
            "transmission_probability": base_transmission_probability,
            "vaccination_efficacy": vaccination_efficacy,
            "vaccinated_fraction": vaccinated_fraction,
            "effective_transmission_probability": effective_transmission_probability,
            "transmission_probability_reduction": transmission_probability_reduction,
            "entity_count": self.num_agents,
            "elapsed_seconds": elapsed_seconds,
            "runtime_mm_ss": runtime_mm_ss,
        }

    def _write_run_log(self, path, rows, delimiter="\t"):
        fieldnames = [
            "timestamp",
            "timestep",
            "susceptible",
            "infected",
            "recovered",
            "vaccinated",
            "transmission_probability",
            "vaccination_efficacy",
            "vaccinated_fraction",
            "effective_transmission_probability",
            "transmission_probability_reduction",
            "entity_count",
            "elapsed_seconds",
            "runtime_mm_ss",
        ]

        # Ensure output directory exists (if user gave a nested path)
        parent = os.path.dirname(os.path.abspath(path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def run(self, steps, log_interval=1000, output_csv_path=None):
        """
        Run the simulation and collect metrics every `log_interval` timesteps.

        Logs are written to a timestamped TSV file (tab-delimited) by default.
        """
        if output_csv_path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_csv_path = f"run_log_{stamp}.tsv"

        # Track total runtime (used for TSV logging)
        self._run_start_perf_counter = time.perf_counter()

        run_rows = []

        for t in range(steps):
            self.step()

            # Record metrics at every 1000 timesteps (and any other interval requested)
            if log_interval and (self.time % log_interval == 0):
                run_rows.append(self._collect_run_metrics())

        # After a successful run, write collected data to disk.
        self._write_run_log(output_csv_path, run_rows, delimiter="\t")
        self.last_run_log_path = output_csv_path

    #Plot points on 2D chart
    def plot(self):
        
        #Used for graphical representation
        import matplotlib.pyplot as plt
        
        #Plot number of each respective type of agent
        plt.plot(self.susceptible_counts, label="Susceptible")
        plt.plot(self.infected_counts, label="Infected")
        plt.plot(self.recovered_counts, label="Recovered")
        
        #Define x axis as time
        plt.xlabel("Time Steps")
        
        #Define y axis as number of agents
        plt.ylabel("Number of Agents")
        
        plt.legend()
        plt.show()