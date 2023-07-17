.. _3denv-getting-started:

3D Environment (3DEnv)
======================

The 3D environment, found in the ``3denv`` directory, provides a real-time visualization of the simulation.
It can be run as a stand-alone component with keyboard input and without any other simulated vehicles besides the ego vehicle.
Typically, though, the 3D environment will be connected to a physical bicycle using the :ref:`bicycleinterface-getting-started` and to the :ref:`evi-getting-started` to allow for fellow traffic and vehicle-to-anything communication (V2X).

Requirements
------------

The 3D environment is built with the `Godot 3D game engine <https://godotengine.org//>`_. This project **requires the .NET version** of the game engine, which enables C# support. We recommend using the latest stable build of version 3.x of the engine.

For development, Godot can `interface with several IDEs <https://docs.godotengine.org/en/stable/tutorials/editor/external_editor.html>`_ such as JetBrains Rider or Visual Studio Code.

Generating a Street Network from an Existing Scenario
-----------------------------------------------------

Open ``3denv/`` as a project in Godot.
After that you can start the project by clicking the play button in the right corner of the screen or pressing the F5 key.
To generate a street network from an existing scenario, find the button next to the label "Street Network File Location" in the on-screen menu.
A window will pop up where you will be able to select your desired scenario.
Existing scenarios can be found in the ``scenarios/`` folder of the VCE.

.. _fig-open-street-network-generator:
.. figure:: ../img/godot_menu.png

    Godot screenshot: Opening the game menu.

After selecting the scenario file (a SUMO ``.net.xml``), press generate to create the 3D environment. After starting up EVI, you can also press the connect button to activate the connection between Godot and EVI.

Further important configuration items include:

:Ego Vehicle Type:
    The type of vehicle you want to control.
    Use ``Bicycle`` if you want to control a bicycle with keyboard controls through the 3D environment itself.
    Use ``Bicycle_Interface`` if you intend to connect to the 3D environment with an instance of the :ref:`bicycleinterface-getting-started`.
    Use ``Car`` if you wish to control a car with your keyboard.
:Evi IP address:
    Address of the :ref:`evi-getting-started`.
    Make sure to stick to the format ``your-evi-address``.
    This setting can be changed after the street network is generated.
:Evi Port:
    Port number of the Evi connection with default value of 12346.
:Procedural Objects Seed:
    Seed used for the environment generation. Affects the height of the buildings.
:Place Street Lights:
    Toggle whether street lamps should be placed in the environment. Visual effect only.

Command Line Arguments
----------------------

The 3D Environment accepts the following command line arguments:

:``--scenario=<scenario>``: A SUMO .net.xml scneario to load on startup
:``--scenario-seed=<seed>``: An integer seed for the procedural generation of buildings, etc.
:``--vehicle-type=<vtype>``: {"BICYCLE", "BICYCLE_WITH_MINIMAP", "BICYCLE_INTERFACE", "CAR"}
:``--evi-address=<address>``: Address (usually IP) of the Ego Vehicle Interface
:``--evi-port=<port>``: Port of the Ego Vehicle Interface
:``--evi-connect-on-launch=True``: Connect to EVI immediately
:``--skip-menu=True``: Don't show menu on launch

.. warning::

    In this case, it is required to seperate key-value pairs with an equal sign!

    :Correct: ``--scenario=/path/to/scenario.net.xml``
    :Wrong:   ``--scenario /path/to/scenario.net.xml``

    Furthermore, every argument must be a key value pair!

    :Correct: ``--skip-menu=True``
    :Wrong:   ``--skip-menu``


Exporting the 3D Environment
----------------------------

In Godot's menu bar, click "Project", then "Export…", and select an export preset.
An export preset for "Linux/X11" is already included in the VCE repository and should appear as a selectable item.
By default, this will export your project to ``3denv/build/`` and create an executable file ``3denv.x86_64``.

In case you have not yet run one of the ``vce-install`` scripts or if your version of Godot has changed in the meantime, Godot will likely prompt you to download export templates for its respective version.
In this case, simply follow the instructions and repeat.

As an alternative to the graphical user interface of the Godot Editor, you can also use the command line for exporting the 3D Environment:

.. code-block:: bash

    godot --export "Linux/X11" "build/3denv.x86_64" "3denv/project.godot"

Here we assume that "Linux/X11" is a valid preset in ``3denv/export_presets.cfg`` and that the export presets for the respective version of Godot are already installed.
The ``vce-install*`` scripts in the ``scripts/`` directory already take care of this.


