# EVI Protocol Definition using Google Protocol Buffers (evi-protobuf)

This project contains the protocol specification for the Ego Vehicle Interface (EVI).
It is also called ASMP (ASM Protocol) due to its first use: connecting EVI to dSPACE ASM.
It uses Google Protocol Buffers (version 2) for message specification.

These specifications can then be compiled for various programming languages.
Of primary concern are:

- Python, for EVI itself and some helper scripts
- C++, for Veins-EVI
- C#, for the driving-simulator

## Installation for Python

Before installation, the python files need to be compiled from the protobuf source files.
There are the following options to do that:

### Installing a checked out clone of this repository

After checking out this code, run the following to compile the protobuf sources to Python:
```bash
python setup.py build
```

You can then install the build directly from this directory:
```bash
pip install .
```

**Note:** you need to repeat these steps after each change to the protobuf sources!


### Building and installing a Python wheel

You can also install a wheel archive instead of the checked out repository.
This needs the `wheel` package installed for your python version.
To build a wheel, run:
```bash
python setup.py bdist_wheel
```

This will compile the protobuf sources to Python and package an archive in the `dist` directory.
The exact name depends on the current version of this code, e.g., `evi_asm_protocol-0.11.0-py3-none-any.whl`.
You can then install this wheel using pip:

```bash
pip install dist/evi_asm_protocol-0.11.0-py3-none-any.whl`
```

**Note:** you need to repeat these steps after each change to the protobuf sources!

The CI pipeline of this repository automatically builds wheels for all tags.
You can find the files at: https://intern.ccs-labs.org/mirror/python-packages/evi-asm-protocol/
Note that this is an internal package repository and may require credentials for access.
