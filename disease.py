# GLOBAL DISEASE PARAMETERS REFERENCED BY Simulation AND Agent INFECTION LOGIC.
class DiseaseModel:
    """PER-CONTACT TRANSMISSION, RECOVERY LENGTH IN STEPS, VAX EFFICACY, CONTACT RADIUS."""

    def __init__(
        self,
        transmission_probability,
        recovery_time,
        vaccination_efficacy=0.5,
        contact_radius=3.0,
    ):
        self.transmission_probability = transmission_probability
        # INFECTED STEPS BEFORE AUTOMATIC RECOVER().
        self.recovery_time = recovery_time
        # EFFICACY 0..1: VACCINATED SUSCEPTIBLES MULTIPLY TRANSMISSION PROB BY (1 - EFFICACY).
        self.vaccination_efficacy = vaccination_efficacy
        # EUCLIDEAN DISTANCE THRESHOLD FOR A CONTACT ATTEMPT (SAME UNITS AS AGENT X,Y).
        self.contact_radius = float(contact_radius)
