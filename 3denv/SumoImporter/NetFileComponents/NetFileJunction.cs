using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;

namespace Env3d.SumoImporter.NetFileComponents
{
	public class NetFileJunction
	{
		public string ID { get; }
		public junctionTypeType JunctionType { get; }
		public Vector3 Location { get; }
		public List<NetFileLane> IncomingLanes { get; }
		public List<NetFileLane> InternalLanes { get; }
		public Vector3[] Shape { get; }

		public NetFileJunction(junctionType Junction, ref Dictionary<string, NetFileLane> existingLanes)
		{
			GD.Print($"Junction.xyz = \"{Junction.x}\", \"{Junction.y}\", \"{Junction.z}\"");
			this.ID = Junction.id;
			this.JunctionType = Junction.type;
			this.Location = new Vector3(
				float.Parse(Junction.x, GameStatics.Provider),
				float.Parse(Junction.y, GameStatics.Provider),
				float.Parse(Junction.z ?? "0", GameStatics.Provider)
			);

			// Get incoming Lanes
			this.IncomingLanes= new List<NetFileLane>();
			foreach(string stringPiece in Junction.incLanes.Split(' '))
			{
				NetFileLane l = new NetFileLane(stringPiece);
				this.IncomingLanes.Add(l);

				// Add to global list
				if(!existingLanes.ContainsKey(l.ID))
					existingLanes.Add(l.ID, l);
			}

			// Get internal Lanes
			this.InternalLanes = new List<NetFileLane>();
			foreach (string stringPiece in Junction.intLanes.Split(' '))
			{
				NetFileLane l = new NetFileLane(stringPiece);
				this.InternalLanes.Add(l);

				// Add to global list
				if (!existingLanes.ContainsKey(l.ID))
					existingLanes.Add(l.ID, l);
			}

			// necessary when the os seperates decimals with , instead of . 
			NumberFormatInfo provider = new NumberFormatInfo();
			provider.NumberDecimalSeparator = ".";

			// Get shape coordinates as List of tuple-arrays
			this.Shape = ImportHelpers.ConvertShapeString(Junction.shape);
		}
		
	}
}
