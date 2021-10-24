import os, sys
import traci
import xml.etree.ElementTree as ET

def makegrid(number: int = 3,length: int = 200 , traffic_light: bool = True, flows: int = 50,additional: str = None,total_cycle_time: int = 90):
    """
    Function to make the .sumocfg for a grid_path

    :param number: the grid will be made according to size numberxnumber
    :param length: The length of the roads in metres
    :param traffic_light: Whether to have traffic lights or not
    :param flows: amount of total cars in the simulation
    """
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")


    if traffic_light:
        os.system(f"netgenerate -g --grid.number={number} --grid.length={length} --default-junction-type traffic_light --tls.cycle.time {total_cycle_time} -L 1 --no-turnarounds true --turn-lanes 2 --no-internal-links --turn-lanes.length 99 --output-file=grid.net.xml")
    else:
        os.system(f"netgenerate -g --grid.number={number} --grid.length={length} --output-file=grid.net.xml")
    os.system("python \"" + tools + f"\\randomTrips.py\" -n grid.net.xml -o flows.xml --end 1 --period 1 --flows {flows}")
    os.system("jtrrouter --route-files=flows.xml --net-file=grid.net.xml --output-file=grid.rou.xml --begin 0 --end 10000 --accept-all-destinations")
    os.system("python \"" + tools + "\\generateContinuousRerouters.py\" -n grid.net.xml --end 10000 -o rerouter.add.xml")
    # Putting the data of the grid into a sumocfg filef
    root = ET.Element("configuration")

    input = ET.SubElement(root, "input")
    ET.SubElement(input, "net-file", value="grid.net.xml")
    ET.SubElement(input, "route-files", value="grid.rou.xml")
    if additional:
        ET.SubElement(input, "additional-files", value=f"rerouter.add.xml,{additional}")
    else:
        ET.SubElement(input, "additional-files", value="rerouter.add.xml")

    time = ET.SubElement(root, "time")
    ET.SubElement(time, "begin", value="0")
    ET.SubElement(time, "end", value="10000")

    output = ET.SubElement(root, "output")
    ET.SubElement(output, "fcd-output", value="grid.output.xml")

    tree = ET.ElementTree(root)
    tree.write("grid.sumocfg")

if __name__ == '__main__':
    # creating a grid
    makegrid()
