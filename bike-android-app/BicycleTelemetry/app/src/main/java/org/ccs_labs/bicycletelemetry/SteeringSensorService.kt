package org.ccs_labs.bicycletelemetry

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Binder
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationCompat.Builder
import androidx.lifecycle.MutableLiveData
import androidx.work.WorkerParameters
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.consumeEach
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

const val ACTION_START_FOREGROUND_SERVICE = "ACTION_START_FOREGROUND_SERVICE"
const val ACTION_STOP_FOREGROUND_SERVICE = "ACTION_STOP_FOREGROUND_SERVICE"
const val ACTION_RESET_STRAIGHT = "ACTION_RESET_STRAIGHT"
const val STEERING_SENSOR_NOTIFICATION_ID = "STEERING_SENSOR_NOTIFICATION_ID"
const val INTENT_EXTRA_SERVER_ADDRESS = "SERVER_ADDRESS"

class SteeringSensorService():
    Service(),
    SensorEventListener {

    inner class SteeringSensorServiceBinder: Binder() {
        // Return this instance of MyService so clients can call public methods
        val service: SteeringSensorService
            // Return this instance of MyService so clients can call public methods
            get() = this@SteeringSensorService
    }

    private val mTAG = "STEERING_SENSOR_SERVICE"

    val currentAzimuthDeg: MutableLiveData<Double> = MutableLiveData<Double>(0.0)
    val statusText: MutableLiveData<String> = MutableLiveData<String>("")
    val stopped: MutableLiveData<Boolean> = MutableLiveData<Boolean>(false)
    // val serverAddress: MutableLiveData<String> = MutableLiveData<String>("") // TODO: set in Activity

    private val mBinder = SteeringSensorServiceBinder()
    private val coroutineScope = CoroutineScope(Dispatchers.IO)
    private val sensorEvents = Channel<SensorEvent>(
        capacity=2, // even 1 might be fine; we don't need old information
        onBufferOverflow=BufferOverflow.DROP_OLDEST
    )

    private var mCommunicator: Communicator? = null

    // Orientation readings according to https://developer.android.com/guide/topics/sensors/sensors_position
    private lateinit var mSensorManager: SensorManager
    internal var mUseGyroscope: Boolean = true
    internal val mSensorDataMutex: Mutex = Mutex()
    private val mAccelerometerReading = FloatArray(3)
    private val mMagnetometerReading = FloatArray(3)
    private val mOrientationAngles = FloatArray(3)
    private val mOrientationAnglesWithoutGyro = FloatArray(3)
    private val mOrientationStraight = FloatArray(3) { 0f }
    private val mOrientationStraightWithoutGyro = FloatArray(3) { 0f }

    override fun onSensorChanged(p0: SensorEvent?) {
        // Process all events in a coroutine so we're able to call setProgress()…
        // See processSensorEvents()
        p0?.let {
            runBlocking {
                sensorEvents.send(it)
            }
        }
    }

    private fun processSensorEvents() = coroutineScope.launch {
        Log.d(mTAG, "processSensorEvents started")

        initializeSensors(true, false)

        sensorEvents.consumeEach(fun (it: SensorEvent) {
            val rotationMatrix = FloatArray(9)

            // TODO: handle possible NullPointerExceptions
            if (it.sensor == null) {
                Log.e(mTAG, "sensor is null!")
            }
            when (it.sensor?.type) {
                Sensor.TYPE_ACCELEROMETER -> {
                    // tested: not 0
                    System.arraycopy(
                        it.values,
                        0,
                        mAccelerometerReading,
                        0,
                        mAccelerometerReading.size
                    )
                }
                Sensor.TYPE_MAGNETIC_FIELD -> {
                    System.arraycopy(
                        it.values,
                        0,
                        mMagnetometerReading,
                        0,
                        mMagnetometerReading.size
                    )
                }
                Sensor.TYPE_ROTATION_VECTOR -> {
                    SensorManager.getRotationMatrixFromVector(rotationMatrix, it.values)
                }
                else -> return
            }

            if (it.sensor.type != Sensor.TYPE_ROTATION_VECTOR) {
                SensorManager.getRotationMatrix(
                    rotationMatrix,
                    null,
                    mAccelerometerReading,
                    mMagnetometerReading
                )
                mSensorDataMutex.withLock {
                    SensorManager.getOrientation(rotationMatrix, mOrientationAnglesWithoutGyro)
                }
            } else {
                mSensorDataMutex.withLock {
                    SensorManager.getOrientation(rotationMatrix, mOrientationAngles)
                }
            }

            currentAzimuthDeg.postValue(normalizeAngleDegrees(
                Math.toDegrees(getCurrentAzimuthRad(false))
                // Normalize angle again b/c who knows what toDegrees will do to
                // my previously normalized angle in radians.
            ))
        })
    }

    override fun onAccuracyChanged(p0: Sensor?, p1: Int) {
        // nothing to do here…
    }

    private fun initializeSensors(
        useGyroscope: Boolean,
        transmitDebugInfo: Boolean,
    ) {
        mSensorManager =
            applicationContext.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        mSensorManager.unregisterListener(this)

        if (!useGyroscope || transmitDebugInfo) {
            mSensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.also { accelerometer ->
                mSensorManager.registerListener(
                    this,
                    accelerometer,
                    // SensorManager.SENSOR_DELAY_FASTEST,
                    SensorManager.SENSOR_DELAY_GAME,
                    SensorManager.SENSOR_DELAY_GAME
                )
            }
            mSensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)?.also { magneticField ->
                mSensorManager.registerListener(
                    this,
                    magneticField,
                    // SensorManager.SENSOR_DELAY_FASTEST,
                    SensorManager.SENSOR_DELAY_GAME,
                    SensorManager.SENSOR_DELAY_GAME
                )
            }
        }
        if (useGyroscope) {
            mSensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)?.also { rotationVector ->
                mSensorManager.registerListener(
                    this,
                    rotationVector,
                    // SensorManager.SENSOR_DELAY_FASTEST,
                    SensorManager.SENSOR_DELAY_GAME,
                    SensorManager.SENSOR_DELAY_GAME
                )
            }
        }
    }

    private fun modulo(a: Double, n: Double): Double {
        var r = (a).rem(n)
        if (r < 0) r += n
        return r
    }

    private fun normalizeAngleDegrees(deg: Double) : Double {
        return modulo(deg + 180.0, 360.0) - 180.0
    }

    internal fun resetStraight() {
        mOrientationStraight[0] = mOrientationAngles[0]
        mOrientationStraight[1] = mOrientationAngles[1]
        mOrientationStraight[2] = mOrientationAngles[2]
        mOrientationStraightWithoutGyro[0] = mOrientationAnglesWithoutGyro[0]
        mOrientationStraightWithoutGyro[1] = mOrientationAnglesWithoutGyro[1]
        mOrientationStraightWithoutGyro[2] = mOrientationAnglesWithoutGyro[2]
    }

    private fun normalizeAngleRadians(rad: Double) : Double {
        return modulo(rad + Math.PI, 2 * Math.PI) - Math.PI
    }

    internal fun getCurrentAzimuthRad(withoutGyro: Boolean = false) : Double {
        val oriAngles = if (withoutGyro) mOrientationAnglesWithoutGyro else mOrientationAngles
        val straight = if (withoutGyro) mOrientationStraightWithoutGyro else mOrientationStraight

        val newAngle: Double = normalizeAngleRadians(
            (oriAngles[0] - straight[0]).toDouble()
        )

        return normalizeAngleRadians(newAngle)
    }

    // Called when another class intends to bind to this service for
    // back-and-forth communication.
    override fun onBind(p0: Intent?): IBinder {
        Log.d(mTAG, "onBind called!")
        return mBinder
    }

    // Called when the service is started,
    // i.e., after onCreate().
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(mTAG, "onStartCommand called!")
        if (intent != null) {
            when (intent.action) {
                ACTION_START_FOREGROUND_SERVICE -> {
                    startSteeringSensor(intent)
                }
                ACTION_STOP_FOREGROUND_SERVICE -> {
                    Log.d(mTAG, "stopping foreground service from notification")
                    stopForegroundService()
                }
                ACTION_RESET_STRAIGHT -> {
                    Log.d(mTAG, "resetting straight from notification")
                    resetStraight()
                }
            }
        }
        // If service killed, after returning from here, restart
        return START_NOT_STICKY
    }

    private fun createNotificationChannel() {
        // Required before any notification can be shown!
        val channel = NotificationChannel(
            STEERING_SENSOR_NOTIFICATION_ID,
            getString(R.string.channel_name),
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = getString(R.string.channel_description)
        }
        // Register the channel with the system
        val notificationManager: NotificationManager =
            getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.createNotificationChannel(channel)
    }

    private fun startSteeringSensor(intent: Intent) {
        processSensorEvents()

        if (intent.extras == null) {
            Log.e(mTAG, "no extras in onStartCommand")
        }
        Log.d(
            mTAG,
            "server address: ${intent.extras!!.getString(INTENT_EXTRA_SERVER_ADDRESS, "not set!!!")}"
        )
        mCommunicator = Communicator(
            //address = workerParams.inputData.getString("ADDRESS").orEmpty(),
            address = intent.extras!!.getString(INTENT_EXTRA_SERVER_ADDRESS)!!,
            intervalMillis = 50,
            steeringSensorService = this,
        )

        // Intent for tapping the "Reset straight" button in the notification:
        val resetStraightIntent = Intent(this, SteeringSensorService::class.java)
            .setAction(ACTION_RESET_STRAIGHT)
        val resetStraightPendingIntent = PendingIntent.getService(
            this,
            ACTION_RESET_STRAIGHT.hashCode(),
            resetStraightIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        // Intent for tapping the "Stop" button in the notification:
        val stopIntent = Intent(this, SteeringSensorService::class.java)
            .setAction(ACTION_STOP_FOREGROUND_SERVICE)
        val stopPendingIntent = PendingIntent.getService(
            this,
            ACTION_STOP_FOREGROUND_SERVICE.hashCode(),
            stopIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        // Intent for tapping the notification itself:
        val contentIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val contentPendingIntent: PendingIntent = PendingIntent.getActivity(
            this, 0, contentIntent, PendingIntent.FLAG_IMMUTABLE)

        // Build the notification for this service:
        val notification = Builder(this, STEERING_SENSOR_NOTIFICATION_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle(getString(R.string.notification_content))
            .setContentIntent(contentPendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .addAction(
                R.drawable.vec_reset_straight,
                getString(R.string.reset_straight),
                resetStraightPendingIntent
            )
            .addAction(
                R.drawable.stop_materialdesignicons,
                getString(R.string.stop_sending),
                stopPendingIntent
            )
            .build()

        startForeground(STEERING_SENSOR_NOTIFICATION_ID.hashCode(), notification)

        coroutineScope.launch {
            mCommunicator!!.transmitBlocking()
        }
    }

    private fun stopForegroundService() {
        mCommunicator?.close()
        mSensorManager.unregisterListener(this)
        stopForeground(Service.STOP_FOREGROUND_REMOVE)
        // Notify main activity that service has stopped
        // (and that the start button can be re-enabled):
        stopped.postValue(true)
        stopSelf()
    }

    // Called when an instance of this service is created,
    // i.e., before onStartCommand().
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onDestroy() {
        // nothing to do here yet
    }
}