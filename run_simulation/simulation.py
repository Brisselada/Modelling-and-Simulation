import os, sys
from collections import defaultdict
import traci
import traci.constants as tc
from collections.abc import Callable
import numpy as np
import string
import strategy


class Junction:
    """"
    Junction class to store all the junctions with their most important data
    """
    def __init__(self, ID: str, tl_combinations) -> None:
        """"
        Constructs the Junction class

        :attribute ID : ID of the junction given by Sumo
        :attribute connected_lanes : All lanes that are arriving at this junctions, contains lane objects
        :attribute tl_combinations : Combination object which describes all the possible traffic light combinations
        :attribute next_state : The next traffic light combination for this junction, used to enable it after a yellow light
        :attribute FCFS_queue: Contains the queue of combination objects for the First Come First Serve (FCFS) method
        """
        self.ID = ID
        self.connected_lanes = []
        self.tl_combinations = tl_combinations
        self.next_state = None
        self.FCFS_queue = {}
        lanes = traci.trafficlight.getControlledLanes(ID)
        for l in lanes:
            self.connected_lanes.append(Lane(l))


class Lane:
    """"
    Lane class to store all the junctions with their most important data
    """
    def __init__(self, ID: str) -> None:
        """"
        Constructs the Lane class

        :attribute previous_junction : The junction ID this lane originated from
        :attribute previous_lane : The lane ID this lane originated from
        :attribute previous_tl_connected_lanes : The lane ID's leading  to the previous_junction mentioned above
        :attribute ID : ID of the lane given by Sumo
        """
        self.previous_junction = ID[2:4]
        self.previous_lane = ID[0:4] + "_0"
        self.previous_tl_connected_lanes = []
        self.ID = ID
        for link in traci.lane.getLinks(self.previous_lane):
            link_ID = link[0]
            self.previous_tl_connected_lanes.append(link_ID)


class Combination:
    """"
    Combination class to store all the traffic light combinations with their most important data
    """
    def __init__(self, ryg_state: str,corresponding_lanes: list) -> None:
        """"
        Constructs the Combination class

        :attribute ryg_state : The Red Yellow Green (RYG) code of the state, used to change a junction's traffic light
        :attribute corresponding_lanes : The lanes to which the traffic lights in this combination belong to
        :attribute score : Score used by queue and global strategy
        """
        self.ryg_state = ryg_state
        self.corresponding_lanes = corresponding_lanes
        self.score = 0


class simulation:
    """"
    Simulation class to store all the info about the simulation and start and run the simulation with a relevant
    strategy
    """
    def __init__(self, n: int, grid_path: str = "../generate_network/grid.sumocfg", gui: bool = False) -> None:
        """"
        Constructs the simulation class

        :attribute n : Grid size in nxn
        :attribute grid_path : Location of the .sumocfg file to run the simulation
        :attribute gui : Bool used to decide whether the gui should be turned on or not
        """
        if gui:
            self.sumoCmd = ["sumo-gui", "-c", grid_path]
        else:
            self.sumoCmd = ["sumo", "-c", grid_path]
        self.gridsize = n


    def prep_data(self) -> None:
        """"
        Function to prepare the simulation. This function constructs all the junction objects and adds relevant lane and
        combination objects to them so that they can be accessed later.
        """

        traffic_lights = traci.trafficlight.getIDList()

        # Excluding the corners by manually adding their ID's
        letters = string.ascii_uppercase
        excluded = [letters[0] + "0", letters[0] + str(self.gridsize-1), letters[self.gridsize-1] + "0",
                    letters[self.gridsize-1] + str(self.gridsize-1)]

        self.lane_scores = defaultdict(int)
        self.connectedFactor = 0.3

        self.junctions = []
        for ID in traffic_lights:
            if ID not in excluded:
                # For different types of junctions (middle, left, right, top bottom) there are different combinations possible
                combinations = []
                # Left
                if ID[0] == "A":
                    for rgy, lane_index in zip(["GrrrGG", "GGGrrr", "rrGGGr"],[[0, 4, 5], [0, 1, 2], [2, 3, 4]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = []
                        for i in lane_index:
                            lane_combinations.append(Lane(lanes[i]))
                        combinations.append(Combination(rgy, lane_combinations))
                # Right
                elif ID[0] == str(letters[self.gridsize-1]):
                    for rgy, lane_index in zip(["GGGrrr", "rrGGGr", "GrrrGG"], [[0, 1, 2], [2, 3, 4], [0, 4, 5]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = []
                        for i in lane_index:
                            lane_combinations.append(Lane(lanes[i]))
                        combinations.append(Combination(rgy, lane_combinations))
                # Bottom
                elif ID[1] == "0":
                    for rgy, lane_index in zip(["rrGGGr", "GrrrGG", "GGGrrr"], [[2, 3, 4], [0, 4, 5], [0, 1, 2]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = []
                        for i in lane_index:
                            lane_combinations.append(Lane(lanes[i]))
                        combinations.append(Combination(rgy, lane_combinations))
                # Top
                elif ID[1] == str(self.gridsize-1):
                    for rgy, lane_index in zip(["GrrrGG", "GGGrrr", "rrGGGr"], [[0, 4, 5], [0, 1, 2], [2, 3, 4]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = []
                        for i in lane_index:
                            lane_combinations.append(Lane(lanes[i]))
                        combinations.append(Combination(rgy, lane_combinations))
                # Middle
                else:
                    for rgy, lane_index in zip(["GrrrrGGrrrrGG", "GGrrrrGGrrrrr", "rrGGrrrrGGrrr","rrrGGrrrrGGrr"], [[0, 5, 6, 11], [0, 1, 6, 7], [2, 3, 8, 9], [3, 4, 9, 10]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = []
                        for i in lane_index:
                            lane_combinations.append(Lane(lanes[i]))
                        combinations.append(Combination(rgy, lane_combinations))

                self.junctions.append(Junction(ID, combinations))

    def start_sim(self,tl_time: int = 10, timestep: int = 1,endstep : int = 10000, strat: str = None):
        """"
        Function to start the simulation.

        ::param tl_time : How long the traffic lights should stay on Green
        ::param timestep : Size of step in which the simulation should run
        ::param endstep : Step number at which the strategy should stop
        ::param strat : Which traffic light Strategy should be used, should be None, queue_size, global or fcfs
        """
        mean_speeds = []
        mean_times = []

        traci.start(self.sumoCmd)
        self.prep_data()


        step = 0
        record_step = 1
        while step < endstep:
            all_vehicles = traci.vehicle.getIDList()
            speed_step = []
            time_step = []
            if step % record_step == 0:
                for ID in all_vehicles:
                    speed_step.append(traci.vehicle.getSpeed(ID))
                    time_step.append(traci.vehicle.getAccumulatedWaitingTime(ID))
                if len(speed_step) > 0:
                    mean_speeds.append(sum(speed_step)/len(speed_step))
                if len(time_step) > 0:
                    mean_times.append(sum(time_step)/len(time_step))
            if strat == "queue_size":
                strategy.eval_tls_queuesize(step,check_interval=tl_time)
            elif strat == "global":
                strategy.eval_tls_global(step, check_interval=tl_time)
            elif strat == "fcfs":
                strategy.eval_tls_fcfs(step, check_interval=tl_time)
            traci.simulationStep()
            step += timestep

        traci.close()

        return mean_speeds,mean_times
