from matplotlib.pyplot import figure, show
import numpy as np
from simulation import simulation

if __name__ == '__main__':
    timestep = 1
    endstep = 10000

    s = simulation(n=5, gui = False)
    mean_speeds, mean_times = s.start_sim(tl_time=4,timestep = timestep,endstep =2000,strat = "fcfc")

    fig=figure()
    frame = fig.add_subplot(1,2,1)
    frame.plot(np.arange(1,len(mean_speeds)*timestep+1,timestep),mean_speeds)

    frame = fig.add_subplot(1,2,2)
    frame.plot(np.arange(1,len(mean_times)*timestep+1,timestep),mean_times)
    show()
