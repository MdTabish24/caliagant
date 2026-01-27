package com.callingagent.app.utils

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.widget.Toast

object WhatsAppHelper {

    private const val TAG = "WhatsAppHelper"

    /**
     * Cleans and formats phone number for WhatsApp
     * WhatsApp requires number WITHOUT + sign, just country code + number
     */
    private fun formatPhoneForWhatsApp(phoneNumber: String?): String {
        if (phoneNumber.isNullOrBlank()) return ""

        Log.d(TAG, "Original phone number: '$phoneNumber'")

        // Trim and remove any whitespace, newlines, tabs
        var cleaned = phoneNumber.trim().replace(Regex("\\s+"), "")

        // Remove any non-digit characters except leading +
        val hasPlus = cleaned.startsWith("+")
        cleaned = cleaned.replace(Regex("[^0-9]"), "")

        // Handle different formats
        val formatted = when {
            // Already has country code (91 for India) and is longer than 10 digits
            cleaned.startsWith("91") && cleaned.length >= 12 -> cleaned
            // Number is exactly 10 digits (Indian mobile without country code)
            cleaned.length == 10 -> "91$cleaned"
            // Number starts with 0 (trunk prefix), remove it and add 91
            cleaned.startsWith("0") && cleaned.length == 11 -> "91${cleaned.substring(1)}"
            // Already formatted with country code
            cleaned.length > 10 -> cleaned
            // Fallback - just return cleaned
            else -> cleaned
        }

        Log.d(TAG, "Formatted phone number for WhatsApp: '$formatted'")
        return formatted
    }

    /**
     * Send WhatsApp message to a phone number
     */
    fun sendMessage(context: Context, phoneNumber: String, message: String): Boolean {
        return try {
            val formattedNumber = formatPhoneForWhatsApp(phoneNumber)

            if (formattedNumber.isEmpty()) {
                Log.e(TAG, "Phone number is empty after formatting")
                Toast.makeText(context, "Invalid phone number", Toast.LENGTH_SHORT).show()
                return false
            }

            Log.d(TAG, "Sending WhatsApp to: $formattedNumber")
            Log.d(TAG, "Message: $message")

            val encodedMessage = Uri.encode(message)
            val uri = Uri.parse("https://api.whatsapp.com/send?phone=$formattedNumber&text=$encodedMessage")

            val intent = Intent(Intent.ACTION_VIEW, uri).apply {
                setPackage("com.whatsapp")
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }

            if (intent.resolveActivity(context.packageManager) != null) {
                context.startActivity(intent)
                Log.d(TAG, "WhatsApp intent started successfully")
                true
            } else {
                // Try WhatsApp Business
                intent.setPackage("com.whatsapp.w4b")
                if (intent.resolveActivity(context.packageManager) != null) {
                    context.startActivity(intent)
                    Log.d(TAG, "WhatsApp Business intent started successfully")
                    true
                } else {
                    Log.e(TAG, "WhatsApp not installed")
                    Toast.makeText(context, "WhatsApp not installed", Toast.LENGTH_SHORT).show()
                    false
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error sending WhatsApp message", e)
            Toast.makeText(context, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
            false
        }
    }

    /**
     * Send WhatsApp message with auto-send using Accessibility Service
     */
    fun sendMessageWithAutoSend(context: Context, phoneNumber: String, message: String): Boolean {
        // First open WhatsApp with the message
        val opened = sendMessage(context, phoneNumber, message)

        if (opened) {
            // The WhatsAppAccessibilityService will handle auto-clicking send
            Log.d(TAG, "WhatsApp opened, accessibility service will auto-send")
        }

        return opened
    }
}
