from matplotlib.pyplot import figure, show
import numpy as np
from simulation import simulation

if __name__ == '__main__':
    timestep = 1
<<<<<<< HEAD
    endstep = 5000
=======
    endstep = 10000
>>>>>>> ec68e1f7fc3c0dfbfe745f296ff956a828f933e0

    s = simulation(5)
    mean_speeds, mean_times = s.start_sim(timestep,endstep)

    fig=figure()
    frame = fig.add_subplot(1,2,1)
    frame.plot(np.arange(1,len(mean_speeds)*timestep+1,timestep),mean_speeds)

    frame = fig.add_subplot(1,2,2)
    frame.plot(np.arange(1,len(mean_times)*timestep+1,timestep),mean_times)
    show()
