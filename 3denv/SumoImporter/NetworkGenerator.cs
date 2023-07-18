using Godot;
using System;
using Env3d.SumoImporter.NetFileComponents;
using System.Collections.Generic;
using Env3d.SumoImporter;
using static Godot.GeometryInstance;

/// <summary>
/// Class which generates all environment objects from given SUMO files
/// </summary>
public class NetworkGenerator : Spatial
{
	private readonly Material streetMaterial =  ResourceLoader.Load<Material>("Environment/Materials/M_Street.tres");
	private readonly Material intersectionMaterial =  ResourceLoader.Load<Material>("Environment/Materials/M_Intersection.tres");
	private readonly Material grasMaterial =  ResourceLoader.Load<Material>("Environment/Materials/M_Gras.tres");

	private readonly Mesh StreetLight = ResourceLoader.Load<Mesh>("Environment/StreetLight/StreetLight_Type2.mesh");

	private readonly PackedScene TrafficLightScene = ResourceLoader.Load<PackedScene>(GameStatics.TrafficLightPath);
	private readonly PackedScene DynamicBuildingResource = ResourceLoader.Load<PackedScene>(GameStatics.DynamicBuildingtPath);

	private Random random  = new (GameStatics.DefaultSeed);


	private readonly PackedScene SignNoEntry = ResourceLoader.Load<PackedScene>(GameStatics.NoEntrySignPath);
	private readonly PackedScene SignNoLeftTrun = ResourceLoader.Load<PackedScene>(GameStatics.NoLeftTurnPath);
	private readonly PackedScene SignNoRightTurn = ResourceLoader.Load<PackedScene>(GameStatics.NoRightTurnPath);
	private readonly PackedScene SignNoStraightOn = ResourceLoader.Load<PackedScene>(GameStatics.NoStraightOnPath);
	private readonly PackedScene SignOneWayLeft = ResourceLoader.Load<PackedScene>(GameStatics.OneWayLeftPath);
	private readonly PackedScene SignOneWayRight = ResourceLoader.Load<PackedScene>(GameStatics.OneWayRightPath);
	private readonly PackedScene SignOnlyLeftTurn = ResourceLoader.Load<PackedScene>(GameStatics.OnlyLeftTurnPath);
	private readonly PackedScene SignOnlyRightTurn = ResourceLoader.Load<PackedScene>(GameStatics.OnlyRightTurnPath);
	private readonly PackedScene SignPriority = ResourceLoader.Load<PackedScene>(GameStatics.PriorityPath);
	private readonly PackedScene SignSpeedLimit50 = ResourceLoader.Load<PackedScene>(GameStatics.SpeedLimit50Path);
	private readonly PackedScene SignSpeedLimit30 = ResourceLoader.Load<PackedScene>(GameStatics.SpeedLimit30Path);
	private readonly PackedScene SignStop = ResourceLoader.Load<PackedScene>(GameStatics.StopPath);
	private readonly PackedScene SignYield = ResourceLoader.Load<PackedScene>(GameStatics.YieldPath);



	public Vector3 SumoOffset { get; private set; }
	public string NetOffset { get; private set; }
	public string ProjParameters { get; private set; }
	public override void _Ready()
	{
	}

