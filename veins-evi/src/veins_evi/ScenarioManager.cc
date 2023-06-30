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

#define MYDEBUG EV
#include "veins_evi/ScenarioManager.h"
#include "veins_evi/md5.h"
#include "veins_evi/CommandInterface.h"
#include "veins_evi/Mobility.h"
#include "veins/modules/mobility/traci/TraCICoordinateTransformation.h"
#include "veins/modules/obstacle/ObstacleControl.h"
#include "veins/base/connectionManager/BaseConnectionManager.h"

Define_Module(veins::evi::ScenarioManager);

namespace veins {
namespace evi {

using milliseconds_t = uint32_t;
const simsignal_t ScenarioManager::activeVehiclesSignal = registerSignal("org_car2x_veins_subprojects_veins_evi_activeVehicles");

// helper functions
namespace {

/*
 * initialize polygons (buildings for signal shadowing) from network init data
 */
void intializeObstacles(ObstacleControl* obstacles, const std::vector<SyncData::Polygon> polygons)
{
    if (obstacles == nullptr) {
        return;
    }
    for (auto&& polygon : polygons) {
        if (obstacles->isTypeSupported(polygon.type)) {
            obstacles->addFromTypeAndShape(polygon.id, polygon.type, polygon.shape);
        }
    }
}

} // end anonymous namespace

bool ScenarioManager::isConnected() const
{
    return isConnected_;
}

const std::map<std::string, cModule*>& ScenarioManager::getManagedHosts()
{
    return hosts;
}

void ScenarioManager::registerGenericWarning(SyncData::GenericWarning gw)
{
    pendingWarnings.push_back(gw);
}

void ScenarioManager::registerReceivedWirelessMessage(SyncData::ReceivedWirelessMessage rwm)
{
    pendingWirelessMessages.push_back(rwm);
}

void ScenarioManager::registerOpenDoorMessage(SyncData::OpenDoorMessage odm)
{
    pendingOpenDoorMessages.push_back(odm);
}

/*
void ScenarioManager::registerHapticSignals(SyncData::HapticSignals hs)
{
    pendingSignals.push_back(hs);
}
*/

void ScenarioManager::executeOneTimestep()
{
    SyncData::TimestepData update_data;
    SyncData::EVIRequestData eviRequest;
    eviRequest.sync_time_s = simTime().dbl();
    eviRequest.genericWarnings = pendingWarnings;
    eviRequest.receivedWirelessMessages = pendingWirelessMessages;
    eviRequest.openDoorMessages = pendingOpenDoorMessages;
    // eviRequest.hapticSignals = pendingSignals;
    pendingWarnings.clear();
    pendingWirelessMessages.clear();
    pendingOpenDoorMessages.clear();
    // pendingSignals.clear();
    try {
        update_data = commandInterface->synchronizeAtTimestep(eviRequest);
    }
    catch (TeardownException& e) {
        timerManager.create(TimerSpecification([this]() { this->teardown(); }).oneshotIn(0));
        return;
    }
    if (simTime() != SimTime(update_data.sync_time_s)) {
        EV_INFO << "EVI time " << SimTime(update_data.sync_time_s)
            << " does not match simTime " << simTime()
            << "! update_data.sync_time_s = " << update_data.sync_time_s << std::endl;
    }
    ASSERT(abs(simTime().dbl() - SimTime(update_data.sync_time_s).dbl()) < 0.001);

    // apply updates
    for (auto& add_vehicle : update_data.addVehicles) {
        addVehicle(add_vehicle);
    }
    for (auto& mod_vehicle : update_data.modVehicles) {
        updateVehicle(mod_vehicle);
    }
    for (auto& del_vehicle_id : update_data.delVehicles) {
        removeVehicle(del_vehicle_id);
    }
    emit(activeVehiclesSignal, static_cast<long>(hosts.size()));
}

void ScenarioManager::initialize(int stage)
{
    cSimpleModule::initialize(stage);
    if (stage != 1) {
        return;
    }
    EV_INFO << "ScenarioManager init" << std::endl;

    // set up connection and command interface
    std::string host_iface = par("host_iface").stdstringValue();
    uint16_t evi_port = par("port");
    commandInterface.reset(new CommandInterface(evi_port, host_iface));

    // parse ego vehicle ids
    egoVehicleIds.clear();
    std::istringstream egoVehicleIdsStream{par("egoVehicleIds").stdstringValue()};
    for (std::string egoVehicleId; std::getline(egoVehicleIdsStream, egoVehicleId, ','); ) {
        egoVehicleIds.push_back(egoVehicleId);
        // ensure ego vehicles will always be the first entries in the node vector
        nodeVectorIndexFor(egoVehicleId);
    }

    // setup timers
    timerManager.create(TimerSpecification([this]() { this->connectAndStart(); }).oneshotAt(0));
    isConnected_ = true;
}

void ScenarioManager::handleMessage(cMessage* msg)
{
    if (!timerManager.handleMessage(msg)) {
        error("ScenarioManager doesn't handle messages from other modules");
    }
}

void ScenarioManager::connectAndStart()
{
    auto init_data = commandInterface->initializeConnection(static_cast<float>(par("margin").doubleValue()));

    sync_interval = SimTime(init_data.sync_interval_s); // round to milliseconds
    intializeObstacles(ObstacleControlAccess().getIfExists(), init_data.polygons);

    // schedule (first) synchronization timestep
    timerManager.create(TimerSpecification([this]() { this->executeOneTimestep(); }).relativeStart(0).interval(sync_interval));
}

void ScenarioManager::teardown()
{
    EV_INFO << "Performing teardown" << std::endl;
    auto hosts_copy = hosts;
    // remove all remaining vehicles
    for (auto& vehiclePair : hosts_copy) {
        EV_INFO << "    Removing leftover vehicle " << vehiclePair.first << std::endl;
        removeVehicle(vehiclePair.first);
    }
    ASSERT(hosts.empty());
    endSimulation(); // may be necessary if the real-time scheduler is used
}

void ScenarioManager::addVehicle(const SyncData::Vehicle& vehicle)
{
    EV_INFO << "Adding Vehicle " << vehicle.external_id
        << ", is ego vehicle: " << vehicle.isEgoVehicle
        << std::endl;
    if (hosts.find(vehicle.external_id) != hosts.end()) {
        error("Tried to register vehicle twice: %s", vehicle.external_id.c_str());
    }

    size_t nodeVectorIndex = nodeVectorIndexFor(vehicle.external_id);

    cModule* parentmod = getParentModule();
    ASSERT(parentmod != nullptr);
    cModuleType* vehicleType = cModuleType::get(par("moduleType"));
    ASSERT(vehicleType != nullptr);

    // create node module
    parentmod->setSubmoduleVectorSize("node", nodeVectorIndex + 1);
    EV_INFO << "Set submodule vector size to " << nodeVectorIndex + 1 << std::endl;
    cModule* vehicleModule = vehicleType->create("node", parentmod, nodeVectorIndex);
    vehicleModule->finalizeParameters();
    std::string displayString = par("moduleDisplayString");
    if (displayString.find("t=") == std::string::npos) {
        displayString += ";t=" + vehicle.external_id;
    }
    vehicleModule->getDisplayString().parse(displayString.c_str());
    vehicleModule->buildInside();

    // set up mobility
    auto mobilityModules = getSubmodulesOfType<Mobility>(vehicleModule);
    ASSERT(!mobilityModules.empty());
    for (auto *mm : mobilityModules) {
        if (vehicle.isEgoVehicle) {
            EV_INFO << "Setting up mobility for an ego vehicle, id: "
                << vehicle.external_id << std::endl;
        }
        mm->setExternalId(vehicle.external_id, vehicle.isEgoVehicle);
        mm->update({vehicle.altitude,
                    vehicle.angle,
                    vehicle.position,
                    vehicle.road_id,
                    vehicle.speed,
                    vehicle.signals,
                    vehicle.stopstates,
                    vehicle.lon,
                    vehicle.lat});
    }

    vehicleModule->callInitialize();
    hosts[vehicle.external_id] = vehicleModule;
    vehicleModule->scheduleStart(simTime() + sync_interval);
}

void ScenarioManager::updateVehicle(const SyncData::Vehicle& vehicle)
{
    // update position in Mobility
    ASSERT(hosts.find(vehicle.external_id) != hosts.end());
    auto *vehicleModule = hosts.at(vehicle.external_id);
    auto mobilityModules = getSubmodulesOfType<Mobility>(vehicleModule);
    ASSERT(!mobilityModules.empty());
    for (auto *mm : mobilityModules) {
        mm->update(
        {
            vehicle.altitude,
            vehicle.angle,
            vehicle.position,
            vehicle.road_id,
            vehicle.speed,
            vehicle.signals,
            vehicle.stopstates,
            vehicle.lon,
            vehicle.lat
        });
    }
}

void ScenarioManager::removeVehicle(const std::string& vehicleId)
{
    auto *vehicleModule = hosts.at(vehicleId);
    auto *nic = vehicleModule->getSubmodule("nic");
    auto *cc = FindModule<BaseConnectionManager*>::findGlobalModule();
    if (cc != nullptr && nic != nullptr) {
        cc->unregisterNic(nic);
    }
    hosts.erase(vehicleId);
    vehicleModule->callFinish();
    vehicleModule->deleteModule();
}

size_t ScenarioManager::nodeVectorIndexFor(const std::string& vehicleId)
{
    const auto search = vehicle_to_node_index.find(vehicleId);
    if (search != vehicle_to_node_index.end()) {
        return search->second;
    }
    const size_t nodeVectorIndex = vehicle_to_node_index.size();
    vehicle_to_node_index[vehicleId] = nodeVectorIndex;
    return nodeVectorIndex;
}

bool ScenarioManager::isEgoVehicle(const SyncData::Vehicle& vehicle) const
{
    return vehicle.isEgoVehicle;
}

bool ScenarioManager::isEgoVehicle(const std::string& vehicle_id) const
{
    ASSERT(!egoVehicleIds.empty());
    return std::find(std::begin(egoVehicleIds), std::end(egoVehicleIds), vehicle_id) != std::end(egoVehicleIds);
}

} // end namespace evi
} // namespace veins
