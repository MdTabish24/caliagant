package com.callingagent.app.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * PC se ADB broadcast receive karta hai
 * PC command: adb shell am broadcast -a com.callingagent.END_CALL -n com.callingagent.app/.receiver.PCCommandReceiver
 */
class PCCommandReceiver : BroadcastReceiver() {
    
    companion object {
        private const val TAG = "PCCommandReceiver"
        const val ACTION_END_CALL = "com.callingagent.END_CALL"
        
        // Callback to MainActivity
        var onEndCallCommand: (() -> Unit)? = null
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        Log.i(TAG, "📡 Received broadcast: ${intent.action}")
        
        when (intent.action) {
            ACTION_END_CALL -> {
                Log.i(TAG, "📴 END_CALL command from PC!")
                onEndCallCommand?.invoke()
            }
        }
    }
}
