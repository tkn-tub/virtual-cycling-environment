tlp_protocol = Proto("TLP", "Type Length Prefixed Protocol")

message_type = ProtoField.uint8("tlp.message_type", "Payload Typecode", base.DEC)
message_length = ProtoField.int32("tlp.message_length", "Payload Length", base.DEC)

tlp_protocol.fields = { message_type, message_length }


function tlp_protocol.dissector(buffer, pinfo, tree)
	length = buffer:len()
	if length == 0 then return end

	pinfo.cols.protocol = tlp_protocol.name

	local payload_type = buffer(0, 1):uint()
	local payload_length = buffer(1, 4):uint()

	local subtree = tree:add(tlp_protocol, buffer(0, payload_length), "TLP Protocol of type " .. payload_type .. " with length " .. payload_length)

	subtree:add(message_type, buffer(0,1))
	subtree:add(message_length, buffer(1,4))

	local protobuf_dissector = Dissector.get("protobuf")
	pinfo.private["pb_msg_type"] = "message,asmp.Message"
	protobuf_dissector:call(buffer(5):tvb(), pinfo, subtree)
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(12345, tlp_protocol)
udp_port:add(12346, tlp_protocol)
