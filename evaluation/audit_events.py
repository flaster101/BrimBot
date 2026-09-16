"""Action trace checks. Zero violations with zero actions is abstention only."""
import json
from pathlib import Path
import argparse

def audit(events):
    findings=[]; previous=None; previous_lateral=None; actions=0
    for e in events:
        if e["action"]=="NONE": continue
        actions+=1
        if e.get("state")!="playing": findings.append(dict(timestamp=e["timestamp_s"],reason="input_outside_playing"))
        if previous and e["timestamp_s"]-previous["timestamp_s"]<.11:
            findings.append(dict(timestamp=e["timestamp_s"],reason="gesture_spam"))
        if e["action"] in {"LEFT","RIGHT"}:
            if previous_lateral and previous_lateral["action"]!=e["action"] and e["timestamp_s"]-previous_lateral["timestamp_s"]<.9:
                findings.append(dict(timestamp=e["timestamp_s"],reason="lane_oscillation"))
            previous_lateral=e
        if e.get("destination_safe") is False:
            findings.append(dict(timestamp=e["timestamp_s"],reason="unsafe_destination"))
        if e.get("lethal_threat") and e.get("reason") in {"SAFE_REWARD","ROLL_ATTACK","JUMP_ATTACK"}:
            findings.append(dict(timestamp=e["timestamp_s"],reason="lethal_threat_ignored"))
        previous=e
    return dict(actions=actions,findings=findings,abstained_entirely=actions==0)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("events",type=Path);a=p.parse_args()
    print(json.dumps(audit(json.loads(x) for x in a.events.read_text().splitlines()),indent=2))
