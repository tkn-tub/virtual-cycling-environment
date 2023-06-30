veins_run_%:
	../../scripts/evid.py --config-file $*.evi.ini --verbosity INFO --sumo-binary sumo-gui --veins-host localhost --veins-port 12347

run_%:
	../../scripts/evid.py --config-file $*.evi.ini --verbosity WARNING --sumo-binary sumo-gui

netedit_%:
	netedit -s $*.net.xml --additional-files $*.poly.xml

sumo-gui_%:
	sumo-gui -c $*.sumo.cfg
