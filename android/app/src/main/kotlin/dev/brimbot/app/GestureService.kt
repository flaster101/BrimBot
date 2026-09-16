package dev.brimbot.app

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.Rect
import android.os.SystemClock
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityWindowInfo
import dev.brimbot.core.Action
import dev.brimbot.core.Decision
import dev.brimbot.core.Viewport
import java.util.concurrent.atomic.AtomicBoolean

class GestureService : AccessibilityService() {
    companion object { @Volatile var instance: GestureService? = null; const val GAME = "com.sybogames.brim" }
    private val busy = AtomicBoolean(false)
    private var lastDispatch = 0L
    override fun onServiceConnected() { instance = this }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) { /* Live window queried at dispatch, not cached. */ }
    override fun onInterrupt() { BotRuntime.sessionActive = false; busy.set(false) }
    override fun onDestroy() { instance = null; BotRuntime.sessionActive = false; super.onDestroy() }

    fun gameViewport(): Viewport? {
        val app = windows.firstOrNull { it.isActive && it.type == AccessibilityWindowInfo.TYPE_APPLICATION } ?: return null
        val root = app.root ?: return null
        if (root.packageName?.toString() != GAME) return null
        val rect = Rect()
        app.getBoundsInScreen(rect)
        if (rect.width() <= 0 || rect.height() <= 0) return null
        return Viewport(rect.left.toFloat(), rect.top.toFloat(), rect.width().toFloat(), rect.height().toFloat())
    }

    fun perform(decision: Decision, frameTimestamp: Long): Boolean {
        val now = SystemClock.elapsedRealtime()
        if (!BotRuntime.sessionActive || !BotRuntime.qualified || decision.action == Action.NONE || now-frameTimestamp !in 0..250) return false
        val viewport = gameViewport() ?: return false
        if (now-lastDispatch < 110 || !busy.compareAndSet(false, true)) return false
        val center = viewport.screen(.5f, .57f)
        val target = when (decision.action) {
            Action.LEFT -> viewport.screen(.25f,.57f)
            Action.RIGHT -> viewport.screen(.75f,.57f)
            Action.UP -> viewport.screen(.5f,.38f)
            Action.DOWN -> viewport.screen(.5f,.76f)
            else -> center
        }
        val tap = decision.action == Action.TAP || decision.action == Action.DOUBLE_TAP
        fun stroke(start: Long) = GestureDescription.StrokeDescription(Path().apply {
            moveTo(center.x,center.y); if (!tap) lineTo(target.x,target.y)
        }, start, if (tap) 45 else 90)
        val builder = GestureDescription.Builder().addStroke(stroke(0))
        if (decision.action == Action.DOUBLE_TAP) builder.addStroke(stroke(140))
        val accepted = dispatchGesture(builder.build(), object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) { busy.set(false) }
            override fun onCancelled(gestureDescription: GestureDescription?) { busy.set(false) }
        }, null)
        if (accepted) lastDispatch = now else busy.set(false)
        return accepted
    }
}
