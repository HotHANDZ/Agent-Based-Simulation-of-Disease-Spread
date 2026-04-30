# GLOBAL DISEASE PARAMETERS REFERENCED BY Simulation AND Agent INFECTION LOGIC.
class DiseaseModel:
    """PER-CONTACT TRANSMISSION, RECOVERY LENGTH IN STEPS, VACCINE RISK REDUCTION FOR VACCINATED SUSCEPTIBLES, CONTACT RADIUS."""

    def __init__(
        self,
        transmission_probability,
        recovery_time,
        vaccine_transmission_risk_reduction_fraction=0.5,
        contact_radius=3.0,
    ):
        # BASE PER-CONTACT INFECTION PROBABILITY FOR A SUSCEPTIBLE (VACCINE SCALES THIS IN Simulation.step).
        self.transmission_probability = transmission_probability
        # INFECTED STEPS BEFORE AUTOMATIC RECOVER().
        self.recovery_time = recovery_time
        # 0..1: FOR A VACCINATED SUSCEPTIBLE, PER-CONTACT P(infection) = BASE × (1 − THIS).
        self.vaccine_transmission_risk_reduction_fraction = vaccine_transmission_risk_reduction_fraction
        # EUCLIDEAN DISTANCE THRESHOLD FOR A CONTACT ATTEMPT (SAME UNITS AS AGENT X,Y).
        self.contact_radius = float(contact_radius)
