.. _multiplayer-getting-started:

Multiplayer
===========

The VCE supports multiple users coexisting in the same simulation.\ :footcite:p:`oczko2023time`
This requires a little bit of additional configuration which will be explained on this page.

The EVI on its own will not work with multiple ego vehicles.
Instead, the Multiplayer Interface serves as a bridge between the EVI and any 3D Environment clients that need to connect to it.
The Multiplayer Interface assumes that the EVI has already been launched and will then wait for incoming connections from 3D Environment instances.

Therefore, let us first start the EVI on the machine that will become the multiplayer host.
The following example is the same as in :ref:`veins-getting-started` with the added change of overriding ``--evi-port``.
A default value for ``evi_port`` is already set in ``paderborn-north.evi.ini``, however, we want to avoid accidentally connecting a 3D Environment to the EVI directly instead of to the Multiplayer Interface.
Assuming that :ref:`veins-getting-started` has already been launched, run the following command from the ``evi`` subdirectory:

.. code-block:: bash

    poetry shell
    cd networks/paderborn-north
    ../../scripts/evid.py \
        --config-file paderborn-north.evi.ini \
        --sumo-binary sumo-gui \
        --veins-host localhost \
        --veins-port 12347 \
        --evi-port 12341

Next, we can start the Multiplayer Interface (again from the ``evi`` subdirectory):

.. code-block:: bash

    poetry shell
    scripts/multiplayer-interface/interface.py \
        --env3d-port 12346 \
        --evi-port 12341 \
        --connections 2

Now you can launch the 3D Environments from any of the client machines.
Make sure to specify the address of the host machine as the EVI address and to use the port specified with ``--env3d-port`` above.

.. note::
    The Multiplayer Interface will only establish a connection to the EVI once the specified number of clients (e.g., ``--connections 2``) have joined.

.. note::
    You can find an example configuration for running EVI, Veins-EVI, and the Multiplayer Interface with the :ref:`launcher` in ``scenarios/paderborn-north/multiplayer-host.launcher.toml``.
    Make sure to use the ``--prepare-only`` option of the VCE Launcher, since launching each component in a specific order automatically is not implemented yet.

.. footbibliography::
