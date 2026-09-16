package dev.brimbot.core

enum class Action { NONE, LEFT, RIGHT, UP, DOWN, TAP, DOUBLE_TAP }
enum class Phase { UNKNOWN, MENU, LOADING, PLAYING, PAUSED, DEAD, RESULTS }
data class Threat(val kind: String, val lane: Int, val ttc: Float, val confidence: Float, val confirmations: Int = 1)
data class World(
    val timestampMs: Long,
    val phase: Phase = Phase.UNKNOWN,
    val phaseConfidence: Float = 0f,
    val phaseConfirmations: Int = 0,
    val lane: Int = 1,
    val laneConfidence: Float = 0f,
    val safe: List<Float> = listOf(0f, 0f, 0f),
    val threats: List<Threat> = emptyList(),
    val rewards: List<Float> = listOf(0f, 0f, 0f),
    val grounded: Boolean = false,
    val jumpLandingSafe: Boolean = false,
    val mounted: Boolean = false,
    val petAvailable: Boolean = false,
    val petConfidence: Float = 0f,
    val objective: String? = null,
    val perceptionValidated: Boolean = false
)
data class Decision(val action: Action, val reason: String, val emergency: Boolean = false)
class DecisionEngine {
    private var lastActionMs = -10000L
    private var lastLateralMs = -10000L
    private var lastLateral: Action? = null
    fun decide(w: World, nowMs: Long = w.timestampMs): Decision {
        fun hold(reason: String) = Decision(Action.NONE, reason)
        if (!w.perceptionValidated) return hold("PERCEPTION_NOT_QUALIFIED")
        if (w.safe.size != 3 || w.rewards.size != 3 ||
            (w.safe + w.rewards + listOf(w.phaseConfidence, w.laneConfidence)).any { !it.isFinite() })
            return hold("INVALID_OBSERVATION")
        if (nowMs - w.timestampMs !in 0..250) return hold("STALE_FRAME")
        if (w.phase != Phase.PLAYING || w.phaseConfidence < .95f || w.phaseConfirmations < 3)
            return hold("NOT_CONFIRMED_PLAYING")
        if (w.lane !in 0..2 || w.laneConfidence < .85f) return hold("UNKNOWN_PLAYER_LANE")
        val threats = w.threats.filter { it.lane in 0..2 && it.ttc.isFinite() && it.confidence.isFinite() &&
            it.ttc in 0f..1f && it.confidence >= .85f && (it.confirmations >= 2 || (it.ttc < .25f && it.confidence >= .98f)) }
        val current = threats.filter { it.lane == w.lane }.sortedBy { it.ttc }
        val danger = current.firstOrNull { it.kind in setOf("gap", "rock", "crusher", "projectile", "wall") }
        val neighbors = listOf(w.lane - 1, w.lane + 1).filter { lane ->
            lane in 0..2 && w.safe[lane] >= .92f && threats.none { it.lane == lane }
        }
        fun move(lane: Int) = if (lane < w.lane) Action.LEFT else Action.RIGHT
        if (danger != null) {
            if (neighbors.isNotEmpty()) return emit(w, move(neighbors.maxBy { w.safe[it] }), "EVADE_${danger.kind.uppercase()}", true)
            if (danger.kind == "gap" && w.grounded && w.jumpLandingSafe)
                return emit(w, Action.UP, "GAP_WITH_CONFIRMED_LANDING", true)
            if (w.petAvailable && w.petConfidence >= .98f && !w.mounted && danger.ttc > .45f)
                return emit(w, Action.DOUBLE_TAP, "DEFENSIVE_PET", true)
            return hold("NO_VERIFIED_ESCAPE")
        }
        if (w.safe[w.lane] < .92f) {
            if (neighbors.isNotEmpty()) return emit(w, move(neighbors.maxBy { w.safe[it] }), "MAINTAIN_SAFE_PATH")
            return hold("UNCERTAIN_PATH")
        }
        val enemy = current.firstOrNull { it.kind in setOf("goon", "looter", "flapper", "wizard") }
        if (enemy != null && enemy.ttc in .2f.. .65f) {
            if (w.mounted) return emit(w, Action.TAP, "MOUNTED_TARGET")
            if (enemy.kind == "flapper" && w.grounded && w.jumpLandingSafe) return emit(w, Action.UP, "JUMP_ATTACK")
            if (enemy.kind in setOf("goon", "looter") && w.grounded) return emit(w, Action.DOWN, "ROLL_ATTACK")
        }
        if (w.objective == "use_pet" && w.petAvailable && w.petConfidence >= .98f && !w.mounted && threats.isEmpty())
            return emit(w, Action.DOUBLE_TAP, "SAFE_PET_OBJECTIVE")
        val rewards = neighbors.filter { w.rewards[it] > w.rewards[w.lane] + .25f }
        if (rewards.isNotEmpty()) return emit(w, move(rewards.maxBy { w.rewards[it] }), "SAFE_REWARD")
        return hold("CONTINUE_FORWARD")
    }
    private fun emit(w: World, action: Action, reason: String, emergency: Boolean = false): Decision {
        if (w.timestampMs - lastActionMs < if (emergency) 110 else 240) return Decision(Action.NONE, "GESTURE_COOLDOWN")
        if (action in listOf(Action.LEFT, Action.RIGHT)) {
            if (!emergency && lastLateral != null && lastLateral != action && w.timestampMs - lastLateralMs < 900)
                return Decision(Action.NONE, "AVOID_OSCILLATION")
            lastLateral = action
            lastLateralMs = w.timestampMs
        }
        lastActionMs = w.timestampMs
        return Decision(action, reason, emergency)
    }
}
