using System;
using Godot;
using System.Globalization;

public class CoordinateTransformation
{
	private double NetOffsetX;
	private double NetOffsetY;
	private double OriginOffsetX;
	private double OriginOffsetY;

	private DotSpatial.Projections.ProjectionInfo Src = DotSpatial.Projections.KnownCoordinateSystems.Geographic.World
		.WGS1984;

	private DotSpatial.Projections.ProjectionInfo Trg;

	public CoordinateTransformation(string pNetOffset, string pProjParameters, double pOriginOffsetX,
		double pOriginOffsetY)
	{
		try
		{
			NumberFormatInfo provider = new NumberFormatInfo();
			provider.NumberDecimalSeparator = ".";

			NetOffsetX = double.Parse(pNetOffset.Split(',')[0], provider);
			NetOffsetY = double.Parse(pNetOffset.Split(',')[1], provider);
			OriginOffsetX = pOriginOffsetX;
			OriginOffsetY = pOriginOffsetY;
			GD.Print($"projParameter=\"{pProjParameters}\", netOffset=\"{pNetOffset}\", originOffsetX={pOriginOffsetX}, originOffsetY={pOriginOffsetY}");
			if (pProjParameters.Equals("!"))
			{
				string fallbackProjParams = "+proj=utm +zone=32 +ellps=WGS84 +datum=WGS84 +units=m +no_defs";
				GD.PushWarning(
					"Could not construct a CoordinateTransformation from the value "
					+ $"of projParameter=\"{pProjParameters}\" in the given .net.xml file. "
					+ $"Using fallback: \"{fallbackProjParams}\" "
					+ "Be advised that this may cause wrong interpretations of coordinates "
					+ "received from Veins messages."
				);
				Trg = DotSpatial.Projections.ProjectionInfo.FromProj4String(
					fallbackProjParams
				);
				return;
			}
			Trg = DotSpatial.Projections.ProjectionInfo.FromProj4String(pProjParameters);
		}
		catch (Exception e)
		{
			GD.Print("Exception caught: " + e.ToString());
		}
	}

	public Vector3 WGS84ToCartesianProj(double lon, double lat, double pHeight)
	{
		double[] coord = new double[2] { lon, lat };
		double[] height = { pHeight };

		DotSpatial.Projections.Reproject.ReprojectPoints(coord, height, Src, Trg, 0, 1);

		return new Vector3((float)(coord[0] + NetOffsetX - OriginOffsetX),
			(float)0,
			(float)(coord[1] + NetOffsetY - OriginOffsetY));
	}
}
