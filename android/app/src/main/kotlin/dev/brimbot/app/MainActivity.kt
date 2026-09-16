package dev.brimbot.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionConfig
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.compose.collectAsStateWithLifecycle

private val Forest=Color(0xFF101918)
private val Surface=Color(0xFF1A2925)
private val Mint=Color(0xFFA1E7C7)
private val Gold=Color(0xFFD9BC82)
private val Ink=Color(0xFFE6EEE8)
private val Muted=Color(0xFFACC1B6)

class MainActivity : ComponentActivity() {
    private val prefs by lazy { getSharedPreferences("brimbot",MODE_PRIVATE) }
    private var awaitingAccess=false
    private var accessDialog by mutableStateOf(false)
    private var error by mutableStateOf<String?>(null)
    private val screenConsent=registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val data=result.data
        if (result.resultCode==RESULT_OK && data!=null) {
            startForegroundService(Intent(this,CaptureService::class.java).putExtra(CaptureService.CONSENT,data))
            packageManager.getLaunchIntentForPackage(GestureService.GAME)?.let { startActivity(it) }
                ?: run { error="Blades of Brim is not installed. Install the game, then return here." }
        } else { BotRuntime.stop("Screen sharing was cancelled.") }
    }
    private val notifications=registerForActivityResult(ActivityResultContracts.RequestPermission()) { requestScreen() }
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme=darkColorScheme(primary=Mint,onPrimary=Forest,secondary=Gold,
                background=Forest,surface=Surface,onSurface=Ink,onBackground=Ink,onSurfaceVariant=Muted)) {
                Surface(modifier=Modifier.fillMaxSize(),color=Forest) {
                    var onboarded by remember { mutableStateOf(prefs.getBoolean("onboarded",false)) }
                    if (!onboarded) Welcome { prefs.edit().putBoolean("onboarded",true).apply(); onboarded=true }
                    else Home()
                    if (accessDialog) AlertDialog(onDismissRequest={accessDialog=false},
                        title={Text("Allow game controls")},
                        text={Text("BrimBot uses Android’s accessibility setting to send swipes and taps to Blades of Brim and to check whether the game is open.\n\nThis preview only observes: automatic controls remain disabled. Screen images stay on your phone.\n\nIn Settings, choose BrimBot controls and turn it on. If Android restricts this setting for an APK, open BrimBot’s App info and allow restricted settings first.")},
                        confirmButton={TextButton(onClick={accessDialog=false; awaitingAccess=true; startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))}) { Text("Open Settings") }},
                        dismissButton={TextButton(onClick={accessDialog=false}){Text("Not now")}})
                    error?.let { message -> AlertDialog(onDismissRequest={error=null},title={Text("Before you start")},text={Text(message)},
                        confirmButton={TextButton(onClick={error=null}){Text("Got it")}}) }
                }
            }
        }
    }
    override fun onResume() {
        super.onResume()
        if (awaitingAccess && GestureService.instance!=null) { awaitingAccess=false; begin() }
    }
    private fun begin() {
        if (BotRuntime.status.value.running) { startService(Intent(this,CaptureService::class.java).setAction(CaptureService.STOP)); return }
        if (GestureService.instance==null) { accessDialog=true; return }
        if (Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) {
            notifications.launch(Manifest.permission.POST_NOTIFICATIONS)
        } else requestScreen()
    }
    private fun requestScreen() {
        val manager=getSystemService(MediaProjectionManager::class.java)
        // Whole-display capture provides an unambiguous relation to screen-space
        // gestures. Android still owns the explicit consent UI for every session.
        val request=if (Build.VERSION.SDK_INT>=34) manager.createScreenCaptureIntent(MediaProjectionConfig.createConfigForDefaultDisplay())
            else manager.createScreenCaptureIntent()
        screenConsent.launch(request)
    }
    @Composable private fun Welcome(done: ()->Unit) {
        Column(Modifier.fillMaxSize().systemBarsPadding().verticalScroll(rememberScrollState()).padding(28.dp),verticalArrangement=Arrangement.spacedBy(22.dp)) {
            Spacer(Modifier.height(32.dp))
            Image(painterResource(R.drawable.ic_brimbot),contentDescription="BrimBot shield",modifier=Modifier.size(108.dp))
            Eyebrow("YOUR ADVENTURE, ASSISTED")
            Text("Welcome to\nBrimBot.",fontSize=40.sp,lineHeight=44.sp,fontWeight=FontWeight.SemiBold)
            Text("A visual companion built to put survival first.",fontSize=19.sp,color=Muted)
            InfoCard("On your phone", "BrimBot looks at the game on your screen. Images are processed locally and are never uploaded.")
            InfoCard("Always your choice", "You choose when a session starts. Stop at any time from BrimBot or its notification.")
            InfoCard("An honest preview", "This version observes the screen. It does not play the game yet. Automatic controls stay off until gameplay reliability is verified.")
            Button(onClick=done,modifier=Modifier.fillMaxWidth().height(56.dp),shape=RoundedCornerShape(18.dp)) { Text("Get started",fontSize=16.sp,fontWeight=FontWeight.Bold) }
            Text("Independent project · Not affiliated with SYBO",color=Muted,fontSize=12.sp)
        }
    }
    @Composable private fun Home() {
        val status by BotRuntime.status.collectAsStateWithLifecycle()
        var page by remember { mutableStateOf("Play") }
        var taps by remember { mutableIntStateOf(0) }
        var developer by remember { mutableStateOf(false) }
        Scaffold(containerColor=Forest,bottomBar={
            NavigationBar(containerColor=Surface) {
                listOf("Play" to "◇","Objectives" to "◎","About" to "✦").forEach { (name,symbol) ->
                    NavigationBarItem(selected=page==name,onClick={page=name},icon={Text(symbol,fontSize=22.sp)},label={Text(name)})
                }
            }
        }) { insets ->
            Column(Modifier.padding(insets).fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),verticalArrangement=Arrangement.spacedBy(20.dp)) {
                Row(verticalAlignment=Alignment.CenterVertically) {
                    Image(painterResource(R.drawable.ic_brimbot),null,Modifier.size(46.dp))
                    Spacer(Modifier.width(10.dp))
                    Text("BRIMBOT",fontSize=22.sp,letterSpacing=3.sp,fontWeight=FontWeight.Bold)
                    Spacer(Modifier.weight(1f))
                    Surface(color=Color(0xFF3C3423),shape=RoundedCornerShape(30.dp)) {
                        Text("PREVIEW",Modifier.padding(horizontal=10.dp,vertical=6.dp),color=Gold,fontSize=10.sp,letterSpacing=1.sp)
                    }
                }
                when(page) {
                    "Play" -> {
                        Spacer(Modifier.height(10.dp))
                        Eyebrow("SURVIVAL COMES FIRST")
                        Text("A steadier path\nthrough Brim.",fontSize=34.sp,lineHeight=40.sp,fontWeight=FontWeight.SemiBold)
                        Text("Built to read the world, choose a safe path, and keep the adventure going.",fontSize=16.sp,lineHeight=24.sp,color=Muted)
                        Card(colors=CardDefaults.cardColors(containerColor=Surface),shape=RoundedCornerShape(24.dp)) {
                            Column(Modifier.padding(22.dp),verticalArrangement=Arrangement.spacedBy(13.dp)) {
                                Text("●  ${status.title}",color=if(status.running) Mint else Gold,fontWeight=FontWeight.SemiBold,fontSize=18.sp)
                                Text(status.detail,color=Muted,lineHeight=22.sp)
                                Button(onClick={begin()},modifier=Modifier.fillMaxWidth().height(58.dp),shape=RoundedCornerShape(16.dp),
                                    colors=ButtonDefaults.buttonColors(containerColor=if(status.running) Gold else Mint)) {
                                    Text(if(status.running) "STOP BRIMBOT" else "START PREVIEW",fontWeight=FontWeight.Bold,letterSpacing=1.sp)
                                }
                                Text("Observation only. You play; BrimBot watches.",fontSize=12.sp,color=Muted)
                            }
                        }
                        InfoCard("Game controls are not ready", "This preview cannot reliably identify every hazard or game state. It will not send gameplay gestures.")
                        if(status.frames>0) InfoCard("This session", "${status.frames} frames observed on your phone. No screen recording is saved.")
                        TextButton(onClick={packageManager.getLaunchIntentForPackage(GestureService.GAME)?.let { startActivity(it) } ?: run { error="Blades of Brim is not installed." }}) { Text("Open Blades of Brim  →") }
                    }
                    "Objectives" -> {
                        Text("A clear priority.",fontSize=32.sp,fontWeight=FontWeight.SemiBold)
                        InfoCard("01  Stay alive", "A safe route always comes before an optional reward.")
                        InfoCard("02  Make useful progress", "Combat, pets and collectibles should support the run.")
                        InfoCard("Current game objectives", "Automatic objective recognition is not yet verified. No mission progress is estimated in this preview.")
                    }
                    else -> {
                        Text("Made for the\nadventure.",fontSize=32.sp,lineHeight=38.sp,fontWeight=FontWeight.SemiBold)
                        InfoCard("Privacy", "Screen analysis stays on this device. BrimBot has no internet permission, does not record your screen, and never reads game memory.")
                        InfoCard("Your controls", "Android asks before every screen-sharing session. Accessibility can be turned off at any time in your phone’s settings.")
                        TextButton(onClick={startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))}) { Text("Manage game-control permission") }
                        TextButton(onClick={taps++; if(taps>=7) developer=true}) { Text("BrimBot ${BuildConfig.VERSION_NAME}") }
                        Text("Independent software. Blades of Brim belongs to SYBO. No game artwork is included.",color=Muted,lineHeight=22.sp)
                        if(developer) InfoCard("Session diagnostics", "Frames: ${status.frames}\nLast analysis: ${status.latencyMs} ms\nGesture qualification: disabled\nNo setting can bypass the release gate.")
                    }
                }
            }
        }
    }
    @Composable private fun Eyebrow(text: String) { Text(text,color=Gold,fontSize=11.sp,letterSpacing=2.sp,fontWeight=FontWeight.SemiBold) }
    @Composable private fun InfoCard(title: String,body: String) {
        Column(Modifier.fillMaxWidth().background(Surface,RoundedCornerShape(20.dp)).padding(20.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
            Text(title,fontWeight=FontWeight.SemiBold,fontSize=16.sp)
            Text(body,color=Muted,fontSize=14.sp,lineHeight=21.sp)
        }
    }
}
