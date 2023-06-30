.. _bicycleinterface-extension:

Bicycle Interface
=================

ESP32
-----

An ESP32 microcontroller board is used to do a combination of the following:

   - Obtaining data from an infrared sensor near the rear wheel spokes to act as a speed sensor
   - (Obtaining data from pressure sensors in the brakes)
   - (Controlling the vibration motors on the handle bars)

The infrared sensor used is a KY-033 "tracking sensor module".
Other infrared sensors should work as long as they don't exhibit too much signal bounce.
For example, the KS0051 produced a handful of superfluous GPIO interrupts for almost every reflective bicycle spoke that cannot be easily filtered out due to the signal bounce interval being larger than the expected interval between bicycle spokes at speeds around 20 km/h.

To build the project in ``bike-interface/esp32/adc2udp`` and to flash it to the ESP32, some build tools are required – mainly ESP-IDF.
The main installation steps are outlined below for ESP-IDF v4.4.2.
For detailed up-to-date instructions, please refer to the `documentation <https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/index.html#installation-step-by-step>`_.

First, clone the ESP-IDF `git repository <https://github.com/espressif/esp-idf>`_:

.. code-block:: bash

   mkdir -p ~/esp
   cd ~/esp
   git clone -b v4.4.2 --recursive https://github.com/espressif/esp-idf.git

Then run the installation script:

.. code-block:: bash

   cd esp-idf/
   ./install.sh esp32
   # If you use the Fish shell, use `./install.fish esp32`.

The following variable needs to be exported before the `export` script can run successfully:

.. code-block:: bash

   # Optionally added to ~/.bashrc:
   export IDF_PATH="$HOME/esp/esp-idf"

   # Or in Fish shell:
   set -Ux IDF_PATH "$HOME/esp/esp-idf"

Before you are able to flash the ESP32, make sure you have the required permissions.

.. code-block:: bash

   # Check which group owns the serial port (typically /dev/ttyUSB0):
   ls -lah /dev/ttyUSB*
   # On Arch-based systems, this will be `uucp`.

   # Add your user to the group:
   sudo usermod -aG uucp $USER

   # Check if any other processes are using /dev/ttyUSB0,
   # otherwise it will be reported as "device or resource busy" in later steps:
   sudo fuser /dev/ttyUSB0
   # If anything is listed, check and close the respective process.


Now, inside the ``bike-interface/esp32/adc2udp`` folder, run the following commands to compile and flash the project to the microcontroller:

.. code-block:: bash

   . $HOME/esp/esp-idf/export.sh
   # Or in Fish shell:
   # . $HOME/esp/esp-idf/export.fish

   # Interactively set configuration options such as the
   # WiFi network or GPIO pins:
   make menuconfig

   # Compile and flash:
   make flash
   # To monitor the output:
   make monitor

   # Alternativaley, run both at the same time:
   make flash monitor

If the ``make monitor`` command only prints random signs, the reason might be the Component config → ESP32-specific → Main XTAL fequency. "Autodetect" should work fine.
