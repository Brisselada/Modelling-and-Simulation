from matplotlib.pyplot import figure, show
import numpy as np
import os,sys
from simulation import simulation
sys.path.append("..")
from generate_network.generate_network import makegrid
import xml.etree.ElementTree as ET


if __name__ == '__main__':
    all_mean_speeds = []
    all_mean_times = []

    timestep = 10
    endstep = 10000
    for i in [4,10,15,20,25,30]:
        makegrid(number = 5,length = 200 , traffic_light = True, flows = 50,total_cycle_time=i*2+6)

        s = simulation(grid_path = "grid.sumocfg")
        mean_speeds, mean_times = s.start_sim(timestep,endstep)

        all_mean_speeds.append(mean_speeds)
        all_mean_times.append(mean_times)

    # Cleanup
    os.remove("flows.xml")
    os.remove("grid.net.xml")
    os.remove("grid.rou.xml")
    os.remove("grid.sumocfg")
    os.remove("rerouter.add.xml")
    os.remove("grid.output.xml")

    fig=figure()
    fig.suptitle(f"Data for different green light times for clock-wise strategy")
    frame = fig.add_subplot(1,2,1)
    frame.boxplot(all_mean_speeds,sym='',labels=[10,20,30,40,50])
    frame.set_ylabel("Mean speed (km/h)")
    frame.set_xlabel("Green light time (s)")
    frame.legend()
    fig.savefig("green_times_speeds.pdf")
    show()

    frame = fig.add_subplot(1,2,2)
    frame.boxplot(all_mean_times,sym='',labels=[10,20,30,40,50])
    frame.set_ylabel("Mean cumulative waiting time (s)")
    frame.set_xlabel("Green light time (s)")
    frame.legend()
    fig.savefig("green_times_times.pdf")
    show()
