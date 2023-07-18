using System;
using System.Collections.Generic;

namespace Env3d.SumoImporter.NetFileComponents
{
    public class NetFileEdge
    {
        public readonly string ID;
        public NetFileJunction From { get; }
        public NetFileJunction To { get; }
        public int Priority { get; }
        public List<NetFileLane> Lanes { get; }        

        public NetFileEdge(edgeType edge, ref Dictionary<string, NetFileJunction> existingJunctions)
        {
            this.ID = edge.id;
            this.Priority = int.Parse(edge.priority, GameStatics.Provider);

            this.Lanes = new List<NetFileLane>();

            this.From = existingJunctions[edge.from];
            this.To = existingJunctions[edge.to];
        }

        public void AddLane(laneType lane, ref Dictionary<string, NetFileLane> existingLanes)
        {
            this.Lanes.Add(new NetFileLane(lane));
            // existingLanes should already contain all lanes,
            // but they were previously only created from their respective
            // lane index.
            existingLanes[lane.id].Update(lane);
        }
    }
}