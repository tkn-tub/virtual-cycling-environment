using System;
using Godot;


public class BicycleRig : Spatial
{

	private Skeleton _skeleton;
	private KinematicBody _vehicle;
	private Transform _frameTransform;
	private int _handleId;
	private Transform _handleTransform;
//     // private Transform _frontWheelTransform;
//     // private Transform _rearWheelTransform;
	private int _pedalCranksetId, _leftPedalId, _rightPedalId;
	private Transform _pedalCranksetTransform, _leftPedalTransform, _rightPedalTransform;
	private Transform _leftBrakeHandle, _frontBrakeBackLever, _frontBrakeFrontLever;
	private Transform _rightBrakeHandle, _rearBrakeBackLever, _rearBrakeFrontLever;
	private int _frontWheelId, _rearWheelId;
	private Transform _frontWheelTransform, _rearWheelTransform;


	private float _currentVelocity = 0f;

//     /*
//      Variables for the bicycle model as defined in these papers:
//      - Meijaard, J. P., Papadopoulos, J. M., Ruina, A., & Schwab, A. L. (2007, August). 
//      Linearized dynamics equations for the balance and steer of a bicycle: a benchmark and review. 
//      In Proceedings of the Royal Society of London A: Mathematical, Physical and Engineering Sciences 
//      (Vol. 463, No. 2084, pp. 1955-1982). The Royal Society.
//      - Schwab, A. L., & Recuero, A. M. (2013). 
//      Design and experimental validation of a haptic steering interface for the control input of a bicycle simulator. 
//      In Proceedings of ECCOMAS Multibody Dynamics Conference (pp. 1-4).
	 
//      For the lean angle, page 104 in the latter is especially useful.

	private float _steeringAngle = 0f;
	private Vector3 _rightVector = new Vector3();
	public Vector3 RightVector
	{
		get { return _rightVector; }
		set { _rightVector = value; }
	}
	private float _pedalDeltaRotation = 0f;


	/// <summary>
	/// Current velocity in m/s.
	/// </summary>
	public float CurrentVelocity
	{
		get { return _currentVelocity; }
		set { _currentVelocity = value; }
	}

	/// <summary>
	/// Current steering angle in degrees.
	/// </summary>
	public float SteeringAngle
	{
		get { return _steeringAngle; }
		set { _steeringAngle = value; }
	}

	// Bicycle object skeleton
	public Skeleton Skeleton
	{
		get { return _skeleton; }
		set { _skeleton = value; }
	}


	public override void _Ready()
	{
		// Ge required bicycle parts from skeleton
		_skeleton = this.GetNode<Skeleton>("Bicycle CCS Armature/Skeleton");

		_frameTransform = _skeleton.GetBonePose(_skeleton.FindBone("Frame"));
		_handleId = _skeleton.FindBone("Handle");
		_handleTransform = _skeleton.GetBonePose(_handleId);
		_pedalCranksetId = _skeleton.FindBone("PedalCrankset");
		_pedalCranksetTransform =  _skeleton.GetBonePose(_pedalCranksetId); 
		_leftPedalId = _skeleton.FindBone("LeftPedal");
		_leftPedalTransform =_skeleton.GetBonePose(_leftPedalId);
		_rightPedalId = _skeleton.FindBone("RightPedal");
		_rightPedalTransform = _skeleton.GetBonePose(_rightPedalId);
		_leftBrakeHandle = _skeleton.GetBonePose(_skeleton.FindBone("LeftBrakeHandle"));
		_rightBrakeHandle = _skeleton.GetBonePose(_skeleton.FindBone("RightBrakeHandle"));
		_frontWheelId = _skeleton.FindBone("FrontWheel");
		_rearWheelId = _skeleton.FindBone("RearWheel");
		_frontWheelTransform = _skeleton.GetBonePose(_frontWheelId);
		_rearWheelTransform = _skeleton.GetBonePose(_rearWheelId);

		GD.Print("Initialyzed BicycleRig");
	}

		// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(float delta)
	{

		// Rotate handle
		Vector3 y_axis = new Vector3(0, 1, 0);
		float frame_angle = _frameTransform.basis.GetEuler().y;
		float handle_angle_to_frame = _handleTransform.basis.GetEuler().y - frame_angle;
		_handleTransform = _handleTransform.Rotated(
			y_axis,
			(frame_angle - _steeringAngle) - handle_angle_to_frame
		);
		_skeleton.SetBonePose(_handleId, _handleTransform);

		// Turn the pedals based on current bicycle speed in the simulation
		Vector3 right_vector = new Vector3(0, 1,0);
		_pedalDeltaRotation = _currentVelocity * Mathf.Pi / 2f * delta;
		_pedalCranksetTransform = _pedalCranksetTransform.Rotated(right_vector, -_pedalDeltaRotation);
		_skeleton.SetBonePose(_pedalCranksetId, _pedalCranksetTransform);
		_leftPedalTransform = _leftPedalTransform.Rotated(
			right_vector,
			-_pedalDeltaRotation
		);
		_rightPedalTransform = _rightPedalTransform.Rotated(
			right_vector,
			_pedalDeltaRotation
		);
		_skeleton.SetBonePose(_leftPedalId, _leftPedalTransform);
		_skeleton.SetBonePose(_rightPedalId, _rightPedalTransform);

		// Turn wheels
		float wheelDeltaRotation = _currentVelocity * Mathf.Pi * delta;
		_frontWheelTransform = _frontWheelTransform.Rotated(
			right_vector,
			-wheelDeltaRotation
		);
		_skeleton.SetBonePose(_frontWheelId, _frontWheelTransform);
		_rearWheelTransform = _rearWheelTransform.Rotated(
			right_vector,
			-wheelDeltaRotation
		);
		_skeleton.SetBonePose(_rearWheelId, _rearWheelTransform);
	}


//     /// <summary>
//     /// Apply all transformations according to speed, braking, and steering.
//     /// This is not the Unity Update method! Must be called manually!
//     /// Also note that this will currently not alter the location or orientation of the bicycle.
//     /// </summary>
	public void Update(float delta)
	{
	   
	}

	/**
		 * Just for testing!
		 * TODO: Use a physically accurate bicycle dynamics model
		 */
	// public float GetLeanAngle()
	// {
	//     return _steeringAngle * -.2f;
	// }
	public Vector3 GetForwardVector()
	{
		return GetRotationVector(Rotation);
	}
	public Vector3 GetRightVector()
	{
		return GetRotationVector(Rotation + new Vector3(0, GameStatics.Rad90, 0));
	}

	private static Vector3 GetRotationVector(Vector3 Rotator)
	{
		float Pitch = (Rotator.z);
		float Yaw = (-Rotator.y);
		
		float sinP = Mathf.Sin(Pitch);
		float sinY = Mathf.Sin(Yaw);
		float cosY = Mathf.Cos(Yaw);
		float cosP = Mathf.Cos(Pitch);
	
		return new Vector3(cosY*cosP, sinP, cosP*sinY);
	}
}

