using Env3d.SumoImporter;
using Godot;
using Env3d.SumoImporter.NetFileComponents;
using System;
using System.Collections.Generic;

public class DynamicBuilding : Spatial
{
	private readonly Material wallMaterial1 = ResourceLoader.Load<Material>("Environment/Materials/M_Wall1.tres");
	private readonly Material wallMaterial2 = ResourceLoader.Load<Material>("Environment/Materials/M_Wall2.tres");
	private readonly Material wallMaterial3 = ResourceLoader.Load<Material>("Environment/Materials/M_Wall3.tres");

	private Random random;
	private bool bUseAssets = true;

	//Assets
	private readonly Mesh simpleWindow = ResourceLoader.Load<Mesh>("Environment/Buildings/Windows/Window1_Cube.mesh");

	//Building set 1
	private readonly Material wallMaterialBT2 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/Wall_Yellow.material");
	private readonly Material wallMaterialBT3 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/Wall_Grey.material");
	private readonly Material wallMaterialBT4 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/Wall_Brown.material");
	private readonly Material wallMaterialBT5 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/Wall_DarkYellow.material");

	private readonly Mesh WindowSet1Large = ResourceLoader.Load<Mesh>("Environment/Buildings/Set1/building_assets_set1_WallOneWindowLarge.mesh");
	private readonly Mesh WindowSet1Two = ResourceLoader.Load<Mesh>("Environment/Buildings/Set1/building_assets_set1_WallTwoWindows.mesh");

	private readonly Material wallWindowMaterialBT2 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/WallWindow_Yellow.material");
	private readonly Material wallWindowMaterialBT3 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/WallWindow_Grey.material");
	private readonly Material wallWindowMaterialBT4 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/WallWindow_Brown.material");
	private readonly Material wallWindowMaterialBT5 = ResourceLoader.Load<Material>("Environment/Buildings/Set1/WallWindow_DarkYellow.material");


