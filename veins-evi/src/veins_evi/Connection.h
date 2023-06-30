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

#ifndef __VEINS_EVI_CONNECTION_H
#define __VEINS_EVI_CONNECTION_H

#include <zmq.hpp>
#include <string>
#include <vector>

namespace veins {
namespace evi {

/**
 * Socket-Like connection abstraction to exchange frames of bytes with an EVI.
 *
 * Intended to hide all zmq interactions.
 */
class Connection {
    // NOTE: if we need more than one connection, we need to share the zmq context in some sane location
public:
    using message_set = std::vector<std::string>;

    Connection(uint16_t port, std::string host_iface = "0.0.0.0");
    /**
     * establish port for ego vehicle interface to connect to
     */
    void bind();
    /**
     * return whether the connection has an open port bound
     */
    bool is_bound() const
    {
        return bound;
    }
    /**
     * return whether the connection to the ego vehicle interface is established
     */
    bool is_connnected() const
    {
        return connected;
    }
    /**
     * send a plain zmq message containing msg
     */
    bool send(const message_set& msgs);
    /**
     * receive message (blocking) and return contents
     */
    message_set recv();
    /*
     * return the ZMQ adress string this connects to
     */
    std::string evi_address() const;

private:
    const uint16_t port;
    const std::string host_iface;
    zmq::context_t context{1}; // Note: this member *has* to be declared before all zmq socket members!
    zmq::socket_t socket{context, ZMQ_REP};
    bool connected = false;
    bool bound = false;
}; // end class Connection

} // end namespace evi
} // end namespace veins

#endif
