"""
Run the simulation: live 2D agent view, then SIR line chart.

Configure everything in scenario.py, then: python main.py
"""
from simulation import Simulation
import scenario

disease = scenario.make_disease()
sim = Simulation(
    scenario.num_agents,
    scenario.width,
    scenario.height,
    disease,
    vaccination_fraction=scenario.vaccination_fraction,
    bedridden=scenario.bedridden,
    movement_step_size=scenario.movement_step_size(),
    initial_infected_count=scenario.initial_infected_count,
)

sim.run_live(
    scenario.timesteps,
    interval_ms=scenario.live_interval_ms,
    steps_per_frame=scenario.live_steps_per_frame,
)
sim.plot()