	public void CreateBuilding(polygonType p, int Seed)
	{
		random = new Random(Seed);
		//bUseAssets = random.Next(2) == 0;
		CreateMeshFromPolygonType(p);
	}

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		
	}

	private Material GetRandomWallWindowMaterial()
	{
		switch (random.Next(4))
		{
			case 0:
				return wallWindowMaterialBT2;
			case 1:
				return wallWindowMaterialBT3;
			case 2:
				return wallWindowMaterialBT4;
			case 3:
				return wallWindowMaterialBT5;
		}
		return wallWindowMaterialBT2;
	}

	private Material GetRandomWallMaterial()
	{
		switch (random.Next(4))
		{
			case 0:
				return wallMaterialBT2;
			case 1:
				return wallMaterialBT3;
			case 2:
				return wallMaterialBT4;
			case 3:
				return wallMaterialBT5;
		}
		switch (random.Next(3))
		{
			case 0:
				return wallMaterial1;
			case 1:
				return wallMaterial2;
			case 2:
				return wallMaterial3;
			default:
				return wallMaterial1;
		}
	}

	private void CreateMeshFromPolygonType(polygonType p)
	{
		PolygonBaseShape shape;
		Vector3[] shapePoints = ImportHelpers.ConvertShapeString(p.shape);

		Vector3 buildingCenter = Vector3.Zero;
		foreach (Vector3 point in shapePoints)
		{
			buildingCenter += point;
		}
		buildingCenter /= shapePoints.Length;
		Translation = buildingCenter;

		for (int i = 0; i < shapePoints.Length; i++)
		{
			shapePoints[i] -= buildingCenter;
		}

		if (p.fill == boolType.Item0)
		{
			Vector3[] orderedVs = new Vector3[shapePoints.Length * 2 + 1];

			for (int i = 0; i < shapePoints.Length; i++)
			{
				Vector3 lastPoint = shapePoints[Math.Max(i - 1, 0)];
				Vector3 currentPoint = shapePoints[i];
				Vector3 nextPoint = shapePoints[Math.Min(i + 1, shapePoints.Length - 1)];

				Vector3 tangent = (nextPoint - lastPoint);
				Vector3 normal = tangent.Cross(Vector3.Up).Normalized();

				orderedVs[i] = currentPoint - normal
					* float.Parse(p.lineWidth, GameStatics.Provider);
				orderedVs[2 * shapePoints.Length - 1 - i] = currentPoint
					+ normal * float.Parse(p.lineWidth, GameStatics.Provider);
			}

			orderedVs[orderedVs.Length -1] = orderedVs[0];
			shape = new PolygonBaseShape(p.id, p.type, new List<Vector3>(orderedVs));
		}
		else
		{
			shape = new PolygonBaseShape(p.id, p.type, new List<Vector3>(shapePoints));
			shape.FixOrder();
		}


		//Vector3[] vertices = new Vector3[shape.Count * 2 + 2];
		//Vector2[] uvs = new Vector2[shape.Count * 2 + 2];
		//int[] triangles = new int[shape.Count * 2 * 3];

		List<Vector3> verticesList = new List<Vector3>();
		List<Vector2> uvsList = new List<Vector2>();
		List<int> trianglesList = new List<int>();

		float wallHeight = random.Next(1, 10) * 2.5f;


		List<Transform> windowTransforms = new List<Transform>(); 

		List<List<Vector3>> fillWalls = new List<List<Vector3>>();

		if (bUseAssets)
		{
			for (int i = 0; i < shape.Count; i++)
			{
				Vector3 startPos = shape[i];
				Vector3 endPos = shape[(i + 1) % shape.Count];

				Vector3 direction = endPos - startPos;
				float wallLength = direction.Length();


				if (wallLength >= 4.0f)
				{

					int numberOfWindows = Mathf.FloorToInt(wallLength / 4.0f);

					float offset = (wallLength - numberOfWindows * 4) / 2.0f + 2.0f;

					bool wasLast = false;

					for (int j = 0; j < numberOfWindows; j++)
					{
						if (!wasLast && random.NextDouble() < 0.33)
						{
							Vector3 start = startPos + direction / wallLength * ((offset-2.0f) + j * 4);
							Vector3 end = startPos + direction / wallLength * ((offset+2.0f) + j * 4);
							List<Vector3> fillWall = new List<Vector3>();
							fillWall.Add(start);
							fillWall.Add(end);
							fillWalls.Add(fillWall);
							wasLast = true;
						}
						else
						{
							wasLast = false;
							Vector3 orign = startPos + direction / wallLength * (offset + j * 4);
							Quat rotation = new Quat(Vector3.Up, Mathf.Atan2(-direction.z, direction.x) - GameStatics.Rad180);

							for (float k = 0; k < wallHeight; k = k + 2.5f)
							{
								Transform windowTransform = new Transform(rotation, orign + Vector3.Up * k);
								windowTransforms.Add(windowTransform);
							}
						}
					}

					List<Vector3> fillWallStart = new List<Vector3>();
					fillWallStart.Add(startPos);
					fillWallStart.Add(startPos + direction / wallLength * (offset - 2.0f));
					fillWalls.Add(fillWallStart);



					List<Vector3> fillWallEnd = new List<Vector3>();
					fillWallEnd.Add(endPos - direction / wallLength * (offset - 2.0f));
					fillWallEnd.Add(endPos);
					fillWalls.Add(fillWallEnd);

				}
				else
				{
					List<Vector3> fillWall = new List<Vector3>();
					fillWall.Add(startPos);
					fillWall.Add(endPos);
					fillWalls.Add(fillWall);
				}
			}

			foreach(List<Vector3> fillWall in fillWalls)
			{
				BuildWall(fillWall.ToArray(), wallHeight, ref verticesList, ref trianglesList, ref uvsList);
			}
		}
		else
		{
			BuildWall(shape.Vertices.ToArray(), wallHeight, ref verticesList, ref trianglesList, ref uvsList);
			//AddWindows(startPos, direction, wallLength, wallHeight);
		}


		List<Vector3> shapeCopy = shape.Vertices;
		shapeCopy.RemoveAt(shapeCopy.Count - 1);


		int[] roofTriangles = Triangulator.Triangulate(shapeCopy.ToArray());
		//add roof

		for (int i = 0; i < roofTriangles.Length; i++)
		{
			trianglesList.Add(roofTriangles[i] + verticesList.Count);
		}

		for (int i = 0; i < shapeCopy.Count; i++)
		{
			verticesList.Add(shapeCopy[i] + new Vector3(0, wallHeight, 0));
			uvsList.Add(new Vector2(shapeCopy[i].x, shapeCopy[i].z));
		}


		if (windowTransforms.Count > 0)
		{
			MultiMesh windows = new MultiMesh();

			Mesh windowWall = random.Next(2) == 0 ? WindowSet1Two : WindowSet1Large;
			//windowWall.SurfaceSetMaterial(0, GetRandomWallWindowMaterial());
			windows.Mesh = windowWall;

			windows.TransformFormat = MultiMesh.TransformFormatEnum.Transform3d;
			windows.InstanceCount = windowTransforms.Count;

			MultiMeshInstance mmi = new MultiMeshInstance();
			mmi.Multimesh = windows;
			mmi.CastShadow = GeometryInstance.ShadowCastingSetting.On;

			for (int i = 0; i < windowTransforms.Count; i++)
			{
				mmi.Multimesh.SetInstanceTransform(i, windowTransforms[i]);
			}

			AddChild(mmi);
		}


		Vector3[] vertices = verticesList.ToArray();
		Vector2[] uvs = uvsList.ToArray();
		int[] triangles = trianglesList.ToArray();

		Vector3[] normals;
		float[] tangents;
		ImportHelpers.CalculateNormals(vertices, triangles, uvs, out normals, out tangents);
		ImportHelpers.AddMesh(this, vertices, normals, triangles, tangents, uvs, GetRandomWallMaterial());
	}

	private void BuildWall(Vector3[] shape, float Height, ref List<Vector3> vertices, ref List<int> triangles, ref List<Vector2> uvs)
	{
		float totalWallLength = 0;

		int triangleOffset = vertices.Count;

		for (int i = 0; i < shape.Length; i++)
		{
			Vector3 startPos = shape[i];
			Vector3 endPos = shape[(i + 1) % shape.Length];

			Vector3 direction = endPos - startPos;
			float wallLength = direction.Length();

			Vector3 wallTopPoint = startPos + new Vector3(0, Height, 0);
			vertices.Add(startPos);
			vertices.Add(wallTopPoint);

			uvs.Add(new Vector2(totalWallLength, 0));
			uvs.Add(new Vector2(totalWallLength, Height / 2.0f));


			totalWallLength += wallLength / 2.0f;

			if (i < shape.Length - 1)
			{
				triangles.Add(triangleOffset + i * 2);
				triangles.Add(triangleOffset + i * 2 + 2);
				triangles.Add(triangleOffset + i * 2 + 1);

				triangles.Add(triangleOffset + i * 2 + 1);
				triangles.Add(triangleOffset + i * 2 + 2);
				triangles.Add(triangleOffset + i * 2 + 3);
			}
		}
	}

	//private void BuildWall(Vector3[] shape, float Height, out Vector3[] vertices, out List<int> triangles, out List<Vector2> uvs)
	//{
	//	for (int i = 0; i <= shape.Length; i++)
	//	{
	//		Vector3 startPos = shape[i % shape.Length];
	//		Vector3 endPos = shape[(i + 1) % shape.Length];

	//		Vector3 direction = endPos - startPos;
	//		float wallLength = direction.Length();

	//		Vector3 wallTopPoint = startPos + new Vector3(0, Height, 0);
	//		vertices[i * 2] = (startPos);
	//		vertices[i * 2 + 1] = (wallTopPoint);

	//		uvs[i * 2] = new Vector2(totalWallLength, 0);
	//		uvs[i * 2 + 1] = new Vector2(totalWallLength, Height / 2.0f);




	//		totalWallLength += wallLength / 2.0f;

	//		if (i < shape.Count)
	//		{
	//			triangles[i * 6] = (i * 2);
	//			triangles[i * 6 + 1] = (i * 2 + 2);
	//			triangles[i * 6 + 2] = (i * 2 + 1);

	//			triangles[i * 6 + 3] = (i * 2 + 1);
	//			triangles[i * 6 + 4] = ((i * 2 + 2));
	//			triangles[i * 6 + 5] = ((i * 2 + 3));
	//		}
	//	}
	//}

	private void AddWindows(Vector3 wallStart, Vector3 direction, float wallLength, float height)
	{
		int numberOfWindows = Mathf.FloorToInt(wallLength * 0.5f);
		int numberOfWindowsHeight = Mathf.FloorToInt(height / 1.5f);

		if ((numberOfWindowsHeight - 1) * (numberOfWindows - 1) <= 0)
			return;


		MultiMesh windows = new MultiMesh();
		windows.Mesh = simpleWindow;
		windows.TransformFormat = MultiMesh.TransformFormatEnum.Transform3d;
		windows.InstanceCount = (numberOfWindowsHeight - 1) * (numberOfWindows - 1);

		MultiMeshInstance mmi = new MultiMeshInstance();
		mmi.Multimesh = windows;
		mmi.CastShadow = GeometryInstance.ShadowCastingSetting.Off;

		for (int y = 1; y < numberOfWindowsHeight; y++)
		{
			for (int x = 1; x < numberOfWindows; x++)
			{
				Vector3 orign = wallStart + direction * x / numberOfWindows + Vector3.Up * 1.5f * y;
				Quat rotation = new Quat(Vector3.Up, Mathf.Atan2(-direction.z, direction.x) - GameStatics.Rad180);

				Transform instanceTransform = new Transform(rotation, orign);
				mmi.Multimesh.SetInstanceTransform((y - 1) * (numberOfWindows - 1) + (x - 1), instanceTransform);
			}
		}

		AddChild(mmi);
	}
}
