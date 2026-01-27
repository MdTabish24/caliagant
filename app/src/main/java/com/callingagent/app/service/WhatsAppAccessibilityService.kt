package com.callingagent.app.service

import android.accessibilityservice.AccessibilityService
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlin.random.Random

class WhatsAppAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "WhatsAppA11y"
        private const val WHATSAPP_PACKAGE = "com.whatsapp"
        var isEnabled = false
        var shouldAutoSend = false
    }

    private val handler = Handler(Looper.getMainLooper())
    private var lastActionTime = 0L

    override fun onServiceConnected() {
        super.onServiceConnected()
        isEnabled = true
        Log.i(TAG, "✅ Accessibility Service Connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event?.packageName != WHATSAPP_PACKAGE) return
        if (!shouldAutoSend) return
        
        Log.i(TAG, "👁️ Event: ${event.eventType} | ${event.className}")
        
        when (event.eventType) {
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED,
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> {
                val delay = Random.nextLong(2000, 4000)
                
                val now = System.currentTimeMillis()
                if (now - lastActionTime < 5000) {
                    Log.i(TAG, "⏱️ Cooldown active, skipping")
                    return
                }
                
                Log.i(TAG, "⏳ Waiting ${delay}ms before clicking...")
                handler.postDelayed({
                    tryClickSendButton()
                }, delay)
            }
        }
    }

    private fun tryClickSendButton() {
        try {
            val rootNode = rootInActiveWindow
            if (rootNode == null) {
                Log.w(TAG, "❌ Root node null")
                return
            }
            
            Log.i(TAG, "🔍 Searching for send button...")
            
            val sendButton = findSendButton(rootNode)
            
            if (sendButton != null) {
                Log.i(TAG, "✅ Send button found! Clickable: ${sendButton.isClickable}, Enabled: ${sendButton.isEnabled}")
                
                if (sendButton.isEnabled && sendButton.isClickable) {
                    handler.postDelayed({
                        val clicked = sendButton.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                        if (clicked) {
                            lastActionTime = System.currentTimeMillis()
                            shouldAutoSend = false
                            Log.i(TAG, "✅✅✅ SEND BUTTON CLICKED!")
                        } else {
                            Log.e(TAG, "❌ Click action failed")
                        }
                        sendButton.recycle()
                    }, Random.nextLong(50, 150))
                } else {
                    Log.w(TAG, "⚠️ Button not clickable/enabled")
                    sendButton.recycle()
                }
            } else {
                Log.w(TAG, "❌ Send button NOT found")
            }
            
            rootNode.recycle()
        } catch (e: Exception) {
            Log.e(TAG, "Error: ${e.message}")
            e.printStackTrace()
        }
    }

    private fun findSendButton(node: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        val byDesc = node.findAccessibilityNodeInfosByText("Send")
        if (byDesc.isNotEmpty()) return byDesc[0]
        
        val byId = node.findAccessibilityNodeInfosByViewId("$WHATSAPP_PACKAGE:id/send")
        if (byId.isNotEmpty()) return byId[0]
        
        return searchSendButton(node)
    }

    private fun searchSendButton(node: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        val desc = node.contentDescription?.toString()?.lowercase()
        if (desc?.contains("send") == true && node.isClickable) {
            return node
        }
        
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            val result = searchSendButton(child)
            if (result != null) return result
            child.recycle()
        }
        
        return null
    }

    override fun onInterrupt() {
        Log.w(TAG, "Service interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        isEnabled = false
        handler.removeCallbacksAndMessages(null)
        Log.i(TAG, "❌ Service destroyed")
    }
}
