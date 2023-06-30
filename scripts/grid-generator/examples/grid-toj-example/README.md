# Grid TOJ Example

This example scenario comprises two VCE scenarios, each a grid street network with buildings, traffic priority signs, as well as points of interest for temporal order judgment (TOJ) trials, tutorial banners in the first of the two scenario blocks, and level end markers.

## Generating the Scenario Files

This example assumes that the Ego Vehicle Interface (EVI) and the vcegrid package sources are available locally in the following paths:
- evi: `../../../evi/`
- vcegrid: `../../`

To set up a Python environment in this folder under `./venv/`, run
```bash
make python_env
```

Then generate the two scenarios with
```bash
make generate
```

In order to run one of the scenarios, use either of the following two commands:
```bash
make start-block0
# or:
make start-block1
```
