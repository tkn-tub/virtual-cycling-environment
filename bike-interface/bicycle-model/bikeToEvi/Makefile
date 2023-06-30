#UNITY_HOST=131.234.121.241
UNITY_HOST=localhost
WHEEL_DIAMETER_M=0.7
NUM_SPOKES=18

.PHONY:
run: run-irspeedesp32-androidsteer

.PHONY:
run-irspeedesp32-androidsteer:
	./main.py \
		--unity-ip $(UNITY_HOST) \
		--wheel-diameter $(WHEEL_DIAMETER_M) \
		--num-spokes $(NUM_SPOKES) \
		--steering-sensor android \
		--android-deadzone 0 \
		--speed-sensor irspeed_esp32 \
		--initial-orientation 0 \
		--speed-factor 2

.PHONY:
run-irspeed-androidsteer:
	./main.py \
		--unity-ip $(UNITY_HOST) \
		--steering-sensor android \
		--android-deadzone 0 \
		--speed-sensor irspeed \
		--initial-orientation 0

.PHONY:
run-fluxsmart-androidsteer:
	./main.py \
		--unity-ip $(UNITY_HOST) \
		--steering-sensor android \
		--android-deadzone 0 \
		--speed-sensor flux-smart \
		--initial-orientation 0

.PHONY:
debug_ir_esp32:
	./main.py \
		--unity-ip $(UNITY_HOST) \
		--steering-sensor keyboard \
		--speed-sensor irspeed_esp32 \
		--initial-orientation 0

.PHONY:
debug:
	./main.py \
		--unity-ip $(UNITY_HOST) \
		--steering-sensor keyboard \
		--speed-sensor keyboard \
		--initial-orientation 0

.PHONY:
calibrate:
	python3 calibrate.py

.PHONY:
run-tacx:
	python3 main.py --unity-ip 131.234.121.241 --unity-port 15006

.PHONY:
run-android-steering:
	python3 main.py --speed-sensor keyboard --steering-sensor android --android-port 15007 --unity-ip localhost --unity-port 15006

.PHONY:
log-all-sensors:
	# …while using the Tacx cadence sensor for speed and the Android app for steering:
	./main.py --steering-sensor android --speed-sensor tacx --additional-sensors tacx-steering --logfile "$(date --utc +%FT%TZ)_all-sensors.log"

.PHONY:
log-steering-sensors:
	./main.py \
		--unity-ip $(UNITY_HOST) \
		--steering-sensor android \
		--android-deadzone 0 \
		--initial-orientation 0 \
		--speed-sensor irspeed \
		--additional-sensors tacx-steering \
		--logfile "$(date --utc +%FT%TZ)_steering-sensors.log"


SCENARIOS = 301 302 342 243
# Bicycle start points:
# 301: south, 301: south, 342: east, 243: west

.PHONY:
.ONESHELL:
record-trace-301:
	@read -p "Cyclist: " CYCLIST
	@read -p "Style: " STYLE
	@read -p "Iteration: " ITERATION
	./main.py \
		--unity-ip 131.234.121.241\
		--steering-sensor android \
		--android-deadzone 7\
		--speed-sensor irspeed \
		--initial-orientation 0 \
		--model-tracing-file "biketraces/biketrace_301_$$CYCLIST-$$STYLE-$$ITERATION-$(shell date --utc +%FT%H_%M_%S).log"

.PHONY:
.ONESHELL:
record-trace-302:
	@read -p "Cyclist: " CYCLIST
	@read -p "Style: " STYLE
	@read -p "Iteration: " ITERATION
	./main.py \
		--unity-ip 131.234.121.241\
		--steering-sensor android \
		--android-deadzone 7\
		--speed-sensor irspeed \
		--initial-orientation 0 \
		--model-tracing-file "biketraces/biketrace_302_$$CYCLIST-$$STYLE-$$ITERATION-$(shell date --utc +%FT%H_%M_%S).log"

.PHONY:
.ONESHELL:
record-trace-342:
	@read -p "Cyclist: " CYCLIST
	@read -p "Style: " STYLE
	@read -p "Iteration: " ITERATION
	./main.py \
		--unity-ip 131.234.121.241\
		--steering-sensor android \
		--android-deadzone 7\
		--speed-sensor irspeed \
		--initial-orientation 270 \
		--model-tracing-file "biketraces/biketrace_342_$$CYCLIST-$$STYLE-$$ITERATION-$(shell date --utc +%FT%H_%M_%S).log"

.PHONY:
.ONESHELL:
record-trace-243:
	@read -p "Cyclist: " CYCLIST
	@read -p "Style: " STYLE
	@read -p "Iteration: " ITERATION
	./main.py \
		--unity-ip 131.234.121.241\
		--steering-sensor android \
		--android-deadzone 7\
		--speed-sensor irspeed \
		--initial-orientation 90 \
		--model-tracing-file "biketraces/biketrace_243_$$CYCLIST-$$STYLE-$$ITERATION-$(shell date --utc +%FT%H_%M_%S).log"
