import os, sys
import traci
import xml.etree.ElementTree as ET
import string



def makegrid(number: int = 3, length: int = 200, traffic_light: bool = True, flows: int = 50,
             total_cycle_time: int = 90, custom_tl: bool = True):
    """
    Function to make the .sumocfg for a grid_path

    :param additional:
    :param total_cycle_time:
    :param custom_tl: Whether the default tl should be overwritten with a format that doesn't make cars cross
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
        os.system(f"netgenerate -g --grid.number={number} --grid.length={length} --default-junction-type "
                  f"traffic_light --tls.cycle.time {total_cycle_time} -L 1 --no-turnarounds true --turn-lanes 2 "
                  f"--no-internal-links --turn-lanes.length 99 --output-file=grid.net.xml")
        if custom_tl:
            make_custom_tl(number)
    else:
        os.system(f"netgenerate -g --grid.number={number} --grid.length={length} --output-file=grid.net.xml")
    os.system(
        "python \"" + tools + f"\\randomTrips.py\" -n grid.net.xml -o flows.xml --end 1 --period 1 --flows {flows}")
    os.system(
        "jtrrouter --route-files=flows.xml --net-file=grid.net.xml --output-file=grid.rou.xml --begin 0 --end 10000 "
        "--accept-all-destinations")
    os.system(
        "python \"" + tools + "\\generateContinuousRerouters.py\" -n grid.net.xml --end 10000 -o rerouter.add.xml")
    # Putting the data of the grid into a sumocfg file
    root = ET.Element("configuration")

    input = ET.SubElement(root, "input")
    ET.SubElement(input, "net-file", value="grid.net.xml")
    ET.SubElement(input, "route-files", value="grid.rou.xml")
    if custom_tl:
        ET.SubElement(input, "additional-files", value=f"rerouter.add.xml, default_tl.xml")
    else:
        ET.SubElement(input, "additional-files", value="rerouter.add.xml")

    time = ET.SubElement(root, "time")
    ET.SubElement(time, "begin", value="0")
    ET.SubElement(time, "end", value="10000")

    output = ET.SubElement(root, "output")
    ET.SubElement(output, "fcd-output", value="grid.output.xml")

    tree = ET.ElementTree(root)
    tree.write("grid.sumocfg")


def make_custom_tl(number: int) -> None:
    additional = ET.Element("additional")

    letters = string.ascii_uppercase
    # Middle sides - left and right
    for i in range(1, number-1):
        left = ET.SubElement(additional, "tlLogic", id="A" + str(i), type="static", programID="1", offset="0")
        ET.SubElement(left, "phase", duration="20", state="GrrrGG")
        ET.SubElement(left, "phase", duration="3", state="yrrryy")
        ET.SubElement(left, "phase", duration="20", state="GGGrrr")
        ET.SubElement(left, "phase", duration="3", state="yyyrrr")
        ET.SubElement(left, "phase", duration="20", state="rrGGGr")
        ET.SubElement(left, "phase", duration="3", state="rryyyr")


        right = ET.SubElement(additional, "tlLogic", id=letters[number-1] + str(i), type="static", programID="1", offset="0")
        ET.SubElement(right, "phase", duration="20", state="GGGrrr")
        ET.SubElement(right, "phase", duration="3", state="yyyrrr")
        ET.SubElement(right, "phase", duration="20", state="rrGGrr")
        ET.SubElement(right, "phase", duration="3", state="rryyrr")
        ET.SubElement(right, "phase", duration="20", state="GrrrGG")
        ET.SubElement(right, "phase", duration="3", state="yrrryy")
    # Middle sides - Top and bottom
    for i in range(1, number-1):
        top = ET.SubElement(additional, "tlLogic", id=letters[i] + str(number-1), type="static", programID="1", offset="0")
        ET.SubElement(top, "phase", duration="20", state="GrrrGG")
        ET.SubElement(top, "phase", duration="3", state="yrrryy")
        ET.SubElement(top, "phase", duration="20", state="GGGrrr")
        ET.SubElement(top, "phase", duration="3", state="yyyrrr")
        ET.SubElement(top, "phase", duration="20", state="rrGGGr")
        ET.SubElement(top, "phase", duration="3", state="rryyyr")

        bottom = ET.SubElement(additional, "tlLogic", id=letters[i] + "0", type="static", programID="1",
                              offset="0")
        ET.SubElement(bottom, "phase", duration="20", state="rrGGGr")
        ET.SubElement(bottom, "phase", duration="3", state="rryyyr")
        ET.SubElement(bottom, "phase", duration="20", state="rrrrGG")
        ET.SubElement(bottom, "phase", duration="3", state="rrrryy")
        ET.SubElement(bottom, "phase", duration="20", state="GGGrrr")
        ET.SubElement(bottom, "phase", duration="3", state="yyyrrr")
    for i in range(1, number-1):
        for k in range(1, number-1):
            middle = ET.SubElement(additional, "tlLogic", id=letters[i] + str(k), type="static", programID="1",
                                offset="0")
            ET.SubElement(middle, "phase", duration="20", state="GrrrrGGrrrrGG")
            ET.SubElement(middle, "phase", duration="3", state="yrrrryyrrrryy")
            ET.SubElement(middle, "phase", duration="20", state="GGrrrrGGrrrrr")
            ET.SubElement(middle, "phase", duration="3", state="yyrrrryyrrrrr")
            ET.SubElement(middle, "phase", duration="20", state="rrGGrrrrGGrrr")
            ET.SubElement(middle, "phase", duration="3", state="rryyrrrryyrrr")
            ET.SubElement(middle, "phase", duration="20", state="rrrGGrrrrGGrr")
            ET.SubElement(middle, "phase", duration="3", state="rrryyrrrryyrr")
    tree = ET.ElementTree(additional)
    tree.write("default_tl.xml")


if __name__ == '__main__':
    makegrid()
