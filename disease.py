

class DiseaseModel:
    
    #Constructor with ability to tweak odds of transmitting infection and defining a tiem for infection recovery
    def __init__(self, transmission_probability=0.3, recovery_time=50):
        
        self.transmission_probability = transmission_probability #Define the probability of infection
        
        self.recovery_time = recovery_time #Define recovery time