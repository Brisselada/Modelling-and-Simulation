from matplotlib.pyplot import figure, show
import numpy as np
import os,sys
from simulation import simulation
sys.path.append("..")
from generate_network.generate_network import makegrid
from multiprocessing import Pool

# Have to use a function object instead of a function because multiprocessing pools don't take lambda functions
class run_simulation(object):
    def __init__(self, simulation, time = 20, timestep = 1, endstep = 5000, gridsize = 5,strategy = "queue_size"):
        self.s = simulation
        self.time = time
        self.timestep = timestep
        self.endstep = endstep
        self.gridsize = gridsize
        self.strategy = strategy
    def __call__(self,i):
        mean_speeds, mean_times = self.s.start_sim(tl_time = self.time, timestep = self.timestep, endstep = self.endstep, strat = self.strategy)
        return mean_speeds, mean_times

if __name__ == '__main__':
    # Doesn't work for less than 3
    for flow in [150,300,450]:
        for i in [3,4,5]:
            # Amount of lanes
            lanes = 48 + 32 * (i - 3) + 16 * (i - 2) * (i - 1)

            # At 60 roads we want 100 flows, so we normalise to 60 roads
            norm = lanes / 304
            flows = int(flow * norm)

            makegrid(number=i, flows=flows)
            print(f"Made grid for size {i}")

            all_mean_speeds = []
            all_mean_times = []
            for strategy,tl_time in zip([None, "fcfs", "queue_size", "global"],[20,20,20,20]):
                timestep = 1
                endstep = 5000

                # Starting the simulation
                s = simulation(n=i, grid_path = "grid.sumocfg")
                mean_speeds_per_step = []
                mean_times_per_step = []

                pool = Pool()  # Create a multiprocessing Pool

                f = run_simulation(simulation = s,time=tl_time, timestep=1, endstep=endstep, gridsize=i, strategy=strategy)

                # To ensure statistical soundness, we run each simulation 8 times
                result = pool.map(f, range(8))
                for k in result:
                    mean_speeds_per_step.append(k[0])
                    mean_times_per_step.append(k[1])
                all_mean_speeds.append(np.mean(mean_speeds_per_step, axis=0))
                all_mean_times.append(np.mean(mean_times_per_step, axis=0))

            # Plotting
            fig = figure(figsize=(8,10))
            fig.suptitle(f"Data for grid size {i} and flows {flow}")
            frame = fig.add_subplot(2, 1, 1)
            frame.boxplot(all_mean_speeds, sym='', labels=["Clock-based", "fcfs", "queue_size", "global"])
            frame.set_xlabel("Simulation step")
            frame.set_ylabel("Mean speed (km/h)")

            frame = fig.add_subplot(2, 1, 2)
            for strategy, time in zip(["Clock-based", "fcfs", "queue_size", "global"],all_mean_times):
                frame.plot(np.arange(1, len(time) * timestep + 1, timestep), time,label=f"{strategy}")
            frame.set_xlabel("Simulation step")
            frame.set_ylabel("Mean cumulative waiting time (s)")
            fig.legend()
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])
            fig.savefig(f"final_grid{i}_flow{flow}.pdf")


        # Cleaning up
        os.remove("flows.xml")
        os.remove("grid.net.xml")
        os.remove("grid.rou.xml")
        os.remove("grid.sumocfg")
        os.remove("rerouter.add.xml")
        os.remove("grid.output.xml")


