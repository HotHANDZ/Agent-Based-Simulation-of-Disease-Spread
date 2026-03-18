from disease import DiseaseModel
from simulation import Simulation

#Define parameters for initializing components
num_agents = 1000

#Use a significantly larger simulation area so that movement
#from the border to the center and back is more visible.
width = 1000
height = 1000
transmission_prob = .05
recovery_time = 1600
timesteps = 10000

#Initialize disease and simulation
disease = DiseaseModel(transmission_prob, recovery_time)
sim = Simulation(num_agents, width, height, disease)

#Run the simulation
sim.run(timesteps)

#Plot results on 2D graph
sim.plot()