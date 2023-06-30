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

#include "veins_evi/Mobility.h"
#include "veins/base/utils/Heading.h"

Register_Class(veins::evi::Mobility);

namespace {

veins::Coord antennaPosition(veins::Coord vehiclePos, veins::Heading heading, double antennaPositionOffset)
{
    if (antennaPositionOffset >= 0.001) {
        // adjust antenna position of vehicle according to antenna offset
        vehiclePos -= heading.toCoord() * antennaPositionOffset;
    }
    return vehiclePos;
}

void tickVehicleDisplayString(cDisplayString& displayString)
{
    if (std::string(displayString.getTagArg("veins", 0)) == ". ") {
        displayString.setTagArg("veins", 0, " .");
    }
    else {
        displayString.setTagArg("veins", 0, ". ");
    }
}

} // end anonymous namespace

namespace veins {
namespace evi {

void Mobility::update(VehicleState newState)
{
    vState = std::move(newState);
    hasValidState = true;
    if (isInitialized) {
        changePosition();
    }
}

void Mobility::setExternalId(std::string newExternalId, bool isEgoVehicle)
{
    vConf.external_id = newExternalId;
    par("externalId") = newExternalId;
    vConf.isEgoVehicle = isEgoVehicle;
    //par("isEgoVehicle") = isEgoVehicle;
}

std::string Mobility::getExternalId() const
{
    return vConf.external_id;
}

bool Mobility::getIsEgoVehicle() const
{
    return vConf.isEgoVehicle;
}

VehicleState Mobility::getState() const
{
    return vState;
}

std::string Mobility::getRoadId() const
{
    return vState.road_id;
}

Coord Mobility::getRoadPosition() const
{
    return vState.roadPosition;
}

double Mobility::getSpeed() const
{
    return vState.speed;
}

Heading Mobility::getAngleRad() const
{
    return vState.angle;
}

VehicleSignalSet Mobility::getSignals() const
{
    return vState.signals;
}

bool Mobility::getSignal(veins::VehicleSignal vs) const
{
    return vState.signals.test(vs);
}

void Mobility::setSignal(veins::VehicleSignal vs, bool value)
{
    vState.signals.set(vs, value);
}

VehicleStopStateSet Mobility::getVehicleStopStates() const
{
    return vState.stopstates;
}

bool Mobility::getVehicleStopState(veins::VehicleStopState vss) const
{
    return vState.stopstates.test(vss);
}

void Mobility::initialize(int stage)
{
    // ensure we have some valid position state
    assert(hasValidState);
    if (stage != 1) {
        // don't call BaseMobility::initialize at stage 1
        // our parent will take care to call changePosition later
        BaseMobility::initialize(stage);
    }

    if (stage == 0) {
        vConf.antennaPositionOffset = par("antennaPositionOffset");
    }
    else if (stage == 1) {
        isInitialized = true;
        changePosition();
    }
}

void Mobility::finish()
{
}

// void handleSelfMsg(cMessage* msg)
// {
// }

void Mobility::fixIfHostGetsOutside()
{
    // check for actual error
    Coord pos = move.getStartPos();
    bool outsideX = (pos.x < 0) || (pos.x >= playgroundSizeX());
    bool outsideY = (pos.y < 0) || (pos.y >= playgroundSizeY());
    bool outsideZ = (!world->use2D()) && ((pos.z < 0) || (pos.z >= playgroundSizeZ()));
    if (outsideX || outsideY || outsideZ) {
        error("Tried moving host to (%f, %f) which is outside the playground", pos.x, pos.y);
    }
    // perform BaseMobility's handling
    Coord dummy = Coord::ZERO;
    double dum;
    handleIfOutside(RAISEERROR, pos, dummy, dummy, dum);
}

void Mobility::changePosition()
{
    // ensure we have some valid position state
    assert(hasValidState);
    // ensure we're not called twice in one time step
    ASSERT(simTime() == 0 || lastPositionUpdate < simTime());
    lastPositionUpdate = simTime();

    // make the vehicles display string tick back and forth
    tickVehicleDisplayString(getParentModule()->getDisplayString());

    // determine next position of antenna
    Coord nextPos = antennaPosition(vState.roadPosition, vState.angle, vConf.antennaPositionOffset);
    nextPos.z = move.getStartPosition().z; // keep z position

    // update Move object
    move.setStart(nextPos);
    move.setDirectionByVector(vState.angle.toCoord());
    move.setSpeed(vState.speed); // TODO: make setting speed optional (as with TraCIMobility)
    if (isInitialized) {
        fixIfHostGetsOutside();
        updatePosition();
    }
}

} // namespace evi
} // namespace veins
