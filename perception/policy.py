"""Deterministic policy. Observations are evidence, commands are not observations."""
from __future__ import annotations
from dataclasses import dataclass, field
import math


@dataclass
class Threat:
    kind: str
    lane: int
    ttc: float
    confidence: float
    confirmations: int=1


@dataclass
class World:
    timestamp_ms: int
    phase: str="unknown"
    phase_confidence: float=0
    phase_confirmations: int=0
    lane: int=1
    lane_confidence: float=0
    safe: tuple[float,float,float]=(0.,0.,0.)
    threats: list[Threat]=field(default_factory=list)
    rewards: tuple[float,float,float]=(0.,0.,0.)
    grounded: bool=False
    jump_landing_safe: bool=False
    mounted: bool=False
    pet_available: bool=False
    pet_confidence: float=0
    objective: str | None=None
    perception_validated: bool=False


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    emergency: bool=False


class Policy:
    def __init__(self):
        self.last_action_ms=-10000
        self.last_lateral_ms=-10000
        self.last_lateral=None

    def decide(self,w: World,now_ms: int | None=None) -> Decision:
        now=w.timestamp_ms if now_ms is None else now_ms
        hold=lambda r:Decision("NONE",r)
        if not w.perception_validated:
            return hold("PERCEPTION_NOT_QUALIFIED")
        values=[w.phase_confidence,w.lane_confidence,*w.safe,*w.rewards]
        if any(not math.isfinite(v) for v in values) or len(w.safe)!=3 or len(w.rewards)!=3:
            return hold("INVALID_OBSERVATION")
        if not 0<=now-w.timestamp_ms<=250:
            return hold("STALE_FRAME")
        if w.phase!="playing" or w.phase_confidence<.95 or w.phase_confirmations<3:
            return hold("NOT_CONFIRMED_PLAYING")
        if w.lane not in (0,1,2) or w.lane_confidence<.85:
            return hold("UNKNOWN_PLAYER_LANE")
        threats=[t for t in w.threats if t.lane in (0,1,2) and math.isfinite(t.ttc)
                 and math.isfinite(t.confidence) and 0<=t.ttc<=1.0
                 and t.confidence>=.85 and (t.confirmations>=2 or (t.ttc<.25 and t.confidence>=.98))]
        current=sorted((t for t in threats if t.lane==w.lane),key=lambda t:t.ttc)
        danger=next((t for t in current if t.kind in {"gap","rock","crusher","projectile","wall"}),None)
        # A path is not safe if any imminent threat occupies it; lateral route is
        # adjacent only. A two-lane teleport is never permitted.
        def safe(lane):
            return w.safe[lane]>=.92 and not any(t.lane==lane for t in threats)
        neighbors=[x for x in (w.lane-1,w.lane+1) if x in (0,1,2) and safe(x)]
        if danger:
            if neighbors:
                dest=max(neighbors,key=lambda x:w.safe[x])
                return self._emit(w,"LEFT" if dest<w.lane else "RIGHT","EVADE_"+danger.kind.upper(),True)
            if danger.kind=="gap" and w.grounded and w.jump_landing_safe:
                return self._emit(w,"UP","GAP_WITH_CONFIRMED_LANDING",True)
            if w.pet_available and w.pet_confidence>=.98 and not w.mounted and danger.ttc>.45:
                return self._emit(w,"DOUBLE_TAP","DEFENSIVE_PET",True)
            return hold("NO_VERIFIED_ESCAPE")
        if w.safe[w.lane]<.92:
            if neighbors:
                dest=max(neighbors,key=lambda x:w.safe[x])
                return self._emit(w,"LEFT" if dest<w.lane else "RIGHT","MAINTAIN_SAFE_PATH")
            return hold("UNCERTAIN_PATH")
        enemy=next((t for t in current if t.kind in {"goon","looter","flapper","wizard"}),None)
        if enemy and .2<=enemy.ttc<=.65:
            if w.mounted:
                return self._emit(w,"TAP","MOUNTED_TARGET")
            if enemy.kind=="flapper" and w.grounded and w.jump_landing_safe:
                return self._emit(w,"UP","JUMP_ATTACK")
            if enemy.kind in {"goon","looter"} and w.grounded:
                return self._emit(w,"DOWN","ROLL_ATTACK")
        if w.objective=="use_pet" and w.pet_available and w.pet_confidence>=.98 and not w.mounted and not threats:
            return self._emit(w,"DOUBLE_TAP","SAFE_PET_OBJECTIVE")
        rewards=[n for n in neighbors if w.rewards[n]>w.rewards[w.lane]+.25]
        if rewards:
            dest=max(rewards,key=lambda x:w.rewards[x])
            return self._emit(w,"LEFT" if dest<w.lane else "RIGHT","SAFE_REWARD")
        return hold("CONTINUE_FORWARD")

    def _emit(self,w,action,reason,emergency=False):
        elapsed=w.timestamp_ms-self.last_action_ms
        if elapsed<(110 if emergency else 240):
            return Decision("NONE","GESTURE_COOLDOWN")
        if action in {"LEFT","RIGHT"}:
            if not emergency and self.last_lateral and self.last_lateral!=action and w.timestamp_ms-self.last_lateral_ms<900:
                return Decision("NONE","AVOID_OSCILLATION")
            self.last_lateral=action
            self.last_lateral_ms=w.timestamp_ms
        self.last_action_ms=w.timestamp_ms
        return Decision(action,reason,emergency)
