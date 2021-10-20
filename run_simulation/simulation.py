import os, sys
import traci
import traci.constants as tc
from collections.abc import Callable
import numpy as np
from dataclasses import dataclass

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
            self.tl_to_lanes[ID] = []
            self.tl_from_lanes[ID] = []

        # List of all the lanes
        lanes = traci.lane.getIDList()

        for l in lanes:
            # this might be due to a bug in traci, but it it gets all lanes twice, the first time in a weird format starting with ":", so we skip those
            if l[0]==":":
                continue
            print(l)
            lane_from_edge = l[0:2]
            lane_to_edge = l[2:4]

            if lane_from_edge in self.tl_to_lanes:
                self.tl_from_lanes[lane_from_edge].append(l)
            if lane_to_edge in self.tl_to_lanes:
                self.tl_to_lanes[lane_to_edge].append(l)

        print(self.tl_from_lanes)
        print("")
        print(self.tl_to_lanes)
    def start_sim(self,timestep: int = 1,endstep : int = 10000):
        mean_speeds = []
        mean_times = []

        traci.start(self.sumoCmd)
        self.prep_data()

        self.all_tl = traci.trafficlight.getIDList()

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
            traci.simulationStep()
            step += timestep

        traci.close()

        return mean_speeds,mean_times
