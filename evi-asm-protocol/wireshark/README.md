Wireshark-Dissector for ASMP
============================

With this dissector, Wireshark can show the contents of ASMP messages.

*Requires Wireshark version 3.2 or newer (for built-in Protobuf-support)*


Installation
------------

First make Wireshark aware of the lua files in this diretory.
This can be done by either:

- copying/linking this `wireshark` directory into one of Wireshark's plugin folders (click Help->About Wireshark->Folders), e.g. `ln -s /path/to/protobuf-evi/wireshark evi` (from within your plugins directory) or
- passing the location of the scripts to Wireshark on startup, e.g. `wireshark -X lua_script:/path/to/this/zmtp-dissector.lua -X lua_script:/path/to/this/zmtp-protobuf-dissector.lua`

Then register the `.proto` files of ASMP with Wireshark:

- Open the `Preferences Edit -> Preferences`
- On the left, select `Protocols -> ProtoBuf`
- Click `Edit` next to `Protobuf seach paths`
- Add a new entry and make it point to the `protobuf` directory of this reposotory (containing `asmp` and `asmp.proto`
- Tick the `Load all files` box

Now, Wireshark should be able to automatically dissect messages.
If you send on non default ports (other than 12345 and 12346), you may have to manually select the protocol.

This respository also bundles the [ZMTP Dissector](https://github.com/whitequark/zmtp-wireshark) to support protobuf wrapped in ZMQ.
That is set up as a default for port tcp:12347 to analyze the communication with Veins-EVI.
But you can also extend/configure it for other port, e.g., for communication with the VCE/Unity.

For more info, see: https://www.wireshark.org/docs/wsug_html_chunked/ChProtobufSearchPaths.html
