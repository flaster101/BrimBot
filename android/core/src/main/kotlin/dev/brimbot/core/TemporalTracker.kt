package dev.brimbot.core

import kotlin.math.abs
import kotlin.math.max

data class Observation(val kind: String, val x: Float, val y: Float, val confidence: Float)
data class Track(val id: Int, val observation: Observation, val lastMs: Long, val hits: Int, val velocityY: Float) {
    fun timeToContact(contactY: Float = .88f): Float =
        if (velocityY > .01f) max(0f, (contactY - observation.y) / velocityY) else Float.POSITIVE_INFINITY
}
class TemporalTracker {
    private var tracks = emptyList<Track>()
    private var nextId = 1
    fun update(observations: List<Observation>, nowMs: Long): List<Track> {
        val available = tracks.filter { nowMs - it.lastMs in 1..400 }.toMutableList()
        tracks = observations.filter { it.confidence.isFinite() && it.x in 0f..1f && it.y in 0f..1f }.map { obs ->
            val match = available.filter { it.observation.kind == obs.kind && abs(it.observation.x - obs.x) < .10f && abs(it.observation.y - obs.y) < .15f }
                .minByOrNull { abs(it.observation.x - obs.x) + abs(it.observation.y - obs.y) }
            if (match == null) Track(nextId++, obs, nowMs, 1, 0f)
            else {
                available.remove(match)
                val velocity = (obs.y - match.observation.y) * 1000f / (nowMs - match.lastMs)
                Track(match.id, obs, nowMs, match.hits + 1, .5f * velocity + .5f * match.velocityY)
            }
        }
        return tracks
    }
    fun reset() { tracks = emptyList() }
}
