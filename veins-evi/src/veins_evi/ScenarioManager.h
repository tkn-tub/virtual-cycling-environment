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

#ifndef __VEINS_EVI_SCENARIOMANAGER_H
#define __VEINS_EVI_SCENARIOMANAGER_H

#include "veins/base/utils/Coord.h"
#include "veins/modules/mobility/traci/TraCICoord.h"
#include "veins/modules/utility/TimerManager.h"

#include <omnetpp.h>
#include <memory>
#include <unordered_map>

// forward declarations (header includes only in implementation file)
namespace veins {
class TraCICoordinateTransformation; // directly in namespace veins for now
namespace evi {
namespace SyncData {
struct Vehicle;
struct GenericWarning;
struct ReceivedWirelessMessage;
struct OpenDoorMessage;
struct HapticSignals;
} // end namespace SyncData
class CommandInterface;
} // end namespace evi
} // end namespace veins

namespace veins {
namespace evi {

class ScenarioManager : public cSimpleModule {
public:
    const static simsignal_t activeVehiclesSignal;

    ~ScenarioManager() override = default;
    /**
     * return whether the scenario manager is connected to the traffic simulation already
     */
    virtual bool isConnected() const;
    /**
     * return all synchronized network modules managed by this scenario manager
     */
    virtual const std::map<std::string, cModule*>& getManagedHosts();

    /**
     * tell omnet that this module wants multiple init stages.
     */
    int numInitStages() const override
    {
        return std::max(cSimpleModule::numInitStages(), 2);
    }

    void registerGenericWarning(SyncData::GenericWarning gw);

    void registerReceivedWirelessMessage(SyncData::ReceivedWirelessMessage rwm);

    void registerOpenDoorMessage(SyncData::OpenDoorMessage odm);

    /**
     * Check whether the given vehicle is an ego vehicle.
     */
    bool isEgoVehicle(const SyncData::Vehicle& vehicle) const;
    bool isEgoVehicle(const std::string& vehicle_id) const;

protected:
    /**
     * perform one time step in the traffic simulation and refresh synchronized data
     */
    virtual void executeOneTimestep();

    /*
     * initialize simulation object using omnet machinery.
     */
    void initialize(int stage) override;

    /**
     * handle (event) message
     *
     * Only allows to react on self-scheduled events.
     */
    void handleMessage(cMessage* msg) override;

private:
    /**
     * run all preparations needed before and schedule syncronization start
     */
    void connectAndStart();

    /**
     * cleanly tear down the simulation after notice from EVI
     */
    void teardown();

    /**
     * Add a vehicle to C2X simulation.
     */
    void addVehicle(const SyncData::Vehicle& vehicle);

    /**
     * Update vehicle position and state.
     */
    void updateVehicle(const SyncData::Vehicle& vehicle);

    /**
     * Remove a vehicle from C2X simulation.
     */
    void removeVehicle(const std::string& vehicleId);

    /**
     * Look up or generate an index in the node vector for the given vehicle id.
     */
    size_t nodeVectorIndexFor(const std::string& vehicleId);

    // config options
    simtime_t sync_interval;

    // syncronization components
    std::shared_ptr<CommandInterface> commandInterface;

    // internal timers
    TimerManager timerManager{this};
    bool isConnected_ = false;
    std::vector<std::string> egoVehicleIds;
    // TODO: stuff to replace
    std::vector<SyncData::GenericWarning> pendingWarnings;
    std::vector<SyncData::ReceivedWirelessMessage> pendingWirelessMessages;
    std::vector<SyncData::OpenDoorMessage> pendingOpenDoorMessages;
    std::vector<SyncData::HapticSignals> pendingSignals;

    // vector of all hosts managed by us
    std::map<std::string, cModule*> hosts;
    // mapping external id to host index
    std::unordered_map<std::string, size_t> vehicle_to_node_index;
}; // end class ScenarioManager

} // end namespace evi
} // end namespace veins

#endif
