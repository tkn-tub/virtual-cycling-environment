package org.ccs_labs.bicycletelemetry

import android.util.Log
import androidx.work.workDataOf
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.withLock
import java.io.Closeable
import java.io.IOException
import java.net.*
import java.util.*
import kotlin.math.max

const val COMMUNICATOR_DEBUG_TAG : String = "BikeCommunicator"

class Communicator(
    private val address: String,
    private val intervalMillis: Long,
    private val steeringSensorService: SteeringSensorService,
    private val transmitDebugInfo: Boolean = false,
) : Closeable {

    abstract class TransmissionError() : Exception() {}
    class TransmissionErrorInvalidPort(public val notAPort: String) : TransmissionError() {}
    class TransmissionErrorServerAddress() : TransmissionError() {}

    var stopSending = false
    private var datagramSocket : DatagramSocket? = null
    private val coroutineScope = CoroutineScope(Dispatchers.IO)

    suspend fun transmitBlocking() {
        val job = coroutineScope.launch { run() }
        job.join()
        close()
    }

    /**
     * Continuously transmit the current steering angle as measured by the given
     * SteeringSensorWorker.
     *
     * Since this is running in the Dispatchers.IO scope,
     * launched in transmitBlocking, blocking calls for IO should be ok.
     * Cp. https://youtrack.jetbrains.com/issue/KTIJ-838/False-positive-Inappropriate-blocking-method-call-with-coroutines-and-DispatchersIO
     */
    @Suppress("BlockingMethodInNonBlockingContext")
    private suspend fun run() {
        try {
            val addressElements = address.split(":")
            if (addressElements.size != 2) {
                throw TransmissionErrorServerAddress()
                // activity.setConnectionStatusText(activity.getString(R.string.invalid_address))
                // return
            }
            val host = addressElements[0]
            var port: Int? = null
            try {
                port = addressElements[1].toInt()
            } catch (e: NumberFormatException) {
                throw TransmissionErrorInvalidPort(addressElements[1])
                // activity.setConnectionStatusText(
                //     activity.getString(R.string.invalid_port).format(addressElements[1])
                // )
            }

            datagramSocket = DatagramSocket(port, InetAddress.getByName("0.0.0.0"))
            datagramSocket!!.connect(InetAddress.getByName(host), port)
            var previousTime: Long = System.currentTimeMillis()

            // setConnected(true)

            while (!Thread.currentThread().isInterrupted && !stopSending) {
                steeringSensorService.mSensorDataMutex.withLock {
                    val msg = if (!transmitDebugInfo) {
                        val azimuth = steeringSensorService.getCurrentAzimuthRad(
                            withoutGyro = !steeringSensorService.mUseGyroscope && !transmitDebugInfo
                        )
                        "%.5f\n".format(Locale.ROOT, azimuth).toByteArray(Charsets.UTF_8)
                    } else {
                        val azimuth = steeringSensorService.getCurrentAzimuthRad(withoutGyro = false)
                        val azWithoutGyro = steeringSensorService.getCurrentAzimuthRad(withoutGyro = true)
                        "%.5f,%.5f\n".format(Locale.ROOT, azimuth, azWithoutGyro)
                            .toByteArray(Charsets.UTF_8)
                    }
                    val datagramPacket = DatagramPacket(msg, msg.size)

                    try {
                        datagramSocket!!.send(datagramPacket)
                    } catch (e: IOException) {
                        // "if an I/O error occurs."
                        steeringSensorService.statusText.postValue(steeringSensorService.getString(
                            R.string.send_io_exception
                        ).format(e))
                        // setConnectionStatusText(
                        //     activity.getString(R.string.send_io_exception).format(e.message)
                        // )
                        Log.e(COMMUNICATOR_DEBUG_TAG, e.toString())
                    } catch (e: SecurityException) {
                        // "if a security manager exists and its checkMulticast or
                        // checkConnect method doesn't allow the send."
                        steeringSensorService.statusText.postValue(steeringSensorService.getString(
                            R.string.send_security_exception
                        ).format(e))
                        // setConnectionStatusText(
                        //     activity.getString(R.string.send_security_exception)
                        //         .format(e.message)
                        // )
                        Log.e(COMMUNICATOR_DEBUG_TAG, e.toString())
                    } catch (e: PortUnreachableException) {
                        // "may be thrown if the socket is connected to a currently unreachable destination.
                        // Note, there is no guarantee that the exception will be thrown."
                        steeringSensorService.statusText.postValue(steeringSensorService.getString(
                            R.string.send_port_unreachable_exception
                        ))
                        // setConnectionStatusText(
                        //     activity.getString(R.string.send_port_unreachable_exception)
                        // )
                        Log.e(COMMUNICATOR_DEBUG_TAG, e.toString())
                    }

                    tryReconnect(host, port)
                }

                delay(max(
                    0,
                    intervalMillis - (System.currentTimeMillis() - previousTime)
                ))
                previousTime = System.currentTimeMillis()
            }
        } catch (e: SocketException) {
            // DatagramSocket constructor:
            // "if the socket could not be opened, or the socket could not bind to the specified local port."
            // setConnectionStatusText(
            //     activity.getString(R.string.socket_exception).format(e.message)
            // )
            Log.e(COMMUNICATOR_DEBUG_TAG, e.toString())
            throw e
        } catch (e: SecurityException) {
            // DatagramSocket constructor:
            // "if a security manager exists and its checkListen method doesn't allow the operation."
            // setConnectionStatusText(activity.getString(R.string.security_exception))
            Log.e(COMMUNICATOR_DEBUG_TAG, e.toString())
            throw e
        } finally {
            datagramSocket?.close()
            // setConnected(false)
        }
    }

    /**
     * Apply this communicator's connection status in the parent activity.
     * Also sets this.stopSending to true if connected. Set this to false if you want to stop transmitting.
     */
    // private fun setConnected(connected: Boolean) {
    //     // TODO: this is not very MVC…
    //     stopSending = !connected
    //     activity.mCommunicatorStarted = connected
    //     activity.runOnUiThread {
    //         if (connected) {
    //             setConnectionStatusText(activity.getString(R.string.connection_status_sending))
    //             activity.setConnectButtonText(activity.getString(R.string.stop_sending))
    //         } else {
    //             setConnectionStatusText(activity.getString(R.string.connection_status_not_connected))
    //             activity.setConnectButtonText(activity.getString(R.string.connect))
    //         }
    //     }
    // }
    // TODO: use the SteeringDataModel listeners in MainActivity instead


    private suspend fun tryReconnect(host: String, port: Int) {
        try {
            datagramSocket!!.disconnect()
            datagramSocket!!.connect(InetAddress.getByName(host), port)
            if (datagramSocket!!.isConnected) {

                steeringSensorService.statusText.postValue(steeringSensorService.getString(
                    R.string.connection_status_sending
                ))
            }
        } catch (e: SocketException) {
            // DatagramSocket constructor:
            // "if the socket could not be opened, or the socket could not bind to the specified local port."

            // Do not replace the status text here because the error that lead to this reconnect attempt
            // could be more important… TODO: really?
            // setConnectionStatusText(activity.getString(R.string.socket_exception).format(e.message))
            Log.e(COMMUNICATOR_DEBUG_TAG, e.toString())
        }
    }

    override fun close() {
        stopSending = true
        // should also cause the socket to be closed (see `finally` in `run()`)
    }
}
