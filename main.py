from disease import DiseaseModel
from simulation import Simulation

#Define parameters for initializing components
num_agents = 50
width = 50
height = 50
transmission_prob = .8
recovery_time = 200
timesteps = 500

#Initialize disease and simulation
disease = DiseaseModel(transmission_prob, recovery_time)
sim = Simulation(num_agents, width, height, disease)

#Run the simulation
sim.run(timesteps)

#Plot results on 2D graph
sim.plot()