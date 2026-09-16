"""Reject uncertain pseudo labels. Never promote pseudo labels to ground truth."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

CLASSES = {"goon", "flapper", "crusher", "wizard", "looter", "summoning_crystal",
           "rock", "pot", "projectile", "coin", "essence", "powerup", "portal", "player"}


def rejection(label: dict, sample: dict) -> str | None:
    if sample["split"] == "test":
        return "test_is_quarantined"
    if label.get("class") not in CLASSES:
        return "unknown_class"
    box = label.get("box", [])
    if len(box) != 4 or any(not isinstance(x,(float,int)) or not math.isfinite(x) for x in box):
        return "invalid_box"
    x1,y1,x2,y2=box
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        return "out_of_bounds"
    if (x2-x1)*(y2-y1) < .0001:
        return "too_small"
    if not label.get("teacher") or not label.get("teacher_revision"):
        return "missing_provenance"
    if label.get("confidence",0) < .85:
        return "low_confidence"
    if label.get("track_confirmations",0) < 3:
        return "unconfirmed_track"
    if label.get("appearance_consistency",0) < .8 or label.get("temporal_iou",0) < .45:
        return "inconsistent_track"
    return None


def audit(samples: list[dict], labels: list[dict]) -> dict:
    by_id={s["id"]:s for s in samples}
    accepted, rejected, seen = [], [], set()
    for label in labels:
        sample=by_id.get(label.get("sample_id"))
        reason="missing_sample" if sample is None else rejection(label,sample)
        identity=(label.get("sample_id"),label.get("class"),tuple(label.get("box",[])))
        if identity in seen:
            reason="duplicate_label"
        seen.add(identity)
        if reason:
            rejected.append(dict(label=label,reason=reason))
        else:
            accepted.append(dict(label,label_status="pseudo",split=sample["split"]))
    return dict(accepted=accepted,rejected=rejected,ground_truth_count=0)


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("samples",type=Path); p.add_argument("labels",type=Path); p.add_argument("output",type=Path)
    a=p.parse_args()
    read=lambda path:[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    a.output.write_text(json.dumps(audit(read(a.samples),read(a.labels)),indent=2),encoding="utf-8")
