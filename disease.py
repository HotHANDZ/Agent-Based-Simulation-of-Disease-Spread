class DiseaseModel:
    """
    Global disease parameters shared by all agents.

    - transmission_probability: per eligible contact per timestep (see Simulation.step).
    - recovery_time: infected timesteps before transition to Recovered.
    - vaccination_efficacy: multiplicative risk reduction for vaccinated susceptibles only.
    - contact_radius: distance threshold (same units as Agent x/y) for a contact attempt each step.
    """
    def __init__(
        self,
        transmission_probability,
        recovery_time,
        vaccination_efficacy=0.5,
        contact_radius=3.0,
    ):
        self.transmission_probability = transmission_probability
        self.recovery_time = recovery_time
        # 0 = no protection, 1 = vaccinated susceptibles cannot be infected (with current formula).
        self.vaccination_efficacy = vaccination_efficacy
        self.contact_radius = float(contact_radius)