	/// <summary>
	/// Call to load and generate a new Environment form SUMO files
	/// When calling this methode the old environment is removed and a new one is generated as children of this object
	/// </summary>
	/// <param name="NetFilePath">Path to the sumo.net.xml file (net file) other files like the poly file are expected to in the same location</param>
	/// <param name="Seed">Seed for random generation</param>
	/// <param name="GenerateStreetLights">Add street lights indendet of the poly file</param>
	public void LoadNetwork(string NetFilePath, int Seed = GameStatics.DefaultSeed, bool GenerateStreetLights = true)
	{
		random = new Random(Seed);

		//Clear previously generated environments
		foreach (System.Object child in GetChildren())
		{
			((Spatial)child).QueueFree();
		}

		if (!System.IO.File.Exists(NetFilePath))
		{
			GD.PushWarning(
				$"Selected file not found: {NetFilePath}"
				+ "Make sure the scenario is on the same drive as the game."
			);
			return;
		}

		string baseFilePath = NetFilePath.Remove(NetFilePath.Length - ".net.xml".Length, ".net.xml".Length);
		string shapesFilePath = baseFilePath + ".poly.xml";
		string playerRoutePath = baseFilePath + ".path";


		netType netFile = ImportHelpers.LoadXMLFile<netType>(NetFilePath);
		// Get map boundaries
		string[] boundaries = netFile.location.convBoundary.Split(',');
		float xMax = -float.Parse(boundaries[0], GameStatics.Provider);
		float yMin = float.Parse(boundaries[1], GameStatics.Provider);
		float xMin = -float.Parse(boundaries[2], GameStatics.Provider);
		float yMax = float.Parse(boundaries[3], GameStatics.Provider);

		SumoOffset = new Vector3((xMax + xMin) / 2.0f, 0, (yMin + yMax) / 2.0f);

		ProjParameters = netFile.location.projParameter;
		NetOffset = netFile.location.netOffset;

		Dictionary<string, List<connectionType>> connections;
		Dictionary<string, NetFileJunction> junctions;
		Dictionary<string, NetFileEdge> edges;
		Dictionary<string, NetFileLane> lanes;
		LoadNetFile(netFile, out connections, out junctions, out edges, out lanes);

		AddLandscape(yMin, xMin, yMax, xMax);
		AddJunctions(junctions);

		foreach (NetFileEdge netFileEdge in edges.Values)
		{
			NetFileJunction junctionTo = netFileEdge.To;
			NetFileJunction junctionFrom = netFileEdge.From;
			AddTrafficLights(netFileEdge, junctionTo, lanes, connections);

			foreach (NetFileLane lane in netFileEdge.Lanes)
			{
				AddLane(lane, junctionTo, junctionFrom);
			}

			if (GenerateStreetLights)
			{
				NetFileLane netFileLane = netFileEdge.Lanes[0];
				AddStreetLights(netFileLane);
			}
		}

		LoadAndGenerateEnvironment(shapesFilePath);
	}

	private void AddStreetLights(NetFileLane netFileLane)
	{
		if (netFileLane.Length < 2.0f)
			return;

		int streetLightCount = 0;
		float streetLightSpace = 25.0f;
		int numberOfLights = Mathf.FloorToInt(netFileLane.Length / streetLightSpace);

		float distanceToNext = (netFileLane.Length - (numberOfLights * streetLightSpace)) / 2.0f;
		numberOfLights++;

		MultiMesh streetLights = new MultiMesh();
		streetLights.Mesh = StreetLight;
		streetLights.TransformFormat = MultiMesh.TransformFormatEnum.Transform3d;
		streetLights.InstanceCount = numberOfLights;

		MultiMeshInstance mmi = new MultiMeshInstance();
		mmi.Multimesh = streetLights;


		for (int i = 1; i < netFileLane.Shape.Length; i++)
		{
			Vector3 startPoint = netFileLane.Shape[i - 1];
			Vector3 endPoint = netFileLane.Shape[i];

			Vector3 direction = endPoint - startPoint;
			float length = direction.Length();
			direction /= length;

			float currentLength = 0;

			while(currentLength + distanceToNext <= length)
			{
				currentLength += distanceToNext;
				distanceToNext = streetLightSpace;

				Vector3 orign = startPoint + direction * currentLength + direction.Cross(Vector3.Up).Normalized() * 3.5f;
				Quat rotation = new Quat(Vector3.Up, Mathf.Atan2(-direction.z, direction.x) + GameStatics.Rad90);

				Transform instanceTransform = new Transform(rotation, orign);
				mmi.Multimesh.SetInstanceTransform(streetLightCount++, instanceTransform);
			}

			distanceToNext -= (length - currentLength);
		}

		AddChild(mmi);
	}

