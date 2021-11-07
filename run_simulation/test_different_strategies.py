from matplotlib.pyplot import figure, show
import numpy as np
import os,sys
from simulation import simulation
sys.path.append("..")
from generate_network.generate_network import makegrid


if __name__ == '__main__':
    all_mean_speeds = []
    all_mean_times = []

    # Amount of lanes is 2*(size*(size+1))
    size = 5
    lanes = 2 * size * (size + 1)

    # At 60 roads we want 100 flows, so we normalise to 60 roads
    norm = lanes / 60
    flows = int(100 * norm)

    makegrid(number=size, flows=flows)
    print(f"Made grid for size {size}")

    timestep = 1
    endstep = 1000
    record_step = 1 # Step at which the values are recorded
    strategies = [None, "queue_size", "global", "fcfs"]
    for strategy in strategies:

        # Starting the simulation
        s = simulation(n=5, gui=False)
        mean_speeds, mean_times = s.start_sim(timestep=timestep, endstep=endstep, strat=strategy)

        all_mean_speeds.append(mean_speeds)
        all_mean_times.append(mean_times)
        print(f"Finished simulation for strategy {strategy}")
    # Cleaning up
    os.remove("flows.xml")
    os.remove("grid.net.xml")
    os.remove("grid.rou.xml")
    os.remove("grid.sumocfg")
    os.remove("rerouter.add.xml")
    # os.remove("grid.output.xml")

    strategy_names = ["Basic", "Queue-size based", "Global", "FCFS"]

    # Plotting
    fig=figure()
    fig.suptitle(f"Mean speeds for different strategies, flow = {flows}")
    frame = fig.add_subplot(1,1,1)
    for i,speed in enumerate(all_mean_speeds):
        frame.plot(np.arange(1,len(speed)*timestep*record_step+1,timestep*record_step),speed,label=f"{strategy_names[i]} Strategy")
    frame.set_xlabel("Simulation step")
    frame.set_ylabel("Mean speed (km/h)")
    frame.legend()
    fig.savefig("mean_speeds.pdf")
    show()

    fig=figure()
    fig.suptitle(f"Mean cumulative waiting time for different strategies, flow = {flows}")
    frame = fig.add_subplot(1,1,1)
    for i,time in enumerate(all_mean_times):
        frame.plot(np.arange(1,len(time)*timestep*record_step+1,timestep*record_step),time,label=f"{strategy_names[i]} Strategy")
    frame.set_xlabel("Simulation step")
    frame.set_ylabel("Mean cumulative waiting time (s)")
    frame.legend()
    fig.savefig("mean_times.pdf")
    show()
