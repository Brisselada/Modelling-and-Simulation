from matplotlib.pyplot import figure, show
import numpy as np
import os,sys
from simulation import simulation
sys.path.append("..")
from generate_network.generate_network import makegrid

if __name__ == '__main__':
    all_mean_speeds = []
    all_mean_times = []
    # Doesn't work for less than 3
    for i in [3,4,5,6,7,8,9,10]:
        # Amount of lanes is 2*(i*(i+1))
        lanes =2*i*(i+1)

        # At 60 roads we want 100 flows, so we normalise to 60 roads
        norm = lanes/60
        flows = int(100*norm)

        makegrid(number = i,length = 200 , traffic_light = True, flows = flows)
        print(f"Made grid for size {i}")

        timestep = 1
        endstep = 10000

        # Starting the simulation
        s = simulation(n=i, grid_path = "grid.sumocfg")
        mean_speeds, mean_times = s.start_sim(timestep,endstep)

        all_mean_speeds.append(mean_speeds)
        all_mean_times.append(mean_times)
        print(f"Finished simulation for grid size {i}")
    # Cleaning up
    os.remove("flows.xml")
    os.remove("grid.net.xml")
    os.remove("grid.rou.xml")
    os.remove("grid.sumocfg")
    os.remove("rerouter.add.xml")
    os.remove("grid.output.xml")



    # Plotting
    fig=figure()
    fig.suptitle("Mean speeds for different grid sizes, flow = 250")
    frame = fig.add_subplot(1,1,1)
    for i,speed in enumerate(all_mean_speeds):
        frame.plot(np.arange(1,len(speed)*timestep+1,timestep),speed,label=f"Grid size {i+3}")
    frame.set_xlabel("Simulation step")
    frame.set_ylabel("Mean speed (km/h)")
    frame.legend()
    fig.savefig("mean_speads.pdf")
    show()

    fig=figure()
    fig.suptitle("Mean cumulative waiting time for different grid sizes, flow = 250")
    frame = fig.add_subplot(1,1,1)
    for i,time in enumerate(all_mean_times):
        frame.plot(np.arange(1,len(time)*timestep+1,timestep),time,label=f"Grid size {i+3}")
    frame.set_xlabel("Simulation step")
    frame.set_ylabel("Mean cumulative waiting time (s)")
    frame.legend()
    fig.savefig("mean_times.pdf")
    show()
