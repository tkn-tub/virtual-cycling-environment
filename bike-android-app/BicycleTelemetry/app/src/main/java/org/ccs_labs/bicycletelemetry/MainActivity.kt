package org.ccs_labs.bicycletelemetry

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.os.IBinder
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import org.ccs_labs.bicycletelemetry.databinding.ActivityMainBinding
import java.util.*

const val STATE_SERVER_ADDRESS = "serverAddress"
const val STATE_COMMUNICATOR_STARTED = "communicatorStarted"

class MainActivity : AppCompatActivity() {
    private lateinit var activityMainBinding: ActivityMainBinding

    /**
     * Indicates whether we should attempt to restore the communicator on resume or not.
     */
    var mCommunicatorStarted = false

    private val mTAG = "STEERING_SENSOR_ACTIVITY"

    private var mSteeringSensorService: SteeringSensorService? = null
    private var mSteeringSensorServiceIsBound: Boolean? = null

    /**
     * Interface for getting the instance of binder from our service class
     * So client can get instance of our service class and can directly communicate with it.
     */
    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(className: ComponentName, iBinder: IBinder) {
            Log.d(mTAG, "ServiceConnection: connected to service.")
            // We've bound to MyService, cast the IBinder and get MyBinder instance
            val binder = iBinder as SteeringSensorService.SteeringSensorServiceBinder
            mSteeringSensorService = binder.service
            mSteeringSensorServiceIsBound = true

            // create relevant observers for any live data:
            observeCurrentAzimuth()
            observeSensorStatusText()
            observeServiceStopped()
        }

        override fun onServiceDisconnected(arg0: ComponentName) {
            Log.d(mTAG, "ServiceConnection: disconnected from service.")
            mSteeringSensorServiceIsBound = false
            activityMainBinding.btConnect.isEnabled = true
        }

        override fun onBindingDied(name: ComponentName?) {
            Log.d(mTAG, "ServiceConnection: binding died")
            mSteeringSensorServiceIsBound = false
            activityMainBinding.btConnect.isEnabled = true
        }
    }

    private fun startSteeringSensorService() {
        activityMainBinding.btConnect.isEnabled = false
        saveCurrentServerAddress()
        Intent(this, SteeringSensorService::class.java)
            .putExtra(
                INTENT_EXTRA_SERVER_ADDRESS,
                activityMainBinding.etServerAddress.text.toString()
            )
            .setAction(ACTION_START_FOREGROUND_SERVICE)
            .also { intent ->
                startService(intent)
            }
    }

    /**
     * Used to bind to our service class
     */
    private fun bindSteeringSensorService() {
        Intent(this, SteeringSensorService::class.java)
            .also { intent ->
            bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
        }
    }

    /**
     * Used to unbind and stop our service class
     */
    private fun unbindSteeringSensorService() {
        try {
            Intent(this, SteeringSensorService::class.java).also { intent ->
                unbindService(serviceConnection)
            }
        } catch (e: IllegalArgumentException) {
            Log.d(mTAG, "can't unbind steering sensor service; probably already stopped")
        } finally {
            mSteeringSensorServiceIsBound = false
        }
    }

    private fun observeCurrentAzimuth() {
        mSteeringSensorService?.currentAzimuthDeg?.observe(this) {
            activityMainBinding.tvCurrentSteeringAngle.text = String.format(
                Locale.ROOT, "%.0f", it
            )
        }
    }

    private fun observeServiceStopped() {
        mSteeringSensorService?.stopped?.observe(this) {
            if (it) {
                Log.d(mTAG, "SteeringSensorService stopped -> unbinding")
                unbindSteeringSensorService()
                activityMainBinding.btConnect.isEnabled = true
            }
        }
    }

    private fun observeSensorStatusText() {
        mSteeringSensorService?.statusText?.observe(this) {
            setConnectionStatusText(it)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        activityMainBinding = ActivityMainBinding.inflate(layoutInflater)
        val view = activityMainBinding.root
        setContentView(view)

        activityMainBinding.btConnect.setOnClickListener {
            startSteeringSensorService()
            bindSteeringSensorService()
        }

        activityMainBinding.btResetStraight.setOnClickListener {
            if (mSteeringSensorServiceIsBound == true) {
                mSteeringSensorService?.resetStraight()
            }
        }

        if (savedInstanceState != null) {
            /*
            Restore app state. (Needed e.g. for persistence after device rotation.)
            Won't happen if the app was restarted.
             */
            //Log.d(DEBUG_TAG, "Loading saved instance state")
            mCommunicatorStarted = savedInstanceState.getBoolean(STATE_COMMUNICATOR_STARTED)
            val addr = savedInstanceState.getString(STATE_SERVER_ADDRESS)
            activityMainBinding.etServerAddress.setText(
                if (addr != null && addr.isNotEmpty())
                    addr
                else getSavedServerAddress()
            )
        } else {
            /* No saved app instance -> try to load settings from previous sessions, else use defaults: */
            activityMainBinding.etServerAddress.setText(getSavedServerAddress())
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.main_activity_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_default_server -> {
                activityMainBinding.etServerAddress.setText(getString(R.string.server_address_default))
                true
            }
            else -> {
                super.onOptionsItemSelected(item)
            }
        }
    }

    private fun setConnectionStatusText(msg: String) {
        runOnUiThread {
            activityMainBinding.tvConnectionStatus.text = msg
        }
    }

//    fun setConnectButtonText(text: String) {
//        runOnUiThread {
//            activityMainBinding.btConnect.text = text
//        }
//    }

    private fun saveCurrentServerAddress() {
        val sharedPref = getPreferences(Context.MODE_PRIVATE) ?: return
        with (sharedPref.edit()) {
            putString(getString(R.string.sharedprefs_key_server_address), activityMainBinding.etServerAddress.text.toString())
            apply()
        }
    }

    private fun getSavedServerAddress() : String {
        val sharedPref = getPreferences(Context.MODE_PRIVATE) ?: return getString(R.string.server_address_default)
        return sharedPref.getString(
            getString(R.string.sharedprefs_key_server_address), getString(R.string.server_address_default)) as String
    }

    override fun onResume() {
        super.onResume()
    }

    override fun onPause() {
        super.onPause()
    }

    override fun onDestroy() {
        super.onDestroy()
        unbindSteeringSensorService()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        /*
        Save current app state. (Needed e.g. for persistence after device rotation.)
         */
        outState.putString(STATE_SERVER_ADDRESS, activityMainBinding.etServerAddress.text.toString())
        outState.putBoolean(STATE_COMMUNICATOR_STARTED, mCommunicatorStarted)

        super.onSaveInstanceState(outState)
    }


}
