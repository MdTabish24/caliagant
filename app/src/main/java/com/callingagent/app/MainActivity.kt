package com.callingagent.app

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioManager
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.telecom.TelecomManager
import android.util.Log
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.callingagent.app.service.CallingService
import com.callingagent.app.service.CallStateService
import com.callingagent.app.util.ExcelReader
import com.callingagent.app.receiver.PCCommandReceiver

/**
 * AI Calling Agent - AT Telecom Mode (No PC Connection)
 * 
 * Direct calling with Excel file selection
 */
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "CallingAgent"
        private const val CALL_GAP_MS = 5000L
    }

    // Views
    private lateinit var statusText: TextView
    private lateinit var currentNumberText: TextView
    private lateinit var selectExcelBtn: Button
    private lateinit var startCallingBtn: Button
    private lateinit var stopBtn: Button
    private lateinit var numbersCountText: TextView

    // State
    private var phoneNumbers = mutableListOf<String>()
    private var currentIndex = 0
    private var currentNumber = ""
    private var isCalling = false
    private var lastCallTime = 0L
    
    // SharedPreferences for progress
    private val PREFS_NAME = "CallingAgentPrefs"
    private val KEY_CURRENT_INDEX = "currentIndex"
    private val KEY_TOTAL_NUMBERS = "totalNumbers"

    // Components
    private lateinit var audioManager: AudioManager
    private lateinit var telecomManager: TelecomManager
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main_simple)

        initViews()
        checkPermissions()
        
        audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        telecomManager = getSystemService(Context.TELECOM_SERVICE) as TelecomManager
        
        // Setup callback from InCallService
        setupCallStateCallback()
        
        // Setup PC command callback
        setupPCCommandCallback()
        
        Log.i(TAG, "App started - AT Telecom Mode with PC Control")
    }

    private fun setupCallStateCallback() {
        CallStateService.onCallStateChanged = { state, number, isOutgoing ->
            runOnUiThread {
                handleCallState(state, number, isOutgoing)
            }
        }
        Log.i(TAG, "📞 CallStateService callback registered")
    }
    
    private fun setupPCCommandCallback() {
        PCCommandReceiver.onEndCallCommand = {
            runOnUiThread {
                Log.i(TAG, "📡 PC END_CALL command received!")
                updateStatus("📡 PC: End call")
                
                // End current call
                endCurrentCall()
                
                // Next call after gap (if auto-calling)
                if (isCalling) {
                    handler.postDelayed({ callNextNumber() }, CALL_GAP_MS)
                }
            }
        }
        Log.i(TAG, "📡 PCCommandReceiver callback registered")
    }
    
    private fun handleCallState(state: Int, number: String, isOutgoing: Boolean) {
        val direction = if (isOutgoing) "outgoing" else "incoming"
        val stateName = when (state) {
            CallStateService.STATE_IDLE -> "IDLE"
            CallStateService.STATE_RINGING -> "RINGING"
            CallStateService.STATE_DIALING -> "DIALING"
            CallStateService.STATE_ACTIVE -> "ACTIVE"
            CallStateService.STATE_DISCONNECTED -> "DISCONNECTED"
            else -> "UNKNOWN"
        }
        
        Log.i(TAG, "📞 handleCallState: $stateName | $number | $direction")
        
        when (state) {
            CallStateService.STATE_RINGING -> {
                // Incoming call ringing
                if (!isOutgoing) {
                    currentNumber = number
                    Log.i(TAG, "📲 INCOMING RINGING: $number")
                    updateStatus("📲 Incoming: $number")
                }
            }
            
            CallStateService.STATE_DIALING -> {
                // Outgoing call dialing (ringing on other side)
                if (isOutgoing) {
                    Log.i(TAG, "📞 OUTGOING DIALING: $number")
                    updateStatus("📞 Dialing...")
                }
            }
            
            CallStateService.STATE_ACTIVE -> {
                // Call connected!
                Log.i(TAG, "✅ CALL ACTIVE: $number ($direction)")
                updateStatus("✅ Connected!")
            }
            
            CallStateService.STATE_DISCONNECTED -> {
                // Call ended
                Log.i(TAG, "📴 CALL ENDED: $number ($direction)")
                updateStatus("📴 Call ended")
                
                // Next call if auto-calling
                if (isCalling && isOutgoing) {
                    currentNumber = ""
                    handler.postDelayed({ callNextNumber() }, CALL_GAP_MS)
                }
            }
        }
    }

    private fun initViews() {
        statusText = findViewById(R.id.statusText)
        currentNumberText = findViewById(R.id.currentNumberText)
        selectExcelBtn = findViewById(R.id.selectExcelBtn)
        startCallingBtn = findViewById(R.id.startCallingBtn)
        stopBtn = findViewById(R.id.stopBtn)
        numbersCountText = findViewById(R.id.numbersCountText)

        selectExcelBtn.setOnClickListener { selectExcelFile() }
        startCallingBtn.setOnClickListener { startCalling() }
        stopBtn.setOnClickListener { stopCalling() }

        startCallingBtn.isEnabled = false
        stopBtn.isEnabled = false
    }

    private fun loadExcelFile(uri: Uri) {
        try {
            val numbers = ExcelReader.readPhoneNumbers(this, uri)
            phoneNumbers.clear()
            phoneNumbers.addAll(numbers)
            
            // Load saved progress
            val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val savedTotal = prefs.getInt(KEY_TOTAL_NUMBERS, 0)
            val savedIndex = prefs.getInt(KEY_CURRENT_INDEX, 0)
            
            // If same file (same total), resume from saved index
            if (savedTotal == phoneNumbers.size && savedIndex > 0 && savedIndex < phoneNumbers.size) {
                currentIndex = savedIndex
                updateStatus("✅ Loaded ${phoneNumbers.size} numbers (Resume from #$currentIndex)")
                updateCurrentNumber("Ready to resume from #$currentIndex")
                Toast.makeText(this, "Resume from number #$currentIndex", Toast.LENGTH_LONG).show()
                Log.i(TAG, "Resuming from index $currentIndex")
            } else {
                // New file or completed - start fresh
                currentIndex = 0
                prefs.edit().clear().apply()
                updateStatus("✅ Loaded ${phoneNumbers.size} numbers")
                updateCurrentNumber("Ready to call")
                Toast.makeText(this, "${phoneNumbers.size} numbers loaded", Toast.LENGTH_SHORT).show()
                Log.i(TAG, "Starting fresh - ${phoneNumbers.size} numbers")
            }
            
            updateNumbersCount("📊 ${phoneNumbers.size} numbers loaded")
            startCallingBtn.isEnabled = phoneNumbers.isNotEmpty()
        } catch (e: Exception) {
            Toast.makeText(this, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
            Log.e(TAG, "Excel load error", e)
        }
    }

    private val excelLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { loadExcelFile(it) }
    }

    private fun selectExcelFile() {
        excelLauncher.launch("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }

    private fun startCalling() {
        if (phoneNumbers.isEmpty()) {
            Toast.makeText(this, "Load numbers first!", Toast.LENGTH_SHORT).show()
            return
        }

        isCalling = true
        
        // Save total numbers count
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putInt(KEY_TOTAL_NUMBERS, phoneNumbers.size).apply()
        
        startService(Intent(this, CallingService::class.java).apply {
            action = CallingService.ACTION_START
        })
        
        startCallingBtn.isEnabled = false
        stopBtn.isEnabled = true
        selectExcelBtn.isEnabled = false
        
        updateStatus("🚀 Calling started from #$currentIndex!")
        Log.i(TAG, "Starting calls from index $currentIndex - ${phoneNumbers.size} total")
        
        callNextNumber()
    }

    private fun stopCalling() {
        isCalling = false
        
        // Save current progress before stopping
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .putInt(KEY_CURRENT_INDEX, currentIndex)
            .putInt(KEY_TOTAL_NUMBERS, phoneNumbers.size)
            .apply()
        
        startService(Intent(this, CallingService::class.java).apply {
            action = CallingService.ACTION_STOP
        })
        
        endCurrentCall()

        startCallingBtn.isEnabled = true
        stopBtn.isEnabled = false
        selectExcelBtn.isEnabled = true
        updateStatus("⛔ Stopped at #$currentIndex")
        updateCurrentNumber("Paused at $currentIndex/${phoneNumbers.size}")
        Toast.makeText(this, "Paused at #$currentIndex - Resume anytime!", Toast.LENGTH_LONG).show()
        Log.i(TAG, "Calling paused at index $currentIndex")
    }

    private fun callNextNumber() {
        if (!isCalling) return
        
        if (currentIndex >= phoneNumbers.size) {
            isCalling = false
            
            // Clear saved progress - all done!
            val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            prefs.edit().clear().apply()
            
            startService(Intent(this, CallingService::class.java).apply {
                action = CallingService.ACTION_STOP
            })
            
            startCallingBtn.isEnabled = true
            stopBtn.isEnabled = false
            selectExcelBtn.isEnabled = true
            updateStatus("✅ All ${phoneNumbers.size} calls done!")
            updateCurrentNumber("Completed!")
            Toast.makeText(this, "All calls completed!", Toast.LENGTH_LONG).show()
            Log.i(TAG, "All calls completed")
            return
        }

        currentNumber = phoneNumbers[currentIndex]
        currentIndex++
        
        // Save progress after each call
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putInt(KEY_CURRENT_INDEX, currentIndex).apply()

        Log.i(TAG, "📞 Calling: $currentNumber ($currentIndex/${phoneNumbers.size})")
        updateCurrentNumber("📞 $currentNumber ($currentIndex/${phoneNumbers.size})")
        updateStatus("📞 Calling...")
        
        makeCall(currentNumber)
    }

    private fun makeCall(number: String) {
        Log.d(TAG, "makeCall: $number")
        
        // Save current number to file for PC to read
        try {
            val file = java.io.File(getExternalFilesDir(null), "current_number.txt")
            file.writeText(number)
            Log.i(TAG, "💾 Saved number to file: $number")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to save number: ${e.message}")
        }

        // Track call start time
        lastCallTime = System.currentTimeMillis()
        
        // Set timeout - if call not active in 20 seconds, move to next
        handler.postDelayed({
            if (isCalling && currentNumber == number) {
                val elapsed = System.currentTimeMillis() - lastCallTime
                if (elapsed >= 20000) {
                    Log.i(TAG, "⏰ Call timeout (20s) - moving to next: $number")
                    updateStatus("⏰ Timeout - Next call")
                    endCurrentCall()
                    handler.postDelayed({ callNextNumber() }, 2000)
                }
            }
        }, 20000)

        // NO speaker mode - audio goes to audio card/earpiece
        
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED) {
            try {
                val uri = Uri.parse("tel:$number")
                val extras = Bundle().apply {
                    // NO speakerphone - use default audio routing (earpiece/audio card)
                    putBoolean(TelecomManager.EXTRA_START_CALL_WITH_SPEAKERPHONE, false)
                }
                telecomManager.placeCall(uri, extras)
                
            } catch (e: Exception) {
                Log.e(TAG, "Call error: ${e.message}")
                updateStatus("❌ Call failed")
                handler.postDelayed({ callNextNumber() }, CALL_GAP_MS)
            }
        }
    }

    // Speaker mode removed - audio goes to audio card/earpiece
    
    private fun endCurrentCall() {
        try {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ANSWER_PHONE_CALLS) == PackageManager.PERMISSION_GRANTED) {
                telecomManager.endCall()
            }
        } catch (e: Exception) {
            Log.e(TAG, "endCall error: ${e.message}")
        }
    }

    private fun updateStatus(status: String) {
        runOnUiThread { statusText.text = "Status: $status" }
    }

    private fun updateCurrentNumber(text: String) {
        runOnUiThread { currentNumberText.text = text }
    }

    private fun updateNumbersCount(text: String) {
        runOnUiThread { numbersCountText.text = text }
    }

    private fun checkPermissions() {
        val permissions = arrayOf(
            Manifest.permission.CALL_PHONE,
            Manifest.permission.READ_PHONE_STATE,
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.ANSWER_PHONE_CALLS,
            Manifest.permission.MODIFY_AUDIO_SETTINGS,
            Manifest.permission.INTERNET,
            Manifest.permission.POST_NOTIFICATIONS,
            Manifest.permission.MANAGE_OWN_CALLS
        )
        val needed = permissions.filter { 
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED 
        }
        if (needed.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, needed.toTypedArray(), 100)
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        isCalling = false
        handler.removeCallbacksAndMessages(null)
        CallStateService.onCallStateChanged = null
    }
}
