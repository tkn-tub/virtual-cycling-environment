EVID=evid.py

OUTPUT_PREFIX_BLOCK0=grid-toj_block0
OUTPUT_PREFIX_BLOCK1=grid-toj_block1

GENERATE_GRID_RESULTS=\
	.net.xml \
	.poly.xml \
	.toj-route.yaml \
	.triggers.yaml \
	.stats.txt \
	.rou.xml \
	.evi.ini \
	.evi-remote-sumo.ini \
	.sumo.cfg \
	.remote-sumo.cfg

results_block0=$(addprefix $(OUTPUT_PREFIX_BLOCK0), $(GENERATE_GRID_RESULTS))
results_block1=$(addprefix $(OUTPUT_PREFIX_BLOCK1), $(GENERATE_GRID_RESULTS))

venv/pyvenv.cfg:
	python3 -m venv venv/; \
		source venv/bin/activate; \
		python3 -m ensurepip; \
		pip install pipenv; \
		pipenv install;

.PHONY:
python_env: venv/pyvenv.cfg

.PHONY:
generate $(OUTPUT_PREFIX_BLOCK0) $(OUTPUT_PREFIX_BLOCK1): \
		$(results_block0) \
		$(results_block1)

.PHONY:
start-block0: $(results_block0)
	$(EVID) --config-file $(OUTPUT_PREFIX_BLOCK0).evi.ini

.PHONY:
start-block1: $(results_block1)
	$(EVID) --config-file $(OUTPUT_PREFIX_BLOCK1).evi.ini

.PHONY:
start-block0-with-gui: $(results_block0)
	$(EVID) --config-file $(OUTPUT_PREFIX_BLOCK0).evi.ini --sumo-binary sumo-gui

.PHONY:
start-block1-with-gui: $(results_block1)
	$(EVID) --config-file $(OUTPUT_PREFIX_BLOCK1).evi.ini --sumo-binary sumo-gui

.PHONY:
netedit-block0: $(results_block0)
	netedit -s ./$(OUTPUT_PREFIX_BLOCK0).net.xml --sumo-shapes-file $(OUTPUT_PREFIX_BLOCK0).poly.xml

.PHONY:
netedit-block1: $(results_block1)
	netedit -s ./$(OUTPUT_PREFIX_BLOCK1).net.xml --sumo-shapes-file $(OUTPUT_PREFIX_BLOCK1).poly.xml


.PHONY:
start-block0-remote-sumo: $(results_block0)
	SUMO_HOME=. $(EVID) --config-file $(OUTPUT_PREFIX_BLOCK0).evi-remote-sumo.ini

.PHONY:
start-block1-remote-sumo: $(results_block1)
	SUMO_HOME=. $(EVID) --config-file $(OUTPUT_PREFIX_BLOCK1).evi-remote-sumo.ini

.PHONY:
start-block0-remote-gui: $(results_block0)
	sumo-gui -c $(OUTPUT_PREFIX_BLOCK0).remote-sumo.cfg

.PHONY:
start-block1-remote-gui: $(results_block1)
	sumo-gui -c $(OUTPUT_PREFIX_BLOCK1).remote-sumo.cfg


$(results_block0) $(results_block1):
	@echo Generating the following files:
	@echo $(results_block0) $(results_block1)
	@echo
	./generate.py

.PHONY:
clean:
	rm -f \
		$(results_block0) \
		$(results_block1) \
		arrow.png priority.png yield.png
