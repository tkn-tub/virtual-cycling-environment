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

#include "veins_evi/Connection.h"

#include <sstream>

namespace veins {
namespace evi {

using message_set = Connection::message_set;

Connection::Connection(uint16_t port, std::string host_iface)
    : port(port)
    , host_iface(std::move(host_iface))
{
    socket.setsockopt(ZMQ_IMMEDIATE, 0);
}

void Connection::bind()
{
    socket.bind(evi_address());
    bound = true;
}

bool Connection::send(const message_set& msgs)
{
    assert(connected);
    bool result = true;
    for (auto it = msgs.begin(); it != msgs.end(); ++it) {
        int flags = ZMQ_DONTWAIT;
        if (it + 1 != msgs.end()) flags |= ZMQ_SNDMORE;
        int bytes_sent = socket.send(it->data(), it->size(), flags);
        if (bytes_sent != it->size()) result = false;
    }
    return result;
}

message_set Connection::recv()
{
    assert(bound);
    zmq::message_t msg;
    message_set result;
    do {
        socket.recv(&msg);
        result.emplace_back(static_cast<char*>(msg.data()), msg.size());
    } while (socket.getsockopt<int>(ZMQ_RCVMORE) == 1);
    connected = true;
    return result;
}

std::string Connection::evi_address() const
{
    std::ostringstream ss;
    ss << "tcp://" << host_iface << ":" << port;
    return ss.str();
}

} // end namespace evi
} // end namespace veins
