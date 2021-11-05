from matplotlib.pyplot import figure, show
import numpy as np
import os,sys
from simulation import simulation
from multiprocessing import Pool

def run_simulation(time, timestep = 1, endstep = 5000, gridsize = 5,strategy = "queue_size"):
    s = simulation(gridsize)
    mean_speeds, mean_times = s.start_sim(timestep, endstep, strategy, time)
    return mean_speeds, mean_times


# Have to use a function object instead of a function because multiprocessing pools don't take lambda functions
class run_simulation(object):
    def __init__(self, time, timestep = 1, endstep = 5000, gridsize = 5,strategy = "queue_size"):
        self.s = simulation(gridsize)
        self.time = time
        self.timestep = timestep
        self.endstep = endstep
        self.gridsize = gridsize
        self.strategy = strategy
    def __call__(self,i):
        mean_speeds, mean_times = self.s.start_sim(tl_time = self.time, timestep = self.timestep, endstep = self.endstep, strategy = self.strategy)
        return mean_speeds, mean_times


if __name__ == '__main__':


    for strategy in ["queue_size", "global", "fcfs"]:
        # To ensure statistical soundness, we run each simulation 10 times
        all_mean_speeds = []
        all_mean_times = []
        possible_times = np.arange(14, 32, 2)
        # possible_times = [10,20]
        for time in possible_times:
            mean_speeds_per_step = []
            mean_times_per_step = []
            #for i in possible_times:
            #    s = simulation(gridsize)
            #    mean_speeds, mean_times = s.start_sim(timestep, endstep, "queue_size", i)
            #    all_mean_speeds.append(mean_speeds)
            #    all_mean_times.append(mean_times)

            pool = Pool()  # Create a multiprocessing Pool

            result = pool.map(run_simulation(time = time, timestep = 1, endstep = 10000, gridsize = 5, strategy = strategy), range(8))
            for i in result:
                mean_speeds_per_step.append(i[0])
                mean_times_per_step.append(i[1])
            all_mean_speeds.append(np.mean(mean_speeds_per_step,axis=0))
            all_mean_times.append(np.mean(mean_times_per_step,axis=0))

        fig = figure()
        fig.suptitle(f"Data for different green light times for strategy {strategy}")
        frame = fig.add_subplot(1, 2, 1)
        frame.boxplot(all_mean_speeds, sym='', labels=possible_times)
        frame.set_ylabel("Mean speed (km/h)")
        frame.set_xlabel("Green time")
        fig.legend()

        frame = fig.add_subplot(1, 2, 2)
        frame.boxplot(all_mean_times, sym='', labels=possible_times)
        frame.set_ylabel("Mean cumulative waiting time (s)")
        frame.set_xlabel("Simulation step")
        fig.legend()
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(f"green_time_strategy_{strategy}.pdf")
