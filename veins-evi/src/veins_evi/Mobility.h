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

#ifndef __VEINS_EVI_MOBILITY_H
#define __VEINS_EVI_MOBILITY_H

#include "veins/base/modules/BaseMobility.h"
#include "veins_evi/VehicleState.h"

namespace veins {
namespace evi {

class Mobility : public BaseMobility {
public:
    ~Mobility() override = default;

    // vehicle state access (write)
    virtual void update(VehicleState newState);
    virtual void setExternalId(std::string newExternalId, bool isEgoVehicle);
    virtual void setSignal(veins::VehicleSignal vs, bool value);
    // vehicle state access (read)
    virtual std::string getExternalId() const;
    virtual bool getIsEgoVehicle() const;
    virtual VehicleState getState() const;
    virtual std::string getRoadId() const;
    virtual Coord getRoadPosition() const;
    virtual double getSpeed() const;
    virtual Heading getAngleRad() const;
    virtual VehicleSignalSet getSignals() const;
    virtual bool getSignal(veins::VehicleSignal vs) const;
    virtual VehicleStopStateSet getVehicleStopStates() const;
    virtual bool getVehicleStopState(veins::VehicleStopState vss) const;

    // OMNeT++ module interface implementation
    void initialize(int) override;
    void finish() override;

    // BaseMobility implementation (public part)
    // virtual void handleSelfMsg(cMessage* msg) override;

protected:
    // BaseMobility implementation (protected part)
    void fixIfHostGetsOutside() override;

    // data members
    VehicleConfiguration vConf;
    VehicleState vState;

private:
    void changePosition();
    simtime_t lastPositionUpdate;
    bool hasValidState = false;
    bool isInitialized = false;
};

} // namespace evi
} // namespace veins

#endif
