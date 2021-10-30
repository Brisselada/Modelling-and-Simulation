import os, sys
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


class simulation:
    def __init__(self, n: int, grid_path: str = "../generate_network/grid.sumocfg") -> None:
        self.sumoCmd = ["sumo", "-c", grid_path]
        self.gridsize = n



    def prep_data(self) -> None:

        traffic_lights = traci.trafficlight.getIDList()

        # Excluding the corners by manually adding their ID's
        letters = string.ascii_uppercase
        excluded = [letters[0] + "0", letters[0] + str(self.gridsize-1), letters[self.gridsize-1] + "0",
                    letters[self.gridsize-1] + str(self.gridsize-1)]

        self.junctions = []
        for ID in traffic_lights:
            if ID not in excluded:
                # For different types of junctions (middle, left, right, top bottom) there are different combinations possible
                combinations = []
                # Left
                if ID[0] == "A":
                    for rgy, lane_index in zip(["GrrrGG", "GGGrrr", "rrGGGr"],[[0, 4, 5], [0, 1, 2], [2, 3, 4]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = lanes[lane_index]
                        combinations.append(Combination(rgy, lane_combinations))
                # Right
                elif ID[0] == str(letters[self.gridsize-1]):
                    for rgy, lane_index in zip(["GGGrrr", "rrGGGr", "GrrrGG"], [[0, 1, 2], [2, 3, 4], [0, 4, 5]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = lanes[lane_index]
                        combinations.append(Combination(rgy, lane_combinations))
                # Bottom
                elif ID[1] == "0":
                    for rgy, lane_index in zip(["rrGGGr", "GrrrGG", "GGGrrr"], [[2, 3, 4], [0, 4, 5], [0, 1, 2]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = lanes[lane_index]
                        combinations.append(Combination(rgy, lane_combinations))
                # Top
                elif ID[1] == str(self.gridsize-1):
                    for rgy, lane_index in zip(["GrrrGG", "GGGrrr", "rrGGGr"], [[0, 4, 5], [0, 1, 2], [2, 3, 4]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = lanes[lane_index]
                        combinations.append(Combination(rgy, lane_combinations))
                # Middle
                else:
                    for rgy, lane_index in zip(["GrrrrGGrrrrGG", "GGrrrrGGrrrrr", "rrGGrrrrGGrrr","rrrGGrrrrGGrr"], [[0, 5, 6, 11], [0, 1, 6, 7], [2, 3, 8, 9], [3, 4, 9, 10]]):
                        lanes = np.array(traci.trafficlight.getControlledLanes(ID))
                        lane_combinations = lanes[lane_index]
                        combinations.append(Combination(rgy, lane_combinations))

                self.junctions.append(Junction(ID, combinations))

    def start_sim(self,timestep: int = 1,endstep : int = 10000):
        mean_speeds = []
        mean_times = []

        traci.start(self.sumoCmd)
        self.prep_data()


        step = 0
        while step < endstep:
            all_vehicles = traci.vehicle.getIDList()
            speed_step = []
            time_step = []
            for ID in all_vehicles:
                speed_step.append(traci.vehicle.getSpeed(ID))
                time_step.append(traci.vehicle.getAccumulatedWaitingTime(ID))
            if len(speed_step) > 0:
                mean_speeds.append(sum(speed_step)/len(speed_step))
            if len(time_step) > 0:
                mean_times.append(sum(time_step)/len(time_step))
            # self.eval_tls_queuesize()
            # self.eval_tls_global()
            traci.simulationStep()
            step += timestep

        traci.close()

        return mean_speeds,mean_times

    # Evaluates all traffic lights in the system (alleen op 4-way intersections?) and sets the new corresponding state
    # Uses the queue size based strategy
    def eval_tls_queuesize(self):
        for junc in traci.junction.getIDList(): # Alleen de middelste junctions beschouwen?
            # Kan geen duidelijke data structure vinden voor combinations,
            # waarschijnlijk ook custom data structure voor nodig? En moet mogelijk in setup
            # opgebouwd worden?
            for TL_combination in junc.combinations:
                TL_combination.score = 0
                for TL in TL_combination:
                    lane = traci.trafficlight.getControlledLanes(TL)[0] # Each TL should control 1 lane
                    TL_combination.score += self.getNumVehicles(lane)
            newPhase = self.getNewCombination(junc.combinations) # Moet nog combination aan phase koppelen
            # Nog beslissen wat beste manier van phase setten is, enkele manieren beschikbaar
            junc.setPhase(newPhase)

    # Evaluates all traffic lights in the system (alleen op 4-way intersections?) and sets the new corresponding state
    # Uses the smart/global strategy
    # Overwegend hetzelfde als queue size based strategy, maar dan met extra phase en de extra connectedScore
    def eval_tls_global(self):
        # Phase 1: First calculate all connected scores for each TL
        for TL in traci.trafficlight.getIDList(): # Alleen de stoplichten van middelste junctions beschouwen?
            for connectedEdge in TL.connectedEdges: # only 1 in our case, since each lane has a distinct direction
                for CE_TL in connectedEdge.trafficLights: # iterate TL's corresponding to connected edge
                    # Hebben wss aparte data structure nodig om connected scores op te slaan
                    CE_TL.connectedScore += (1 / len(connectedEdge.trafficLights)) # usually 1/3

        # Phase 2: Add connected score and own score, determine new TL combination
        connectedFactor = 0.3 # Nog definen als constant
        for junc in traci.junction.getIDList(): # Alleen de middelste junctions beschouwen?
            # Kan geen duidelijke data structure vinden voor combinations,
            # waarschijnlijk ook custom data structure voor nodig? En moet mogelijk in setup
            # opgebouwd worden?
            for TL_combination in junc.combinations:
                TL_combination.score = 0
                for TL in TL_combination:
                    lane = traci.trafficlight.getControlledLanes(TL)[0] # Each TL should control 1 lane
                    ownScore = self.getNumVehicles(lane)
                    TL_combination.score += ownScore + (TL.ConnectedScore * connectedFactor)
            newPhase = self.getNewCombination(junc.combinations) # Moet nog combination aan phase koppelen
            # Nog beslissen wat beste manier van phase setten is, enkele manieren beschikbaar
            junc.setPhase(newPhase)


    # Returns number of vehicles on the given lane, within X distance of the junction
    def getNumVehicles(self, lane):
        total = 0
        for vehicle in traci.lane.getLastStepVehicleIDs(lane):
            if traci.vehicle.getLanePosition(vehicle) < 90: # Moet wss specifieker
                total += 1
        return total

    # Returns the traffic light combination with the highest score
    def getNewCombination(self, combinations):
        highScore = 0
        newCombination = [] # The new traffic light combination
        for combination in combinations:
            if combination.score > highScore:
                combination.score = highScore
                newCombination = combination
        return newCombination









