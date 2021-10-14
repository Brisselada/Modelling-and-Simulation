import os, sys
import traci
import traci.constants as tc
from collections.abc import Callable
import numpy as np

class simulation:
    def __init__(self,grid_path: str ="../generate_network/grid.sumocfg") -> None:
        self.sumoCmd = ["sumo", "-c", grid_path]

    def prep_data(self) -> None:
        # Getting all traffic light lane connections
        self.all_tl = traci.trafficlight.getIDList()

        # Final data sctructures contain lanes reading to tl and from tl
        self.tl_to_lanes = {}
        self.tl_from_lanes = {}

        for ID in self.all_tl:
            # Storing it in a set to make sure we do not have duplicates
            self.tl_to_lanes[ID] = []
            self.tl_from_lanes[ID] = []

        for ID in self.all_tl:
            lanes = traci.trafficlight.getControlledLanes(ID)

            # For some reason getControlledLanes() gets every lane four times, trick below removes copies
            lanes = list(dict.fromkeys(lanes))
            # We want to seperate in lines leaving from the traffic light and arriving at the traffic light
            for lane in lanes:
                # the edges with the lane come and go to
                lane_from_edge = lane[0:2]
                lane_to_edge = lane[2:4]

                # Appending them ot the sets, I know this is very inefficient, since we are essentially doing all lanes multiple times, but the grid is small enough to be lazy
                if ID==lane_from_edge:
                    self.tl_from_lanes[ID].append(lane)
                if ID==lane_to_edge:
                    self.tl_to_lanes[ID].append(lane)
        print(self.tl_to_lanes)
    def start_sim(self,timestep: int = 1,endstep : int = 10000):
        mean_speeds = []
        mean_times = []

        traci.start(self.sumoCmd)
        #self.prep_data()

        step = 0
        while step < endstep:
            all_vehicles = traci.vehicle.getIDList()
            speed_step = []
            time_step = []
            for ID in all_vehicles:
                speed_step.append(traci.vehicle.getSpeed(ID))
                time_step.append(traci.vehicle.getAccumulatedWaitingTime(ID))
            if len(speed_step)>0:
                mean_speeds.append(sum(speed_step)/len(speed_step))
            if len(time_step)>0:
                mean_times.append(sum(time_step)/len(time_step))

            # Go over all traffic lights
            #for ID in self.all_tl:
            #    for lane in self.tl_to_lanes[ID]:
            #        pass
            traci.simulationStep()
            step += timestep

        traci.close()

        return mean_speeds,mean_times
