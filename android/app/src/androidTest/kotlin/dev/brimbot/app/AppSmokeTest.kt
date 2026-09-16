package dev.brimbot.app

import android.content.Intent
import android.content.ContentValues
import android.graphics.Bitmap
import android.provider.MediaStore
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import java.io.File

class AppSmokeTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun onboardingMainObjectivesAndAboutAreHonestAndAccessible() {
        if (compose.onAllNodesWithText("Get started").fetchSemanticsNodes().isNotEmpty()) {
            compose.onNodeWithText("Get started").performScrollTo().performClick()
        }
        compose.onNodeWithText("START PREVIEW").assertExists()
        compose.onNodeWithText("Game controls are not ready").assertExists()
        assertFalse(BotRuntime.qualified)
        assertFalse(BotRuntime.sessionActive)
        compose.waitForIdle()
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        val resolver=instrumentation.targetContext.contentResolver
        val screenshotUri=resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME,"brimbot-home-final.png")
            put(MediaStore.Downloads.MIME_TYPE,"image/png")
            put(MediaStore.Downloads.RELATIVE_PATH,"Download/BrimBotTests")
        })!!
        instrumentation.uiAutomation.takeScreenshot().let { image ->
            resolver.openOutputStream(screenshotUri)!!.use { image.compress(Bitmap.CompressFormat.PNG,100,it) }; image.recycle()
        }
        compose.onNodeWithText("Objectives",useUnmergedTree=true).performClick()
        compose.onNodeWithText("Current game objectives").assertExists()
        compose.onNodeWithText("About",useUnmergedTree=true).performClick()
        compose.onNodeWithText("Privacy").assertExists()
        compose.onNodeWithText("Play",useUnmergedTree=true).performClick()
        compose.onNodeWithText("START PREVIEW").performClick()
        compose.onNodeWithText("Allow game controls").assertExists()
        compose.onNodeWithText("Not now").performClick()
        assertFalse(BotRuntime.sessionActive)
    }
    @Test fun missingCaptureConsentCannotStartSession() {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        context.startService(Intent(context,CaptureService::class.java))
        compose.waitForIdle()
        assertFalse(BotRuntime.sessionActive)
    }
}
