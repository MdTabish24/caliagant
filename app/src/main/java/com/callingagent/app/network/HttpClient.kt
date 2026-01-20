package com.callingagent.app.network

import android.util.Log
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

/**
 * HTTP Client - PC se communicate karta hai
 */
class HttpClient {
    
    companion object {
        private const val TAG = "HttpClient"
        private const val TIMEOUT = 5000
    }
    
    private var baseUrl = ""
    
    fun connect(ip: String, port: Int): Boolean {
        baseUrl = "http://$ip:$port"
        return ping()
    }
    
    fun ping(): Boolean {
        return try {
            val url = URL("$baseUrl/ping")
            val conn = url.openConnection() as HttpURLConnection
            conn.connectTimeout = TIMEOUT
            conn.readTimeout = TIMEOUT
            conn.requestMethod = "GET"
            
            val responseCode = conn.responseCode
            conn.disconnect()
            
            responseCode == 200
        } catch (e: Exception) {
            Log.e(TAG, "Ping failed: ${e.message}")
            false
        }
    }
    
    fun sendCallState(state: String, number: String, direction: String = "outgoing"): Boolean {
        val endpoint = when (state) {
            "ringing" -> "/call/ringing"
            "active" -> "/call/active"
            "ended" -> "/call/ended"
            "idle" -> "/call/idle"
            else -> return false
        }
        
        return try {
            val url = URL("$baseUrl$endpoint")
            val conn = url.openConnection() as HttpURLConnection
            conn.connectTimeout = TIMEOUT
            conn.readTimeout = TIMEOUT
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.doOutput = true
            
            val json = """{"number": "$number", "direction": "$direction"}"""
            
            OutputStreamWriter(conn.outputStream).use { writer ->
                writer.write(json)
                writer.flush()
            }
            
            val responseCode = conn.responseCode
            conn.disconnect()
            
            Log.d(TAG, "Sent $state ($direction) for $number - Response: $responseCode")
            responseCode == 200
        } catch (e: Exception) {
            Log.e(TAG, "Send state failed: ${e.message}")
            false
        }
    }
}
