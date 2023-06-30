.. _bicycleinterface-getting-started:

Bicycle Interface
=================

The Bicycle Interface is what allows you to use a real bicycle as an input device for the VCE, as opposed to keyboard controls within the 3D environment for example.
For speed sensing, certain Tacx bike trainers as well as a custom solution using an infrared sensor are supported.
For steering angle sensing, typically an Android app is used.

The Bicycle Model accepts the sensor data from the selected steering and speed sensors and uses them to continuously update the position and orientation of a virtual bicycle in an empty environment.
This position and orientation are then sent to the 3D environment.

.. note::
   If you are using :ref:`the VCE container<apptainer-getting-started>`, you may skip parts of the installation.
   If you are planning to use any of the TacX sensors, you will likely need to run the installation steps for the USB dongle driver on the host system, though.
   Make sure to run the commands for running the bicycle model from within a Poetry Python environment and from inside the container.

To install the Bicycle Model, navigate to the folder ``bike-interface/bicycle-model/bikeToEvi/`` and run the following:

.. code-block:: bash

    poetry install

    # Only required if you're using any Garmin/Tacx sensors,
    # such as might be integrated in a smart training stand:
    # To install the driver for the USB dongle, run the following
    # on the host system (not in a container):
    poetry shell
    > cd dependencies/openant
    > sudo python3 setup.py udev_rules

Then, still from within the ``poetry shell``, go back to ``bike-interface/bicycle-model/bikeToEvi/`` and run ``./main.py -h``.
This should list all available configuration options.
Have a look at the ``Makefile`` for some example configurations.
For example, the following command will start the Bicycle Model with the Android app steering sensor and infrared speed sensor:

.. code-block:: bash

    ./main.py \
        --unity-ip localhost \
        --wheel-diameter 0.7 \
        --num-spokes 18 \
        --steering-sensor android \
        --speed-sensor irspeed_esp32 \
        --initial-orientation 0 \
        --speed-factor 2

Note the setting of the initial orientation.
The bicycle model will override the orientation of the spawn point in the 3D environemnt, so the orientation has to be defined here, for now.
For similar reasons, keep in mind that if you start the Bicycle Model first with a person already on the bicycle, and that person then turns the pedals before the 3D Environment is started, the initial position will be offset from the desired spawning point!

Using the Android App for Steering
----------------------------------

The steering sensor app can be found in `the Google Play Store <https://play.google.com/store/apps/details?id=org.ccs_labs.bicycletelemetry>`_ or in the folder ``bike-android-app/`` in your VCE repository.

Launch the Bicycle Model with the ``--steering-sensor android`` parameter.

Once the app is installed, enter the IP address or URL and port of your instance of the Bicycle Model in the format ``<address>:<port>`` (e.g., ``1.1.1.1:15007``) and tap "Connect".
Keep the handle bar straight and tap "Calibrate Straight" – the reported steering angle should ideally show 0 degrees with no drift.
