-- Register a subdissector "my_subdissector" to the ZMTP protocol table for TCP port 1234
local zmtp = DissectorTable.get("zmtp.protocol")

evi_protocol = Proto("EVI-ZMQ", "EVI Protobuf wrapped in ZMQ")

function evi_protocol.dissector(buffer, pinfo, tree)
	local protobuf_dissector = Dissector.get("protobuf")
	pinfo.private["pb_msg_type"] = "message,asmp.Message"
	protobuf_dissector:call(buffer, pinfo, tree)
end

zmtp:add(12347, evi_protocol)
-- Register the ZMTP dissector as the default for that TCP port (so no "decode as" is needed)
local zmtp_dissector = Dissector.get("zmtp")
local tcp_table = DissectorTable.get("tcp.port")
tcp_table:add(12347, zmtp_dissector)
