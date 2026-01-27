package com.callingagent.app.service

import android.telecom.Call
import android.telecom.InCallService
import android.util.Log

/**
 * InCallService - Actual call state detection using Telecom API
 * This is the ONLY reliable way to get real call states
 */
class CallStateService : InCallService() {

    companion object {
        private const val TAG = "CallStateService"
        
        // Callback for MainActivity
        var onCallStateChanged: ((state: Int, number: String, isOutgoing: Boolean) -> Unit)? = null
        
        // Call states
        const val STATE_IDLE = 0
        const val STATE_RINGING = 1
        const val STATE_DIALING = 2
        const val STATE_ACTIVE = 3
        const val STATE_DISCONNECTED = 4
    }
    
    private var currentCall: Call? = null
    
    private val callCallback = object : Call.Callback() {
        override fun onStateChanged(call: Call, state: Int) {
            handleCallState(call, state)
        }
    }
    
    override fun onCallAdded(call: Call) {
        super.onCallAdded(call)
        currentCall = call
        call.registerCallback(callCallback)
        
        val number = call.details?.handle?.schemeSpecificPart ?: "Unknown"
        val isOutgoing = call.details?.callDirection == Call.Details.DIRECTION_OUTGOING
        
        Log.i(TAG, "📞 Call ADDED: $number | Outgoing: $isOutgoing")
        
        // Initial state - use details.state instead of call.state
        val initialState = call.details?.state ?: Call.STATE_NEW
        handleCallState(call, initialState)
    }
    
    override fun onCallRemoved(call: Call) {
        super.onCallRemoved(call)
        call.unregisterCallback(callCallback)
        
        val number = call.details?.handle?.schemeSpecificPart ?: "Unknown"
        val isOutgoing = call.details?.callDirection == Call.Details.DIRECTION_OUTGOING
        
        Log.i(TAG, "📴 Call REMOVED: $number | Outgoing: $isOutgoing")
        Log.i(TAG, "🔔 Triggering DISCONNECTED callback...")
        
        onCallStateChanged?.invoke(STATE_DISCONNECTED, number, isOutgoing)
        
        currentCall = null
    }
    
    private fun handleCallState(call: Call, state: Int) {
        val number = call.details?.handle?.schemeSpecificPart ?: "Unknown"
        val isOutgoing = call.details?.callDirection == Call.Details.DIRECTION_OUTGOING
        
        val stateName = when (state) {
            Call.STATE_NEW -> "NEW"
            Call.STATE_DIALING -> "DIALING"
            Call.STATE_RINGING -> "RINGING"
            Call.STATE_HOLDING -> "HOLDING"
            Call.STATE_ACTIVE -> "ACTIVE"
            Call.STATE_DISCONNECTED -> "DISCONNECTED"
            Call.STATE_CONNECTING -> "CONNECTING"
            Call.STATE_DISCONNECTING -> "DISCONNECTING"
            Call.STATE_SELECT_PHONE_ACCOUNT -> "SELECT_ACCOUNT"
            Call.STATE_PULLING_CALL -> "PULLING"
            else -> "UNKNOWN($state)"
        }
        
        Log.i(TAG, "📞 State: $stateName | Number: $number | Outgoing: $isOutgoing")
        
        val mappedState = when (state) {
            Call.STATE_RINGING -> STATE_RINGING           // Incoming ringing
            Call.STATE_DIALING, Call.STATE_CONNECTING -> STATE_DIALING  // Outgoing dialing
            Call.STATE_ACTIVE -> STATE_ACTIVE             // Call connected
            Call.STATE_DISCONNECTED, Call.STATE_DISCONNECTING -> STATE_DISCONNECTED
            else -> -1
        }
        
        if (mappedState >= 0) {
            onCallStateChanged?.invoke(mappedState, number, isOutgoing)
        }
    }
}
