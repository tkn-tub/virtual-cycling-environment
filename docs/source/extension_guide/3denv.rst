.. _3denv-extension:

3D Environment
==============

The main entry point of the 3D Environment is the ``VCEInstance`` class in ``3denv/VCEInstance.cs``.
Here, either a default scenario is loaded or a scenario that has been specified via the command line interface.
To read these initial settings, an instance of ``LevelAndConnectionSettings`` (``3denv/UI/LevelAndConnectionSettings.cs``) is first obtained from the scene tree and then queried.
Afterwards, again depending on the settings at launch time, the main menu will be activated and the connection to the Ego Vehicle Interface (EVI) may or may not be established immediately.

Street Network Generation
-------------------------

Scenario generation from SUMO files is managed by the ``NetworkGenerator`` class (``3denv/SumoImporter/NetworkGenerator.cs``) via the ``LoadNetwork`` method.

Based on the selected ``.net.xml`` and ``.poly.xml`` SUMO configuration files, this method uses ``LoadNetFile()`` and ``LoadAndGenerateEnvironment()`` to read the respective XML file and to populate the scene.


Communication with the EVI
--------------------------

The central class for communicating with the EVI is the ``EviConnector``.
These are roughly the steps that happen when a simulation is launched:

:``_Ready()``:
   - A ``ThreadedRequestWorker`` named ``netWorker`` is set up and started for handling the transmission and reception of ZeroMQ messages to and from the EVI.
     This will later be used in the ``_Process()`` method.
   - A new ``VehicleManager`` node is created and added to the scene. The ``VehicleManager`` is responsible for synchronizing the vehicles between the simulation in Godot and SUMO.
   - ``SyncEgoVehicle()`` of the ``VehicleManager`` node is called for the first time.
     Since this is the first time, ``egoVehicleRegistered == false`` and, thus, ``MakeRegisterCommand()`` is called to register the current type and position of the ego vehicle with the EVI.
   - ``vehicleUpdateTimer`` is created, which will be used to only update the ego vehicle in set intervals in ``_Process()``.
:``_Process()``: Called every frame.

   - If ``netWorker`` has received registration commands for new fellow vehicles or unregistration commands for existing vehicles, ``VehicleManager.UpdateFellowVehicles()`` will be called with the corresponding vehicle data.
   - If ``netWorker`` has received updated vehicle states, apply them using ``VehicleManager.UpdateFellowVehicles()`` as well.
   - If ``netWorker`` has no updated vehicle states in this Godot frame. In this case each vehicle will interpolate their next position based on the last desired position received from EVI.
   - Then, any remaining updates that ``netWorker`` has received are handled by type:

      - Trafficlight
      - Visualization (i.e., warning messages from Veins used to spawn indicator arrows in the minimap view)
   - If sufficient time has passed (based on the value of ``vehicleUpdateStep``), transmit the updated ego vehicle position to the EVI with ``VehicleManager.SyncEgoVehicle()``.


Communication with the Bicycle Interface
----------------------------------------

Position and rotation updates from the bicycle interface (i.e., the physical bicycle with steering and speed sensor) are handled by the ``NetworkListener``.

In ``_Ready()``, a thread is started for listening to incoming UDP messages.
This thread runs the ``ReceiveData()`` method.
If a message is received, ``ReceiveData()`` will update member variables of the ``NetworkListener`` to the current position, rotation, and speed of the vehicle.

These values are then applied in every game engine time step in the ``_PhysicsProcess()`` method.
In case of a bicycle ego vehicle, the ``PlayerVehicle`` of the ``VCEInstance`` will be a ``BicycleInterfaceController`` instance, which makes use of the class ``BicycleRig`` for taking care of applying the correct handle bar, wheel, and pedal rotations.
