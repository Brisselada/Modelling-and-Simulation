# Modelling-and-Simulation

## Requirements

To run this project, the following Python packages are required:

- numpy
- traci
- matplotlib
- string
- multiprocessing

The project should be run on at least Python 3.8. 
Furthermore, a recent version of SUMO is required, which can be downloaded from https://www.eclipse.org/sumo/.

## Running the code

This project contains various Python files which can be run: 

- generate_network.py is used to create grids with the given size and traffic congestion level.
- start.py can be used for quickly running a single simulation, assuming a grid has already been generated. Outputs plots for the mean speed and mean cumulative delay.
- final.py runs simulations for all strategies, for various grid sizes and traffic congestion levels. The latter values can easily be changed in the file itself.

Two files which contain auxiliary classes and functions: 

- simulation.py contains the simulation class, with the required methods to set it up. It also contains the Junction, Combination and Lane objects which define the grid and its connections. 
- strategy.py contains the implementations of the traffic light strategies. 