	private void LoadNetFile(
		netType netFile,
		out Dictionary<string, List<connectionType>> connections, 
		out Dictionary<string, NetFileJunction> junctions, 
		out Dictionary<string, NetFileEdge> edges, 
		out Dictionary<string, NetFileLane> lanes
	){
		connections = new Dictionary<string, List<connectionType>>();
		junctions = new Dictionary<string, NetFileJunction>();
		edges = new Dictionary<string, NetFileEdge>();
		lanes = new Dictionary<string, NetFileLane>();

		// Get all junctions
		foreach (junctionType junction in netFile.junction)
		{
			//only generate junctions which are connected to lanes and are not internal
			if (junction.type != junctionTypeType.@internal && junction.incLanes != "")
			{	
				NetFileJunction newJunction = new NetFileJunction(junction, ref lanes);
				junctions.Add(junction.id, newJunction);
			}
		}

		// Get all edges and lane objects
		foreach (edgeType edge in netFile.edge)
		{
			// Only non-internal edges
			if (edge.functionSpecified)
			{
				continue;
			}

			NetFileEdge newEdge = new NetFileEdge(edge, ref junctions);

			foreach (laneType lane in edge.Items)
			{
				// Add all lanes which belong to this edge
				// lanes.Add(lane.id, new NetFileLane(lane));
				newEdge.AddLane(lane, ref lanes);
			}

			// Add to global list
			edges.Add(newEdge.ID, newEdge);
		}

		// Get all connections in order to visualize traffic lights correctly
		foreach (connectionType ct in netFile.connection)
		{
			// ct.viaField is junctionId + internal lanes
			if (ct.via is null && ct.fromLane is null)
			{
				continue;	
			}

			NetFileEdge fromEdge;
			if (!edges.TryGetValue(ct.from, out fromEdge))
			{
				continue;
			}

			string fromLane = fromEdge.Lanes[int.Parse(ct.fromLane)].ID;
			if (connections.ContainsKey(fromLane))
			{
				connections[fromLane].Add(ct);
			}
			else
			{
				List<connectionType> connectionTypes = new List<connectionType>();
				connectionTypes.Add(ct);
				connections.Add(fromLane, connectionTypes);
			}
		}
	}

	private void AddJunctions(in Dictionary<string, NetFileJunction> junctions)
	{
		//Draw all Junction areas
		foreach (NetFileJunction junction in junctions.Values)
		{
			Vector3[] vertices = junction.Shape;
			if (vertices.Length < 3) //Check if the junction has enough points to build at least on triangle
			{
				continue;
			}

			int[] triangles;
			// Use the triangulator to get indices for creating triangles
			if (vertices.Length == 3)
			{
				triangles = new int[vertices.Length];
				triangles[0] = 0;
				triangles[1] = 1;
				triangles[2] = 2;
			}
			else
			{
				triangles = Triangulator.Triangulate(vertices);
			}

			Vector2[] uvs = new Vector2[vertices.Length];
			float textureScale = 1;// .35f; // How often to repeat the texture per meter.
			for (int i = 0; i < vertices.Length; i++)
			{
				uvs[i] = new Vector2(vertices[i].x * textureScale, vertices[i].z * textureScale);
			}

			Vector3[] normals;
			float[] tangents;
			ImportHelpers.CalculateNormals(vertices, triangles, uvs, out normals, out tangents);
			ImportHelpers.AddMesh(this, vertices, normals, triangles, tangents, uvs, intersectionMaterial, castShadow: ShadowCastingSetting.Off);

		}
	}


	private void AddLandscape(float yMin, float xMin, float yMax, float xMax)
	{
		Vector3[] vertices = new Vector3[4];
		Vector2[] uvs = new Vector2[4];
		int[] triangles = new int[6];

		vertices[0] = new Vector3(xMax, -0.01f, yMax) - SumoOffset;
		vertices[1] = new Vector3(xMax, -0.01f, yMin) - SumoOffset;
		vertices[2] = new Vector3(xMin, -0.01f, yMin) - SumoOffset;
		vertices[3] = new Vector3(xMin, -0.01f, yMax) - SumoOffset;

		//make landscape a little bit large then sumo file defines
		vertices[0] += vertices[0].Normalized() * 100.0f;
		vertices[1] += vertices[1].Normalized() * 100.0f;
		vertices[2] += vertices[2].Normalized() * 100.0f;
		vertices[3] += vertices[3].Normalized() * 100.0f;


		uvs[0] = new Vector2(0, 0);
		uvs[1] = new Vector2(0, yMax - yMin) / 2.0f;
		uvs[2] = new Vector2(xMax - xMin, yMax - yMin) / 2.0f;
		uvs[3] = new Vector2(xMax - xMin, 0) / 2.0f;

		triangles[0] = 1;
		triangles[1] = 0;
		triangles[2] = 2;
		triangles[3] = 2;
		triangles[4] = 0;
		triangles[5] = 3;

		Vector3[] normals;
		float[] tangents;
		ImportHelpers.CalculateNormals(vertices, triangles, uvs, out normals, out tangents);
		ImportHelpers.AddMesh(this, vertices, normals, triangles, tangents, uvs, grasMaterial, castShadow: ShadowCastingSetting.Off);
	}


