package dev.brimbot.app

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.SystemClock
import android.view.WindowManager
import dev.brimbot.core.DecisionEngine
import kotlin.math.roundToInt

class CaptureService : Service() {
    companion object { const val STOP="dev.brimbot.STOP"; const val CONSENT="consent"; private const val ID=7 }
    private var projection: MediaProjection? = null
    private var display: VirtualDisplay? = null
    private var reader: ImageReader? = null
    private var worker: HandlerThread? = null
    private var handler: Handler? = null
    private var perception: PerceptionEngine? = null
    private val policy = DecisionEngine()
    private var frames=0L
    private var lastFrame=0L
    private var captureWidth=0
    private var captureHeight=0
    private var stopping=false
    override fun onBind(intent: Intent?): IBinder? = null
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == STOP) { BotRuntime.stop(); stopSelf(); return START_NOT_STICKY }
        if (projection != null || stopping) return START_NOT_STICKY
        val consent = if (Build.VERSION.SDK_INT >= 33) intent?.getParcelableExtra(CONSENT,Intent::class.java)
            else @Suppress("DEPRECATION") intent?.getParcelableExtra<Intent>(CONSENT)
        if (consent == null) { stopSelf(); return START_NOT_STICKY }
        val notification = notification()
        if (Build.VERSION.SDK_INT >= 29) startForeground(ID,notification,ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        else startForeground(ID,notification)
        BotRuntime.sessionActive=true
        BotRuntime.qualified=false // Cannot be enabled by a preference or developer switch.
        BotRuntime.publish(BotStatus(true,"Starting…","Preparing private, on-device screen analysis."))
        worker=HandlerThread("BrimBotCapture").also { it.start() }
        handler=Handler(worker!!.looper)
        try {
            perception=PerceptionEngine(this)
            val manager=getSystemService(MediaProjectionManager::class.java)
            projection=manager.getMediaProjection(Activity.RESULT_OK,consent)
            projection!!.registerCallback(object : MediaProjection.Callback() {
                override fun onStop() { BotRuntime.stop("Screen sharing ended."); stopSelf() }
                override fun onCapturedContentResize(width: Int,height: Int) { if (!stopping) resize(width,height) }
                override fun onCapturedContentVisibilityChanged(isVisible: Boolean) {
                    if (!isVisible) BotRuntime.publish(BotStatus(true,"Waiting for Blades of Brim…","Open the game to continue observing."))
                }
            },handler)
            val wm=getSystemService(WindowManager::class.java)
            val bounds = if (Build.VERSION.SDK_INT>=30) wm.maximumWindowMetrics.bounds else {
                val metrics=android.util.DisplayMetrics()
                @Suppress("DEPRECATION") wm.defaultDisplay.getRealMetrics(metrics)
                android.graphics.Rect(0,0,metrics.widthPixels,metrics.heightPixels)
            }
            resize(bounds.width(),bounds.height())
            display=projection!!.createVirtualDisplay("BrimBot",captureWidth,captureHeight,resources.configuration.densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,reader!!.surface,null,handler)
        } catch (_: Exception) {
            BotRuntime.stop("Screen analysis could not start. Please try again.")
            stopSelf()
        }
        return START_NOT_STICKY
    }
    private fun resize(width: Int,height: Int) {
        if (width<=0 || height<=0) return
        val scale=minOf(1f,960f/maxOf(width,height))
        val w=(width*scale).roundToInt().coerceAtLeast(1)
        val h=(height*scale).roundToInt().coerceAtLeast(1)
        if (w==captureWidth && h==captureHeight && reader!=null) return
        val old=reader
        val next=ImageReader.newInstance(w,h,PixelFormat.RGBA_8888,2)
        next.setOnImageAvailableListener({ source -> readFrame(source) },handler)
        reader=next; captureWidth=w; captureHeight=h
        display?.resize(w,h,resources.configuration.densityDpi)
        display?.surface=next.surface
        old?.close()
    }
    private fun readFrame(source: ImageReader) {
        val image=try { source.acquireLatestImage() } catch (_: IllegalStateException) { null } ?: return
        image.use {
            val now=SystemClock.elapsedRealtime()
            if (stopping || !BotRuntime.sessionActive || now-lastFrame<100) return
            lastFrame=now
            if (GestureService.instance?.gameViewport()==null) {
                BotRuntime.publish(BotStatus(true,"Waiting for Blades of Brim…","Open the game. You remain in control.",frames))
                return
            }
            try {
                val plane=image.planes[0]
                if (plane.pixelStride!=4) return
                val paddedWidth=plane.rowStride/plane.pixelStride
                val padded=Bitmap.createBitmap(paddedWidth,image.height,Bitmap.Config.ARGB_8888)
                padded.copyPixelsFromBuffer(plane.buffer)
                val bitmap=Bitmap.createBitmap(padded,0,0,image.width,image.height)
                try {
                    val world=perception!!.analyze(bitmap,now)
                    val decision=policy.decide(world,SystemClock.elapsedRealtime())
                    if (world.perceptionValidated) GestureService.instance?.perform(decision,now)
                    frames++
                    BotRuntime.publish(BotStatus(true,"Observing gameplay","Preview: automatic controls are disabled.",frames,SystemClock.elapsedRealtime()-now))
                } finally { if (bitmap !== padded) bitmap.recycle(); padded.recycle() }
            } catch (_: Exception) {
                BotRuntime.stop("Screen analysis stopped safely. Please restart BrimBot.")
                stopSelf()
            }
        }
    }
    private fun notification(): Notification {
        val nm=getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel("brimbot","BrimBot session",NotificationManager.IMPORTANCE_LOW))
        val open=PendingIntent.getActivity(this,0,Intent(this,MainActivity::class.java),PendingIntent.FLAG_IMMUTABLE)
        val stop=PendingIntent.getService(this,1,Intent(this,CaptureService::class.java).setAction(STOP),PendingIntent.FLAG_IMMUTABLE)
        return Notification.Builder(this,"brimbot").setSmallIcon(dev.brimbot.app.R.drawable.ic_brimbot)
            .setContentTitle("BrimBot preview is running").setContentText("Observation only • tap Stop to end screen analysis")
            .setContentIntent(open).addAction(Notification.Action.Builder(null,"Stop",stop).build()).setOngoing(true).build()
    }
    override fun onDestroy() {
        stopping=true; BotRuntime.sessionActive=false
        val oldProjection=projection; projection=null
        handler?.post {
            display?.release(); display=null
            reader?.close(); reader=null
            perception?.close(); perception=null
            oldProjection?.stop()
            worker?.quitSafely()
        }
        stopForeground(STOP_FOREGROUND_REMOVE)
        if (BotRuntime.status.value.running) BotRuntime.stop()
        super.onDestroy()
    }
}
