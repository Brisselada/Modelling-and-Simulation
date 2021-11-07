from matplotlib.pyplot import figure, show
import numpy as np
from simulation import simulation

# Mainly used for quickly running a single simulation
if __name__ == '__main__':
    timestep = 1
    endstep = endstep

    s = simulation(n=5, gui = False)
    mean_speeds, mean_times = s.start_sim(tl_time=4, timestep=timestep, endstep=2000, strat="fcfs")

    # Plot the mean speeds
    fig=figure()
    frame = fig.add_subplot(1,2,1)
    frame.plot(np.arange(1,len(mean_speeds)*timestep+1,timestep),mean_speeds)

    # Plot the mean cumulative waiting times
    frame = fig.add_subplot(1,2,2)
    frame.plot(np.arange(1,len(mean_times)*timestep+1,timestep),mean_times)
    show()
