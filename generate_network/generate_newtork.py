import os, sys
import traci
import xml.etree.ElementTree as ET

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

if __name__ == '__main__':
    # creating a grid
    os.system("netgenerate -g --grid.number=5 --grid.length=200 --output-file=grid.net.xml")
    os.system("python \"" + tools + "\\randomTrips.py\" -n grid.net.xml -o flows.xml --end 1 --period 1 --flows 200")
    os.system("jtrrouter --route-files=flows.xml --net-file=grid.net.xml --output-file=grid.rou.xml --begin 0 --end 10000 --accept-all-destinations")
    os.system("python \"" + tools + "\\generateContinuousRerouters.py\" -n grid.net.xml --end 10000 -o rerouter.add.xml")

    # Putting the data of the grid into a sumocfg file
    root = ET.Element("configuration")

    input = ET.SubElement(root, "input")
    ET.SubElement(input, "net-file", value="grid.net.xml")
    ET.SubElement(input, "route-files", value="grid.rou.xml")
    ET.SubElement(input, "additional-files", value="rerouter.add.xml")


    time = ET.SubElement(root, "time")
    ET.SubElement(time, "begin", value="0")
    ET.SubElement(time, "end", value="10000")

    output = ET.SubElement(root, "output")
    ET.SubElement(output, "fcd-output", value="grid.output.xml")

    tree = ET.ElementTree(root)
    tree.write("grid.sumocfg")
