# Modelling-and-Simulation

## Requirements

For this project the following python packages are required

- Numpy
- traci
- maptlotlib
- string

It should be run on at least python 3.8.

Furthermore a recent version of SUMO is necessary.

## Running the code

This projects contains various python files, the most important one is final.py, which runs all strategies for grid sizes 3,4,5 and flows 150, 300, 450. These numbers can easily be changed in the file itself. Furthermore start.py contains the simulation class with it's required methods to set it up and also the junction, combination and lane objects which define the grid and its connections. The strategies are in strategy.py.
