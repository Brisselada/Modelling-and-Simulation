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
    for i in range(5,61,5):
        makegrid(number = 4,length = 200 , traffic_light = True, flows = 200,total_cycle_time=i*2+6)

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
    fig.suptitle("Mean speeds for different grid sizes, flow = 250")
    frame = fig.add_subplot(1,1,1)
    for i,speed in enumerate(all_mean_speeds):
        frame.plot(np.arange(1,len(speed)*timestep,timestep),speed,label=f"Green light for {i} s")
    frame.set_xlabel("Simulation step")
    frame.set_ylabel("Mean speed (km/h)")
    frame.legend()
    fig.savefig("green_times_speeds.pdf")
    show()

    fig=figure()
    fig.suptitle("Mean cumulative waiting time for different grid sizes, flow = 250")
    frame = fig.add_subplot(1,1,1)
    for i,time in enumerate(all_mean_times):
        frame.plot(np.arange(1,len(time)*timestep,timestep),time,label=f"Green light for {i} s")
    frame.set_xlabel("Simulation step")
    frame.set_ylabel("Mean cumulative waiting time (s)")
    frame.legend()
    fig.savefig("green_times_times.pdf")
    show()
