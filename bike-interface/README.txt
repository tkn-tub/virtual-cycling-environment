The repository contains four components of the bike interface needed for the Virtual Cycling Environment (VCE).

1. bicycle-model:
    This folder contains a simulation which collects all the sensor data and computes a trajectory for the bicycle.
    Go to the directory 'bicycle-model/bikeToEvi'.
    To run the simulation, build a python virtual environment with the help of the requirements.txt file, source the venv and call a makefile target of 'Makefile'.

2. ir-sensor:
    This folder contains software for the ir-sensor mounted at the bicycle and connected to the raspberry pi.
    Run "python3 irsensorapp.py -v --pin 4  <ip-address of the host running the bicycle-model>"

3. vibration-motors:
    This folder contains software which controls the vibration motos.
    If you want to run it the first time, you have to compile the protobuf files first with the following two commands:
    1. "protoc -I=. --python_out=. hapticsignals.proto"
    2. "protoc -I=. --python_out=. asmp.proto"
    To run the script which controls the vibration-motos enter: "python main.py --evi-port 12346 --pi-port 12348"

4. hall-brake-sensor:
    This folder contains software which can read the ADC of an ESP32 and transmit its value using UDP and wifi. Documentation can be found here:
    https://wiki.ccs-labs.org/wiki/software/vce/extending/hall-brake-sensor-microcontroller
