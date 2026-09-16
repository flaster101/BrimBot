package dev.brimbot.app

import android.Manifest
import android.app.NotificationManager
import android.content.Intent
import android.content.pm.ActivityInfo
import android.os.SystemClock
import android.view.accessibility.AccessibilityNodeInfo
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.filters.SdkSuppress
import androidx.test.rule.GrantPermissionRule
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Real Android consent and projection lifecycle on the English test emulator.
 * This test does not supply game-state evidence or authorize any gestures. */
@SdkSuppress(minSdkVersion=33)
class CaptureLifecycleTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @get:Rule val notificationPermission: GrantPermissionRule =
        GrantPermissionRule.grant(Manifest.permission.POST_NOTIFICATIONS)

    private fun eventually(message: String, condition: () -> Boolean) {
        val deadline=SystemClock.elapsedRealtime()+12000
        while(SystemClock.elapsedRealtime()<deadline) {
            if(condition()) return
            SystemClock.sleep(100)
        }
        val root=InstrumentationRegistry.getInstrumentation().uiAutomation.rootInActiveWindow
        fun describe(node: AccessibilityNodeInfo?): String {
            if(node==null) return "<no window>"
            return "[${node.viewIdResourceName}: ${node.text}; clickable=${node.isClickable}]"+
                (0 until node.childCount).joinToString("") { describe(node.getChild(it)) }
        }
        fail(message+" Window: "+describe(root))
    }

    @Test fun systemConsentRotationAndNotificationStop() {
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        val context=instrumentation.targetContext
        val manager=context.getSystemService(NotificationManager::class.java)
        try {
            // Enter the same consent launcher used after permission onboarding.
            // Accessibility is unnecessary for testing capture with input disabled.
            compose.runOnUiThread { compose.activity.requestScreen() }
            eventually("Android screen-sharing consent did not appear") {
                val root=instrumentation.uiAutomation.rootInActiveWindow
                val dialog=root?.findAccessibilityNodeInfosByViewId("com.android.systemui:id/screen_share_permission_dialog")
                if(dialog.isNullOrEmpty()) return@eventually false
                val button=root.findAccessibilityNodeInfosByViewId("android:id/button1")
                    ?.firstOrNull { it.isClickable && it.isEnabled }
                button?.performAction(AccessibilityNodeInfo.ACTION_CLICK)==true
            }
            eventually("Capture session did not start") { BotRuntime.status.value.running }
            eventually("No captured frame reached the game-window check") {
                BotRuntime.status.value.title=="Waiting for Blades of Brim…"
            }
            assertFalse(BotRuntime.qualified)
            compose.runOnUiThread { compose.activity.requestedOrientation=ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE }
            SystemClock.sleep(1200)
            assertTrue("Rotation unexpectedly ended screen sharing",BotRuntime.sessionActive)
            val notification=manager.activeNotifications.first { it.id==7 }.notification
            val stop=notification.actions.first { it.title.toString()=="Stop" }
            stop.actionIntent.send()
            eventually("Notification Stop did not end capture") {
                !BotRuntime.sessionActive && manager.activeNotifications.none { it.id==7 }
            }
            assertFalse(BotRuntime.qualified)
        } finally {
            context.startService(Intent(context,CaptureService::class.java).setAction(CaptureService.STOP))
        }
    }
}
