all:
	@echo Generating python classes from proto files
	@protoc -I=. --python_out=. hapticsignals.proto
	@protoc -I=. --python_out=. asmp.proto
	@echo Generated python classes

clean:
	rm hapticsignals_pb2.py asmp_pb2.py
