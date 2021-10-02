import os, sys
import traci
import traci.constants as tc
from matplotlib.pyplot import figure, show
import numpy as np

# Settings
timestep = 1

sumoCmd = ["sumo ", "-c", "../generate_network/grid.sumocfg"]

traci.start(sumoCmd)

mean_speeds = []

step = 0
while step < 10000:
    all_vehicles = traci.vehicle.getIDList()
    speed_step = []
    for ID in all_vehicles:
        speed_step.append(traci.vehicle.getSpeed(ID))

    if len(speed_step)>0:
        mean_speeds.append(sum(speed_step)/len(speed_step))
    traci.simulationStep()
    step += timestep

traci.close()



fig=figure()
frame = fig.add_subplot(1,1,1)
frame.scatter(np.arange(1,10000,timestep),mean_speeds)
show()