	private void AddTrafficLights(in NetFileEdge netFileEdge, in NetFileJunction junction, in Dictionary<string, NetFileLane> lanes, in Dictionary<string, List<connectionType>> connections)
	{
		bool edgeHasTrafficLight = junction.JunctionType == junctionTypeType.traffic_light;

		if (!edgeHasTrafficLight)
		{
			return;
		}

		int edgeLaneCount = netFileEdge.Lanes.Count;

		Vector3 lanesCenter = Vector3.Zero;
		float laneCenterWidth = 0;
		Vector3 laneCenterDirection = Vector3.Zero;

		List<NetFileLane> edgeLanes = new List<NetFileLane>();

		//Spawn traffic lights
		for (int i = 0; i < edgeLaneCount; i++)
		{
			NetFileLane lane = netFileEdge.Lanes[i];
			edgeLanes.Add(lane);

			// Calculate the position (in line with the lane) coordinates of last two street vertices
			Vector3 preLaneEndPoint = lane.Shape[lane.Shape.Length - 2];
			Vector3 laneEndPoint = lane.Shape[lane.Shape.Length - 1];

			lanesCenter += laneEndPoint;
			laneCenterWidth += lane.Width;
			laneCenterDirection += (laneEndPoint - preLaneEndPoint).Normalized();
		}


		lanesCenter /= edgeLaneCount;
		laneCenterWidth = laneCenterWidth * 0.5f + 1.0f;
		laneCenterDirection /= edgeLaneCount;

		float angle = Mathf.Atan2(laneCenterDirection.x, laneCenterDirection.z);

		laneCenterDirection = laneCenterDirection.Cross(Vector3.Up);
		laneCenterDirection = laneCenterDirection.Normalized();

		Vector3 trafficLightPosition = lanesCenter + laneCenterDirection * laneCenterWidth;

		TrafficLight trafficLightInstance = TrafficLightScene.Instance<TrafficLight>();
		trafficLightInstance.Translation = trafficLightPosition;
		trafficLightInstance.Rotation = new Vector3(0f, angle, 0f);
		AddChild(trafficLightInstance, true);

		edgeLanes.Sort((x, y) => (x.Shape[x.Shape.Length - 1] - trafficLightPosition).LengthSquared().CompareTo((y.Shape[y.Shape.Length - 1] - trafficLightPosition).LengthSquared()));



		for (int i = 0; i < edgeLaneCount; i++)
		{
			NetFileLane lane = edgeLanes[i];
			int laneIndexInJunction = 0;
			for (int laneCount = 0; laneCount < junction.IncomingLanes.Count; laneCount++)
			{
				NetFileLane incLane = junction.IncomingLanes[laneCount];
				if (lane.ID == incLane.ID)
				{
					break;
				}
				else
				{
					List<connectionType> incLanesConnections;
					if (connections.TryGetValue(incLane.ID, out incLanesConnections))
					{
						laneIndexInJunction += incLanesConnections.Count;
					}
				}
			}


			trafficLightInstance.AddPoolExtension(i);

			List<connectionType> lct;
			if (connections.TryGetValue(lane.ID, out lct))
			{
				int totalPanels = lct.Count;
				for (int currentPanelIndex = 0; currentPanelIndex < totalPanels; currentPanelIndex++)
				{
					connectionType ct = lct[currentPanelIndex];
					if ((ct.tl == null) || string.Compare((ct.@from + "_" + ct.fromLane), lane.ID, StringComparison.OrdinalIgnoreCase) != 0)
					{
						continue;
					}

					string tlID = "tl_" + MD5Hasher.getMD5(junction.ID) + "_" + laneIndexInJunction++;
					trafficLightInstance.AddPanel(tlID, i, currentPanelIndex, totalPanels, ct.dir);

				}
			}
		}
	}

