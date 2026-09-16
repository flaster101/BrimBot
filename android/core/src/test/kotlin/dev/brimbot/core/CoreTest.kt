package dev.brimbot.core

import org.junit.Assert.*
import org.junit.Test

class CoreTest {
    private fun active() = World(1000,Phase.PLAYING,.99f,3,laneConfidence=.99f,safe=listOf(.99f,.99f,.99f),grounded=true,perceptionValidated=true)
    @Test fun survivalOverridesReward() {
        val decision=DecisionEngine().decide(active().copy(threats=listOf(Threat("gap",1,.4f,.99f,3)),rewards=listOf(0f,1f,0f)))
        assertEquals(Action.LEFT,decision.action); assertEquals("EVADE_GAP",decision.reason)
    }
    @Test fun noMenuGestures() {
        Phase.entries.filter { it!=Phase.PLAYING }.forEach { phase ->
            assertEquals(Action.NONE,DecisionEngine().decide(active().copy(phase=phase)).action)
        }
    }
    @Test fun noRewardIntoHazard() {
        val w=active().copy(rewards=listOf(1f,0f,0f),threats=listOf(Threat("gap",0,.4f,.99f,3)))
        assertEquals(Action.NONE,DecisionEngine().decide(w).action)
    }
    @Test fun noBlindJump() {
        val w=active().copy(safe=listOf(0f,1f,0f),threats=listOf(Threat("gap",1,.4f,.99f,3)))
        assertEquals(Action.NONE,DecisionEngine().decide(w).action)
        assertEquals(Action.UP,DecisionEngine().decide(w.copy(jumpLandingSafe=true)).action)
    }
    @Test fun staleFramesAndQualification() {
        assertEquals("STALE_FRAME",DecisionEngine().decide(active(),1400).reason)
        assertEquals("PERCEPTION_NOT_QUALIFIED",DecisionEngine().decide(active().copy(perceptionValidated=false)).reason)
        assertEquals("INVALID_OBSERVATION",DecisionEngine().decide(active().copy(safe=listOf(1f,Float.NaN,1f))).reason)
    }
    @Test fun petNotUsedWithoutReason() {
        assertEquals(Action.NONE,DecisionEngine().decide(active().copy(petAvailable=true,petConfidence=1f)).action)
    }
    @Test fun aspectRatioRoundTrips() {
        listOf(720 to 1280,1080 to 1920,1080 to 2400,1440 to 3200,2208 to 1840,1920 to 1080).forEach { (w,h) ->
            val tr=Letterbox(w,h,320,320)
            val p=tr.toModel(w*.12f,h*.87f); val q=tr.toSource(p.x,p.y)
            assertEquals(w*.12f,q.x,.001f); assertEquals(h*.87f,q.y,.001f)
        }
    }
    @Test fun tensorLayoutParity() {
        val pixels=intArrayOf(0xFF0000,0x00FF00,0x0000FF,0xFFFFFF)
        val a=Preprocessor.rgb(pixels,2,2,TensorSpec(longArrayOf(1,3,8,8)))
        val b=Preprocessor.rgb(pixels,2,2,TensorSpec(longArrayOf(1,8,8,3)))
        for (i in 0 until 64) for(c in 0..2) assertEquals(a[c*64+i],b[i*3+c],0f)
    }
    @Test fun trackerUsesOneToOneMatchingAndExpires() {
        val t=TemporalTracker()
        t.update(listOf(Observation("goon",.5f,.3f,.99f)),1000)
        val tracks=t.update(listOf(Observation("goon",.5f,.4f,.99f),Observation("goon",.51f,.4f,.99f)),1100)
        assertEquals(2,tracks.size); assertEquals(1,tracks.count { it.hits==2 })
        assertEquals(1,t.update(listOf(Observation("goon",.5f,.5f,.99f)),2000).single().hits)
    }
    @Test fun dispatchDebounced() {
        val engine=DecisionEngine()
        val w=active().copy(rewards=listOf(1f,0f,0f))
        assertEquals(Action.LEFT,engine.decide(w).action)
        assertEquals("GESTURE_COOLDOWN",engine.decide(w.copy(timestampMs=1100)).reason)
    }
}
