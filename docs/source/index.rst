.. Virtual Cycling Environment documentation master file, created by
   sphinx-quickstart on Tue Apr 12 15:18:13 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the Documentation of the Virtual Cycling Environment!
================================================================

Virtual Environment for Realistic Cycling Behavior

See our `website <https://www.ccs-labs.org/software/vce/>`_ for more information.

Summary
-------

In order to trace and record realistic and reliable cyclist behavior, we developed the Virtual Cycling Environment (VCE).
It allows cyclists to ride a virtual bicycle in a 3D virtual reality environment by interacting with a physical bicycle on a training stand.
Foreign traffic (i.e., cars) and wireless networking are provided by the specialized simulators SUMO and Veins, respectively.
The physical bike simulator is then coupled via the Ego-Vehicle Interface (EVI) to this simulation platform.
The VCE provides a high degree of realism to the cyclist, thanks to the haptics of a physical bicycle combined with virtual reality systems.
Researchers can leverage this to study the interaction of cyclists and their traffic environment without the danger of physical harm.
Thanks to the coupling to Veins, even future assistance systems relying on communication can be tested.

License
-------

This project is lincensed under GNU GPLv3. See the LICENSE file in the root directory for the full license text.

Reference
---------

If you are using components (or the concept) of the VCE or traces we recorded with the VCE, we would appreciate a citation:

Julian Heinovski, Lukas Stratmann, Dominik S. Buse, Florian Klingler, Mario Franke, Marie-Christin H. Oczko, Christoph Sommer, Ingrid Scharlau and Falko Dressler, "Modeling Cycling Behavior to Improve Bicyclists' Safety at Intersections – A Networking Perspective," Proceedings of 20th IEEE International Symposium on a World of Wireless, Mobile and Multimedia Networks (WoWMoM 2019), Washington, D.C., June 2019.

.. highlight: bibtex

::

   @inproceedings{heinovski2019modeling,
       address = {Washington, D.C.},
       author = {Heinovski, Julian and Stratmann, Lukas and Buse, Dominik S. and Klingler, Florian and Franke, Mario and Oczko, Marie-Christin H. and Sommer, Christoph and Scharlau, Ingrid and Dressler, Falko},
       booktitle = {20th IEEE International Symposium on a World of Wireless, Mobile and Multimedia Networks (WoWMoM 2019)},
       doi = {10.1109/WoWMoM.2019.8793008},
       isbn = {978-1-7281-0270-2},
       month = {6},
       publisher = {IEEE},
       title = {{Modeling Cycling Behavior to Improve Bicyclists' Safety at Intersections -- A Networking Perspective}},
       year = {2019},
   }


Contents
========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started/index
   hardware_setup/index
   scenario_creation/index
   extension_guide/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
