#Create venv
c:\Python39\python -m venv C:/Users/jc056455/Documents/DashApps/Pump_Viz/app

#Activate venv (deactivate with "deactivate")
C:/Users/jc056455/Documents/DashApps/Pump_Viz/app/Scripts/activate

#Run 
C:/Users/jm069937/Documents/DashApps/Pump_Viz/app/Pump_Visualization_Dashboard_Working.py

#After installing all packages:
pip freeze > C:/Users/jc056455/Documents/DashApps/Pump_Viz/app/requirements.txt

#Delete anything in the req that references windows

#Build like:
docker build -t pump_visualization .


#
have to run from command line.

#run
// -v is a volume

## note used -- docker run -it --rm -v C:/Users/Public/Documents/ExtendSim10/Extensions/Includes:/app/data -p 8050:8050 replica_includes_map
docker run -it --rm -p 8050:8050 pump_visualization
find . -type f \( -name "*.sh" -o -name "*.png" \)