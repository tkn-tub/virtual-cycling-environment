using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Godot;
// using PsychExperiment;
// using UnityEngine;

public class NetworkListener : Spatial
{
	private bool _paused = false;


	// read Thread
	System.Threading.Thread readThread;

	// udpclient object
	UdpClient client;

	// port number
	public int port = 15006;

	// static ego vehicle
	private BicycleInterfaceController egoVehicleController;
	private PackedScene egoVehicleControllerScene;
	// public static GameObject steeringDevice;
	private double _x;
	private double _y;
	private double _z;
	private Vector3 _location;
	private float _roll;
	private float _pitch;
	private float _yaw;
	private double _steeringAngle;
	private double _speed;

	public double Speed => _speed;

	private double _prevSpeed;
	private double _pos;
	private bool _isCar = true;

	public double xOffset; // matlab simulation starts always at 0,0. to compensate this add offset to matlab coordinates

	public double yOffset;


	// /// <summary>
	// /// The Matlab and the bicycle model simulation (which processes all the sensor data)
	// /// always start at (0,0) with the same initial orientation.
	// /// Use this matrix to map our desired initial position and orientation to that coordinate system.
	// /// </summary>


	public static bool gotFirstUpdate = false;

	// /// <summary>
	// /// Acceleration in m/s^2 calculated (and interpolated)
	// /// from the speed difference between the current and the previous update.
	// /// </summary>
	private double _acceleration;

	private const int _accelerationMovingAverageWindowSize = 4;
	private List<double> _accelerationMovingAverageWindow = new List<double>();

	private long _previousDataUpdateTimeTicks;
	private double _dataUpdateDeltaTimeSeconds;


	// bicycle-specific:


	/// <summary>
	/// Start applying brakes if acceleration in m/s^2 is below this value.
	/// </summary>
	 private float _brakeStartThreshold = -1.5f;

	/// <summary>
	/// Fully apply brakes if acceleration in m/s^2 is below this value.
	/// </summary>
	 private float _brakeFullThreshold = -3f;


	public void Init()
	{

	}
	public override void _Ready()
	{

		// Get vehicle controller, update its skeleton and bicycle rig
		egoVehicleController = (BicycleInterfaceController)GameStatics.GameInstance.PlayerVehicle;

		// Connection to speed sensors
		readThread = new System.Threading.Thread(new ThreadStart(ReceiveData)) { IsBackground = true };
		readThread.Start();
		GD.Print("Created network listener");
	}

	// Update sensor data in controller
	public override void _PhysicsProcess(float delta)
	{
		_pos += delta * _speed / 3.6f;

		egoVehicleController.Update(
			_location,
			(float)_yaw,
			(float)_speed,
			(float)_acceleration,
			(float)_steeringAngle
		);
	}


	// Unity Application Quit Function
	void OnApplicationQuit()
	{
		StopThread();
	}

	// Stop reading UDP messages
	private void StopThread()
	{
		if (readThread.IsAlive)
		{
			readThread.Abort();
		}

		client.Close();
	}

	// receive thread function
	private void ReceiveData()
	{
		client = new UdpClient(port);
		GD.Print("opened connection to UDP");
		_acceleration = 0;
		_accelerationMovingAverageWindow.Clear();

		while (true)
		{
			try
			{
				// receive bytes
				IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
				byte[] data = client.Receive(ref anyIP);
				gotFirstUpdate = true;

				_dataUpdateDeltaTimeSeconds = (double)(DateTime.Now.Ticks - _previousDataUpdateTimeTicks) / 1e7;

				_y = BitConverter.ToDouble(data, 0);
				_x = BitConverter.ToDouble(data, 8) * -1;
				_z = BitConverter.ToDouble(data, 16);
				_location = new Vector3((float)_x, (float)_y, (float)_z);
				_roll = Mathf.Deg2Rad((float)BitConverter.ToDouble(data, 24));
				_pitch = Mathf.Deg2Rad((float)BitConverter.ToDouble(data, 32));
				_yaw = Mathf.Deg2Rad((float)BitConverter.ToDouble(data, 40));
				_steeringAngle = BitConverter.ToDouble(data, 48);
				_prevSpeed = _speed;
				_speed = BitConverter.ToDouble(data, 56);
				/* Use a moving average for the acceleration calculation, since it is possible that the bicycle model
				 mistakenly sends the same speed value in successive updates. */
				double instantaneousAcc = (_speed - _prevSpeed) / _dataUpdateDeltaTimeSeconds;
				if (_accelerationMovingAverageWindow.Count >= _accelerationMovingAverageWindowSize)
					_accelerationMovingAverageWindow.RemoveAt(0);
				_accelerationMovingAverageWindow.Add(instantaneousAcc);
				_acceleration += instantaneousAcc / _accelerationMovingAverageWindowSize -
								 _accelerationMovingAverageWindow[0] / _accelerationMovingAverageWindowSize;
				//GD.Print(_location); // TODO: this is NaN!
				_acceleration = instantaneousAcc;

				// if (_experimentSubject != null)
				//     _experimentSubject.CurrentVelocity = (float)_speed;

				_previousDataUpdateTimeTicks = DateTime.Now.Ticks;
			}
			catch (Exception err)
			{
				GD.Print(err.ToString());
			}
		}
	}
}
