package dev.brimbot.core

import kotlin.math.floor
import kotlin.math.min

data class Point(val x: Float, val y: Float)
data class Viewport(val left: Float, val top: Float, val width: Float, val height: Float) {
    init { require(listOf(left, top, width, height).all { it.isFinite() } && width > 0 && height > 0) }
    fun screen(x: Float, y: Float) = Point(left + x.coerceIn(0f, 1f) * width, top + y.coerceIn(0f, 1f) * height)
}
data class Letterbox(val sw: Int, val sh: Int, val tw: Int, val th: Int) {
    init { require(minOf(sw, sh, tw, th) > 0) }
    val scale = min(tw.toFloat() / sw, th.toFloat() / sh)
    val padX = (tw - sw * scale) / 2f
    val padY = (th - sh * scale) / 2f
    fun toModel(x: Float, y: Float) = Point(x * scale + padX, y * scale + padY)
    fun toSource(x: Float, y: Float) = Point((x - padX) / scale, (y - padY) / scale)
}
enum class Layout { NCHW, NHWC }
data class TensorSpec(val shape: LongArray) {
    init {
        require(shape.size == 4 && shape[0] == 1L && shape.all { it > 0 })
        require((shape[1] == 3L) xor (shape[3] == 3L)) { "Unsupported or ambiguous RGB layout" }
        require(shape.all { it <= 4096 })
    }
    val layout = if (shape[1] == 3L) Layout.NCHW else Layout.NHWC
    val width = shape[if (layout == Layout.NCHW) 3 else 2].toInt()
    val height = shape[if (layout == Layout.NCHW) 2 else 1].toInt()
}
object Preprocessor {
    fun rgb(pixels: IntArray, width: Int, height: Int, spec: TensorSpec): FloatArray {
        require(pixels.size == width * height)
        val tr = Letterbox(width, height, spec.width, spec.height)
        val out = FloatArray(spec.width * spec.height * 3)
        for (y in 0 until spec.height) for (x in 0 until spec.width) {
            val source = tr.toSource(x + .5f, y + .5f)
            val color = if (source.x >= 0 && source.x < width && source.y >= 0 && source.y < height)
                pixels[floor(source.y).toInt() * width + floor(source.x).toInt()] else 0x727272
            for (c in 0..2) {
                val value = ((color shr (16 - c * 8)) and 255) / 255f
                val index = if (spec.layout == Layout.NCHW) c * spec.width * spec.height + y * spec.width + x
                    else (y * spec.width + x) * 3 + c
                out[index] = value
            }
        }
        return out
    }
}
