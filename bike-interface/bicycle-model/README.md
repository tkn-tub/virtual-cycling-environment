This folder contains my work regarding the bike with the ANT powered speed- and steering angle sensors.

See
https://wiki.ccs-labs.org/wiki/proj/safety4bikes/ant
for further documentation.

# VirtualBox

There are some problems with kernel 4.14 on Manjaro/Archlinux not correctly triggering the openant udev-rule.
A working system is Ubuntu 16.04 (xenial) with kernel 4.4.
There is a Vagrantfile in this folder that can automatically setup such a VM for you.
Install `virtualbox` with the `virtualbox-oracle-extensions` and `vagrant` on your system and from within this folder execute:

    vagrant up

to create and boot the VM. Then use

    vagrant reload

to get the graphical login screen. From there you can use the VMs GUI or alternatively ssh into the VM with

    vagrant ssh

You can access this directory from the VM via `/vagrant` (it's synchronized).
For further info google *vagrant*.

# Installation

With a terminal started in this directory as working directory (or `/vagrant` in the VM)

    virtualenv -p python3 venv  # Setup new python virtualenv
    source venv/bin/activate  # Activate the virtualenv
    cd bikeToEvi
    pip install -r requirements.txt  # Install dependencies

On the lab machines you do not have root rights. Thefore you will likely get an error message stating that you can't install `udev_rules`. Make sure the udev rules, found in `dependencies/openant/resources/ant-usb-sticks.rules` are correctly installed at `/etc/udev/rules.d/ant-usb-sticks.rules` (e.g. ask Florian to do that). On your notebook you can simply install the rules by running the following with working directory `dependencies/openant`:

    sudo ../../../venv/bin/python3 setup.py udev_rules

## OpenAnt Module
The `bikeToEvi/dependencies/openant` folder contains a modified version of https://github.com/Tigge/openant .
The repo including changes can be found at https://github.com/stloewen/openant .

The BikeToEvi project relies on the changes made there (connect to multiple ANT networks; send broadcasts to keep BlackTrack turned on)
The requirements.txt is set to use this local version of openant.
It's also installed in *editable* mode which means changes in the openant folder are immediately visible to all using programs without needing to reinstall openant.

For some reason this sometimes failed and used the pip installable upstream version. If you encounter this ensure you got the right version by running `pip list` in the venv and looking at the "Location" of openant.

# Usage

## Turn on devices
**BlackTrack**: steer full left to turn the device on.  
**Speed- and Cadence Sensor**: Rotate the wheel so a magnet activates the sensor.

## Calibrate angle
The BlackTrack is not a very precise piece of hardware.
BikeToEvi needs calibration data to correctly calculate the steering angle.
To calibrate, turn the BlackTrack on, run

    make calibrate

and follow the instructions.

## Run BikeToEvi
Turn on both devices and run

    make run

# Notes / Troubleshooting on Windows
This folder contains a vagrant file.
With the help of this vagrant file it is possible to start a virtual machine.
This VM runs the python scripts for the bicycle simulator.

But there is an issue running vagrant on windows.
It is not possible to build a python virtual environment.
But in the instructions above, you are asked to build a virtual environment.

## Work around:
Don't build the python virtual machine.
Skip the build python virtual machine part.
Go to bikeToEvi directory and install all package with the following command:

	sudo pip3 install -r requirements.txt
