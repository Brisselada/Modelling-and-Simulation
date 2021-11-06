import os, sys
from collections import defaultdict
import traci
import traci.constants as tc
from collections.abc import Callable
import numpy as np
import string


class Junction:
    def __init__(self, ID: str, tl_combinations) -> None:
        self.ID = ID
        self.connected_lanes = []
        self.tl_combinations = tl_combinations
        self.recently_change = False
        self.countdown_next_change = 0
        self.next_state = None
        self.FCFS_queue = []
        lanes = traci.trafficlight.getControlledLanes(ID)
        for l in lanes:
            self.connected_lanes.append(Lane(l))


class Lane:
    def __init__(self, ID: str) -> None:
        self.previous_junction = ID[2:4]
        self.previous_lane = ID[0:4] + "_0"
        self.previous_tl_connected_lanes = []
        self.ID = ID
        for link in traci.lane.getLinks(self.previous_lane):
            link_ID = link[0]
            self.previous_tl_connected_lanes.append(link_ID)


class Combination:
    def __init__(self, ryg_state: str,corresponding_lanes: list) -> None:
        self.ryg_state = ryg_state
        self.corresponding_lanes = corresponding_lanes
        self.score = 0


class simulation:
    def __init__(self, n: int, grid_path: str = "../generate_network/grid.sumocfg", gui = False) -> None:
        if gui:
            self.sumoCmd = ["sumo-gui", "-c", grid_path]
        else:
            self.sumoCmd = ["sumo", "-c", grid_path]
        self.gridsize = n


    def prep_data(self) -> None:

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

    def start_sim(self,tl_time: int = 10, timestep: int = 1,endstep : int = 10000, strategy: str = None):
        mean_speeds = []
        mean_times = []

        traci.start(self.sumoCmd)
        self.prep_data()


        step = 0
        record_step = 5
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
            if strategy == "queue_size":
                self.eval_tls_queuesize(step,check_interval=tl_time)
            elif strategy == "global":
                self.eval_tls_global(step, check_interval=tl_time)
            elif strategy == "fcfs":
                self.eval_tls_fcfs(step, check_interval=4)
            traci.simulationStep()
            step += timestep

        traci.close()

        return mean_speeds,mean_times

    # Evaluates all traffic lights in the system (alleen op 4-way intersections?) and sets the new corresponding state
    # Uses the queue size based strategy
    def eval_tls_queuesize(self,step: int, check_interval: int):
        # If the step is a multiple of the check interval, do the calculations
        if step % check_interval == 0:
            for junc in self.junctions:
                for tl_combination in junc.tl_combinations:
                    tl_combination.score = 0
                    for lane in tl_combination.corresponding_lanes:
                        tl_combination.score += self.getNumVehicles(lane.ID)
                newState = self.getNewRYGState(junc.tl_combinations)
                # Nog beslissen wat beste manier van phase setten is, enkele manieren beschikbaar
                junc.next_state = newState

                # Getting the current state and making all red lights yellow
                current_state = traci.trafficlight.getRedYellowGreenState(junc.ID)
                if newState:
                    if current_state != newState:
                        traci.trafficlight.setRedYellowGreenState(junc.ID, current_state.replace("G", "y"))
        elif (step-3) % check_interval == 0:
            for junc in self.junctions:
                if junc.next_state:
                    traci.trafficlight.setRedYellowGreenState(junc.ID, junc.next_state)



    # Evaluates all traffic lights in the system (alleen op 4-way intersections?) and sets the new corresponding state
    # Uses the smart/global strategy
    # Overwegend hetzelfde als queue size based strategy, maar dan met extra phase en de extra connectedScore
    def eval_tls_global(self, step: int, check_interval: int):
        # # Phase 1: First calculate all connected scores for each TL
        # for TL in traci.trafficlight.getIDList(): # Alleen de stoplichten van middelste junctions beschouwen?
        #     for connectedEdge in TL.connectedEdges: # only 1 in our case, since each lane has a distinct direction
        #         for CE_TL in connectedEdge.trafficLights: # iterate TL's corresponding to connected edge
        #             # Hebben wss aparte data structure nodig om connected scores op te slaan
        #             CE_TL.connectedScore += (1 / len(connectedEdge.trafficLights)) # usually 1/3

        # Phase 1: Calculate own score for each TL
        # If the step is a multiple of the check interval, do the calculations
        if step % check_interval == 0:
            for junc in self.junctions:
                for lane in junc.connected_lanes:  # Each TL should control 1 lane
                    self.lane_scores[lane.ID] = self.getNumVehicles(lane.ID)

            # Phase 2: Add connected score and own score, determine new TL combination
            for junc in self.junctions:
                for tl_combination in junc.tl_combinations:
                    tl_combination.score = 0
                    for lane in tl_combination.corresponding_lanes:
                        connected_score = 0
                        for connected_lane in lane.previous_tl_connected_lanes:
                            connected_score += self.lane_scores[connected_lane]
                        tl_combination.score += self.lane_scores[lane.ID] + (connected_score * self.connectedFactor)
                newState = self.getNewRYGState(junc.tl_combinations)
                junc.next_state = newState

                # Getting the current state and making all red lights yellow
                current_state = traci.trafficlight.getRedYellowGreenState(junc.ID)
                if newState:
                    if current_state != newState:
                        traci.trafficlight.setRedYellowGreenState(junc.ID, current_state.replace("G", "y"))
        # If the yellow light has been on for 3 seconds we switch to the new state
        elif (step-3) % check_interval == 0:
            for junc in self.junctions:
                if junc.next_state:
                    traci.trafficlight.setRedYellowGreenState(junc.ID, junc.next_state)


    # Evaluates all traffic lights in the system and sets the new corresponding state
    # Uses the first-come-first-serve strategy
    def eval_tls_fcfs(self,step: int, check_interval: int):
        # We append to the queue
        for junc in self.junctions:
            self.laneCheckFCFS(junc)


        # If the step is a multiple of the check interval, do the calculations
        if step % check_interval == 0:
            for junc in self.junctions:
                if not junc.FCFS_queue:
                    continue
                newState = junc.FCFS_queue[0]
                junc.next_state = newState[0]

                # Getting the current state and making all red lights yellow
                current_state = traci.trafficlight.getRedYellowGreenState(junc.ID)
                if newState:
                    if current_state != newState:
                        traci.trafficlight.setRedYellowGreenState(junc.ID, current_state.replace("G", "y"))
        # If the yellow light has been on for 3 seconds we switch to the new state
        elif (step-3) % check_interval == 0:
            for junc in self.junctions:
                if junc.next_state:
                    traci.trafficlight.setRedYellowGreenState(junc.ID, junc.next_state)


    # Returns number of vehicles on the given lane, within X distance of the junction
    def getNumVehicles(self, lane: str):
        total = 0
        for vehicle in traci.lane.getLastStepVehicleIDs(lane):
            if traci.vehicle.getLanePosition(vehicle) > (traci.lane.getLength(lane) - 100):
                total += 1
        return total

    # Returns the traffic light combination with the highest score
    def getNewRYGState(self, tl_combinations):
        highScore = 0
        new_ryg_state = None # The new traffic light combination
        for combination in tl_combinations:
            if combination.score > highScore:
                highScore = combination.score
                new_ryg_state = combination.ryg_state
        return new_ryg_state

    # Checks per TL combination whether vehicles are waiting on corresponding lanes
    def laneCheckFCFS(self, junc):
        if len(junc.FCFS_queue)>0:
            for i, FCFS_queue in enumerate(junc.FCFS_queue):
                tl_combination = FCFS_queue[0]
                vehicles = FCFS_queue[1]
                current_vehicles = 0

                # Check if vehicle is still on lane or if it has departed already
                for lane in tl_combination.corresponding_lanes:
                    for vehicle in traci.lane.getLastStepVehicleIDs(lane.ID):
                        if vehicle in vehicles:
                            current_vehicles += 1
                if current_vehicles == 0:
                    junc.FCFS_queue.pop(i)

        for tl_combination in junc.tl_combinations:
            for lane in tl_combination.corresponding_lanes:
                vehicles = []
                for vehicle in traci.lane.getLastStepVehicleIDs(lane.ID):
                    # position = traci.vehicle.getLanePosition(vehicle)
                    # speed = traci.vehicle.getSpeed(vehicle)
                    # if (traci.vehicle.getLanePosition(vehicle) > 0) & (traci.vehicle.getSpeed(vehicle) == 0):
                    vehicles.append(vehicle)
                junc.FCFS_queue.append((tl_combination, vehicles))










