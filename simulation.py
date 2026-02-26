import random
from agent import Agent

class Simulation:
    
    #Construct the simulation with variable agent amounts, variable width and height of border, and a self value
    def __init__(self, num_agents, width, height, disease):
        
        #Set the number of agents equal to input value
        self.num_agents = num_agents
        
        #Set the boundary of the simulatio
        self.width = width
        self.height = height
        
        #Create an array for the agents (Will be used to set initial spawnpoints and house the agents)
        self.agents = []
        
        #Use the DiseaseModel class [Inside disease.py] for reference on infection
        self.disease = disease
        
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
                        if agent.distance(other) < 3:
                            
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
        
        #Get the sum of every agent of type Susceptible, Infected and Recovered
        s = sum(1 for a in self.agents if a.state == "Susceptible")
        i = sum(1 for a in self.agents if a.state == "Infected")
        r = sum(1 for a in self.agents if a.state == "Recovered")

        #Change values depending on current counts
        self.susceptible_counts.append(s)
        self.infected_counts.append(i)
        self.recovered_counts.append(r)
        
    #Itterate through "time" as per the number defined by "time steps" in Main
    def run(self, steps):
        for t in range(steps):
            self.step()
            
            
            #DEBUG PRINT
            #print(f"Step {t}: Susceptible={self.susceptible_counts[-1]} Infected={self.infected_counts[-1]} Recovered={self.recovered_counts[-1]}")

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