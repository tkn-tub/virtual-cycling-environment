Design Decisions / Current State
================================

- configuration for multiple ego vehicle ids and routes
	* for now assume that all egos have the same route
	* sumo assumes they are just given to it (preconfigured)
	* evid has to take care of generating reasonable config
	* veins just needs to know which vehicles are ego vehicles
	* ASM/RTI needs a pre-configured mapper and derives its own list of ego ids (to filter out egos from fellows)
- (new) concept of ego vehicle lifetimes
	* ego vehicles should be registered and unregistered on demand (as told by rt simulator)
	* make sure this information is passed from rti to sumo (and asm) via the state (may be done already)
	* no more explicit call to register ego vehicle from ynode or such, sumo only gets state updates
	* sumo needs to keep track of active foreign (ego) vehicles and regiister/unregister them as needed.
	* special case: last ego vehicle unregistered: shut down evi
	* as a result, maybe we cannot send fellows in the first time step (acceptable as ASM needs to settle in anyway)
- ego vehicles should not be part of traffic (vehicles returned by sumo)
	* every place that needs the state of the ego vehicles gets them anyway
	* the sumo interface can do checking if, e.g., they are close enough
	* veins and rt interfaces do not have to filter for them (again)