	private void AddLane(in NetFileLane lane, in NetFileJunction junctionTo, in NetFileJunction junctionFrom)
	{
		float laneWidthPadding = 0.0f;
		float laneWidth = lane.Width * 0.5f + laneWidthPadding;
		
		Vector3[] laneShape = lane.Shape;
		if (laneShape.Length < 2)
		{
			GD.PushWarning($"Lane {lane.ID} has less than 2 vertices.");
			return;
		}

		Vector3[] vertices = new Vector3[laneShape.Length * 2];
		Vector2[] uvs = new Vector2[vertices.Length];

		int[] triangles = new int[(laneShape.Length - 1) * 2 * 3];
		//add start points
		AddLaneEnds(junctionFrom, laneShape[0], laneShape[1], laneWidth, true, ref vertices);

		triangles[0] = 1;
		triangles[1] = 0;
		triangles[2] = 2;
		triangles[3] = 1;
		triangles[4] = 2;
		triangles[5] = 3;


		//Build road between start and end
		for (int i = 1; i < laneShape.Length - 1; i++)
		{
			triangles[i * 6] = i * 2 + 1;
			triangles[i * 6 + 1] = i * 2;
			triangles[i * 6 + 2] = i * 2 + 2;
			triangles[i * 6 + 3] = i * 2 + 1;
			triangles[i * 6 + 4] = i * 2 + 2;
			triangles[i * 6 + 5] = i * 2 + 3;

			Vector3 lastDirection = laneShape[i - 1] - laneShape[i];
			Vector3 nextDirection = laneShape[i + 1] - laneShape[i];

			float lastLength = lastDirection.Length();
			float nextLength = nextDirection.Length();

			float lastFactor = 1, nextFactor = 1;

			if (nextLength > lastLength)
			{
				nextFactor = lastLength / nextLength;
			}
			else
			{
				lastFactor = nextLength / lastLength;
			}

			Vector3 direction =  lastDirection * lastFactor - nextFactor * nextDirection;
			Vector3 rightVector = direction.Cross(Vector3.Up).Normalized() * laneWidth;

			vertices[i * 2] = ImportHelpers.LineIntersection2D(vertices[(i - 1) * 2], lastDirection, laneShape[i], rightVector);
			vertices[i * 2 + 1] = ImportHelpers.LineIntersection2D(vertices[(i - 1) * 2 + 1], lastDirection, laneShape[i], rightVector);

		}

		//Add End Points
		AddLaneEnds(junctionTo, laneShape[laneShape.Length - 1], laneShape[laneShape.Length - 2], laneWidth, false, ref vertices);


		float distanceLeft = 0;
		float distanceRight = 0;
		for (int i = 0; i < uvs.Length; i += 2)	
		{
			if (i >= 2)
			{
				distanceLeft += (vertices[i] - vertices[i - 2]).Length() / lane.Width;
				distanceRight += (vertices[i+1] - vertices[i - 1]).Length() / lane.Width;
			}
			uvs[i] = new Vector2(0, distanceLeft);
			uvs[i+1] = new Vector2(1, distanceRight);
		}

		Vector3[] normals;
		float[] tangents;
		ImportHelpers.CalculateNormals(vertices, triangles, uvs, out normals, out tangents);
		ImportHelpers.AddMesh(this, vertices, normals, triangles, tangents, uvs, streetMaterial, castShadow: ShadowCastingSetting.Off);
	}
	
