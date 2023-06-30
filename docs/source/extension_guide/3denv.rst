.. _3denv-extension:

3D Environment
==============

Street Network Generation
-------------------------

The implemenation of the Street Network Generator comprises two main components:
The graphical user interface in ``3denv/3denv/Assets/Editor/StreetnetworkGenerator/Generator3DCourse.cs`` and the actual generation of a new Unity scene in ``3denv/3denv/Assets/Editor/StreetnetworkGenerator/SUMOImporter/ImportAndGenerate.cs``.

The heart of the ``Generator3DCourse`` class is the ``OnGUI()`` method, which populates all relevant configuration variables using the outputs of Editor GUI elements before handing them over to the ``ImportAndGenerate`` class once the Start button is pressed.

The first important call on ``ImportAndGenerate`` is the static method ``ParseXmlFiles()``.
Based on the ``.net.xml`` and ``.poly.xml`` SUMO configuration files selected in the GUI, this method will mainly store lists or hash maps of street network elements like street segments, junctions, and buildings in static variables for later use.

``DrawStreetNetwork()`` places all static objects in the scene, i.e., everything except for vehicles and pedestrians, which are spawned at runtime.
For this, it calls the following methods:

:``GenerateStreetMeshes()``:
   For each lane segment contained in each street segment of the SUMO street network (``.net.xml``), draw a quad and move the corner vertices to the intersection points of the imaginary infinitely long left and right sides of neighboring segments. :footcite:p:`vaaraniemi2011high`
:``DrawJunctions()``:
   Create a planar polygon for each junction as defined in the ``.net.xml``.
:``DrawTrafficLights()``:
   Place traffic lights as required.

Further important calls in the ``Generator3DCourse`` ``OnGUI()`` method on ``ImportAndGenerate`` include:

:``GeneratePolyBuildings()``:
   Based on the 2D polygons provided by the SUMO ``.poly.xml``, create a building for each using the ``CreateBuildingMesh()`` method.
:``InsertEgoVehicle()``:
   Insert an empty GameObject into the scene where the ego vehicle is supposed to spawn.
   The ego vehicle itself will be spawned when the simulation starts.
   This makes it possible to select the desired kind of vehicle in the main menu as configured in ``EVIConnector``.
:``OpenSumoFilesAndSaveToTextFile()``:
   Create an ``EVIConnector`` instance and add it to the StreetNetwork GameObject.
   Apply settings from the GUI to member variables of the ``EVIConnector`` instance.


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

Position and rotation updates from the bicycle interface are handled by the ``NetworkListener``, which is attached to all ego vehicle prefabs with ``_UDP`` in their name.
(Other prefabs like the keyboard-controlled bicycle have their own scripts for controlling the movement of the vehicle.)

In ``Start()``, the member variable ``egoVehicle`` is assigned to the corresponding game object and a thread is started for listening to incoming UDP messages.
This thread runs the ``ReceiveData()`` method.
If a message is received, ``ReceiveData()`` will update member variables of the ``NetworkListener`` to the current position, rotation, and speed of the vehicle.

These values are then applied in every Unity time step in the ``Update()`` method.
In case of a bicycle ego vehicle, the ``NetworkListener`` uses the class ``BicycleRig`` for taking care of applying the correct wheel and pedal rotations.


.. footbibliography::
