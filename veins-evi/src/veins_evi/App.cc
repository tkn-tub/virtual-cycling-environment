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

#include "veins_evi/App.h"

#include "veins_evi/md5.h"
#include "veins_evi/Mobility.h"
#include "veins_evi/ScenarioManager.h"
#include "veins_evi/CommandInterface.h"
#include "veins_evi/messages/CAMMessage_m.h"
#include "veins/modules/utility/Consts80211p.h"
#include "veins/base/utils/FindModule.h"
#include "veins/modules/mobility/traci/TraCICoordinateTransformation.h"
#include <chrono>
#include <functional>

Define_Module(veins::evi::App);

namespace {

auto hash_function = std::hash<std::string>();
veins::TraCICoordinateTransformation angle_helper({0, 0}, {0, 0}, 0);

} // anonymous namespace

namespace veins {
namespace evi {

void App::initialize(int stage)
{
    BaseApplLayer::initialize(stage);

    if (stage == 0) {
        // set up beaconing timer
        auto triggerBeacon = [this]() { this->beacon(); };
        auto timerSpec = TimerSpecification(triggerBeacon)
            .relativeStart(uniform(0, par("beaconInterval")))
            .interval(par("beaconInterval"));
        timerManager.create(timerSpec);

        // find mobility submodule
        auto mobilityModules = getSubmodulesOfType<Mobility>(getParentModule());
        ASSERT(mobilityModules.size() == 1);
        mobility = mobilityModules.front();

        // derive vehicle id and mac address from external id
        myId = hash_function(mobility->getExternalId());
        EV_INFO << "Initializing App for vehicle with hashed external id: " << myId << std::endl;
        std::ostringstream macBuilder;
        macBuilder << "f2:"
            << std::hex << ((myId & (0xFF << 0)) >> 0) << ":"
            << std::hex << ((myId & (0xFF << 2)) >> 2) << ":"
            << std::hex << ((myId & (0xFF << 4)) >> 4) << ":"
            << std::hex << ((myId & (0xFF << 6)) >> 6) << ":"
            << std::hex << ((myId & (0xFF << 8)) >> 8);
        myMacAddress = macBuilder.str();
        par("macAddress") = myMacAddress;
    }
    else if (stage == 1) {
        manager = FindModule<ScenarioManager*>::findGlobalModule();
        par("isEgoVehicle") = manager->isEgoVehicle(mobility->getExternalId());
    }
}

void App::finish()
{
}

void App::handleSelfMsg(cMessage* msg)
{
    timerManager.handleMessage(msg);
}

void App::beacon()
{
    // just some demo content
    // EV_INFO << "BEACON of " << getFullPath() << "\n";

    // perpare the CAM payload
    int64_t currTime = std::chrono::high_resolution_clock::now().time_since_epoch() / std::chrono::nanoseconds(1);
    auto myId = getParentModule()->getId();

    auto state = mobility->getState();
    CAMData camData;
    camData.stationId = myId;
    camData.lastSendingTime = lastSentCamTime;
    lastSentCamTime = currTime;
    camData.speed = state.speed;
    camData.heading = angle_helper.omnet2traciHeading(state.angle);
    // omnet2traciHeading returns an angle < 180 and > -180 degree, cam needs an angle < 360 and > 0 degree
    // 0 degree representing north and 90 degree representing east
    if (camData.heading < 0) {
        camData.heading += 360.0;
    }
    camData.latitude = state.latitude;
    camData.longitude = state.longitude;
    camData.altitude = state.altitude;
    camData.length = 0; // FIXME: set vehicle length
    camData.acceleration = 0; // FIXME: set vehicle acceleration
    camData.yawRate = 0; // FIXME: set vehicle yaw rate
    
    /* // This block was deleted / not present in Chi's master's thesis. Not sure if on purpose.
    if ((!sentOpenDoorWarning) && (mobility->getSignal(veins::VehicleSignal::door_open_right) || mobility->getSignal(veins::VehicleSignal::door_open_left))) {
        camData.rightDoorOpen = mobility->getSignal(veins::VehicleSignal::door_open_right);
        camData.leftDoorOpen = mobility->getSignal(veins::VehicleSignal::door_open_left);
        sentOpenDoorWarning = true;
        std::cout << "a door is open" << std::endl;
    }else if(sentOpenDoorWarning){  // A warning regarding the open door is already sent
        camData.rightDoorOpen = false;
        camData.leftDoorOpen = false;
        if (!mobility->getSignal(veins::VehicleSignal::door_open_right) && !mobility->getSignal(veins::VehicleSignal::door_open_left)) {    // both doors are closed, sent a new warning if a door opens again
            sentOpenDoorWarning = false;
        }
    }else{  // initialize struct data with actual door state
        camData.rightDoorOpen = mobility->getSignal(veins::VehicleSignal::door_open_right);
        camData.leftDoorOpen = mobility->getSignal(veins::VehicleSignal::door_open_left);
    }
    */

    // std::cout << camData.stationId << " sent cam: heading: " << camData.heading << ", latitude: " << camData.latitude << ", longitude: " << camData.longitude << ", rightDoor: " << camData.rightDoorOpen << ", left door: " << camData.leftDoorOpen << std::endl;

    auto *msg = new CAMMessage("CAM");
    msg->setCamData(camData);
    msg->setTimestamp(simTime());
    msg->setRecipientAddress(-1);
    msg->setBitLength(headerLength);
    msg->setPsid(-1);
    msg->setChannelNumber(static_cast<int>(Channel::cch));
    msg->addBitLength(par("beaconLengthBits"));
    msg->setUserPriority(par("beaconUserPriority"));
    msg->setSrcmac(myMacAddress.c_str());

    sendDown(msg);
}

void App::handleLowerMsg(cMessage* msg)
{
    if (isEgoVehicle()) {
        auto cam = check_and_cast<CAMMessage*>(msg);
        // auto myCam = cam->getCam();

        // cooperative awareness logic
        auto& camData = cam->getCamData();
        auto latitude = camData.latitude;
        auto longitude = camData.longitude;
        // auto heading = camData.heading;
        // auto speed = camData.speed;
        // auto length = camData.length;
        // auto acceleration = camData.acceleration;
        // auto yawRate = camData.yawRate;

        // Send cooperative awareness warning to unity
        SyncData::GenericWarning warning;
        warning.intensity = 1;
        // TODO set individual entity_ids
        warning.entity_id = (uint32_t)(latitude + longitude);

        // fill warning with useful information
        warning.description = "Car from left!";
        manager->registerGenericWarning(warning);
    }
    cancelAndDelete(msg);
}

bool App::isEgoVehicle() const
{
    return par("isEgoVehicle");
}

} // namespace evi
} // namespace veins
