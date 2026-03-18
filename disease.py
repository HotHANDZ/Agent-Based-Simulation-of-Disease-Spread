class DiseaseModel:
    
    #Constructor with ability to tweak odds of transmitting infection and defining a tiem for infection recovery
    def __init__(self, transmission_probability, recovery_time, vaccination_efficacy=0.5):
        
        self.transmission_probability = transmission_probability #Define the probability of infection
        
        self.recovery_time = recovery_time #Define recovery time

        # How much vaccination reduces infection risk for vaccinated *susceptible* agents.
        # Example: vaccination_efficacy=0.5 means vaccinated agents get infected with
        # (1 - 0.5) = 50% of the usual probability.
        self.vaccination_efficacy = vaccination_efficacy