	/// <summary>
	/// Used to add the start and end vertices of a lane to the given vertices array.
	/// Alligns the end correctly with the connecting junction
	/// </summary>
	/// <param name="junction"></param>
	/// <param name="shapePoint1"></param>
	/// <param name="shapePoint2"></param>
	/// <param name="laneWidth"></param>
	/// <param name="bIsStart"></param>
	/// <param name="vertices"></param>
	private void AddLaneEnds(in NetFileJunction junction, Vector3 shapePoint1, Vector3 shapePoint2, float laneWidth, bool bIsStart, ref Vector3[] vertices)
	{
		int shapeLength = junction.Shape.Length;
		int bestIndex = 0;
		Vector3 junctionIntersection = Vector3.Zero;

		float bestDistance = float.MaxValue;

		for (int i = 0; i < shapeLength; i++)
		{
			Vector3 testPoint;
			bool isInSegment = ImportHelpers.ClosestPointOnSegment(shapePoint1, junction.Shape[i], junction.Shape[(i + 1) % shapeLength], out testPoint);
			float distanceSq = (testPoint - shapePoint1).LengthSquared();
			if (distanceSq < bestDistance)
			{
				bestIndex = i;
				bestDistance = distanceSq;

				
				junctionIntersection = isInSegment ? testPoint : shapePoint1;
				
			}
		}

		Vector3 rightVector = (junction.Shape[bestIndex] - junction.Shape[(bestIndex + 1) % shapeLength]).Normalized() * laneWidth;

		Vector3 fDirection = (shapePoint1 - shapePoint2).Cross(Vector3.Up);

		rightVector = rightVector.Abs() * fDirection.Sign();
		

		vertices[bIsStart ? 0 : vertices.Length - 1] = junctionIntersection + rightVector;
		vertices[bIsStart ? 1 : vertices.Length - 2] = junctionIntersection - rightVector;
	}

	/// <summary>
	/// Load the poly file which is in the same location as the specified net file
	/// </summary>
	/// <param name="shapesFilePath">Poly file path</param>
	private void LoadAndGenerateEnvironment(string shapesFilePath)
	{
		if (!System.IO.File.Exists(shapesFilePath))
		{
			GD.Print("No poly.xml file found");
			return;
		}

		additionalType additional = ImportHelpers.LoadXMLFile<additionalType>(shapesFilePath);

		if (additional is null)
		{
			GD.Print("poly.xml is invalid.");
			return;
		}

		int invalidTypesCount = 0;
		foreach (object item in additional.Items)
		{
			switch (item)
			{
				case polygonType p:
					AddPolygonType(p);
					break;

				case poiType p:
					AddPOI(p);
					break;

				case parkingAreaType p:
					break;

				default:
					invalidTypesCount++;
					break;
			}
		}

		if (invalidTypesCount > 0)
		{
			GD.Print(invalidTypesCount + " Objects cound not be created.");
		}
	}

	private void AddPolygonType(polygonType p)
	{
		switch(p.type.ToLower())
		{
			case "building":
				DynamicBuilding newBuilding = DynamicBuildingResource.Instance<DynamicBuilding>();
				newBuilding.CreateBuilding(p, random.Next(int.MaxValue));
				AddChild(newBuilding, true);
				break;
		}
	}

	/// <summary>
	/// Spawn a tree at the given position
	/// TODO
	/// </summary>
	/// <param name="Position">Tree position</param>
	private void SpawnTree(Vector3 Position)
	{
		//Old unity code
		//GameObject treePrefab = AssetDatabase.LoadMainAssetAtPath(PathConstants.tree) as GameObject;
		//GameObject tree = GameObject.Instantiate(treePrefab);
		//tree.transform.position = new Vector3(v.x - xmin, 0, v.y - ymin);
		//tree.name = "Tree" + v.x.ToString();
		//tree.transform.rotation = Quaternion.Euler(0.0f, UnityEngine.Random.Range(0, 360), 0.0f);
		//float uniformScale = UnityEngine.Random.Range(0.7f, 1.0f);
		//tree.transform.localScale = new Vector3(uniformScale, uniformScale, uniformScale);
		//tree.transform.SetParent(Trees.transform);
	}

