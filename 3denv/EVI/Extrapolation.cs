//TODO: handle yawRate
using System;
using System.Globalization;
using System.Xml.Serialization;
using System.IO;
using Godot;
using System.Collections.Generic;
using System.Diagnostics;

namespace extrapolation
{
	public class Extrapolation
	{
		public static Dictionary<string, NetFileJunction> junctions;
		public static Dictionary<string, NetFileLane> lanes;
		public static Dictionary<string, NetFileEdge> edges;
		static string sumoFilesPath;

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
					NetFileJunction j = new NetFileJunction(junction.id, junction.type, junction.x, junction.y, junction.z,
						junction.incLanes, junction.intLanes, junction.shape);
						//GD.Print(j);

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
					string edge_id = edge.id;
					NetFileEdge e = new NetFileEdge(edge_id, edge.from, edge.to, edge.priority, edge.shape);
					//GD.Print(e);

					// Add to global list
					if (!edges.ContainsKey(edge_id))
						edges.Add(edge_id, e);

	   
					foreach (laneType l in edge.Items)
					{
						// Add all lanes which belong to this edge
						e.addLane(
							l.id,
							l.index,
							l.speed,
							l.length,
							l.width > .1f ? l.width : 3.2f,
							l.shape,
							l.allow,
							l.disallow
						);
					}
				}
			}
		}
		public NetFileLane ComputeLane(Vector3 pos, string edgeId, uint laneNum, double xOffset, double yOffset)
		{
			string laneId = "";
			
			//get all lanes of edge
			List<NetFileLane> lanes = null;
			bool onIntersection = false;
			try
			{
				lanes = Extrapolation.edges[edgeId].getLanes();
			}
			catch (KeyNotFoundException)
			{
				foreach (var j in junctions)
				{
					lanes = junctions[j.Key].incLanes;
					foreach (var jl in lanes)
					{
						if (jl.Equals(edgeId))
							return jl;
			   
					}
				}

			}
			// get lane out of lanes based on lane number
			if (onIntersection == false)
			{
				foreach (var l in lanes)
				{
					string id = l.id;
					if (int.Parse(id[id.Length - 1].ToString()) == laneNum)
					{
						laneId = id;
						return l;
					}

				}
			}
			return null;
		}

		// check if close to an intersection
		public static Boolean CloseToIntersection(Vector3 pos, double speed, string edgeId, uint laneNum, double xOffset, double yOffset)
		{
			//get all lanes of edge
			List<NetFileLane> lanes = null;
			try
			{
				//GD.Print(edges[edgeId]);
				lanes = Extrapolation.edges[edgeId].getLanes();
			}
			catch (ArgumentNullException)
			{
			   return true;
			}
			// get lane out of lanes based on lane number
			foreach (var l in lanes)
			{
				string id = l.id;
				if (int.Parse(id[id.Length - 1].ToString()) == laneNum)
				{
					//veh.lane = l;
				}
					
			}
			// check which intersections road ends in
			NetFileJunction junction = Extrapolation.edges[edgeId].getTo();
				
			Vector3 vJunction = new Vector3(
						(float)(junction.x - xOffset),
						(float)0,
						(float)(junction.y - yOffset));

			float distance = DistanceIntersection(pos, vJunction);

			return IsClose(distance, speed);
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
		public static int TurningLightValue(ForeignVehicleController vehicle)
		{
			//0 no lights, 1 left, 2 right
			if (vehicle.TurnLeftSignalOn)
				return 1;
			else if (vehicle.TurnRightSignalOn)
				return 2;
			else
				return 0;
		}

		public static ForeignVehicleController KeepSpeedAndDirection(ForeignVehicleController veh, double time)
		{
			// get position
			Vector3 position = veh.translation;
			
			//Quat currentRotation = new Quat(veh.rotation).Normalized();
			GD.Print(veh.rotation);
			
			//GD.Print(currentRotation);
			//Vector3 intermediate = rotation.GetEuler();
			float yawRate = veh.rotation.y;
			
			Vector3 vspeed = GetSpeedVector(yawRate - 90, veh.vehicleSpeed);
			// compute position after time of last frame update
			Vector3 result = position + vspeed * ((float)time); //Math.Abs(Node.GetProcessDeltaTime()));
			veh.targetTranslation = result;
			return veh;
		}

		public static ForeignVehicleController KeepSpeedAndStayonStreet(double time, ForeignVehicleController veh, NetFileLane lane, double xOffset, double yOffset)
		{
			Vector3 sumoVehPosition = new Vector3(
				(float)(veh.translation.x+xOffset),
				(float)0,
				(float)(veh.translation.z+yOffset));
			Vector3 vehPosition = veh.translation;
			//Quat currentRotation = new Quat(veh.rotation).Normalized();

			//float yawRate = rotation.GetEuler().y;
			float yawRate = veh.rotation.y;
			Vector3 vspeed = GetSpeedVector(yawRate - 90, veh.vehicleSpeed);
			//Vector3 vspeed = veh.vehicleSpeed;
	
			// get closest point
			Vector3 closestPoint = ClosestPoint(sumoVehPosition, lane.shape, xOffset, yOffset);
			int closestPointIndex = lane.shape.FindIndex(x => (x[0] == closestPoint.x && x[1] == closestPoint.z));

			// get which point defines the current part of the street
			// TODO: auskommentieren?
			float distance = DistanceIntersection(sumoVehPosition, closestPoint);

			int section = VehicleOnSection(lane.shape, sumoVehPosition, closestPointIndex);

			List<Vector3> sectionPoints = new List<Vector3>();
			sectionPoints.Add(new Vector3((float)(lane.shape[section][0]-xOffset),0, (float)(lane.shape[section][1]-yOffset)));
			sectionPoints.Add(new Vector3((float)(lane.shape[section+1][0]-xOffset), 0, (float)(lane.shape[section+1][1]-yOffset)));

			Vector3 streetSection = sectionPoints[1] - sectionPoints[0];

			float angle = vspeed.SignedAngleTo(streetSection, Vector3.Up);
			
			
			yawRate = (yawRate + angle + 360) % 360;
			
			vspeed = GetSpeedVector(yawRate - 90, veh.vehicleSpeed);
			
			// compute position after time of last frame update
			Vector3 result = vehPosition + vspeed * ((float)time); //(Math.Abs(Node.GetProcessDeltaTime()));
			
			veh.targetTranslation = result;
			
			//TODO targetroatation

			return veh;
		}

		private static int VehicleOnSection(List<float[]> shape, Vector3 sumoVehPosition, int closestPointIndex)
		{
			if(closestPointIndex == 0)
			{
				return 0;
			}
			else if(closestPointIndex == shape.Count - 1)
			{
				return shape.Count - 2;
			}
			else
			{
				if(sumoVehPosition.x <= Math.Max(shape[closestPointIndex-1][0],shape[closestPointIndex][0])
					&& sumoVehPosition.x >= Math.Min(shape[closestPointIndex - 1][0], shape[closestPointIndex][0])
					&& sumoVehPosition.z <= Math.Max(shape[closestPointIndex - 1][1], shape[closestPointIndex][1])
					&& sumoVehPosition.z >= Math.Min(shape[closestPointIndex - 1][1], shape[closestPointIndex][1]))
				{
					return closestPointIndex - 1;
				}
				else
				{
					return closestPointIndex;
				}
			}
		   
		}
	
		public static Vector3 ClosestPoint(Vector3 position, List<float[]> shape, double xOffset, double yOffset)
		{
			float smallestDistance=float.PositiveInfinity;
			float distance;
			Vector3 result = new Vector3(
				(float)0,
				(float)0,
				(float)0);
		   
			foreach(var s in shape)
			{
				//compute Distance
				
				Vector3 shapePos = new Vector3(
			   (float)(s[0]),
			   (float)0,
			   (float)(s[1]));
				//UnityEngine.Debug.Log(shapePos);
				distance = DistanceIntersection(position,shapePos);
				//UnityEngine.Debug.Log(distance);
				if (distance < smallestDistance)
				{
					smallestDistance = distance;
					//set result Vector
					result.x =(float)(s[0]);
					result.z =(float)(s[1]);
				}
			}
			return result;
		}

		public static ForeignVehicleController StopAtIntersection(ForeignVehicleController veh)
		{

			if(veh.vehicleSpeed > 0)
			{
				veh.vehicleSpeed = 0;
			}
			return veh;
		}

		private static Vector3 GetSpeedVector(double pYawRate, double pSpeed)
		{
			//MonoBehaviour.print ("YawRate: " + pYawRate + " Speed: " + pSpeed);
			double yawRateRad = Math.PI * pYawRate / 180;
			float speedX = (float)(Math.Cos(yawRateRad) * pSpeed);
			float speedZ = (float)(Math.Sin(yawRateRad) * pSpeed);

			if (yawRateRad >= 0 && yawRateRad <= Math.PI)
			{
				speedZ = -1 * Math.Abs(speedZ);
			}
			else
			{
				speedZ = Math.Abs(speedZ);
			}

			if (yawRateRad >= (Math.PI / 2) && yawRateRad <= ((3 * Math.PI) / 2))
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

