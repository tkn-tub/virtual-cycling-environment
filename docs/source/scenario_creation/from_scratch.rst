.. _scenario-from-scratch:

Creating a New Scenario From Scratch
====================================

SUMO Network and Configuration
------------------------------

EVI Configuration
-----------------

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
