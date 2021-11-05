from matplotlib.pyplot import figure, show
import numpy as np
import os,sys
from simulation import simulation
from multiprocessing import Pool

def run_simulation(time, timestep = 1, endstep = 5000, gridsize = 5,strategy = "queue_size"):
    s = simulation(gridsize)
    mean_speeds, mean_times = s.start_sim(timestep, endstep, strategy, time)
    return mean_speeds, mean_times

if __name__ == '__main__':

    timestep = 1
    endstep = 5000
    gridsize = 5



    all_mean_speeds = []
    all_mean_times = []
    possible_times = [10,11,12,13,14,15,16,17,18,19,20]
    #for i in possible_times:
    #    s = simulation(gridsize)
    #    mean_speeds, mean_times = s.start_sim(timestep, endstep, "queue_size", i)
    #    all_mean_speeds.append(mean_speeds)
    #    all_mean_times.append(mean_times)

    pool = Pool()  # Create a multiprocessing Pool
    result = pool.map(run_simulation, possible_times)

    all_mean_speeds = []
    all_mean_times = []
    for i in result:
        all_mean_speeds.append(i[0])
        all_mean_times.append(i[1])

    fig = figure()
    fig.suptitle("Mean speeds for different green light times")
    frame = fig.add_subplot(1, 1, 1)
    frame.boxplot(all_mean_speeds, sym='', labels=possible_times)
    frame.set_ylabel("Mean speed (km/h)")
    frame.set_xlabel("Green time")
    fig.legend()
    fig.savefig("green_time_queue_speed.pdf")
    show()

    fig = figure()
    frame = fig.add_subplot(1, 1, 1)
    fig.suptitle("Mean cumulative waiting time for different green light times")
    frame.boxplot(all_mean_times, sym='', labels=possible_times)
    frame.set_ylabel("Mean cumulative waiting time (s)")
    frame.set_xlabel("Simulation step")
    fig.legend()
    fig.savefig("green_time_queue_time.pdf")
    show()
