# Car Interface for the Unity 3D

This is a matlab simulation that calculates a trajectory of a car
based on the inputs of a steering wheel.

It is tested with matlab version R2018a.

The version in the master branch uses a proprietary windows
driver to access the steering wheel. Therefore, you have to run the
matlab simulation on a windows machine.

In the branch no-proprietary-driver, there is a version which does
not use the proprietary driver. In this version matlab simulation
gets all values it needs via udp. The inputs of the steering wheel
are read with the help of a python script which sends all inputs to
the matlab simulation. Since it does not use the proprietary driver,
the matlab simulation can be run on a linux machine. But it is
"work in progress".

How to run the simulation which is in the master branch:

What you need:
 - a windows machine
 - matlab R2018a
 - a steering wheel (only tested with Logitech Driving Force GT)

How to start:
 1. Plug in the pedals into the steering wheel.
 2. Connect the steering wheel to power.
 3. Plug in the USB plug of the steering wheel into the PC.
 4. Wait for the steering wheel finishing its calibration.
 5. Start matlab.
 6. Select the folder 'matlab_car_model' using the folder icon with a
    green arrow pointing downwards in the top left corner.
 7. Add the folders 'Common_Files' and 'Normal_Mode' to path by right-
    clicking on the folder -> Add to Path -> Selected Folders
 8. Click on 'Common_Files/Start.m' and press 'F9' to run it.
 9. Click on 'Normal_Mode/Start_normal_mode_Simulator.m' and press 'F9'
    to run it.
10. Double-Click on Model_Platform.slx
11. Verify that the right ip adress is set in 'Model_Platform > Vehicle
    model > Communication_with_visualisation_normal_mode1 > Subsystem2

    Double-Click on 'UDP Send'

    Set the right ip address

    Click on Apply and then on OK
12. Run the simulation by clicking on the green play button
13. Be sure to engage the front gear by pulling the gear stick
14. The vehicle should now move forward


Problems that might occur:

If the file 'sfun_rttime.mex64' is missing, generate it with
'mex -O sfun_rttime.c' in the matlab Command Window on a windows machine.
For a linux machine type in 'mex -O sfun_rttime.c -lrt'.

If the following error occurs:

Error reported by S-function 'joyinput' in 'Model_Platform/Vehicle model/HMI Realtime normal mode/HMI Logitech1/Joystick_Input1':
This block cannot be used with the demonstration version of Simulink 3D Animation.

Thats because the simulation uses a block from the Simulink Virtual_Reality_Toolbox.
The Paderborn University only owns a single license for this toolbox and the error message
occurs when the license is already in use.

The following website shows who is currently using the license:
http://licenses.uni-paderborn.de/cgi-bin/lmstat.pl?server=27000@license1.uni-paderborn.de&feature=Virtual_Reality_Toolbox
