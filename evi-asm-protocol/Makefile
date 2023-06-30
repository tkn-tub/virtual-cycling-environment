# NOTE: Run this with a protobuf compiler v3.0
# with never versions you will get errors like "'GeneratedClrTypeInfo' does not contain a constructor that takes 7 arguments"
# A compiler like that is available in debian stretch, so using podman (or docker) you can do (from the repo base dir):
#   podman run --rm -it -v (pwd):/work -w /work debian:stretch
#   apt update; apt install -y protobuf-compiler make
#   cd unity3d/protobuf-unity/
#   make clean
#   make

SUBCLASSES = \
	Cloud \
	Session \
	Trafficlight \
	Vehicle \
	Visualization \
    Hapticsignals \
	Horizon
ROOT_PROTO_DIR = protobuf
SUBCLASSES_PROTO_DIR = $(ROOT_PROTO_DIR)/asmp
OUT_DIR = ../3denv/3denv/Assets/Scripts/Vehicle
SUBCLASSES_OUT_DIR = $(OUT_DIR)/asmp
# When adding new classes, it may be required to manually import them
# in Unity for generating the respective Output.cs.meta file.

subclasses_lower = $(shell echo "$(SUBCLASSES)" | tr '[:upper:]' '[:lower:]')
subclasses_results = $(addsuffix .cs, $(addprefix $(SUBCLASSES_OUT_DIR)/, $(SUBCLASSES)))

.PHONY:
all: $(OUT_DIR)/Asmp.cs $(subclasses_results)
	@echo "Subclasses directory: $(SUBCLASSES_DIR)"
	@echo "Built $(OUT_DIR)/Asmp.cs as well as the following: $(subclasses_results)"

$(OUT_DIR)/Asmp.cs: protobuf/asmp.proto
	protoc -I=$(ROOT_PROTO_DIR) --csharp_out=$(OUT_DIR) $<

$(subclasses_results): $(addsuffix .proto, $(addprefix $(SUBCLASSES_PROTO_DIR)/, $(subclasses_lower)))
	mkdir -p $(SUBCLASSES_OUT_DIR)
	# For the input.proto, take the output filename, remove the .cs suffix and convert to lower case:
	protoc --csharp_out=$(SUBCLASSES_OUT_DIR) \
		$(SUBCLASSES_PROTO_DIR)/$(shell basename $@ | sed 's|\.cs|| ; s|\(.*\)|\L\1|').proto

.PHONY:
clean:
	rm -f $(subclasses_results) Asmp.cs
