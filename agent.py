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

        #Remember the agent's "home" location (spawn point on the border)
        self.home_x = x
        self.home_y = y
        
        #Tracking of current agent state
        self.state = state  # Susceptible, Infected or Recovered
        self.time_infected = 0 # Timeframe used to determine if current agent has had ample time to recover from infection (MAY CHANGE)

        #Each agent travels: home -> random destination -> home (repeats)
        #Valid phases: "to_target", "to_home", "at_home"
        self.phase = "at_home"

        #Per-trip random destination (set when leaving home)
        self.target_x = None
        self.target_y = None

    def choose_new_target(self, width, height, border_margin=1.0):
        #Pick a random point inside the simulation area (avoid exact border points)
        self.target_x = random.uniform(border_margin, max(border_margin, width - border_margin))
        self.target_y = random.uniform(border_margin, max(border_margin, height - border_margin))



    #Move rules defined for the agent with tweakable stepping size
    def move(self, width, height, step_size=2):

            #If the agent is at home, start a new trip with a fresh random destination
            if self.phase == "at_home":
                self.choose_new_target(width, height)
                self.phase = "to_target"

            #Determine the current movement target
            if self.phase == "to_target":
                target_x, target_y = self.target_x, self.target_y
            elif self.phase == "to_home":
                target_x, target_y = self.home_x, self.home_y
            else:
                target_x, target_y = self.x, self.y

            #Vector toward the target
            vx = target_x - self.x
            vy = target_y - self.y

            distance_to_target = math.hypot(vx, vy)

            if distance_to_target > 0:
                #Normalize the vector and move up to step_size toward the target
                scale = min(step_size, distance_to_target) / distance_to_target
                dx = vx * scale
                dy = vy * scale
            else:
                dx = 0
                dy = 0

            #Update position, clamped to the simulation bounds
            self.x = max(0, min(width, self.x + dx))
            self.y = max(0, min(height, self.y + dy))

            #Update phase transitions based on proximity to targets
            #Thresholds can be tuned; they are in simulation units
            target_threshold = step_size  # close enough to the destination
            home_threshold = step_size  # close enough to home

            #Check if we have reached the destination and should start going home
            if self.phase == "to_target":
                if math.hypot(self.x - self.target_x, self.y - self.target_y) <= target_threshold:
                    self.phase = "to_home"

            #Check if we have returned home; if so, start a new trip next step
            if self.phase == "to_home":
                if math.hypot(self.x - self.home_x, self.y - self.home_y) <= home_threshold:
                    self.phase = "at_home"

        
        
        
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