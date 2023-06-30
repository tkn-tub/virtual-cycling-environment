// TODO: add license
// Authors:
// Dominik S. Buse <buse@ccs-labs.org>
// Lukas Stratmann <stratmann@ccs-labs.org>

import veins.modules.messages.BaseFrame1609_4;

cplusplus {{
    #include "veins/modules/messages/BaseFrame1609_4_m.h"
    // Container for dummy CAM data

    namespace veins {
    struct CAMData {
        double altitude;
        double latitude;
        double longitude;
        double speed;
        double heading;
        double length;
        double acceleration;
        double yawRate;
        uint32_t stationId;
        int64_t lastSendingTime;
        bool rightDoorOpen;
        bool leftDoorOpen;
    };
    } // namespace veins
}}

namespace veins;

class CAMData {
    @existingClass;
};

packet CAMMessage extends BaseFrame1609_4 {
    CAMData camData;
    string srcmac;
}
