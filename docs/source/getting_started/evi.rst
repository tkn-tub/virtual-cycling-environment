.. _evi-getting-started:

Ego Vehicle Interface (EVI)
===========================

The ego vehicle interface (EVI) is responsible for connecting the :ref:`3denv-getting-started` with the traffic simulation in :ref:`sumo-getting-started` and :ref:`veins-getting-started`.
It forwards the movement of the ego vehicle from the :ref:`3denv-getting-started` to :ref:`sumo-getting-started`, allows :ref:`veins-getting-started` to consider all vehicles for the simulation of wireless communication, and transmits all relevant information back to the :ref:`3denv-getting-started`.


Installation
------------

.. note::
   If you are using :ref:`the VCE container<apptainer-getting-started>`, you may skip this step.
   Make sure to run the commands for running a scenario from within a Poetry Python environment and from inside the container.

Make sure that you have the `Protobuf <https://developers.google.com/protocol-buffers>`_ compiler installed.
You can check with ``protoc --version``.

Follow the instructions for your preferred installation method in the EVI Readme file.
The recommended method is to use `Poetry <https://python-poetry.org/>`_.
This will also build and install the ``evi-asm-protocol`` package (from ``../evi-asm-protocol/``) containing the Protobuf definitions used for communication between VCE components.

To check that the installation was successful, run ``scripts/evid.py --help`` from the EVI root directory.


Running a Scenario
------------------

The ``evi/networks`` folder contains a number of example scenarios.
Let's start with ``paderborn-north``.

Paderborn North
^^^^^^^^^^^^^^^

This folder should contain the following files:

:paderborn-north.sumo.cfg:
    The :ref:`sumo-getting-started` configuration.
    In this case, it instructs SUMO to use ``paderborn-north.net.xml`` for the street network, ``ego-vehicle-only.rou.xml`` and ``paderborn-north.rou.xml`` for vehicle and route definitions, and ``paderborn-north.poly.xml`` to draw some 2D buildings if run with ``sumo-gui``.
    The ``time`` parameters will be overridden by EVI, but still must be present.

    You can preview the scenario with ``sumo-gui -c paderborn-north.sumo.cfg``.
:paderborn-north.evi.ini:
    The EVI configuration.
    Any parameter in this configuration file must correspond to one of the parameters listed when you run ``scripts/evid.py`` from the EVI root folder.
    (Please be aware that command line arguments with dashes, e.g., ``--rt-simulator``, must be written with underscores in the ``.evi.ini`` file, i.e., ``rt_simulator``.)

    One parameter you may need to adjust in some of the example scenarios is ``rt_simulator``.
    In the case of ``paderborn-north`` it is correctly set to ``Unity``, but EVI also supports other real-time simulators not directly related to the VCE.

To run the EVI, start ``scripts/evid.py`` with the ``--config-file`` and any additional parameters not yet declared in ``paderborn-north.evi.ini``.
From the ``paderborn-north`` directory:

.. code-block:: bash

    ../../scripts/evid.py --config-file paderborn-north.evi.ini --verbosity WARNING --sumo-binary sumo-gui

The EVI should now be waiting for the :ref:`3denv-getting-started` to connect.

Connecting the 3D Environment to EVI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Refer to the guide on :ref:`3denv-getting-started` for configuring the EVI address in the 3D environment.
Changes in the ``StreetNetwork`` GameObject will override the setting made in the Street Network Generator, and the settings of the main menu will override the ``StreetNetwork`` configuration in turn, if the main menu is used.

