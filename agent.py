import random
import math

# SINGLE PERSON: POSITION, HOME ON BORDER, SIR STATE, COMMUTE OR QUARANTINE MOVE RULES.
class Agent:
    """COMMUTE HOME<->INTERIOR OR STAY-HOME-WHEN-SICK IF INFECTED AND BEDRIDDEN FLAG."""

    def __init__(self, x, y, state="Susceptible", vaccinated=False, home_x=None, home_y=None):

        # CURRENT POSITION (MAY START ANYWHERE INSIDE THE RECTANGLE).
        self.x = x
        self.y = y

        # BORDER HOME USED FOR RETURN TRIPS AND QUARANTINE TARGET.
        self.home_x = x if home_x is None else home_x
        self.home_y = y if home_y is None else home_y

        # SIR STATE; time_infected TICKS UP EACH STEP WHILE INFECTED.
        self.state = state
        self.time_infected = 0

        # STATIC TRAIT; Simulation SCALES INFECTION RISK WHEN SUSCEPTIBLE.
        self.vaccinated = vaccinated

        # COMMUTE STATE MACHINE: at_home -> to_target -> to_home -> at_home.
        self.phase = "at_home"

        # INTERIOR DESTINATION FOR CURRENT TRIP.
        self.target_x = None
        self.target_y = None

        # SET BY infect(bedridden=True); CLEARS ON recover().
        self._stay_home_until_recovered = False

    def choose_new_target(self, width, height, border_margin=1.0):
        # RANDOM INTERIOR POINT; border_margin AVOIDS EXACTLY SITTING ON THE EDGE.
        self.target_x = random.uniform(border_margin, max(border_margin, width - border_margin))
        self.target_y = random.uniform(border_margin, max(border_margin, height - border_margin))

    def move(self, width, height, step_size=5):
        # BEDRIDDEN / QUARANTINE: INFECTED AGENTS STEER TO HOME AND SKIP NORMAL COMMUTE UNTIL RECOVER().
        if self.state == "Infected" and getattr(self, "_stay_home_until_recovered", False):
            target_x, target_y = self.home_x, self.home_y
            vx = target_x - self.x
            vy = target_y - self.y
            distance_to_target = math.hypot(vx, vy)
            if distance_to_target > 0:
                scale = min(step_size, distance_to_target) / distance_to_target
                dx, dy = vx * scale, vy * scale
            else:
                dx, dy = 0, 0
            self.x = max(0, min(width, self.x + dx))
            self.y = max(0, min(height, self.y + dy))
            return

        # LEAVE HOME: PICK NEW RANDOM TARGET AND SWITCH PHASE.
        if self.phase == "at_home":
            self.choose_new_target(width, height)
            self.phase = "to_target"

        # AIM AT INTERIOR TARGET OR HOME DEPENDING ON PHASE.
        if self.phase == "to_target":
            target_x, target_y = self.target_x, self.target_y
        elif self.phase == "to_home":
            target_x, target_y = self.home_x, self.home_y
        else:
            target_x, target_y = self.x, self.y

        vx = target_x - self.x
        vy = target_y - self.y

        distance_to_target = math.hypot(vx, vy)

        # MOVE AT MOST step_size TOWARD TARGET ALONG UNIT VECTOR.
        if distance_to_target > 0:
            scale = min(step_size, distance_to_target) / distance_to_target
            dx = vx * scale
            dy = vy * scale
        else:
            dx = 0
            dy = 0

        self.x = max(0, min(width, self.x + dx))
        self.y = max(0, min(height, self.y + dy))

        # ARRIVAL USES step_size AS PROXIMITY THRESHOLD (GRID UNITS).
        target_threshold = step_size
        home_threshold = step_size

        if self.phase == "to_target":
            if math.hypot(self.x - self.target_x, self.y - self.target_y) <= target_threshold:
                self.phase = "to_home"

        if self.phase == "to_home":
            if math.hypot(self.x - self.home_x, self.y - self.home_y) <= home_threshold:
                self.phase = "at_home"

    def distance(self, other_agent):
        # EUCLIDEAN DISTANCE FOR CONTACT CHECKS IN Simulation.step.
        return math.sqrt((self.x - other_agent.x) ** 2 + (self.y - other_agent.y) ** 2)

    def infect(self, bedridden=False):
        # ONLY SUSCEPTIBLE -> INFECTED; RESET TIMER; OPTIONAL STAY-HOME BEHAVIOR.
        if self.state == "Susceptible":
            self.state = "Infected"
            self.time_infected = 0
            self._stay_home_until_recovered = bedridden

    def recover(self):
        # CLEARS QUARANTINE FLAG SO NORMAL MOVEMENT RESUMES NEXT STEP.
        self.state = "Recovered"
        self._stay_home_until_recovered = False
