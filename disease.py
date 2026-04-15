class DiseaseModel:
    """
    Global disease parameters shared by all agents.

    - transmission_probability: per eligible contact per timestep (see Simulation.step).
    - recovery_time: infected timesteps before transition to Recovered.
    - vaccination_efficacy: multiplicative risk reduction for vaccinated susceptibles only.
    """
    def __init__(self, transmission_probability, recovery_time, vaccination_efficacy=0.5):
        self.transmission_probability = transmission_probability
        self.recovery_time = recovery_time
        # 0 = no protection, 1 = vaccinated susceptibles cannot be infected (with current formula).
        self.vaccination_efficacy = vaccination_efficacy