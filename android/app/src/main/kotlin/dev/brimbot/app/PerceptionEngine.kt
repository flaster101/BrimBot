package dev.brimbot.app

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import ai.onnxruntime.TensorInfo
import android.content.Context
import android.graphics.Bitmap
import dev.brimbot.core.Preprocessor
import dev.brimbot.core.TensorSpec
import dev.brimbot.core.World
import java.nio.FloatBuffer

/** Diagnostic path candidate model. It cannot establish safe traversability. */
class PerceptionEngine(context: Context) : AutoCloseable {
    private val env = OrtEnvironment.getEnvironment()
    private val options = OrtSession.SessionOptions().apply { setIntraOpNumThreads(2) }
    private val session: OrtSession? = if (context.assets.list("")?.contains("path-candidate.onnx") == true)
        env.createSession(context.assets.open("path-candidate.onnx").use { it.readBytes() }, options) else null
    private val inputName = session?.inputNames?.singleOrNull()
    private val spec = inputName?.let { name ->
        TensorSpec((session!!.inputInfo.getValue(name).info as TensorInfo).shape)
    }
    var lastGroundFraction = 0f
        private set
    fun analyze(bitmap: Bitmap, timestamp: Long): World {
        val inputSpec = spec
        val model = session
        if (inputSpec != null && model != null && inputName != null) {
            val pixels = IntArray(bitmap.width * bitmap.height)
            bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)
            val floats = Preprocessor.rgb(pixels, bitmap.width, bitmap.height, inputSpec)
            OnnxTensor.createTensor(env, FloatBuffer.wrap(floats), inputSpec.shape).use { tensor ->
                model.run(mapOf(inputName to tensor)).use { results ->
                    val out = results[0] as OnnxTensor
                    val values = out.floatBuffer
                    var valid = 0
                    var count = 0
                    while (values.hasRemaining()) { val v=values.get(); if (v.isFinite() && v > .85f) valid++; count++ }
                    lastGroundFraction = if (count > 0) valid.toFloat()/count else 0f
                }
            }
        }
        // Missing gameplay state, hazard and player estimators must stay UNKNOWN.
        // A segmentation candidate is not evidence of active gameplay or safe lanes.
        return World(timestampMs = timestamp, perceptionValidated = false)
    }
    override fun close() { session?.close(); options.close() }
}
