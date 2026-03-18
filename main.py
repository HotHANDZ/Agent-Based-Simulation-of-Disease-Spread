from disease import DiseaseModel
from simulation import Simulation

#Define parameters for initializing components
num_agents = 1000

# Fraction of agents that start vaccinated (deterministic assignment inside Simulation)
vaccination_fraction = 0.2

# When True, infected agents go home and stay there until they recover.
bedridden = False

#Use a significantly larger simulation area so that movement
#from the border to the center and back is more visible.
width = 1000
height = 1000
transmission_prob = .05
recovery_time = 1600
timesteps = 10000

#Initialize disease and simulation
disease = DiseaseModel(transmission_prob, recovery_time)
# Pass vaccination and bedridden settings from main into the simulation
sim = Simulation(num_agents, width, height, disease, vaccination_fraction=vaccination_fraction, bedridden=bedridden)

#Run the simulation
sim.run(timesteps)

#Plot results on 2D graph
sim.plot()