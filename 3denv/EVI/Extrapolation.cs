//TODO: handle angle
using System;
using System.Xml.Serialization;
using System.IO;
using Godot;
using System.Collections.Generic;
using Env3d.SumoImporter.NetFileComponents;

namespace Env3d.SumoImporter
{
	public class Extrapolation
	{
		public static Dictionary<string, NetFileJunction> junctions;
		public static Dictionary<string, NetFileLane> lanes;
		public static Dictionary<string, NetFileEdge> edges;
		static string sumoFilesPath;
		public Vector3 _sumoOffset;

		// ParseXMLFiles copied from the ImportAndGenerate.cs
		public static void ParseXmlFiles(string pSumoFilesPath)
		{
			sumoFilesPath = pSumoFilesPath;
			string netFilePath = pSumoFilesPath;
			lanes = new Dictionary<string, NetFileLane>();
			edges = new Dictionary<string, NetFileEdge>();
			junctions = new Dictionary<string, NetFileJunction>();

			netType netFile;
			XmlSerializer serializer = new XmlSerializer(typeof(netType));
			FileStream fs = new FileStream(netFilePath, FileMode.OpenOrCreate);
			TextReader rd = new StreamReader(fs);
			netFile = (netType)serializer.Deserialize(rd);
			rd.Close();
			fs.Close();

			// Get all junctions and preinstantiate lanes
			foreach (junctionType junction in netFile.junction)
			{
				if (junction.type != junctionTypeType.@internal)
				{
					// Only non-internal edges
					NetFileJunction j = new NetFileJunction(junction, ref lanes);

					// Add to global list
					if (!junctions.ContainsKey(junction.id))
						junctions.Add(junction.id, j);
				}
			}

			// Get all edges and complete lane objects
			foreach (edgeType edge in netFile.edge)
			{
				if (!edge.functionSpecified)
				{
					// Only non-internal edges
					NetFileEdge e = new NetFileEdge(edge, ref junctions);
					//GD.Print(e);

					// Add to global list
					if (!edges.ContainsKey(edge.id))
						edges.Add(edge.id, e);
	   
					foreach (laneType l in edge.Items)
					{
						// Add all lanes which belong to this edge
						e.AddLane(l, ref lanes);
					}
				}
			}
		}
		
		public static NetFileLane ComputeLane(VehicleData veh, double xOffset, double yOffset)
		{
			string laneId = "";
			Vector3 vehicle = new Vector3(
				(float)veh.xCoord,
				(float)0,
				(float)veh.yCoord
			);
			//get all lanes of edge
			List<NetFileLane> lanes = null;
			bool onIntersection = false;
			try
			{
				lanes = Extrapolation.edges[veh.edgeId].Lanes;
			}
			catch (KeyNotFoundException)
			{
				foreach (var j in junctions)
				{
					lanes = junctions[j.Key].IncomingLanes;
					foreach (var jl in lanes)
					{
						if (jl.Equals(veh.edgeId))
							return jl;
					}
				}

			}
			// get lane out of lanes based on lane number
			if (onIntersection == false)
			{
				foreach (var l in lanes)
				{
					string id = l.ID;
					if (int.Parse(id[id.Length - 1].ToString()) == veh.laneId)
					{
						laneId = id;
						return l;
					}
				}
			}
			return null;
		}

		// check if close to an intersection
		public static Boolean CloseToIntersection(VehicleData veh, string edgeId, uint laneNum, double xOffset, double yOffset)
		{
			//get all lanes of edge
			List<NetFileLane> lanes = null;
			Vector3 vehicle = new Vector3(
				(float)veh.xCoord,
				(float)0,
				(float)veh.yCoord
			);
			try
			{
				//GD.Print(edges[edgeId]);
				lanes = Extrapolation.edges[edgeId].Lanes;
			}
			catch (Exception ex)
			{
			   if(ex is ArgumentNullException || ex is KeyNotFoundException)
					return true;
			}
			// get lane out of lanes based on lane number
			foreach (var l in lanes)
			{
				string id = l.ID;
				if (int.Parse(id[id.Length - 1].ToString()) == laneNum)
				{
					//veh.lane = l;
				}
					
			}
			// check which intersections road ends in
			NetFileJunction junction = Extrapolation.edges[edgeId].To;
				
			Vector3 vJunction = new Vector3(
				(float)(junction.Location.x - xOffset),
				0f,
				(float)(junction.Location.y - yOffset)
			);

			float distance = DistanceIntersection(vehicle, vJunction);

			return IsClose(distance, veh.speed);
		}

		// get distance
		public static float DistanceIntersection(Vector3 vehicle, Vector3 junction)
		{
			float res = vehicle.DistanceTo(junction);
			if (res < 0)
				res = res * -1;
			return res;
		}

		// is close
		public static Boolean IsClose(float distance, double speed)
		{
			return distance < 7;
		}
		
		// get turning lights value
		public static int TurningLightValue(VehicleData vehicle)
		{
			//0 no lights, 1 left, 2 right
			if (vehicle.turnSignalLeftOn)
				return 1;
			else if (vehicle.turnSignalRightOn)
				return 2;
			else
				return 0;
		}

