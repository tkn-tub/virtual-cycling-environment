using Godot;
public class ForeignCarController : ForeignVehicleController
{


    private Spatial _wheelFrontLeft;
    private Spatial _wheelFrontRight;
    private Spatial _wheelRearLeft;
    private Spatial _wheelRearRight;
    private Spatial[] _wheels;
    private MeshInstance[] _caseMeshes;
    // Called when the node enters the scene tree for the first time.
    public override void _Ready()
    {
        MeshInstance carCase = GetNode<MeshInstance>("Car/CarCase");

        Godot.Collections.Array wheels = carCase.GetChildren();
        _wheelFrontLeft = (Spatial)wheels[0];
        _wheelFrontRight = (Spatial)wheels[1];
        _wheelRearLeft = (Spatial)wheels[2];
        _wheelRearRight = (Spatial)wheels[3];
        _wheels = new Spatial[] { _wheelFrontLeft, _wheelFrontRight, _wheelRearLeft, _wheelRearRight };

    }

    public override void UpdateWheels(float delta, float angleRad = 0)
    {

        var rotationAngleDelta = (float)(delta * vehicleSpeed / wheelRadius);

        // Rotating the wheels
        foreach (var wheel in _wheels)
        {
            wheel.RotateZ(rotationAngleDelta);
        }

        // Turning the wheels left and right using approximation of the steering angle, while preserving the rotation around the Z axis
        // Right wheel's initial angle is 180 degrees, so we need to subtract PI from the angle in rad
        var turningAngle = angleRad * steeringAngleApproximationFactor;
        var currentZFrontL = _wheelFrontLeft.Rotation.z;
        var currentZFrontR = _wheelFrontRight.Rotation.z;

        _wheelFrontLeft.Rotation = new Vector3(0.0f, turningAngle, currentZFrontL);
        _wheelFrontRight.Rotation = new Vector3(0.0f, turningAngle - 3.14159f, currentZFrontR);

    }

    public override void ChangeColor(Color color)
    {
        if (_caseMeshes == null)
        {
            MeshInstance carCase = GetNode<MeshInstance>("Car/CarCase");
            MeshInstance doorFront = GetNode<MeshInstance>("Car/DoorFront");
            MeshInstance doorBack = GetNode<MeshInstance>("Car/DoorBack");
            _caseMeshes = new MeshInstance[] { carCase, doorFront, doorBack };
        }

        var material = new SpatialMaterial();
        material.AlbedoColor = color;

        foreach (var mesh in _caseMeshes)
        {
            mesh.SetSurfaceMaterial(0, material);
        }
    }

}
