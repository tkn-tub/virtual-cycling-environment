.. _apptainer-getting-started:

Installation with Container
===========================

.. note::

    This installation method requires ``wget`` and `Apptainer <https://apptainer.org/>`_ to be installed.

This is the recommended method to install the VCE.
Simply run the following command from the root directory of the VCE repository:

.. code-block:: bash

    scripts/vce-install-container.sh

This will automatically download a pre-built image of the Apptainer `container for the VCE <https://github.com/lumpiluk/vce-container>`_ which comes with SUMO, OMNeT++, Veins (all installed to ``/opt/``), Protobuf, and other dependencies preinstalled, which can help to avoid dependency conflicts on some systems.
Then it will automatically call the ``scripts/vce-install-native.sh`` script from inside the container to set up the respective VCE components in your checked-out repository.

At this point, head to the following pages of the Getting Started guide to learn how to launch or, if needed, recompile the VCE components.
If you used the containerized method to install the VCE, remember to use this container to run any of the commands shown in this guide.
An easy way to do this is to launch a subshell for the container:

.. code-block:: bash

    apptainer shell vce-container.sif

.. note::

   The following pages will show you how to run and configure each component of the VCE individually.
   However, if you'd like to skip to running your first example scenario in one go, head over to :ref:`launcher`.

.. warning::

   Commands like ``poetry shell`` will source the ``.bashrc`` on your host system.
   If you have at one point installed SUMO or OMNeT++ natively and if you are using ``.bashrc`` to add them to your ``PATH``, then this might override the ``PATH`` defined within the container.
   In this case it is advisable to move your ``PATH`` definitions to your ``.bash_profile`` instead, which is only sourced once at login.

   Also be advised that a local installation of Pyenv can cause a version of Python on your host system to take precedence over that in a container if, for example, a ``pyproject.toml`` defines a minimum Python version that is different from that installed in the container.
