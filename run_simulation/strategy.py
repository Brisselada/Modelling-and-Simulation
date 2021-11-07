import os, sys
from collections import defaultdict
import traci
import traci.constants as tc
from collections.abc import Callable
import numpy as np
import string


# Evaluates all traffic lights in the system (alleen op 4-way intersections?) and sets the new corresponding state
# Uses the queue size based strategy
def eval_tls_queuesize(self, step: int, check_interval: int):
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
    elif (step - 3) % check_interval == 0:
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
    elif (step - 3) % check_interval == 0:
        for junc in self.junctions:
            if junc.next_state:
                traci.trafficlight.setRedYellowGreenState(junc.ID, junc.next_state)


# Evaluates all traffic lights in the system and sets the new corresponding state
# Uses the first-come-first-serve strategy
def eval_tls_fcfs(self, step: int, check_interval: int):
    # If the step is a multiple of the check interval, do the calculations
    if step % check_interval == 0:
        for junc in self.junctions:
            self.updateFCFS_queue(junc)
            if not junc.FCFS_queue:
                continue
            key = list(junc.FCFS_queue.keys())[0]
            newState = junc.FCFS_queue[key]
            junc.next_state = newState

            # See if vehicle has left yet, if so we can move on to the next value in the queue
            pop = True
            for tl_combination in junc.tl_combinations:
                for lane in tl_combination.corresponding_lanes:
                    for vehicle in traci.lane.getLastStepVehicleIDs(lane.ID):
                        if key == vehicle:
                            pop = False
            if pop:
                junc.FCFS_queue.pop(key)

            # Getting the current state and making all red lights yellow
            current_state = traci.trafficlight.getRedYellowGreenState(junc.ID)
            if junc.next_state:
                if current_state != junc.next_state:
                    traci.trafficlight.setRedYellowGreenState(junc.ID, current_state.replace("G", "y"))
    # If the yellow light has been on for 3 seconds we switch to the new state
    elif (step - 3) % check_interval == 0:
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
    new_ryg_state = None  # The new traffic light combination
    for combination in tl_combinations:
        if combination.score > highScore:
            highScore = combination.score
            new_ryg_state = combination.ryg_state
    return new_ryg_state


# Checks per TL combination whether vehicles are waiting on corresponding lanes
def updateFCFS_queue(self, junc):
    for tl_combination in junc.tl_combinations:
        for lane in tl_combination.corresponding_lanes:
            for vehicle in traci.lane.getLastStepVehicleIDs(lane.ID):
                junc.FCFS_queue[vehicle] = tl_combination.ryg_state
