# Virtual Cycling Environment (VCE)

Virtual Cycling Environment for interactive bicycling experiments with vehicle-to-anything (V2X) communication.

See our [website](https://www.tkn.tu-berlin.de/software/vce/) for more information.

## Summary

In order to trace and record realistic and reliable cyclist behavior, we developed the Virtual Cycling Environment (VCE).
It allows cyclists to ride a virtual bicycle in a 3D virtual reality environment by interacting with a physical bicycle on a training stand.
Foreign traffic (i.e., cars) and wireless networking are provided by the specialized simulators SUMO and Veins, respectively.
The physical bike simulator is then coupled via the Ego-Vehicle Interface (EVI) to this simulation platform.
The VCE provides a high degree of realism to the cyclist, thanks to the haptics of a physical bicycle combined with virtual reality systems.
Researchers can leverage this to study the interaction of cyclists and their traffic environment without the danger of physical harm.
Thanks to the coupling to Veins, even future assistance systems relying on communication can be tested.

## Installation Instructions and Documentation

You can find detailed information instructions in our [documentation](https://vce.readthedocs.io).
Refer to [`docs/README.md`](docs/README.md) if you want to build the documentation yourself.

### Quick Start

```bash
scripts/vce-install-container.sh
scripts/vce-launcher.py --container scenarios/example-intersection/network.launcher.toml
```

## Components

You can find all components of the Virtual Cycling Environment within the following directories:

```
bike-android-app  # android app for measuring the angle of the steering handle
bike-interface  # scripts for the hardware interfacing with the physical bicycle
3denv  # tools for visualizing the environment with Unity
evi  # the Ego-Vehicle Interface (EVI)
evi-asm-protocol  # the Google Protobuf definitions for the Ego-Vehicle Interface (EVI)
veins-evi  # the Veins subproject for the Ego-Vehicle Interface (EVI)
```

## License

This project is licensed under GNU GPLv3.
See the [LICENSE](LICENSE) file for the full license text.

## Reference

If you are using components (or the concept) of the VCE or traces we recorded with the VCE, we would appreciate a citation:

Julian Heinovski, Lukas Stratmann, Dominik S. Buse, Florian Klingler, Mario Franke, Marie-Christin H. Oczko, Christoph Sommer, Ingrid Scharlau and Falko Dressler, "Modeling Cycling Behavior to Improve Bicyclists' Safety at Intersections – A Networking Perspective," Proceedings of 20th IEEE International Symposium on a World of Wireless, Mobile and Multimedia Networks (WoWMoM 2019), Washington, D.C., June 2019.

```
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
```
