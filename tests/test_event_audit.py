from evaluation.audit_events import audit

def test_detects_unsafe_actions_and_does_not_mistake_abstention_for_play():
    assert audit([dict(timestamp_s=0,state="unknown",action="NONE")])["abstained_entirely"]
    result=audit([
        dict(timestamp_s=0,state="menu",action="LEFT",destination_safe=False),
        dict(timestamp_s=.05,state="playing",action="RIGHT",reason="SAFE_REWARD",lethal_threat=True)])
    reasons={r["reason"] for r in result["findings"]}
    assert reasons=={"input_outside_playing","unsafe_destination","gesture_spam","lane_oscillation","lethal_threat_ignored"}
