import random
import math

class Agent:
    
    #Create the agent class with attributes that we can call on later.  We will need a movement system, a system to track the
    #status of current infection state, and a way to check how close to another agent the current agent is for transmission.
    
    
    #Constructor for agent
    def __init__(self, x, y, state="Susceptible"):
        
        #Position tracking on an X Y coordinate
        self.x = x
        self.y = y
        
        #Tracking of current agent state
        self.state = state  # Susceptible, Infected or Recovered
        self.time_infected = 0 # Timeframe used to determine if current agent has had ample time to recover from infection (MAY CHANGE)


    