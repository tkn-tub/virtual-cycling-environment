//mostly copied from 3denv/3denv/Assets/Editor/StreetnetworkGenerator/SUMOImporter/NetFileComponents/NetFileJunction.cs
//#if (UNITY_EDITOR) 
using System;
using System.Collections.Generic;
using System.Globalization;

namespace extrapolation
{
    public class NetFileJunction
    {
        public string id;
        public junctionTypeType type;
        public float x;
        public float y;
        public float z;

        public List<NetFileLane> incLanes;
        public List<NetFileLane> intLanes;
        public List<float[]> shape;

        public NetFileJunction(string id, junctionTypeType  type, float x, float y, float z, string incLanes, string intLanes, string shape)
        {
            this.id = id;
            this.type = type;
            this.x = x;
            this.y = y;
            this.z = z;

            // Get incoming Lanes
            this.incLanes= new List<NetFileLane>();
            foreach(string stringPiece in incLanes.Split(' '))
            {
                NetFileLane l = new NetFileLane(stringPiece);
                this.incLanes.Add(l);

                // Add to global list
                if(!Extrapolation.lanes.ContainsKey(l.id))
                    Extrapolation.lanes.Add(l.id, l);
            }

            // Get intermediate Lanes
            this.intLanes = new List<NetFileLane>();
            foreach (string stringPiece in intLanes.Split(' '))
            {
                NetFileLane l = new NetFileLane(stringPiece);
                this.intLanes.Add(l);

                // Add to global list
                if (!Extrapolation.lanes.ContainsKey(l.id))
                    Extrapolation.lanes.Add(l.id, l);
            }

            //necessary when the os seperates decimals with , instead of . 
            NumberFormatInfo provider = new NumberFormatInfo();
            provider.NumberDecimalSeparator = ".";

            // Get shape coordinates as List of tuple-arrays
            this.shape = new List<float[]>();
            foreach(string stringPiece in shape.Split(' '))
            {
                float xC = float.Parse(stringPiece.Split(',')[0], provider);
                float yC = float.Parse(stringPiece.Split(',')[1], provider);
                this.shape.Add(new float[] { xC, yC });
            }
        }
        
    }
}
//#endif
