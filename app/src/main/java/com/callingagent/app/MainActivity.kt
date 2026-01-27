package com.callingagent.app

import android.Manifest
import android.app.AlertDialog
import android.app.role.RoleManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.telecom.TelecomManager
import android.util.Log
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SwitchCompat
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.callingagent.app.service.CallingService
import com.callingagent.app.service.CallStateService
import com.callingagent.app.util.ExcelReader
import com.callingagent.app.receiver.PCCommandReceiver

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "CallingAgent"
        private const val CALL_GAP_MS = 5000L
        private const val REQUEST_ROLE_DIALER = 101
    }

    // Views
    private lateinit var statusText: TextView
    private lateinit var currentNumberText: TextView
    private lateinit var selectExcelBtn: Button
    private lateinit var startCallingBtn: Button
    private lateinit var stopBtn: Button
    private lateinit var numbersCountText: TextView

    // WhatsApp views
    private lateinit var whatsappToggle: SwitchCompat
    private lateinit var whatsappMessageInput: EditText
    private lateinit var selectMediaBtn: Button
    private lateinit var enableCallDetectionBtn: Button
    private lateinit var whatsappOptionsLayout: LinearLayout

    // State
    private var phoneNumbers = mutableListOf<String>()
    private var currentIndex = 0
    private var currentNumber = ""
    private var isCalling = false
    private var lastCallTime = 0L

    // WhatsApp state
    private var whatsappEnabled = false
    private var whatsappMessage = ""
    private var whatsappMediaUri: Uri? = null

    // SharedPreferences
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
        checkOverlayPermission()

        audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        telecomManager = getSystemService(Context.TELECOM_SERVICE) as TelecomManager

        setupCallStateCallback()
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
                endCurrentCall()
                // WhatsApp will be triggered in STATE_DISCONNECTED handler
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

        Log.i(TAG, "� handleCallState: $stateName | $number | $direction")

        when (state) {
            CallStateService.STATE_RINGING -> {
                if (!isOutgoing) {
                    currentNumber = number
                    Log.i(TAG, "� INCOMING RINGING: $number")
                    updateStatus("� Incoming: $number")
                }
            }

            CallStateService.STATE_DIALING -> {
                if (isOutgoing) {
                    Log.i(TAG, "📞 OUTGOING DIALING: $number")
                    updateStatus("📞 Dialing...")
                }
            }

            CallStateService.STATE_ACTIVE -> {
                // Store number when call becomes active
                if (isOutgoing && number.isNotEmpty()) {
                    currentNumber = number
                }
                Log.i(TAG, "✅ CALL ACTIVE: $number ($direction)")
                updateStatus("✅ Connected!")
            }

            CallStateService.STATE_DISCONNECTED -> {
                Log.i(TAG, "📴 CALL ENDED: $number ($direction)")
                updateStatus("📴 Call ended")

                if (isCalling && isOutgoing) {
                    val numberToSend = currentNumber

                    // Trigger WhatsApp if enabled
                    if (whatsappEnabled && numberToSend.isNotEmpty()) {
                        Log.i(TAG, "📱 Sending WhatsApp to: $numberToSend")
                        sendWhatsAppMessage(numberToSend)

                        // Wait 15 sec for WhatsApp to send, then next call
                        handler.postDelayed({
                            currentNumber = ""
                            callNextNumber()
                        }, 15000L)
                    } else {
                        // No WhatsApp, call next after 5 sec
                        currentNumber = ""
                        handler.postDelayed({ callNextNumber() }, CALL_GAP_MS)
                    }
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

        // WhatsApp views
        whatsappToggle = findViewById(R.id.whatsappToggle)
        whatsappMessageInput = findViewById(R.id.whatsappMessageInput)
        selectMediaBtn = findViewById(R.id.selectMediaBtn)
        enableCallDetectionBtn = findViewById(R.id.enableCallDetectionBtn)
        whatsappOptionsLayout = findViewById(R.id.whatsappOptionsLayout)

        selectExcelBtn.setOnClickListener { selectExcelFile() }
        startCallingBtn.setOnClickListener { startCalling() }
        stopBtn.setOnClickListener { stopCalling() }

        // WhatsApp listeners
        whatsappToggle.setOnCheckedChangeListener { _, isChecked ->
            whatsappEnabled = isChecked
            Log.i(TAG, "📱 WhatsApp toggle: $isChecked")

            // Show/hide WhatsApp options
            whatsappOptionsLayout.visibility = if (isChecked) android.view.View.VISIBLE else android.view.View.GONE

            whatsappMessageInput.isEnabled = isChecked
            selectMediaBtn.isEnabled = isChecked

            // Check accessibility when enabled
            if (isChecked) {
                val enabled = isAccessibilityEnabled()
                Log.i(TAG, "🤖 Accessibility enabled: $enabled")
                if (!enabled) {
                    showAccessibilityDialog()
                } else {
                    Toast.makeText(this, "✅ Auto-send enabled!", Toast.LENGTH_SHORT).show()
                }
            }
        }

        selectMediaBtn.setOnClickListener {
            showTestDialog()
        }

        enableCallDetectionBtn.setOnClickListener {
            requestCallDetectionPermission()
        }

        startCallingBtn.isEnabled = false
        stopBtn.isEnabled = false
        whatsappOptionsLayout.visibility = android.view.View.GONE
    }

    private fun showTestDialog() {
        val options = arrayOf("🧪 Test WhatsApp", "📎 Select Media", "Cancel")
        AlertDialog.Builder(this)
            .setTitle("Choose Action")
            .setItems(options) { _, which ->
                when (which) {
                    0 -> showTestNumberDialog()
                    1 -> mediaLauncher.launch("image/*")
                }
            }
            .show()
    }

    private fun showTestNumberDialog() {
        val input = EditText(this)
        input.hint = "Enter phone number"

        AlertDialog.Builder(this)
            .setTitle("🧪 Test WhatsApp")
            .setView(input)
            .setPositiveButton("Test") { _, _ ->
                val testNumber = input.text.toString().trim()
                if (testNumber.isNotEmpty()) {
                    Log.i(TAG, "🧪 Testing WhatsApp with: $testNumber")
                    sendWhatsAppMessage(testNumber)
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private val mediaLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let {
            whatsappMediaUri = it
            selectMediaBtn.text = "📎 Media Selected ✓"
            Toast.makeText(this, "Media selected!", Toast.LENGTH_SHORT).show()
            Log.i(TAG, "📎 Media selected: $it")
        }
    }

    private fun requestCallDetectionPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val roleManager = getSystemService(Context.ROLE_SERVICE) as RoleManager

            if (roleManager.isRoleAvailable(RoleManager.ROLE_DIALER)) {
                if (!roleManager.isRoleHeld(RoleManager.ROLE_DIALER)) {
                    // Show info dialog first
                    AlertDialog.Builder(this)
                        .setTitle("Enable Call Detection")
                        .setMessage("This will set Calling Agent as default phone app temporarily to detect call states.\n\nYou can change it back anytime in Settings.")
                        .setPositiveButton("Enable") { _, _ ->
                            val intent = roleManager.createRequestRoleIntent(RoleManager.ROLE_DIALER)
                            startActivityForResult(intent, REQUEST_ROLE_DIALER)
                        }
                        .setNegativeButton("Cancel", null)
                        .show()
                } else {
                    Toast.makeText(this, "✅ Call detection already enabled!", Toast.LENGTH_SHORT).show()
                }
            }
        } else {
            Toast.makeText(this, "Requires Android 10+", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_ROLE_DIALER) {
            val roleManager = getSystemService(Context.ROLE_SERVICE) as RoleManager
            if (roleManager.isRoleHeld(RoleManager.ROLE_DIALER)) {
                Toast.makeText(this, "✅ Call detection enabled!", Toast.LENGTH_SHORT).show()
                Log.i(TAG, "✅ DIALER role granted")
            } else {
                Toast.makeText(this, "❌ Call detection not enabled", Toast.LENGTH_SHORT).show()
                Log.w(TAG, "❌ DIALER role denied")
            }
        }
    }

    private fun checkOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!Settings.canDrawOverlays(this)) {
                AlertDialog.Builder(this)
                    .setTitle("Display Permission Needed")
                    .setMessage("Allow Calling Agent to display over other apps to open WhatsApp from background.")
                    .setPositiveButton("Enable") { _, _ ->
                        val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName"))
                        startActivityForResult(intent, 102)
                    }
                    .setNegativeButton("Skip", null)
                    .show()
            }
        }
    }

    private fun isAccessibilityEnabled(): Boolean {
        val service = "$packageName/.service.WhatsAppAccessibilityService"
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        )
        return enabledServices?.contains(service) == true
    }

    private fun showAccessibilityDialog() {
        AlertDialog.Builder(this)
            .setTitle("🤖 Enable Auto-Send")
            .setMessage("To automatically send WhatsApp messages:\n\n1. Enable 'Calling Agent' in Accessibility\n2. Grant permission\n\n⚠️ This uses human-like delays to avoid detection.")
            .setPositiveButton("Open Settings") { _, _ ->
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
            .setNegativeButton("Later", null)
            .show()
    }

    private fun loadExcelFile(uri: Uri) {
        try {
            val numbers = ExcelReader.readPhoneNumbers(this, uri)
            phoneNumbers.clear()
            phoneNumbers.addAll(numbers)

            val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val savedTotal = prefs.getInt(KEY_TOTAL_NUMBERS, 0)
            val savedIndex = prefs.getInt(KEY_CURRENT_INDEX, 0)

            if (savedTotal == phoneNumbers.size && savedIndex > 0 && savedIndex < phoneNumbers.size) {
                currentIndex = savedIndex
                updateStatus("✅ Loaded ${phoneNumbers.size} numbers (Resume from #$currentIndex)")
                updateCurrentNumber("Ready to resume from #$currentIndex")
                Toast.makeText(this, "Resume from number #$currentIndex", Toast.LENGTH_LONG).show()
                Log.i(TAG, "Resuming from index $currentIndex")
            } else {
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

        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putInt(KEY_CURRENT_INDEX, currentIndex).apply()

        Log.i(TAG, "📞 Calling: $currentNumber ($currentIndex/${phoneNumbers.size})")
        updateCurrentNumber("📞 $currentNumber ($currentIndex/${phoneNumbers.size})")
        updateStatus("📞 Calling...")

        makeCall(currentNumber)
    }

    private fun makeCall(number: String) {
        Log.d(TAG, "makeCall: $number")

        try {
            val file = java.io.File(getExternalFilesDir(null), "current_number.txt")
            file.writeText(number)
            Log.i(TAG, "💾 Saved number to file: $number")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to save number: ${e.message}")
        }

        lastCallTime = System.currentTimeMillis()

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

        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED) {
            try {
                val uri = Uri.parse("tel:$number")
                val extras = Bundle().apply {
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

    private fun endCurrentCall() {
        try {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ANSWER_PHONE_CALLS) == PackageManager.PERMISSION_GRANTED) {
                telecomManager.endCall()
            }
        } catch (e: Exception) {
            Log.e(TAG, "endCall error: ${e.message}")
        }
    }

    private fun cleanPhoneNumber(number: String): String {
        Log.i(TAG, "📞 Cleaning number: $number")

        // Step 1: Remove all non-digits
        var cleaned = number.replace(Regex("[^0-9]"), "")
        Log.i(TAG, "📞 Step 1 - Remove non-digits: $number → $cleaned")

        // Step 2: If exactly 10 digits, return as-is
        if (cleaned.length == 10) {
            Log.i(TAG, "📞 Step 2 - Already 10 digits: $cleaned")
            return cleaned
        }

        // Step 3: If more than 10 digits, remove prefixes
        if (cleaned.length > 10) {
            // Remove +91 or 91 prefix
            if (cleaned.startsWith("91") && cleaned.length == 12) {
                cleaned = cleaned.removePrefix("91")
                Log.i(TAG, "📞 Step 3 - Removed 91 prefix: $cleaned")
            }
            // Remove 01 prefix
            else if (cleaned.startsWith("01") && cleaned.length == 12) {
                cleaned = cleaned.removePrefix("01")
                Log.i(TAG, "📞 Step 3 - Removed 01 prefix: $cleaned")
            }
            // If still > 10, take last 10 digits
            else if (cleaned.length > 10) {
                cleaned = cleaned.takeLast(10)
                Log.i(TAG, "📞 Step 3 - Took last 10 digits: $cleaned")
            }
        }

        // Step 4: If less than 10 digits, log warning
        if (cleaned.length < 10) {
            Log.w(TAG, "⚠️ Number less than 10 digits: $cleaned")
        }

        Log.i(TAG, "📞 Final cleaned: $number → $cleaned")
        return cleaned
    }

    private fun sendWhatsAppMessage(phoneNumber: String) {
        Log.i(TAG, "📱 sendWhatsAppMessage called for: $phoneNumber")
        try {
            // Check if WhatsApp is installed
            val pm = packageManager
            try {
                pm.getPackageInfo("com.whatsapp", PackageManager.GET_ACTIVITIES)
            } catch (e: PackageManager.NameNotFoundException) {
                Toast.makeText(this, "❌ WhatsApp not installed!", Toast.LENGTH_LONG).show()
                Log.e(TAG, "WhatsApp not installed")
                return
            }

            // Read message from input field
            val message = whatsappMessageInput.text.toString().trim()
            Log.i(TAG, "📝 Message: '$message'")
            Log.i(TAG, "📎 Media: ${if (whatsappMediaUri != null) "YES" else "NO"}")

            if (message.isEmpty() && whatsappMediaUri == null) {
                Log.w(TAG, "❌ No message or media to send")
                Toast.makeText(this, "⚠️ WhatsApp: No message/media!", Toast.LENGTH_SHORT).show()
                return
            }

            var cleanNumber = cleanPhoneNumber(phoneNumber)

            if (cleanNumber.length == 10) {
                cleanNumber = "91$cleanNumber"
                Log.i(TAG, "➕ Added country code: $cleanNumber")
            }

            Log.i(TAG, "📞 Final number: $cleanNumber")

            updateStatus("📱 Opening WhatsApp...")
            Toast.makeText(this, "📱 Opening WhatsApp for $cleanNumber", Toast.LENGTH_SHORT).show()

            // Enable auto-send flag
            WhatsAppAccessibilityService.shouldAutoSend = true

            // Send with media using ACTION_SEND
            val intent = Intent(Intent.ACTION_SEND).apply {
                setPackage("com.whatsapp")
                type = if (whatsappMediaUri != null) "image/*" else "text/plain"
                putExtra(Intent.EXTRA_TEXT, message)
                putExtra("jid", "$cleanNumber@s.whatsapp.net")

                if (whatsappMediaUri != null) {
                    putExtra(Intent.EXTRA_STREAM, whatsappMediaUri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }

                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }

            if (intent.resolveActivity(packageManager) != null) {
                startActivity(intent)
                Log.i(TAG, "✅ WhatsApp opened with ${if (whatsappMediaUri != null) "media" else "text"}!")
            } else {
                Toast.makeText(this, "❌ Cannot open WhatsApp", Toast.LENGTH_LONG).show()
                Log.e(TAG, "No activity found to handle WhatsApp intent")
            }

        } catch (e: Exception) {
            Log.e(TAG, "❌ WhatsApp error: ${e.message}")
            e.printStackTrace()
            Toast.makeText(this, "WhatsApp error: ${e.message}", Toast.LENGTH_LONG).show()
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
