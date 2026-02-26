import random
from agent import Agent
from disease import DiseaseModel



class Simulation:
    
    #Construct the simulation with variable agent amounts, variable width and height of border, and a self value
    def __init__(self, num_agents=100, width=100, height=100):
        
        #Set the boundary of the simulation to 100 x 100
        self.width = width
        self.height = height
        
        #Create an array for the agents (Will be used to set initial spawnpoints and house the agents)
        self.agents = []
        
        #Use the DiseaseModel class [Inside disease.py] for reference on infection
        self.disease = DiseaseModel()
        
        #Set initial time at 0 - used as reference for agents to recover and for data gethering
        self.time = 0


        # Initialize agents spawn points randomly for every agent.  (Itterate N number of times based on agent amount)
        for _ in range(num_agents):
            
            #Set a random value between the border values for x and y
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            
            #Initialize a new agent at specified X and Y value gathered from above
            self.agents.append(Agent(x, y))


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
                        if agent.distance(other) < 2:
                            
                            #Reference the probability of infection against random number rolled.  If the random number is less than the probability, infect the agent
                            if random.random() < self.disease.transmission_probability:
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
        s = sum(1 for a in self.agents if a.state == "Susceptible")
        i = sum(1 for a in self.agents if a.state == "Infected")
        r = sum(1 for a in self.agents if a.state == "Recovered")

        #Change values depending on current counts
        self.susceptible_counts.append(s)
        self.infected_counts.append(i)
        self.recovered_counts.append(r)