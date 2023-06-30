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

#ifndef __VEINS_EVI_VEHICLESTATE_H
#define __VEINS_EVI_VEHICLESTATE_H

#include "veins/base/utils/Heading.h"
#include "veins/modules/mobility/traci/VehicleSignal.h"
#include "veins_evi/VehicleStopState.h"
#include <string>

namespace veins {
namespace evi {

struct VehicleState {
    /** altitude in meters */
    double altitude;
    /** azimuth angle (rotation in (x, y) plane) in radian */
    Heading angle;
    /** position of the car's front bumper */
    Coord roadPosition;
    /** string of the road the vehicle currently drives on (including lane) */
    std::string road_id;
    /** current speed of vehicle along the road in meters per second */
    double speed;
    /** signal lights of the vehicle currently flashing */
    VehicleSignalSet signals;
    /** stop state of the vehicle */
    VehicleStopStateSet stopstates;
    /** longitudinal position of the vehicle (in degrees) */
    double longitude;
    /** lateral position of the vehicle (in degrees) */
    double latitude;
}; // end struct VehiclePosition

struct VehicleConfiguration {
public:
    /** position offset of antenna relative to vehicle front bumper in meters */
    double antennaPositionOffset;
    /** string id of the vehicle in the traffic simulation */
    std::string external_id = "";

    bool isEgoVehicle = false;
}; // end struct VehicleState

} // namespace evi
} // namespace veins

#endif
