package dev.brimbot.app

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONObject

data class BotStatus(val running: Boolean = false, val title: String = "Preview ready", val detail: String = "Autonomous play is still being validated.", val frames: Long = 0, val latencyMs: Long = 0)
object BotRuntime {
    private val mutable = MutableStateFlow(BotStatus())
    val status = mutable.asStateFlow()
    @Volatile var sessionActive = false
    @Volatile var qualified = false
    fun publish(status: BotStatus) { mutable.value = status }
    fun stop(detail: String = "You are in control.") {
        sessionActive = false
        mutable.value = BotStatus(title = "Stopped", detail = detail)
    }
    fun releaseStatus(context: Context): JSONObject = context.assets.open("release-status.json").bufferedReader().use { JSONObject(it.readText()) }
}