	private void AddPOI(poiType poi)
	{
		if (string.Compare(poi.type, "Psych_Trial", StringComparison.OrdinalIgnoreCase) == 0)
		{
			//psychTrialPois.Add(poi.id, poi);
		}
		else if (poi.type.StartsWith("StreetSign_", StringComparison.OrdinalIgnoreCase))
		{
			SpawnStreetSign(poi);
		}
		else if (string.Compare(poi.type, "tree", StringComparison.OrdinalIgnoreCase) == 0)
		{
			SpawnTree(
				new Vector3(
					-float.Parse(poi.x, GameStatics.Provider),
					0.0f,
					float.Parse(poi.y, GameStatics.Provider)
				) - SumoOffset
			);
		}
		else if (string.Compare(poi.type, "EgoVehicleStart", StringComparison.OrdinalIgnoreCase) == 0)
		{
			Transform egoStartTransform = new Transform(
				new Quat(Vector3.Up, Mathf.Deg2Rad(float.Parse(poi.angle ?? "0", GameStatics.Provider))),
				new Vector3(
					-float.Parse(poi.x, GameStatics.Provider),
					0,
					float.Parse(poi.y, GameStatics.Provider)
				) - SumoOffset
			);
			GameStatics.GameInstance.UpdatePlayerStartPosition(egoStartTransform);
		}
		else if (string.Compare(poi.type, "EndOfLevel", StringComparison.OrdinalIgnoreCase) == 0)
		{
			//endOfLevelPois.Add(poi.id, poi);
		}
		else if (string.Compare(poi.type, "TutorialBanner",
					 StringComparison.OrdinalIgnoreCase) == 0)
		{
			//tutorialBannerPois.Add(poi.id, poi);
		}
		else
		{
			GD.Print(string.Format("{0} is not a supported poi type!", poi.type));
		}

	}

	private void SpawnStreetSign(poiType poi)
	{
		Spatial signObj;

		switch (poi.type.ToLower())
		{
			case "streetsign_yield":
				signObj = SignYield.Instance<Spatial>();
				break;

			case "streetsign_priority":
				signObj = SignPriority.Instance<Spatial>();
				break;
			case "streetsign_stop":
				signObj = SignStop.Instance<Spatial>();
				break;

			case "streetsign_no_entry":
				signObj = SignNoEntry.Instance<Spatial>();
				break;

			case "streetsign_no_left_turn":
				signObj = SignNoLeftTrun.Instance<Spatial>();
				break;
				
			case "streetsign_no_right_turn":
				signObj = SignNoRightTurn.Instance<Spatial>();
				break;

			case "streetsign_no_straight_on":
				signObj = SignNoStraightOn.Instance<Spatial>();
				break;

			case "streetsign_oneway_left":
				signObj = SignOneWayLeft.Instance<Spatial>();
				break;

			case "streetsign_oneway_right":
				signObj = SignOneWayRight.Instance<Spatial>();
				break;

			case "streetsign_only_left_turn":
				signObj = SignOnlyLeftTurn.Instance<Spatial>();
				break;

			case "streetsign_only_right_turn":
				signObj = SignOnlyRightTurn.Instance<Spatial>();
				break;

			case "streetsign_speed_limit_30":
				signObj = SignSpeedLimit30.Instance<Spatial>();
				break;

			case "streetsign_speed_limit_50":
				signObj = SignSpeedLimit50.Instance<Spatial>();
				break;

			default:
				GD.Print(string.Format("Visualisation of street signs of type {0} is not yet implemented.", poi.type));
				return;
		}
		

		signObj.Transform = new Transform(
			new Quat(
				Vector3.Up,
				Mathf.Deg2Rad(-float.Parse(poi.angle, GameStatics.Provider) - 90.0f)
			),
			new Vector3(
				-float.Parse(poi.x, GameStatics.Provider),
				0,
				float.Parse(poi.y, GameStatics.Provider)
			) - SumoOffset
		);
		signObj.Name = poi.id;
		AddChild(signObj);

	}


	public void DebugSphere(Vector3 Location, Color color)
	{
		SphereMesh debugSphere = new SphereMesh();
		debugSphere.Radius = 0.175f;
		debugSphere.Height = 0.35f;
		debugSphere.RadialSegments = 4;
		debugSphere.Rings = 4;

		SpatialMaterial mColor = new SpatialMaterial();
		mColor.AlbedoColor = color;
		mColor.FlagsUnshaded = true;
		debugSphere.SurfaceSetMaterial(0, mColor);
		

		MeshInstance debugSphereInstance = new MeshInstance();
		debugSphereInstance.Mesh = debugSphere;
		debugSphereInstance.Translation = Location;
		AddChild(debugSphereInstance);

	}

}
