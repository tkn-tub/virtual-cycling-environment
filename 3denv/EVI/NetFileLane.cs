//mostly copied from 3denv/3denv/Assets/Editor/StreetnetworkGenerator/SUMOImporter/NetFileComponents/NetFileLane.cs
//#if (UNITY_EDITOR) 
using System;
using System.Collections.Generic;
using System.Globalization;

namespace extrapolation
{
    public class NetFileLane
    {
        public string id;
        public string allow;
        public string disallow;
        public int index;
        public float speed;
        public float length;
        public float width;
        public List<float[]> shape;
        
        public NetFileLane(string id)
        {
            this.id = id;
        }

        public NetFileLane(string id, int index, float speed, float length, float width, string shape, 
            string allow, string disallow)
        {
            this.id = id;
            this.index = index;
            this.speed = speed;
            this.length = length;
            this.width = width;

            addShapeCoordinates(shape);

            this.allow = allow;
            this.disallow = disallow;
        }

        private void addShapeCoordinates(string shape)
        {
            // Get shape coordinates as List of tuple-arrays
            this.shape = new List<float[]>();

            NumberFormatInfo provider = new NumberFormatInfo();
            provider.NumberDecimalSeparator = ".";

            foreach (string stringPiece in shape.Split(' '))
            {
                float xC = float.Parse(stringPiece.Split(',')[0], provider);
                float yC = float.Parse(stringPiece.Split(',')[1], provider);
                this.shape.Add(new float[] { xC, yC });
            }
        }

        internal void update(int index, float speed, float length, string shape, string allow, string disallow)
        {
            this.index = index;
            this.speed = speed;
            this.length = length;

            addShapeCoordinates(shape);

            this.allow = allow;
            this.disallow = disallow;
        }
    
    }
}
//#endif