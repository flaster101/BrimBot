"""Refine train/val after discovering that the tail is loot UI, before fitting.

The original quarantined test interval is never decoded or reassigned.
"""
import json
from pathlib import Path
import shutil
import cv2
import numpy as np

if __name__=="__main__":
    source=Path("data/reference-diverse"); target=Path("data/surface-candidates")
    (target/"frames").mkdir(parents=True,exist_ok=True)
    rows=[json.loads(x) for x in (source/"frames.jsonl").read_text().splitlines()]
    selected=[]
    for row in rows:
        t=row["timestamp_s"]
        if not (80<t<2700 or 2730<t<3990): continue
        rgb=cv2.cvtColor(cv2.imread(str(source/row["file"])),cv2.COLOR_BGR2RGB).astype(float)
        roi=rgb[int(len(rgb)*.3):int(len(rgb)*.87),int(rgb.shape[1]*.15):int(rgb.shape[1]*.85)]
        green=(roi[:,:,1]>roi[:,:,0]*1.12)&(roi[:,:,1]>roi[:,:,2]*1.25)&(roi[:,:,1]>90)
        fraction=float(green.mean())
        if fraction<.15: continue
        row=dict(row,split="train" if t<2700 else "val",candidate_green_fraction=fraction,
                 selection_limitation="Green-surface subset; no claim of safe traversability")
        shutil.copyfile(source/row["file"],target/row["file"])
        selected.append(row)
    (target/"frames.jsonl").write_text("".join(json.dumps(r)+"\n" for r in selected))
    plan=json.loads((source/"split.json").read_text())
    plan.update(train=[80,2700],val=[2730,3990],surface_subset=True,
                selection_note="Train/val refined before student fitting; original test remains quarantined.",
                selected=len(selected))
    (target/"split.json").write_text(json.dumps(plan,indent=2))
    print({split:sum(r["split"]==split for r in selected) for split in ["train","val"]})
