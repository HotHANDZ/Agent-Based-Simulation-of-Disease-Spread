"""
Entry point: tweak scenario parameters here, then run.

Flow: DiseaseModel (global tp / recovery / vaccine efficacy) → Simulation (agents, movement, SIR dynamics)
→ outputs/ CSV+JSON from run(), chart from plot().
"""
from disease import DiseaseModel
from simulation import Simulation

# Scenario knobs (saved file must be saved before `python main.py` picks up changes).
num_agents = 500

# Fraction of agents that start vaccinated (deterministic assignment inside Simulation)
vaccination_fraction = 1

# When True, infected agents go home and stay there until they recover.
bedridden = True

#Use a significantly larger simulation area so that movement
#from the border to the center and back is more visible.
width = 500
height = 500
transmission_prob = .7
recovery_time = 4000
timesteps = 10000

#Initialize disease and simulation
disease = DiseaseModel(transmission_prob, recovery_time)
# Pass vaccination and bedridden settings from main into the simulation
sim = Simulation(num_agents, width, height, disease, vaccination_fraction=vaccination_fraction, bedridden=bedridden)

#Run the simulation
sim.run(timesteps)

#Plot results on 2D graph
sim.plot()