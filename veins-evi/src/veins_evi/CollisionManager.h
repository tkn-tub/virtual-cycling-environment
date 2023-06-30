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

#ifndef __VEINS_EVI_COLLISIONMANAGER_H
#define __VEINS_EVI_COLLISIONMANAGER_H

#include "veins_evi/ScenarioManager.h"
#include "veins_evi/CommandInterface.h"
#include "veins/modules/utility/TimerManager.h"

namespace veins {
namespace evi {

class Mobility;

class CollisionManager : public cSimpleModule, public cListener {
public:
    ~CollisionManager() override = default;

    // OMNeT++ module interface implementation
    void initialize(int stage) override;
    /**
     *  tell omnet that this module wants multiple init stages.
     */
    int numInitStages() const override
    {
        return std::max(cSimpleModule::numInitStages(), 2);
    }
    void handleMessage(cMessage* msg) override;
    void receiveSignal(cComponent* source, simsignal_t signalID, cObject* obj, cObject* details) override;

protected:
    TimerManager timerManager{this};
    ScenarioManager* manager;
    std::string egoVehicleId;
    bool checkCollisionsOnlyForStoppedVehicles;

private:
    bool isEgoVehicle(std::string vehicleId) const;
    void setBothDoors(veins::evi::Mobility& m, bool value);
    void setLeftDoor(veins::evi::Mobility& m, bool value);
    void setRightDoor(veins::evi::Mobility& m, bool value);
    void CheckForCollision(bool checkOnlyForStoppedVehicles = false);
    /*
     * Checks, if two cars collide based on their coordinates and angles.
     * Based on seperating axis theorem.
     * @param c1 is the coordinate of the first vehicle
     * @param c2 is the coordinate of the second vehicle
     * @param ang1 is the angle of the first vehicle
     * @param ang2 is the angle of the second vehicle
     * @param veh1 is the description of the first vehicle
     * @param veh2 is the description of the second vehicle
     * @return is 1 in case of collision, 0 otherwise
     */
    virtual int collision(Coord c1, Coord c2, Heading ang1, Heading ang2);

    /*
     * Computes the value of a vector v.
     * @param v is the vector the value is computed of
     * @return sum is the value of the vector
     */
    virtual double valueVec(std::vector<double> v);

    /*
     * Compute normal to direction vector.
     * @param direction is the vector the normal should be computed to
     * @return normal is the direction vector of the normal to the given vector
     */
    virtual std::vector<double> computeNormal(std::vector<double> direction);

    /*
     * Normalizes a vector v.
     * @param v is the vector that should be normalized
     * @return vector is the normalized vector
     */
    virtual std::vector<double> normalizeVec(std::vector<double> v);

    /*
     * Computes the point with the given distance and the direction vector to start vector.
     * @param start is the staring point
     * @param direction is the direction in which the new point should lie
     * @param distance is the distance the new point should have to start
     * @return vnew is the vector of the computed point
     */
    virtual std::vector<double> computeVertices(std::vector<double> start, std::vector<double> direction, double distance);

    /*
     * Computes the vertices of a vehicle, depending in the type of the vehicle, the position of the vehicle and the direction vector and the normal to it.
     * @param n is the normal to the direction vector of the vehicle, d is the direction vector, coord is the position of the vehicle as a vector
     * @return a vector containing vor vectors which represent the vertices, beginning with left front, right front, left back, right back
     */
    const std::vector<std::vector<double>> getVerticesCar(std::vector<double> n,std::vector<double> d, std::vector<double> coord);

    /*
     * Computes the vertices of a vehicle, depending in the type of the vehicle, the position of the vehicle and the direction vector and the normal to it.
     * @param n is the normal to the direction vector of the vehicle, d is the direction vector, coord is the position of the vehicle as a vector
     * @return a vector containing vor vectors which represent the vertices, beginning with left front, right front, left back, right back
     */
    const std::vector<std::vector<double>> getVerticesBicycle(std::vector<double> n,std::vector<double> d, std::vector<double> coord);

    /*
     * Computes the point, where the normal and the function with starting point "start" and the given direction "direction" cross.
     * s*normal= start+t*direction (assume, that normal goes through (0,0)), s,t in R
     * It follows:
     * s= (start(1)*direction(0)-start(0)*direction(1))/(normal(1)*direction(0)-normal(0)*direction(1)).
     * @param start is vector of the staring point of the first function
     * @param direction is the direction of the first function
     * @param normal is the direction of the normal to the first function
     * @return vnew is the crossing point of the first function and normal
     */
    virtual std::vector<double> computePoint(std::vector<double> normal, std::vector<double> start, std::vector<double> direction);

    /*
     * Checks, if the intervals are overlapping.
     * @param array1 is the array containing the points of the projected vertices of the first vehicle
     * @param array1 is the array containing the points of the projected vertices of the second vehicle4
     * @return 1 if the intervals of the two different arrays are overlapping, 0 otherwise
     */
    virtual int checkArrays(std::vector<double> array1[], std::vector<double> array2[]);
};

} // namespace evi
} // namespace veins

#endif
