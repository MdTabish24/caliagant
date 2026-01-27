package com.callingagent.app.utils

object PhoneUtils {
    
    /**
     * Cleans and formats phone number for WhatsApp
     * Removes all non-digit characters except leading +
     */
    fun formatForWhatsApp(phoneNumber: String?): String {
        if (phoneNumber.isNullOrBlank()) return ""
        
        // Trim and remove any whitespace
        var cleaned = phoneNumber.trim()
        
        // Check if starts with +
        val hasPlus = cleaned.startsWith("+")
        
        // Remove all non-digit characters
        cleaned = cleaned.replace(Regex("[^0-9]"), "")
        
        // If original had +, add it back
        // If number doesn't start with country code, assume India (+91)
        return when {
            hasPlus -> cleaned
            cleaned.startsWith("91") && cleaned.length > 10 -> cleaned
            cleaned.length == 10 -> "91$cleaned"  // Indian number without country code
            else -> cleaned
        }
    }
    
    /**
     * Formats phone number for making calls
     */
    fun formatForCall(phoneNumber: String?): String {
        if (phoneNumber.isNullOrBlank()) return ""
        
        var cleaned = phoneNumber.trim()
        val hasPlus = cleaned.startsWith("+")
        
        cleaned = cleaned.replace(Regex("[^0-9]"), "")
        
        return if (hasPlus) "+$cleaned" else cleaned
    }
    
    /**
     * Validates if the phone number is valid
     */
    fun isValidPhoneNumber(phoneNumber: String?): Boolean {
        if (phoneNumber.isNullOrBlank()) return false
        val cleaned = phoneNumber.replace(Regex("[^0-9]"), "")
        return cleaned.length >= 10
    }
}
