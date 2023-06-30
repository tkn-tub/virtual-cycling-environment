.. _protobuf-extension:

Protobuf (evi-asm-protocol)
===========================

Recompiling
-----------

If you change any of the Protobuf definitions, the respective Python, C#, and C++ code will have to be regenerated.

For the EVI (Python)
^^^^^^^^^^^^^^^^^^^^

Assuming you have used Poetry to install the :ref:`evi-getting-started` as described in the instructions, navigate to the ``evi/`` folder and run the following:

.. code-block:: bash

    poetry shell
    pip uninstall evi-asm-protocol
    > cd ../evi-asm-protocol
    > python ./setup.py build
    > python ./setup.py install

Alternatively, update the version string in ``evi-asm-protocol/setup.py`` and, from the ``evi/`` folder, run ``poetry update``.

For the 3D Environment (C#)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a Makefile in the ``evi-asm-protocol/`` folder for generating C# code for the 3D Environment.
Simply navigate to this folder and run ``make``.
The output files will be automatically written to the ``Assets/`` folder of the 3D environment.

Occasionally, new versions of the Protobuf compiler may break compatibility with the C# Google.Protobuf library provided by ``3denv/3denv/Assets/Scripts/Vehicle/Google.Protobuf.dll``.
Since NuGet is, at the time of writing, not supported in Unity C# projects, a possible workaround is to download an up-to-date package from the `NuGet website <https://www.nuget.org/packages/Google.Protobuf/>`_ and to extract the DLL file from the ``lib/net45/`` subfolder.
Do the same with any dependencies of ``Google.Protobuf.dll``, like `System.Runtime.CompilerServices.Unsafe <https://www.nuget.org/packages/System.Runtime.CompilerServices.Unsafe/>`_.
In this case, we used the DLL from the ``lib/net462`` subfolder.

For Veins-EVI (C++)
^^^^^^^^^^^^^^^^^^^

Protobuf code generation for Veins-EVI is done by the ``veins-evi/configure`` script.
Simply re-run it :ref:`as specified <veins-getting-started>` and don't forget to also run ``make`` again.
