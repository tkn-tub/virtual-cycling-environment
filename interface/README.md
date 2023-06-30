# README

This folder contains:
 - interface.py
 - evi_connector.py
 - unity_connector.py
 - unity.py 
 - eviasmprotocol (folder), copied from the vce project, needed to run the interface

### interface.py
Main class of the interface. Can be started with:

```console
foo@bar:~$ python interface.py --evi-port 12341 –unity-port 12342 –unity-connections 2
```
### evi_connector.py
Class of the interface responsible for connection to EVI.

### unity_connector.py
Class of the interface responsible for connection to Unity.

### unity.py 
Adjusted unity.py class from vce/evi/src/evi folder. 