import dataclasses
import math
import random
import pytest
from perception.policy import Policy, World, Threat


def active(**kwargs):
    base=dict(timestamp_ms=1000,phase="playing",phase_confidence=.99,phase_confirmations=3,
              lane_confidence=.99,safe=(.99,.99,.99),grounded=True,perception_validated=True)
    base.update(kwargs)
    return World(**base)


def test_lethal_gap_overrides_coin_and_pet_objective():
    w=active(threats=[Threat("gap",1,.4,.99,3)],rewards=(0,1,0),objective="use_pet",pet_available=True,pet_confidence=1)
    d=Policy().decide(w)
    assert d.action=="LEFT" and d.reason=="EVADE_GAP"


@pytest.mark.parametrize("phase",["unknown","menu","loading","paused","dead","results"])
def test_no_input_outside_gameplay(phase):
    assert Policy().decide(active(phase=phase,threats=[Threat("crusher",1,.1,1,3)])).action=="NONE"


def test_no_coin_chase_into_gap():
    w=active(rewards=(1,0,0),threats=[Threat("gap",0,.7,.99,3)])
    assert Policy().decide(w).action=="NONE"


def test_imminent_target_enemy_blocks_reward_lane():
    w=active(rewards=(1,0,0),threats=[Threat("goon",0,.1,.99,3)])
    assert Policy().decide(w).action=="NONE"


def test_jump_requires_visible_landing():
    w=active(safe=(0,.99,0),threats=[Threat("gap",1,.4,.99,3)])
    assert Policy().decide(w).action=="NONE"
    assert Policy().decide(dataclasses.replace(w,jump_landing_safe=True)).action=="UP"


def test_unknown_perception_and_player_fail_closed():
    assert Policy().decide(active(perception_validated=False)).reason=="PERCEPTION_NOT_QUALIFIED"
    assert Policy().decide(active(lane_confidence=.1)).reason=="UNKNOWN_PLAYER_LANE"


@pytest.mark.parametrize("now",[999,1251,5000])
def test_stale_and_future_frames(now):
    assert Policy().decide(active(),now).reason=="STALE_FRAME"


def test_pet_preserved_on_easy_section():
    assert Policy().decide(active(pet_available=True,pet_confidence=1)).action=="NONE"


def test_temporal_confirmation_and_emergency_override():
    w=active(threats=[Threat("gap",1,.5,.90,1)])
    assert Policy().decide(w).action=="NONE"
    w.threats=[Threat("gap",1,.1,.99,1)]
    assert Policy().decide(w).action=="LEFT"


def test_gesture_debounce_and_oscillation():
    p=Policy()
    assert p.decide(active(rewards=(1,0,0))).action=="LEFT"
    assert p.decide(active(timestamp_ms=1100,rewards=(1,0,0))).reason=="GESTURE_COOLDOWN"
    assert p.decide(active(timestamp_ms=1400,rewards=(0,0,1))).reason=="AVOID_OSCILLATION"
    assert p.decide(active(timestamp_ms=1500,threats=[Threat("crusher",1,.2,.99,3)],safe=(0,.99,.99))).action=="RIGHT"


def test_randomized_lateral_actions_never_enter_unsafe_lane():
    rng=random.Random(7)
    for _ in range(1500):
        lane=rng.randrange(3)
        safe=tuple(rng.choice([0,.5,.91,.95,1]) for _ in range(3))
        w=active(lane=lane,safe=safe,rewards=tuple(rng.random() for _ in range(3)))
        d=Policy().decide(w)
        if d.action in {"LEFT","RIGHT"}:
            destination=lane+(-1 if d.action=="LEFT" else 1)
            assert 0<=destination<=2 and safe[destination]>=.92


def test_nan_rejected():
    assert Policy().decide(active(safe=(1,math.nan,1))).reason=="INVALID_OBSERVATION"
