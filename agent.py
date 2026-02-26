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



    #Move rules defined for the agent with tweakable stepping size
    def move(self, width, height, step_size=2):
            
            #Set a range that the agent can move between -2 and 2.  Makes for unpredictable movement.  Can be any number between -2 and 2
            dx = random.uniform(-step_size, step_size)
            dy = random.uniform(-step_size, step_size)

            #Add the previously attained value for the random movement of the x and y coordinates and add them to existing x and y coordinate
            self.x = max(0, min(width, self.x + dx))
            self.y = max(0, min(height, self.y + dy))

        
        
        
    #Using the Euclidean Distance Formula to calculate the current distance from current agent to another agent
    def distance(self, other_agent):
        return math.sqrt((self.x - other_agent.x) ** 2 + (self.y - other_agent.y) ** 2)

    
    
    
    #Simple implementation of getting "infected" by checking the current state of the agent and verifying it is "Susceptible" before infecting
    def infect(self):
        
        
        
        #Sets the state to infected if current state is susceptible and sets the time to 0
        if self.state == "Susceptible":
            self.state = "Infected"
            self.time_infected = 0 #Value will increment up as time goes on until specified value for recovery



    #Once the time hits the necessary recovered limit, change the value from "Infected" to "Recovered"
    def recover(self):
        self.state = "Recovered"