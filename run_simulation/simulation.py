import os, sys
import traci
import traci.constants as tc
from collections.abc import Callable
import numpy as np
from dataclasses import dataclass
from typing import Union


class simulation:
    def __init__(self, grid_path: str = "../generate_network/grid.sumocfg") -> None:
        self.sumoCmd = ["sumo", "-c", grid_path]

    def prep_data(self) -> None:
        # Getting all traffic light lane connections
        self.all_tl = traci.trafficlight.getIDList()

        # Final data structures contain lanes reading to tl and from tl
        self.tl_to_lanes = {}
        self.tl_from_lanes = {}

        for ID in self.all_tl:
            self.tl_to_lanes[ID] = []
            self.tl_from_lanes[ID] = []

        # List of all the lanes
        lanes = traci.lane.getIDList()

        for l in lanes:
            # this might be due to a bug in traci, but it it gets all lanes twice, the first time in a weird format
            # starting with ":", so we skip those
            if l[0]==":":
                continue
            lane_from_edge = l[0:2]
            lane_to_edge = l[2:4]

            if lane_from_edge in self.tl_to_lanes:
                self.tl_from_lanes[lane_from_edge].append(l)
            if lane_to_edge in self.tl_to_lanes:
                self.tl_to_lanes[lane_to_edge].append(l)
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









