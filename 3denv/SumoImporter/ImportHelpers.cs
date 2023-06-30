using Godot;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Serialization;
using static Godot.GeometryInstance;

namespace Denv.SumoImporter
{
	public static class ImportHelpers
	{
		public static Vector3[] ConvertShapeString(string Shape)
		{
			string[] sPoint = Shape.Split(' ');
			return Array.ConvertAll(sPoint, s => VStringXYToVector(s));
		}

		public static Vector3 VStringXYToVector(string VectorString)
		{
			string[] xzString = VectorString.Split(',');
			Vector3 outVector = new Vector3(-float.Parse(xzString[0], GameStatics.Provider),
								0,
								float.Parse(xzString[1], GameStatics.Provider));

			return outVector - GameStatics.SumoOffset;
		}

		public static void CalculateNormals(Vector3[] vertices, int[] triangles, Vector2[] uvs, out Vector3[] OutNormals, out float[] tangents)
		{
			OutNormals = new Vector3[vertices.Length];
			tangents = new float[vertices.Length * 4];

			Vector3[] tan1 = new Vector3[vertices.Length];
			Vector3[] tan2 = new Vector3[vertices.Length];

			//Callculate Normals and Tangents for all Sections
			for (int i = 0; i < triangles.Length; i += 3)
			{
				int ia = triangles[i];
				int ib = triangles[i + 1];
				int ic = triangles[i + 2];

				Vector3 e1 = vertices[ia] - vertices[ib];
				Vector3 e2 = vertices[ic] - vertices[ib];

				//Sum up normals
				Vector3 crossP = e1.Cross(e2);
				OutNormals[ia] += crossP;
				OutNormals[ib] += crossP;
				OutNormals[ic] += crossP;


				//Sum up tangents
				Vector2 w1 = uvs[ia];
				Vector2 w2 = uvs[ib];
				Vector2 w3 = uvs[ic];

				float s1 = w2.x - w1.x;
				float t1 = w2.y - w1.y;

				float s2 = w3.x - w1.x;
				float t2 = w3.y - w1.y;

				float r = 1.0f / (s1 * t2 - s2 * t1);

				Vector3 sdir = (t2 * e1 - t1 * e2) * r;
				Vector3 tdir = (s1 * e2 - s2 * e1) * r;

				tan1[ia] += sdir;
				tan1[ib] += sdir;
				tan1[ic] += sdir;

				tan2[ia] += tdir;
				tan2[ib] += tdir;
				tan2[ic] += tdir;
			}

			for (int i = 0; i < vertices.Length; i++)
			{
				Vector3 n = OutNormals[i].Normalized();
				OutNormals[i] = n;


				Vector3 t = tan1[i];
				// Gram-Schmidt orthogonalize
				Vector3 tangent = (t - n * n.Dot(t)).Normalized();
				tangents[i * 4] = tangent.x;
				tangents[i * 4 + 1] = tangent.y;
				tangents[i * 4 + 2] = tangent.z;
				// Calculate handedness
				tangents[i * 4 + 3] = (n.Cross(t).Dot(tan2[i]) < 0.0f) ? -1.0f : 1.0f;
			}
		}

		public static T LoadXMLFile<T>(string FilePath)
		{
			FileStream shapesStreamer = new FileStream(FilePath, FileMode.Open);
			StreamReader shapesReader = new StreamReader(shapesStreamer);

			XmlSerializer serializer = new XmlSerializer(typeof(T));

			T xmlObject = (T)serializer.Deserialize(shapesReader);

			shapesStreamer.Close();
			shapesReader.Close();

			return xmlObject;
		}

		public static bool ClosestPointOnSegment(Vector3 Point, Vector3 StartPoint, Vector3 EndPoint, out Vector3 hitPoint)
		{
			Vector3 Segment = EndPoint - StartPoint;
			Vector3 VectToPoint = Point - StartPoint;

			// Point is before the start point
			float Dot1 = VectToPoint.Dot(Segment);
			if(Dot1 <= 0 )
			{
				hitPoint = StartPoint;
				return false;
			}

			// Point is after the end point
			float Dot2 = Segment.Dot(Segment);
			if(Dot2 <= Dot1 )
			{
				hitPoint = EndPoint;
				return false;
			}

			// closest point is within the start and end point
			hitPoint = StartPoint + Segment * (Dot1 / Dot2);
			return true;
		}

		public static Vector3 LineIntersection2D(Vector3 StartA, Vector3 DirectionA, Vector3 StartB, Vector3 DirectionB)
		{
			float factor = (DirectionB.x * (StartA.z - StartB.z) - DirectionB.z * (StartA.x - StartB.x)) / (-DirectionB.x * DirectionA.z + DirectionA.x * DirectionB.z);
			return StartA + DirectionA * factor;
		}

