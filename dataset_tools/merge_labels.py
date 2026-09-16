"""Merge independent label batches without duplicates or silent mask collisions."""
import argparse
import json
from pathlib import Path
import shutil

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("output",type=Path);p.add_argument("inputs",type=Path,nargs="+");a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    rows=[];seen=set()
    for batch,source in enumerate(a.inputs):
        for row in json.loads((source/"labels.json").read_text()):
            if row["id"] in seen: continue
            if row["split"]=="test": raise ValueError("Quarantined test label")
            seen.add(row["id"])
            mask=f"batch{batch}_{row['mask']}"
            shutil.copyfile(source/row["mask"],a.output/mask)
            rows.append(dict(row,mask=mask))
    (a.output/"labels.json").write_text(json.dumps(rows,indent=2))
    report={s:dict(total=sum(r["split"]==s for r in rows),accepted=sum(r["split"]==s and r["accepted"] for r in rows)) for s in ["train","val"]}
    (a.output/"report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
