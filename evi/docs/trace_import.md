Trace Import
============

The `scripts/pcapreplay.py` script can replay converted traces to act as a dummy ASM instance.
Traces can be read from various sources, including `pcap` files from tools like `wireshark`.

However, it is advised to convert the `pcap` files into a custom `csv`-based format first.
This will make them easier to read with different tools.
During this conversion, one can also adapt the source and destination ports from the recorded trace.
This will yield a ready-to-use trace file for easy replay.

Import
------

First, edit the `pcap` file so that only the messages sent by ASM are left in it.
This can be easily done with `wireshark` by filtering out all other messages and excluding them form an export.
Also check out the dissector from the `evi-protobuf` project.

Ideally, the trace should start with a message containing `RegisterVehicleCommand`s for one or more ego vehicles.
But EVI can also derive registrations from `UpdateVehicleCommands` if necessary.
The last message in the trace is ideally the one containing the `UnregisterVehicleCommand` for the last ego vehicle.
EVI will just shut down after that, so further messages will not be processed anyway.

Next, covert the `pcap` file into the `csv` format with the `pcapreplay.py` script:

```bash
scripts/pcapreplay.py --pcap-infile TRACE.pcap --csv-outfile TRACE.csv --src 127.0.0.1 --dst 127.0.0.1 --sport 12345 --dport 12346
```

Adjust the file names accordingly.
The overrides for the source addresses and ports may not be necessary.
But with the options above, the resulting csv trace will be in the right shape for local testing.
Afterwards, the resulting csv trace file can be read by the `pcapreplay.py` script for replay:

```bash
scripts/pcapreplay.py --replay --csv-infile TRACE.csv --decode --period 0.1
```

Note that you can also provide the address/port overrides when running `pcapreplay.py` script in the `--replay` mode without modifying the trace file.
