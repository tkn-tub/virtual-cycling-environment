# README

This folder contains:
 - interface.py
 - evi\_connector.py
 - env3d\_connector.py
 - env3d.py 
 - eviasmprotocol (folder), copied from the vce project, needed to run the interface

### interface.py
Main class of the interface. Can be started with:

```console
foo@bar:~$ python interface.py --evi-port 12341 --env3d-port 12342 --connections 2
```
### evi\_connector.py
Class of the interface responsible for connection to EVI.

### env3d\_connector.py
Class of the interface responsible for connection to Unity.

### env3d.py 
Adjusted unity.py class from vce/evi/src/evi folder. 
