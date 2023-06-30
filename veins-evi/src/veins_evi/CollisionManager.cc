#include "veins_evi/CollisionManager.h"
#include "veins_evi/md5.h"
#include "veins_evi/Mobility.h"
#include "veins_evi/ScenarioManager.h"
#include "veins_evi/CommandInterface.h"
#include "veins/base/utils/FindModule.h"

#define OPEN_DOOR_THRESHOLD 4
#define COLLISION_TEST_THRESHOLD 1
#define OPEN true
#define CLOSE false

Define_Module(veins::evi::CollisionManager);

namespace veins {
namespace evi {

void CollisionManager::initialize(int stage)
{
    if (stage == 0) {
        egoVehicleId = par("egoVehicleId").stdstringValue();
        checkCollisionsOnlyForStoppedVehicles = par("checkCollisionsOnlyForStoppedVehicles").boolValue();
        getSimulation()->getSystemModule()->subscribe(BaseMobility::mobilityStateChangedSignal, this);
    }
    if (stage == 1) {
        manager = FindModule<ScenarioManager*>::findGlobalModule();
        ASSERT(manager);
    }
}

void CollisionManager::setBothDoors(veins::evi::Mobility& m, bool value)
{
    if (((!m.getSignal(veins::VehicleSignal::door_open_left) || !m.getSignal(veins::VehicleSignal::door_open_right)) && value == OPEN) ||  // at least one door is closed and the aim is to open it
        ((m.getSignal(veins::VehicleSignal::door_open_left) || m.getSignal(veins::VehicleSignal::door_open_right)) && value == CLOSE )){    // at least one doors is open and the aim is to close it

        SyncData::OpenDoorMessage odm;
        odm.vehicleId = std::stoul(m.getExternalId());
        odm.openLeftDoor = value;
        odm.openRightDoor = value;
        manager->registerOpenDoorMessage(odm);
        m.setSignal(veins::VehicleSignal::door_open_left, value);
        m.setSignal(veins::VehicleSignal::door_open_right, value);
        EV_INFO << "externalId: " << m.getExternalId() << ", setBothDoors: " << m.getSignals().to_string() << std::endl;
    }
}

void CollisionManager::setLeftDoor(veins::evi::Mobility& m, bool value)
{
    if ((!m.getSignal(veins::VehicleSignal::door_open_left) && value == OPEN) ||
        (m.getSignal(veins::VehicleSignal::door_open_left) && value == CLOSE)) {

        SyncData::OpenDoorMessage odm;
        odm.vehicleId = std::stoul(m.getExternalId());
        odm.openLeftDoor = value;
        odm.openRightDoor = m.getSignal(veins::VehicleSignal::door_open_right);
        manager->registerOpenDoorMessage(odm);
        m.setSignal(veins::VehicleSignal::door_open_left, value);
        EV_INFO << "externalId: " << m.getExternalId() << ", setLeftDoor: " << m.getSignals().to_string() << std::endl;
    }
}

void CollisionManager::setRightDoor(veins::evi::Mobility& m, bool value)
{
    if ((!m.getSignal(veins::VehicleSignal::door_open_right) && value == OPEN) ||
        (m.getSignal(veins::VehicleSignal::door_open_right) && value == CLOSE)) {

        SyncData::OpenDoorMessage odm;
        odm.vehicleId = std::stoul(m.getExternalId());
        odm.openLeftDoor = m.getSignal(veins::VehicleSignal::door_open_left);
        odm.openRightDoor = value;
        manager->registerOpenDoorMessage(odm);
        m.setSignal(veins::VehicleSignal::door_open_right, value);
        EV_INFO << "externalId: " << m.getExternalId() << ", setRightDoor: " << m.getSignals().to_string() << std::endl;
    }
}

bool CollisionManager::isEgoVehicle(std::string vehicleId) const
{
    const auto egoVehicleExternalId = std::to_string(MD5(egoVehicleId).first4bytes());
    return vehicleId == egoVehicleExternalId;
}

void CollisionManager::receiveSignal(cComponent* source, simsignal_t signalID, cObject* obj, cObject* details)
{
    Enter_Method_Silent();
    if (signalID == BaseMobility::mobilityStateChangedSignal) {
        CheckForCollision(checkCollisionsOnlyForStoppedVehicles);
    }
}

void CollisionManager::handleMessage(cMessage* msg)
{
    EV_ERROR << "Got wrong message!" << std::endl;
}

/*
 * Check for possible Collision.
 */
void CollisionManager::CheckForCollision(bool checkOnlyForStoppedVehicles)
{
    const std::map<std::string, cModule*> &hosts = manager->getManagedHosts();
    std::map<std::string, cModule*>::const_iterator it;
    if (hosts.size() > 1) {
        // Find mobility of ego-Vehicle/bicycle
        Mobility* egoVehicleMobility;
        for (it = hosts.begin(); it != hosts.end(); it++) {
            egoVehicleMobility = getSubmodulesOfType<Mobility>(it->second).front();
            if (isEgoVehicle(egoVehicleMobility->getExternalId())) {
                // ego vehicle mobility found, stop searching
                break;
            }
        }
        for (it = hosts.begin(); it != hosts.end(); it++) {
            Mobility* fellowVehicleMobility = getSubmodulesOfType<Mobility>(it->second).front();
            // Don't compare ego vehicle with itself
            if (egoVehicleMobility->getExternalId() == fellowVehicleMobility->getExternalId()) {
                continue;
            }
            if (checkOnlyForStoppedVehicles && fellowVehicleMobility->getVehicleStopState(veins::VehicleStopState::stopped)) {  // check for collision only with stopped fellow vehicles
                /*coordinates*/
                Coord fellowVehicleCoord = fellowVehicleMobility->getPositionAt(simTime());
                Coord egoVehicleCoord = egoVehicleMobility->getPositionAt(simTime());

                /*angles*/
                auto fellowVehicleAngle = fellowVehicleMobility->getAngleRad();
                auto egoVehicleAngle = egoVehicleMobility->getAngleRad();

                /*distance of both vehicles*/
                double distance = std::sqrt((egoVehicleCoord.y - fellowVehicleCoord.y) * (egoVehicleCoord.y - fellowVehicleCoord.y) + (egoVehicleCoord.x - fellowVehicleCoord.x) * (egoVehicleCoord.x - fellowVehicleCoord.x));

                if (distance < (OPEN_DOOR_THRESHOLD)) {
                    setBothDoors(*fellowVehicleMobility, OPEN);
                }
                /* check for collisions */
                if (distance < COLLISION_TEST_THRESHOLD) {
                    if (collision(fellowVehicleCoord, egoVehicleCoord, fellowVehicleAngle, egoVehicleAngle) == 1) {
                         EV_INFO <<  simTime() << ": Actual collision!! " << fellowVehicleMobility->getExternalId() << " and " << egoVehicleMobility->getExternalId() << ", distance: " << distance << ", fellowVehicleAngle: " << fellowVehicleAngle << ", egoVehicleAngle: " << egoVehicleAngle << std::endl;
                    }
                }
            }else if (!checkOnlyForStoppedVehicles) {   // check for collisions with all fellow vehicles
                /*coordinates*/
                Coord fellowVehicleCoord = fellowVehicleMobility->getPositionAt(simTime());
                Coord egoVehicleCoord = egoVehicleMobility->getPositionAt(simTime());

                /*angles*/
                auto fellowVehicleAngle = fellowVehicleMobility->getAngleRad();
                auto egoVehicleAngle = egoVehicleMobility->getAngleRad();

                /*distance of both vehicles*/
                double distance = std::sqrt((egoVehicleCoord.y - fellowVehicleCoord.y) * (egoVehicleCoord.y - fellowVehicleCoord.y) + (egoVehicleCoord.x - fellowVehicleCoord.x) * (egoVehicleCoord.x - fellowVehicleCoord.x));

                /* check for collisions */
                if (distance < COLLISION_TEST_THRESHOLD) {
                    if (collision(fellowVehicleCoord, egoVehicleCoord, fellowVehicleAngle, egoVehicleAngle) == 1) {
                         EV_INFO <<  simTime() << ": Actual collision!! " << fellowVehicleMobility->getExternalId() << " and " << egoVehicleMobility->getExternalId() << ", distance: " << distance << ", fellowVehicleAngle: " << fellowVehicleAngle << ", egoVehicleAngle: " << egoVehicleAngle << std::endl;
                    }
                }
            }
            // if vehicle is driving close all doors
            if (!fellowVehicleMobility->getVehicleStopState(veins::VehicleStopState::stopped)) {
                if (fellowVehicleMobility->getSignal(veins::VehicleSignal::door_open_left)) {
                    setLeftDoor(*fellowVehicleMobility, CLOSE);
                }
                if (fellowVehicleMobility->getSignal(veins::VehicleSignal::door_open_right)) {
                    setRightDoor(*fellowVehicleMobility, CLOSE);
                }
            }
        }
    }
}

double CollisionManager::valueVec(std::vector<double> v)
{
    double sum = sqrt(v.at(0) * v.at(0) + v.at(1) * v.at(1));
    return sum;
}

std::vector<double> CollisionManager::normalizeVec(std::vector<double> v)
{
    std::vector<double> vnew = {0, 0};
    if (valueVec(v) != 0) {
        vnew.at(0) = (1 / valueVec(v)) * (v.at(0));
        vnew.at(1) = (1 / valueVec(v)) * (v.at(1));
    }
    return vnew;
}

std::vector<double> CollisionManager::computeVertices(std::vector<double> start, std::vector<double> direction, double distance)
{
    std::vector<double> vnew = {0, 0};
    vnew.at(0) = start.at(0) + (direction.at(0) * distance);
    vnew.at(1) = start.at(1) + (direction.at(1) * distance);
    return vnew;
}

std::vector<double> CollisionManager::computePoint(std::vector<double> normal, std::vector<double> start, std::vector<double> direction)
{
    std::vector<double> vnew = {0, 0};
    double a = start.at(1) * direction.at(0) - start.at(0) * direction.at(1);
    double b = direction.at(0) * normal.at(1) - normal.at(0) * direction.at(1);
    // b can never be 0
    double s = a / b;
    vnew.at(0) = s * normal.at(0);
    vnew.at(1) = s * normal.at(1);
    return vnew;
}

std::vector<double> CollisionManager::computeNormal(std::vector<double> direction)
{

    std::vector<double> normal = {0, 0};
    normal.at(0) = direction.at(1);
    normal.at(1) = (-direction.at(0));
    normal = normalizeVec(normal);
    return normal;
}

// TODO: make dynamic --> dependent on sumo network files
const std::vector<std::vector<double>> CollisionManager::getVerticesCar(std::vector<double> n,std::vector<double> d, std::vector<double> coord){
    std::vector<std::vector<double>> vehicle(4);
    vehicle.at(0)=computeVertices(coord,n,0.9);
    vehicle.at(1)=computeVertices(coord,n,-0.9);
    vehicle.at(2)=computeVertices(vehicle.at(0),d,4.3);
    vehicle.at(3)=computeVertices(vehicle.at(1),d,4.3);
    return vehicle;
}

const std::vector<std::vector<double>> CollisionManager::getVerticesBicycle(std::vector<double> n,std::vector<double> d, std::vector<double> coord){
    std::vector<std::vector<double>> vehicle(4);
    vehicle.at(0)=computeVertices(coord,n,0.325);
    vehicle.at(1)=computeVertices(coord,n,-0.325);
    vehicle.at(2)=computeVertices(vehicle.at(0),d,1.6);
    vehicle.at(3)=computeVertices(vehicle.at(1),d,1.6);
    return vehicle;
}

int CollisionManager::collision(Coord c1, Coord c2, Heading ang1, Heading ang2)
{

    // std::regex car_regex("(carflow)(.*)"), bike_regex("(bikeflow)(.*)");
    // coordinates in the middle of the front bumper
    std::vector<double> coord1 = {c1.x, c1.y};
    std::vector<double> coord2 = {c2.x, c2.y};

    // compute direction vectors
    std::vector<double> d1 = { ang1.toCoord().x, ang1.toCoord().y };
    std::vector<double> d2 = { ang2.toCoord().x, ang2.toCoord().y };
    // normal vector to direction vectors
    std::vector<double> n1 = computeNormal(d1);
    std::vector<double> n2 = computeNormal(d2);

    //vertices of vehicle1
    std::vector<std::vector<double>> vertices1=getVerticesCar(n1,d1,coord1);
    //vertices of vehicle2
    std::vector<std::vector<double>> vertices2=getVerticesBicycle(n2,d2,coord2);
    //for the following, let xn1 be left front of vehicle n, xn2 right front of vehicle n, yn1 left back ..., yn2 right back ...(based on driving direction)
    // first vehicle
    std::vector<double> x11=vertices1.at(0);
    std::vector<double> x12=vertices1.at(1);
    std::vector<double> y11=vertices1.at(2);
    std::vector<double> y12=vertices1.at(3);
    // second vehicle
    std::vector<double> x21=vertices2.at(0);
    std::vector<double> x22=vertices2.at(1);
    std::vector<double> y21=vertices2.at(2);
    std::vector<double> y22=vertices2.at(3);

    // save cross points of the different normals to the sides of the vehicles (2 for each) and vertices of the vehicles in two arrays
    // array for projection of vertices
    std::vector<double> vehicle1[4];
    std::vector<double> vehicle2[4];

    // project vertices of figures on normal d1
    vehicle1[0] = computePoint(d1, x11, n1);
    vehicle1[1] = computePoint(d1, x12, n1);
    vehicle1[2] = computePoint(d1, y11, n1);
    vehicle1[3] = computePoint(d1, y12, n1);
    vehicle2[0] = computePoint(d1, x21, n1);
    vehicle2[1] = computePoint(d1, x22, n1);
    vehicle2[2] = computePoint(d1, y21, n1);
    vehicle2[3] = computePoint(d1, y22, n1);

    // Check, if projected vertices of the two polygons are overlapping. If not, return 0.
    if (checkArrays(vehicle1, vehicle2) == 0)
        return 0;

    // project vertices of figures on normal n1
    vehicle1[0] = computePoint(n1, x11, d1);
    vehicle1[1] = computePoint(n1, x12, d1);
    vehicle1[2] = computePoint(n1, y11, d1);
    vehicle1[3] = computePoint(n1, y12, d1);
    vehicle2[0] = computePoint(n1, x21, d1);
    vehicle2[1] = computePoint(n1, x22, d1);
    vehicle2[2] = computePoint(n1, y21, d1);
    vehicle2[3] = computePoint(n1, y22, d1);


    // Check, if projected vertices of the two polygons are overlapping. If not, return 0.
    if (checkArrays(vehicle1, vehicle2) == 0)
        return 0;

    // project vertices of figures on normal n2
    vehicle1[0] = computePoint(n2, x11, d2);
    vehicle1[1] = computePoint(n2, x12, d2);
    vehicle1[2] = computePoint(n2, y11, d2);
    vehicle1[3] = computePoint(n2, y12, d2);
    vehicle2[0] = computePoint(n2, x21, d2);
    vehicle2[1] = computePoint(n2, x22, d2);
    vehicle2[2] = computePoint(n2, y21, d2);
    vehicle2[3] = computePoint(n2, y22, d2);


    // Check, if projected vertices of the two polygons are overlapping. If not, return 0.
    if (checkArrays(vehicle1, vehicle2) == 0)
        return 0;

    // project vertices of figures on normal d2
    vehicle1[0] = computePoint(d2, x11, n2);
    vehicle1[1] = computePoint(d2, x12, n2);
    vehicle1[2] = computePoint(d2, y11, n2);
    vehicle1[3] = computePoint(d2, y12, n2);
    vehicle2[0] = computePoint(d2, x21, n2);
    vehicle2[1] = computePoint(d2, x22, n2);
    vehicle2[2] = computePoint(d2, y21, n2);
    vehicle2[3] = computePoint(d2, y22, n2);

    // Check, if projected vertices of the two polygons are overlapping. If not, return 0.
    if (checkArrays(vehicle1, vehicle2) == 0)
        return 0;

    // if the projected vertices of the two polygons are overlapping, the polygons are overlapping and the objects are colliding
    return 1;
}

int CollisionManager::checkArrays(std::vector<double> array1[], std::vector<double> array2[])
{

    // initialize min and max for both arrays
    double min1x = array1[0].at(0);
    double min1y = array1[0].at(1);
    double max1x = array1[0].at(0);
    double max1y = array1[0].at(1);
    double min2x = array2[0].at(0);
    double min2y = array2[0].at(1);
    double max2x = array2[0].at(0);
    double max2y = array2[0].at(1);

    // find min and max for array1 (min and max based on the x-coordinate (smallest x= minimum), if x's have same value, look at y-coordinates)
    for (int i = 1; i < 4; i++) {
        if ((array1[i].at(0) < min1x) || (array1[i].at(0) == min1x && array1[i].at(1) > min1y)) {
            min1x = array1[i].at(0);
            min1y = array1[i].at(1);
        }
        if ((array1[i].at(0) > max1x) || (array1[i].at(0) == max1x && array1[i].at(1) < max1y)) {
            max1x = array1[i].at(0);
            max1y = array1[i].at(1);
        }
    }
    // find min and max for array2 (min and max based on the x-coordinate (smallest x= minimum), if x's have same value, look at y-coordinates)
    for (int i = 1; i < 4; i++) {
        if ((array2[i].at(0) < min2x) || (array2[i].at(0) == min2x && array2[i].at(1) < min2y)) {
            min2x = array2[i].at(0);
            min2y = array2[i].at(1);
        }
        if ((array2[i].at(0) > max2x) || (array2[i].at(0) == max2x && array2[i].at(1) > max2y)) {
            max2x = array2[i].at(0);
            max2y = array2[i].at(1);
        }
    }

    // min A <= max B && max A >=max B   (A overlaps B: |  B \Overlap| A \)
    if ((min1x < max2x && max1x > max2x) ||
        (min1x == max2x && min1y <= max2y && max1x == max2x && max1y >= max2y) ||
        (min1x == max2x && min1y <= max2y && max1x > max2x) ||
        (min1x < max2x && max1x == max2x && max1y >= max2y)) {
        return 1;
    }
    // min A >= min B && max A<= max B   (A lies in B: |  B \ A \  |)
    if ((min1x > min2x && max1x < max2x) ||
        (min1x == min2x && min1y >= min2y && max1x == max2x && max1y <= max2y) ||
        (min1x == min2x && min1y >= min2y && max1x < max2x) ||
        (min1x > min2x && max1x == max2x && max1y <= max2y)) {
        return 1;
    }
    // min A <= min B && max A >= min B  (B overlaps A: \  A |Overlap\ B |)
    if ((min1x < min2x && max1x > min2x) ||
        (min1x == min2x && min1y <= min2y && max1x == min2x && max1y >= min2y) ||
        (min1x == min2x && min1y <= min2y && max1x > min2x) ||
        (min1x < min2x && max1x == min2x && max1y >= min2y)) {
        return 1;
    }
    // min B => min A && max B<= max A  (B lies in A: \  A | B |  \)
    if ((min2x > min1x && max2x < max1x) ||
        (min2x == min1x && min2y >= min1y && max2x == max1x && max2y <= max1y) ||
        (min2x == min1x && min2y >= min1y && max2x < max1x) ||
        (min2x > min1x && max2x == max1x && max2y <= max1y)) {
        return 1;
    }

    // if there is no overlapping, there is no collision for the given data
    return 0;
}

} // end namespace evi
} // end namespace veins
