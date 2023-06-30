# veins-evi

This contains the [Veins](http://veins.car2x.org/) subproject to interact with the Ego-Vehicle Interface (EVI).
It is used for the Virtual Cycling Environment (VCE).

## Installation

```
./configure --veins <veins_path, e.g., ~/veins-veins-5.0/>
make
```

## Running a scenario

Change into the directory of a scenario of your choice (e.g., examples/miniMap) and exectute
```
./run -u Cmdenv -c LanradioDisabled
```

## Dependencies

Since this code is a subproject to Veins 5.0, you have to install Veins first.
To do so, you can use the documentation from the [website](http://veins.car2x.org/tutorial/).

Further dependencies are:
- protobuf-evi
- ZMQ (libzmq-dev)

## Extending

All source code resists in `src/veins_evi`.
Files in there override or use code from the vanilla Veins 5.0.
You can modify existing files or add new ones as you wish (if you do so, execute `configure` and `make` again).

## Adding further dependencies

For adding further dependencies to the build process, you can use the `src/makefrag`.
