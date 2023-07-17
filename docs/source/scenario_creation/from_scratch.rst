.. _scenario-from-scratch:

Creating a New Scenario From Scratch
====================================

SUMO Network and Configuration
------------------------------

For compatibility with the VCE, your SUMO scenario **must** contain the following:

* A routes file (``.rou.xml``) with the following information:

  .. code-block:: xml

      <vType id="ego-type" color="blue"/>
      <route id="ego-route" edges="-19206342#0 -19206341#6 -19206341#4 -19206341#3 -19206341#1 -323350445#1 -369470720"/>

  :vType:
      A vehicle type definition for ``ego-type``.
  :route:
      The route that the ego vehicle will (likely) travel.
      This is mainly necessary for other traffic participants to react appropriately depending on whether the ego vehicle is going to go straight at an intersection or turn right.

  If you look at some of the example scenarios (e.g., ``scenarios/example-intersection/``), you may notice that they have two ``.rou.xml`` files, and that one of them is named ``ego-vehicle-only.rou.xml``.
  Since the SUMO configuration file (``.sumo.cfg`` or ``.sumocfg``) allows us to define multiple route files for one scenario, we can keep the ego vehicle definition separate from other routes that we might regenerate more frequently.

* A network file (``.net.xml``) with a specific setting of ``projParameter`` in the ``location`` element.
  For the time being, our 3D Environment simply passes this parameter on to a third-party library, which has no understanding of SUMO's ``-`` or ``!`` special definitions of ``projParameter``.
  If your scenario is generated artificially, you may simply copy a value of ``projParameter`` from one of the example scenarios.

* An additionals file (``.poly.xml``).

  When you select a ``.net.xml`` in the 3D Environment, it will automatically look for a file with the same name that has the ``.poly.xml`` file name extension.

  This file should include at least one point of interest (``poi``) of type ``EgoVehicleStart`` to define where the ego vehicle will be spawned.

  In addition the additionals file may include ``poly`` elements of type ``building`` or ``poi`` elements for supported street signs – currently type values starting with ``StreetSign_`` and ending with:

  - ``yield``
  - ``priority``
  - ``stop``
  - ``no_entry``
  - ``no_left_turn``
  - ``no_right_turn``
  - ``no_straight_on``
  - ``oneway_left``
  - ``oneway_right``
  - ``only_left_turn``
  - ``only_right_turn``
  - ``speed_limit_30``
  - ``speed_limit_50``


EVI Configuration
-----------------

.. todo::

   TODO


Optional Triggers File
----------------------

The EVI can optionally read a ``<scenario name>.triggers.yaml`` file and trigger certain events when the ego vehicle approaches a trigger point and gets closer than a defined distance.
Events include the following, corresponding to their respective class in ``evi/src/evi/triggers.py``:

:SpawnEvent:
    Spawn a new vehicle.
:ResumeEvent:
    Resume a previously stopped vehicle.
:SignalEvent:
    Set the active signals of a given vehicle, such as lights or open doors (which are also defined as signals in SUMO).

A triggers file may look as follows:

.. code-block:: yaml

    config:
        default_vehicle_type: default
        triggers_max_radius: 3
    triggers:
        - ego_xy: [42, 1337, 0]
          spawn:
            - arrival_lane:
              vehicle_id: triggered-car0
              arrival_pos:
              arrival_speed:
              depart_delay_seconds:
              depart_lane:
              depart_pos:
              depart_speed:
              num_vehicles: 1
              vehicle_type: default  # we could leave this out because of line 2
              route…


Veins-EVI
---------

.. todo::

    TODO