		public static VehicleData KeepSpeedAndDirection(VehicleData veh, double time, double xOffset, double yOffset)
		{
			Vector3 position = new Vector3(
				(float)(veh.xCoord),
				(float)0,
				(float)(veh.yCoord));
			Vector3 vspeed = GetSpeedVector(veh.angleDeg - 90, veh.speed);
			// Compute position after time of last frame update
			Vector3 result = position + vspeed * ((float)time);
			veh.xCoord = result.x;
			veh.yCoord = result.z;
			return veh;
		}

		
		public static VehicleData KeepSpeedAndStayonStreet(double time, VehicleData veh, NetFileLane lane, double xOffset, double yOffset)
		{
			Vector3 sumoVehPosition = new Vector3(
				(float)(veh.xCoord),
				(float)0,
				(float)(veh.yCoord)
			);

			Vector3[] shape = ComputeLane(
				veh,
				xOffset,
				yOffset
			).Shape;
			
			Vector3 vspeed = GetSpeedVector(veh.angleDeg - 90, veh.speed);
	
			// get closest point
			var (closestPoint, closestPointIndex) = ClosestPoint(sumoVehPosition, shape, xOffset, yOffset);

			// get which point defines the current part of the street
			// TODO: comment out?
			float distance = DistanceIntersection(sumoVehPosition, closestPoint);

			int section = VehicleOnSection(shape, sumoVehPosition, closestPointIndex);

			List<Vector3> sectionPoints = new List<Vector3>();
			sectionPoints.Add(new Vector3((float)(-shape[section].x),0, (float)(shape[section].z)));
			sectionPoints.Add(new Vector3((float)(-shape[section+1].x), 0, (float)(shape[section+1].z)));

			Vector3 streetSection = sectionPoints[1] - sectionPoints[0];

			float angle = vspeed.SignedAngleTo(streetSection, Vector3.Up);
			
			veh.angleDeg = (veh.angleDeg + angle + 360) % 360;
			
			vspeed = GetSpeedVector(veh.angleDeg - 90, veh.speed);
			
			// compute position after time of last frame update
			Vector3 result = sumoVehPosition + vspeed * ((float)time); //(Math.Abs(Node.GetProcessDeltaTime()));
			
			veh.xCoord = result.x;
			veh.yCoord = result.z;

			return veh;
		}

		private static int VehicleOnSection(Vector3[] shape, Vector3 sumoVehPosition, int closestPointIndex)
		{
			if (closestPointIndex == 0)
			{
				return 0;
			}
			else if (closestPointIndex == shape.Length - 1)
			{
				return shape.Length - 2;
			}
			else
			{
				if (
					sumoVehPosition.x <= Math.Max(-shape[closestPointIndex - 1].x, -shape[closestPointIndex].x)
					&& sumoVehPosition.x >= Math.Min(-shape[closestPointIndex - 1].x, -shape[closestPointIndex].x)
					&& sumoVehPosition.z <= Math.Max(shape[closestPointIndex - 1].z, shape[closestPointIndex].z)
					&& sumoVehPosition.z >= Math.Min(shape[closestPointIndex - 1].z, shape[closestPointIndex].z))
				{
					return closestPointIndex - 1;
				}
				else
				{
					return closestPointIndex;
				}
			}
		   
		}
	
		public static (Vector3, int) ClosestPoint(Vector3 position, Vector3[] shape, double xOffset, double yOffset)
		{
			float smallestDistance=float.PositiveInfinity;
			float distance;
			Vector3 result = new Vector3(0, 0, 0);
			int index = -1;
			int i = 0;
		   
			foreach (Vector3 s in shape)
			{
				//compute Distance
				distance = DistanceIntersection(position, s);
				
				if (distance < smallestDistance)
				{
					smallestDistance = distance;
					index = i;
					//set result Vector
					result.x = -s.x;
					result.z = s.z;
				}
				i++;
			}
			return (result, index);
		}

		public static VehicleData StopAtIntersection(VehicleData veh)
		{
			if (veh.speed > 0)
			{
				veh.speed = 0;
			}
			return veh;
		}

		private static Vector3 GetSpeedVector(double pAngleDeg, double pSpeed)
		{
			double angleRad = Math.PI * pAngleDeg / 180;
			
			float speedX = (float)(Math.Cos(angleRad) * pSpeed);
			float speedZ = (float)(Math.Sin(angleRad) * pSpeed);

			if (angleRad >= 0 && angleRad <= Math.PI)
			{
				speedZ = -1 * Math.Abs(speedZ);
			}
			else
			{
				speedZ = Math.Abs(speedZ);
			}

			if (angleRad >= (Math.PI / 2) && angleRad <= ((3 * Math.PI) / 2))
			{
				speedX = -1 * Math.Abs(speedX);
			}
			else
			{
				speedX = Math.Abs(speedX);
			}

			return new Vector3(
				speedX,
				0.0f,
				speedZ
			);
		}
	}
}
