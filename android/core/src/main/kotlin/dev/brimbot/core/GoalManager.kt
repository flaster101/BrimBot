package dev.brimbot.core

data class Goal(val kind: String, val target: Int, val progress: Int, val evidenceText: String)
/** Consumes OCR evidence only; there is no manual configuration or inferred progress. */
class GoalManager {
    private var candidate: String? = null
    private var confirmations=0
    private var lastMs=-1L
    var current: Goal? = null
        private set
    fun observe(text: String, confidence: Float, nowMs: Long): Goal? {
        if (lastMs>=nowMs) return current
        val separated=lastMs>=0 && nowMs-lastMs>1500
        lastMs=nowMs
        if (confidence<.95f || !confidence.isFinite() || separated) {
            candidate=null; confirmations=0; current=null
            if (confidence<.95f || !confidence.isFinite()) return null
        }
        val normalized=text.lowercase().replace(Regex("\\s+")," ").trim()
        if (normalized==candidate) confirmations++ else { candidate=normalized; confirmations=1; current=null }
        if (confirmations<3) return null
        val patterns=listOf(
            Regex("defeat (\\d+) flappers.*? (\\d+)\\s*/\\s*(\\d+)") to "defeat_flappers",
            Regex("do (\\d+) rolls.*? (\\d+)\\s*/\\s*(\\d+)") to "roll",
            Regex("collect (\\d+) essence.*? (\\d+)\\s*/\\s*(\\d+)") to "collect_essence"
        )
        for ((pattern,kind) in patterns) {
            val match=pattern.matchEntire(normalized) ?: continue
            val target=match.groupValues[1].toIntOrNull() ?: continue
            val progress=match.groupValues[2].toIntOrNull() ?: continue
            val denominator=match.groupValues[3].toIntOrNull() ?: continue
            if (target==denominator && target in 1..100000 && progress in 0..target) current=Goal(kind,target,progress,text)
            return current
        }
        current=null
        return null
    }
    fun reset() { candidate=null; confirmations=0; lastMs=-1; current=null }
}
