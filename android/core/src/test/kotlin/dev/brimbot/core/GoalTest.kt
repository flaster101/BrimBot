package dev.brimbot.core
import org.junit.Assert.*
import org.junit.Test

class GoalTest {
    @Test fun requiresThreeIndependentConsistentReads() {
        val g=GoalManager()
        assertNull(g.observe("Defeat 50 Flappers 1/50",.99f,100))
        assertNull(g.observe("Defeat 50 Flappers 1/50",.99f,100))
        assertNull(g.observe("Defeat 50 Flappers 1/50",.99f,200))
        assertEquals(1,g.observe("Defeat 50 Flappers 1/50",.99f,300)?.progress)
        assertNull(g.observe("Unrecognized objective",.99f,400))
    }
    @Test fun impossibleAndLowConfidenceProgressNotShown() {
        val g=GoalManager()
        repeat(4) { assertNull(g.observe("Collect 50 essence 70/50",.99f,it*100L)) }
        assertNull(g.observe("Collect 50 essence 1/50",.50f,1000))
    }
}
