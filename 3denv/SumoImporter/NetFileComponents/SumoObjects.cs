using Denv.SumoImporter;
using Godot;
using Source.SUMOImporter.NetFileComponents;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Source.SUMOImporter.NetFileComponents
{
    public struct NetFileJunction
    {
        public string ID { get; }
        public junctionTypeType JunctionType { get; }
        public Vector3 Location { get; }
        public string[] IncLanes { get; }
        public Vector3[] Shape { get; }

        public NetFileJunction(junctionType Junction)
        {
            ID = Junction.id;
            JunctionType = Junction.type;
            Location = new Vector3(Junction.x, Junction.y, Junction.z);
            IncLanes = Junction.incLanes.Split(" ");
            Shape = ImportHelpers.ConvertShapeString(Junction.shape);
        }
    }

    public struct NetFileLane
    {
        public string ID { get; }
        public string Allow { get; }
        public string Disallow { get; }
        public int Index { get; }
        public float Speed { get; }
        public float Length { get; }
        public float Width { get; }
        public Vector3[] Shape { get; }

        public NetFileLane(laneType Lane)
        {
            ID = Lane.id;
            Allow = Lane.allow;
            Disallow = Lane.disallow;
            Index = Convert.ToInt32(Lane.index);
            Speed = Lane.speed;
            Length = Lane.length;
            Width = Lane.width > 0.1f ? Lane.width : 3.2f;
            Shape = ImportHelpers.ConvertShapeString(Lane.shape);        
        }
    }

    public struct NetFileEdge
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
    }

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
