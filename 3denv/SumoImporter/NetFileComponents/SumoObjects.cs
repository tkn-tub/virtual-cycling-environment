using Godot;
using System.Collections.Generic;

namespace Env3d.SumoImporter.NetFileComponents
{
    /*public struct NetFileEdge
    {
        public readonly string ID;
        public string From { get; }
        public string To { get; }
        public int Priority { get; }
        public List<string> Lanes { get; }

        public NetFileEdge(edgeType edge)
        {
            ID = edge.id;
            Priority = Convert.ToInt32(edge.priority);
            Lanes = new List<string>();
            From = edge.from;
            To = edge.to;
        }

        public void AddLane(string Lane)
        {
            Lanes.Add(Lane);
        }
    }*/

    public struct PolygonBaseShape
    {
        public List<Vector3> Vertices { get; }
        public readonly string ID;
        public readonly string PolyType;

        public PolygonBaseShape(string _ID, string _PolyType, List<Vector3> _Vertices)
        {
            ID = _ID;
            PolyType = _PolyType;
            Vertices = _Vertices;

            //make sure array ends with start vertices
            if (Vertices[Count - 1] != Vertices[0])
            {
                Vertices.Add(Vertices[0]);
            }
        }

        public int Count
        {
            get { return Vertices.Count; }
        }

        public Vector3 this[int key]
        {
            get => Vertices[key];
        }

        public void FixOrder()
        {

            //check if shape is counterclockwise
            if (Count > 1)
            {
                double sum = 0;
                for (var i = 0; i < Count; i++)
                {
                    Vector3 v1 = Vertices[i];
                    Vector3 v2 = Vertices[(i + 1) % Count];
                    sum += (v2.x - v1.x) * (v2.z + v1.z);
                }
                if (sum > 0)
                {
                    Vertices.Reverse();
                }
            }
        }
    }
}
