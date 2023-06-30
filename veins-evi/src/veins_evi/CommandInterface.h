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

#ifndef __VEINS_EVI_COMMANDINTERFACE_H
#define __VEINS_EVI_COMMANDINTERFACE_H

#include "veins_evi/Connection.h"
#include "veins/modules/mobility/traci/TraCICoordinateTransformation.h"
#include "veins/modules/mobility/traci/TraCIColor.h"
#include "veins/modules/mobility/traci/VehicleSignal.h"
#include "veins/base/utils/Coord.h"
#include "veins_evi/VehicleStopState.h"
#include "protobuf/asmp.pb.h"

#include <string>
#include <vector>
#include <memory>
#include <map>

namespace veins {
namespace evi {

namespace SyncData {
// helper classes for results

struct Polygon {
    std::string id;
    std::string type;
    std::vector<Coord> shape;
}; // end struct Polygon

struct Vehicle {
    std::string external_id;
    bool isEgoVehicle;
    VehicleStopStateSet stopstates;
    VehicleSignalSet signals;
    const Coord position;
    std::string road_id;
    double speed;
    Heading angle;
    double altitude;
    double lat;
    double lon;
}; // end struct Vehicle

struct NetworkInitData {
    double sync_interval_s;
    std::vector<Polygon> polygons;
}; // end struct NetworkInitData

struct TimestepData {
    double sync_time_s;
    std::vector<Vehicle> addVehicles;
    std::vector<Vehicle> modVehicles;
    std::vector<std::string> delVehicles;
}; // end struct TimestepData

struct GenericWarning {
    uint32_t entity_id;
    double intensity;
    std::string description;
}; // end struct GenericWarning

struct ReceivedWirelessMessage {
    uint32_t entity_id;
    uint32_t sender_id;
    std::string receiver_id;
    double lon;
    double lat;
    double angle;
}; // end struct ReceivedWirelessMessage

struct OpenDoorMessage {
    uint32_t vehicleId;
    bool openLeftDoor;
    bool openRightDoor;
}; // end struct OpenDoorMessage

struct HapticSignals {
    uint32_t entity_id;
    uint32_t danger;
    std::string pattern;
    std::string vibrationSide;
}; // end struct HapticSignals

struct EVIRequestData {
    double sync_time_s;
    std::vector<GenericWarning> genericWarnings;
    std::vector<ReceivedWirelessMessage> receivedWirelessMessages;
    std::vector<OpenDoorMessage> openDoorMessages;
    std::vector<HapticSignals> hapticSignals;
}; // end struct EVIRequestData

} // end namespace SyncData

class TeardownException : std::exception {
};

class CommandInterface {
public:
    CommandInterface(uint16_t port, std::string host_iface = "0.0.0.0");
    virtual ~CommandInterface() = default;

    /*
     * Initialize connection to EVI by announcing this veins instance and return init data.
     */
    SyncData::NetworkInitData initializeConnection(float playgroundMargin);

    /**
     * signal arrival at sync time and receive new traffic updates
     */
    SyncData::TimestepData synchronizeAtTimestep(const SyncData::EVIRequestData& requestData);

private:
    Connection connection;
    std::shared_ptr<TraCICoordinateTransformation> coordTransform;
}; // end class CommandInterface

} // end namespace evi
} // end namespace veins

#endif