		public static void AddMesh(Spatial parent, Vector3[] vertices, Vector3[] normals, int[] triangles, float[] tangents, Vector2[] uvs, Material material, bool bCreateCollision = true, ShadowCastingSetting castShadow = ShadowCastingSetting.On)
		{
			var array_mesh = new ArrayMesh();
			var arrays = new Godot.Collections.Array();
			arrays.Resize((int)ArrayMesh.ArrayType.Max);
			arrays[(int)ArrayMesh.ArrayType.Vertex] = vertices;
			arrays[(int)ArrayMesh.ArrayType.Normal] = normals;
			arrays[(int)ArrayMesh.ArrayType.Index] = triangles;
			arrays[(int)ArrayMesh.ArrayType.TexUv] = uvs;
			arrays[(int)ArrayMesh.ArrayType.Tangent] = tangents;


			array_mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
			array_mesh.SurfaceSetMaterial(0, material);

			MeshInstance m = new MeshInstance();
			m.Mesh = array_mesh;
			m.CastShadow = castShadow;
			if (bCreateCollision)
				m.CreateConvexCollision();

			parent.AddChild(m);
		}
	}

	public static class Triangulator
	{
		public static int[] Triangulate(Vector3[] points)
		{
			List<int> indices = new List<int>();

			int n = points.Length;
			if (n < 3)
				return indices.ToArray();

			int[] V = new int[n];
			if (Area(points) > 0)
			{
				for (int v = 0; v < n; v++)
					V[v] = v;
			}
			else
			{
				for (int v = 0; v < n; v++)
					V[v] = (n - 1) - v;
			}

			int nv = n;
			int count = 2 * nv;
			for (int m = 0, v = nv - 1; nv > 2;)
			{
				if ((count--) <= 0)
					return indices.ToArray();

				int u = v;
				if (nv <= u)
					u = 0;
				v = u + 1;
				if (nv <= v)
					v = 0;
				int w = v + 1;
				if (nv <= w)
					w = 0;

				if (Snip(points, u, v, w, nv, V))
				{
					int a, b, c, s, t;
					a = V[u];
					b = V[v];
					c = V[w];
					indices.Add(b);
					indices.Add(a);
					indices.Add(c);
					m++;
					for (s = v, t = v + 1; t < nv; s++, t++)
						V[s] = V[t];
					nv--;
					count = 2 * nv;
				}
			}

			indices.Reverse();
			return indices.ToArray();
		}

		private static float Area(Vector3[] points)
		{
			int n = points.Length;
			float A = 0.0f;
			for (int p = n - 1, q = 0; q < n; p = q++)
			{
				Vector3 pval = points[p];
				Vector3 qval = points[q];
				A += pval.x * qval.z - qval.x * pval.z;
			}
			return (A * 0.5f);
		}

		private static bool Snip(Vector3[] points, int u, int v, int w, int n, int[] V)
		{
			int p;
			Vector3 A = points[V[u]];
			Vector3 B = points[V[v]];
			Vector3 C = points[V[w]];
			if (Mathf.Epsilon > (((B.x - A.x) * (C.z - A.z)) - ((B.z - A.z) * (C.x - A.x))))
				return false;
			for (p = 0; p < n; p++)
			{
				if ((p == u) || (p == v) || (p == w))
					continue;
				Vector3 P = points[V[p]];
				if (InsideTriangle(A, B, C, P))
					return false;
			}
			return true;
		}

		private static bool InsideTriangle(Vector3 A, Vector3 B, Vector3 C, Vector3 P)
		{
			float ax, ay, bx, by, cx, cy, apx, apy, bpx, bpy, cpx, cpy;
			float cCROSSap, bCROSScp, aCROSSbp;

			ax = C.x - B.x; ay = C.z - B.z;
			bx = A.x - C.x; by = A.z - C.z;
			cx = B.x - A.x; cy = B.z - A.z;
			apx = P.x - A.x; apy = P.z - A.z;
			bpx = P.x - B.x; bpy = P.z - B.z;
			cpx = P.x - C.x; cpy = P.z - C.z;

			aCROSSbp = ax * bpy - ay * bpx;
			cCROSSap = cx * apy - cy * apx;
			bCROSScp = bx * cpy - by * cpx;

			return ((aCROSSbp >= 0.0f) && (bCROSScp >= 0.0f) && (cCROSSap >= 0.0f));
		}
	}
}
