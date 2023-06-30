//
// Copyright (C) 2018 Dominik S. Buse <buse@ccs-labs.org>
//
// Documentation for these modules is at http://veins.car2x.org/
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//

package org.car2x.veins.subprojects.veins_evi;

//
// Scenario Manager to interact with the Ego Vehicle Interface (EVI)
//
// @author Dominik S. Buse
//

simple ScenarioManager
{
    parameters:
        @display("i=block/network2");
        @class(veins::evi::ScenarioManager);
        @signal[org_car2x_veins_subprojects_veins_evi_activeVehicles](type=long);
        @statistic[activeVehicles](source=org_car2x_veins_subprojects_veins_evi_activeVehicles; record=vector);
        string host_iface = default("0.0.0.0");  // interface to listen on
        int port = default(12347);  // port of EVI
        double margin = default(25);  // margin to add to all received vehicle positions
        string moduleType = default("org.car2x.veins.nodes.Car");
        string moduleDisplayString = default("i=veins/node/car;is=vs");
        string egoVehicleIds = default("1,2,3"); // comma-separated list of the ids of all ego-vehicles
}
