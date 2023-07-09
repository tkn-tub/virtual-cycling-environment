.. _launcher:

VCE Launcher
============

On the previous pages, you learned how to run and configure each VCE component individually.
As you have probably noticed, it can be tedious to keep track of the different (Python) environments and commands to start each component in the configuration that you need for a particular experiment.
To make this easier, the VCE comes with the script ``scripts/vce-launcher.py``.

.. note::

    ``scripts/vce-launcher.py`` does not require any Python modules that aren't already availabe in a standard Python installation. However, ``tomllib`` only comes integrated with Python 3.11 or newer.

    The script assumes that the VCE is already installed.
    In addition to Python, Tmux and optionally Apptainer (depending if you used the VCE container for installation) should be installed.

To try this out with an example, go to the root folder of your VCE installation and run the following command:

.. code-block:: bash

    scripts/vce-launcher.py \
        --container \
        --prepare-only \
        networks/paderborn-north/with-minimap-and-bike-interface.launcher.toml

Here, ``--container`` means that each component will be launched using the Apptainer image ``vce-container.sif`` that ``scripts/vce-install-container.sh`` downloads automatically.

``--prepare-only`` means that the launcher will only ``cd`` into the respective component subfolder and type out the respective command for each component, but you will still be required to hit the enter key for each.
Leave this out to launch every component automatically as soon as they are ready.

Once you run the launcher, a `Tmux <https://github.com/tmux/tmux/wiki>`_ session should open with one window for each component.

.. warning::

   Tmux does not really support nested sessions, so be careful to not run the VCE launcher from inside an active Tmux session.

   The launcher will also fail if another Tmux session from a previous launch is still open. Use ``tmux ls`` to check for active sessions and ``tmux a -t VCE`` to re-enter the active VCE session, then close it if necessary.

If you're not familiar with Tmux yet, closing the session may be a bit unintuitive.
In Tmux, most commands for controlling its behavior (like opening/closing windows or tabs) are prefixed by a special key combination.
By default, this is ``Ctrl+B``.
If you want to close the current session, hit ``Ctrl+B``, then the ``:`` key, then type ``kill-session``, and finally hit enter.

Launch Configurations
---------------------

VCE Launcher configurations are stored in TOML files.
Let's look at an example to understand how you can write your own:

.. literalinclude:: ../../../scenarios/paderborn-north/with-minimap-and-bike-interface.launcher.toml
    :caption:
    :language: toml
    :linenos:

Each VCE component supported by VCE Launcher that you want to include in your simulation should have its own section in your ``launcher.toml``.
You can get a list of all supported components and parameters by running ``scripts/vce-launcher.py --help``.
