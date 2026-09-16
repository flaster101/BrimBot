package dev.brimbot.app

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import ai.onnxruntime.TensorInfo
import android.graphics.BitmapFactory
import androidx.test.platform.app.InstrumentationRegistry
import dev.brimbot.core.Preprocessor
import dev.brimbot.core.TensorSpec
import org.json.JSONObject
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.FloatBuffer
import kotlin.math.abs

class ModelParityTest {
    @Test fun pythonAndAndroidProduceMatchingOutput() {
        val assets=InstrumentationRegistry.getInstrumentation().targetContext.assets
        val fixtures=InstrumentationRegistry.getInstrumentation().context.assets
        // This test intentionally fails when the packaged model/fixture is absent.
        val model=assets.open("path-candidate.onnx").use { it.readBytes() }
        val fixture=fixtures.open("parity.json").bufferedReader().use { JSONObject(it.readText()) }
        val image=fixtures.open("parity.png").use { BitmapFactory.decodeStream(it) }
        val pixels=IntArray(image.width*image.height)
        image.getPixels(pixels,0,image.width,0,0,image.width,image.height)
        val env=OrtEnvironment.getEnvironment()
        OrtSession.SessionOptions().use { options ->
            env.createSession(model,options).use { session ->
                val name=session.inputNames.single()
                val spec=TensorSpec((session.inputInfo.getValue(name).info as TensorInfo).shape)
                val input=Preprocessor.rgb(pixels,image.width,image.height,spec)
                OnnxTensor.createTensor(env,FloatBuffer.wrap(input),spec.shape).use { tensor ->
                    session.run(mapOf(name to tensor)).use { result ->
                        val values=(result[0] as OnnxTensor).floatBuffer
                        val expected=fixture.getJSONArray("expected")
                        assertTrue(values.remaining()==expected.length())
                        var maxError=0.0
                        for(i in 0 until expected.length()) {
                            val value=values.get()
                            assertTrue(value.isFinite())
                            maxError=maxOf(maxError,abs(value-expected.getDouble(i)))
                        }
                        assertTrue("max error=$maxError",maxError<=fixture.getDouble("max_absolute_error"))
                    }
                }
            }
        }
        image.recycle()
    }
}
