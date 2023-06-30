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

#include "veins_evi/CommandInterface.h"
#include "veins/modules/mobility/traci/TraCICoord.h"

namespace veins {
namespace evi {

namespace {

template <typename T, typename V>
void convertAddVehicle(const T& vehicle_cmd, V& container, bool is_ego_vehicle, TraCICoordinateTransformation& ct)
{
    auto& vehicle_pos = vehicle_cmd.state().position();
    container.push_back(SyncData::Vehicle{
                    std::to_string(vehicle_cmd.vehicle_id()),
                    is_ego_vehicle,
                    VehicleStopStateSet(static_cast<uint32_t>(vehicle_cmd.state().stopstate_sum())),
                    VehicleSignalSet(static_cast<uint32_t>(vehicle_cmd.state().signal_sum())),
                    ct.traci2omnet({vehicle_pos.px(), vehicle_pos.py()}),
                    std::to_string(vehicle_pos.road_id()),
                    vehicle_cmd.state().speed_mps(),
                    ct.traci2omnetHeading(vehicle_pos.angle()),
                    vehicle_pos.height(),
                    vehicle_pos.lat(),
                    vehicle_pos.lon()});
}

template <typename T, typename V>
void convertModVehicle(const T& vehicle_cmd, V& container, TraCICoordinateTransformation& ct)
{
    auto& vehicle_pos = vehicle_cmd.state().position();
    container.push_back(SyncData::Vehicle{
                    std::to_string(vehicle_cmd.vehicle_id()),
                    false,
                    VehicleStopStateSet(static_cast<uint32_t>(vehicle_cmd.state().stopstate_sum())),
                    VehicleSignalSet(static_cast<uint32_t>(vehicle_cmd.state().signal_sum())),
                    ct.traci2omnet({vehicle_pos.px(), vehicle_pos.py()}),
                    std::to_string(vehicle_pos.road_id()),
                    vehicle_cmd.state().speed_mps(),
                    ct.traci2omnetHeading(vehicle_pos.angle()),
                    vehicle_pos.height(),
                    vehicle_pos.lat(),
                    vehicle_pos.lon()});
}

} // end anonymous namespace

CommandInterface::CommandInterface(uint16_t port, std::string host_iface)
    : connection(port, host_iface)
{
    connection.bind();
    assert(connection.is_bound());
}

SyncData::NetworkInitData CommandInterface::initializeConnection(float playgroundMargin)
{
    // recv init data from EVI
    auto message_frames = connection.recv();
    assert(message_frames.size() == 1);
    std::string message_bytes = message_frames.front();
    asmp::Message top_message;
    top_message.ParseFromString(message_bytes);
    auto&& init_msg = top_message.session().netinit();

    // check version
    assert(init_msg.version().server() == "evi");

    // extract result data for network boundary object
    auto&& topleft_msg = init_msg.network_boundaries().topleft();
    auto&& bottomright_msg = init_msg.network_boundaries().bottomright();
    TraCICoord topleft(topleft_msg.x(), topleft_msg.y());
    TraCICoord bottomright(bottomright_msg.x(), bottomright_msg.y());
    coordTransform.reset(new TraCICoordinateTransformation(topleft, bottomright, playgroundMargin));

    // extract result data to hand out
    SyncData::NetworkInitData result;
    result.sync_interval_s = init_msg.sync_interval_s();
    for (int i = 0; i < init_msg.polygons_size(); ++i) {
        const auto& polygon = init_msg.polygons(i);
        // build / convert coordinate vector
        std::vector<Coord> shape;
        for (int j = 0; j < polygon.shape_size(); ++j) {
            const auto& point = polygon.shape(j);
            shape.emplace_back(coordTransform->traci2omnet({point.x(), point.y()}));
        }
        result.polygons.push_back(SyncData::Polygon{polygon.id(), polygon.type(), shape});
    }
    return result;
}

SyncData::TimestepData CommandInterface::synchronizeAtTimestep(const SyncData::EVIRequestData& requestData)
{
    // signal progress by replying to EVI
    asmp::Message request;
    request.mutable_session()->mutable_time_reached()->set_time_s(requestData.sync_time_s);
    // include warning messages
    asmp::Message warningMsg;
    for (const auto& warning : requestData.genericWarnings) {
        auto *visCmd = warningMsg.mutable_visualization()->add_commands();
        visCmd->set_entity_id(warning.entity_id);
        visCmd->mutable_generic_warning()->set_intensity(warning.intensity);
        visCmd->mutable_generic_warning()->set_description(warning.description);
    }
    for (const auto& message : requestData.receivedWirelessMessages) {
        auto *visCmd = warningMsg.mutable_visualization()->add_commands();
        visCmd->set_entity_id(message.entity_id);
        visCmd->mutable_wireless_message()->set_sender_id(message.sender_id);
        visCmd->mutable_wireless_message()->set_receiver_id(message.receiver_id);
        auto *location = new asmp::visualization::Location;
        location->set_lon(message.lon);
        location->set_lat(message.lat);
        location->set_angle(message.angle);
        visCmd->mutable_wireless_message()->set_allocated_location(location);
    }
    asmp::Message openDoorRequest;
    openDoorRequest.mutable_vehicle()->set_time_s(requestData.sync_time_s);
    for (const auto& odmMsg : requestData.openDoorMessages) {
        auto *updateVehicleCmd = openDoorRequest.mutable_vehicle()->add_commands();
        updateVehicleCmd->mutable_update_vehicle_command()->set_vehicle_id(odmMsg.vehicleId);
        auto *vState = new asmp::vehicle::VehicleState;
        if (odmMsg.openLeftDoor) {
            vState->add_signals(asmp::vehicle::VehicleState_VehicleSignal_DOOR_OPEN_LEFT);
        }
        if (odmMsg.openRightDoor) {
            vState->add_signals(asmp::vehicle::VehicleState_VehicleSignal_DOOR_OPEN_RIGHT);
        }
        updateVehicleCmd->mutable_update_vehicle_command()->set_allocated_state(vState);
    }
    connection.send({warningMsg.SerializeAsString(), request.SerializeAsString(), openDoorRequest.SerializeAsString()});
    // receive traffic update
    auto reply_frames = connection.recv();
    assert(reply_frames.size() == 1);
    auto reply_str = reply_frames.front();
    asmp::Message reply;
    reply.ParseFromString(reply_str);
    // check type of reply
    if (reply.has_session() && reply.session().has_teardown()) {
        // signal teardown
        throw TeardownException();
    }
    if (!reply.has_vehicle()) {
        throw std::runtime_error("Unexpected message class received from EVI");
    }

    // build and return result struct
    SyncData::TimestepData result;
    auto vehicle_msg = reply.vehicle();
    result.sync_time_s = vehicle_msg.time_s();

    for (int i = 0; i < vehicle_msg.commands_size(); ++i) {
        const auto& vehicle_cmd_container = vehicle_msg.commands(i);
        if (vehicle_cmd_container.has_register_vehicle_command()) {
            convertAddVehicle(
                vehicle_cmd_container.register_vehicle_command(),
                result.addVehicles,
                vehicle_cmd_container.register_vehicle_command().is_ego_vehicle(),
                *coordTransform
            );
        }
        else if (vehicle_cmd_container.has_update_vehicle_command()) {
            convertModVehicle(
                vehicle_cmd_container.update_vehicle_command(),
                result.modVehicles,
                *coordTransform
            );
        }
        else if (vehicle_cmd_container.has_unregister_vehicle_command()) {
            result.delVehicles.push_back(
                std::to_string(vehicle_cmd_container.unregister_vehicle_command().vehicle_id())
            );
        }
    }
    return result;
}

} // end namespace evi
} // end namespace veins
