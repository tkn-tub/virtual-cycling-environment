//mostly copied from 3denv/3denv/Assets/Editor/StreetnetworkGenerator/SUMOImporter/NetFileComponents/NetFileEdge.cs
//#if (UNITY_EDITOR) 
using System;
using System.Collections.Generic;
//using UnityEngine;

namespace extrapolation
{
    public class NetFileEdge
    {
        string id;
        NetFileJunction from;
        NetFileJunction to;
        int priority;
        List<NetFileLane> lanes;        

        public NetFileEdge(string id, string from, string to, string priority, string shape)
        {
            this.id = id;
            this.priority = Convert.ToInt32(priority);

            this.lanes = new List<NetFileLane>();

            this.from = Extrapolation.junctions[from];
            this.to = Extrapolation.junctions[to];
        }

        public int getPriority()
        {
            return this.priority;
        }

        public void addLane(String id, string index, float speed, float length, float width, string shape, 
            string allow, string disallow)
        {
            NetFileLane lane = Extrapolation.lanes[id];
            lane.update(Convert.ToInt32(index), speed, length, shape, allow, disallow);
            this.lanes.Add(new NetFileLane(id, Convert.ToInt32(index), speed, length, width, shape, allow, disallow));
        }

        public List<NetFileLane> getLanes()
        {
            return this.lanes;
        }

        public NetFileJunction getFrom()
        {
            return this.from;
        }

        public NetFileJunction getTo()
        {
            return this.to;
        }

        public string getId()
        {
            return this.id;
        }
    }
}
//#endif
