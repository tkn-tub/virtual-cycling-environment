using Godot;

namespace Env3d.SumoImporter.NetFileComponents
{
    public class NetFileLane
    {
        public string ID {get; }
        public string Allow {get; private set;}
        public string Disallow {get; private set;}
        public int Index {get; private set;}
        public float Speed {get; private set;}
        public float Length {get; private set;}
        public float Width {get; private set;}
        public Vector3[] Shape {get; private set;}
        
        public NetFileLane(string id)
        {
            this.ID = id;
        }

        public NetFileLane(laneType lane)
        {
            this.ID = lane.id;
            this.Index = int.Parse(lane.index, GameStatics.Provider);
            this.Speed = lane.speed;
            this.Length = lane.length;
            this.Width = lane.width > .1f ? lane.width : 3.2f;
            this.Allow = lane.allow;
            this.Disallow = lane.disallow;
            this.Shape = ImportHelpers.ConvertShapeString(lane.shape);
        }

        // Sometimes we only get the lane ID as a string and have to update later
        public void Update(laneType lane)
        {
            this.Index = int.Parse(lane.index, GameStatics.Provider);
            this.Speed = lane.speed;
            this.Length = lane.length;
            this.Width = lane.width > .1f ? lane.width : 3.2f;
            this.Allow = lane.allow;
            this.Disallow = lane.disallow;
            this.Shape = ImportHelpers.ConvertShapeString(lane.shape);
        }
    }
}