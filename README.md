# Pump_Visualization
This dashabord is used to assess pump performance by plotting pump curves versus system curves. The System Curve and Pump Curve excel files can be used to test the app. The app can be built using the following docker commands and run locally. Furthermore the video in the Pump_Viz_tool.mp4 provides a demonstration of how to operate the tool.


# Docker
## Build:
docker build -f DockerfileBase -t pump_visualization .

## Run:
docker run -it --rm -p 8050:8050 pump_visualization
