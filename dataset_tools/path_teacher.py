"""Prompt agreement + adjacent-frame flow QC for research-only surface labels.

Semantic ground is NOT proof of traversability. Labels remain pseudo labels and
cannot qualify game control. No test frames are decoded by this tool.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw
import torch
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation

MODEL="CIDAS/clipseg-rd64-refined"
PROMPTS=["the ground path in a video game", "the road surface"]


def run(video: Path, dataset: Path, output: Path, count: int=60):
    output.mkdir(parents=True,exist_ok=True)
    rows=[json.loads(x) for x in (dataset/"frames.jsonl").read_text().splitlines()]
    if any(r["split"]=="test" for r in rows):
        raise ValueError("Test rows must never be supplied to the teacher")
    selected=[]
    for split,limit in [("train",count),("val",max(8,count//4))]:
        group=[r for r in rows if r["split"]==split and r["timestamp_s"]>80]
        selected += [group[i] for i in np.linspace(0,len(group)-1,min(limit,len(group)),dtype=int)]
    torch.set_num_threads(4)
    processor=CLIPSegProcessor.from_pretrained(MODEL)
    model=CLIPSegForImageSegmentation.from_pretrained(MODEL).eval()
    revision=model.config._commit_hash
    cap=cv2.VideoCapture(str(video))
    manifest=[]
    panels=[]
    start=time.perf_counter()
    @torch.inference_mode()
    def predict(rgb):
        pic=Image.fromarray(rgb)
        inputs=processor(text=PROMPTS,images=[pic,pic],padding=True,return_tensors="pt")
        logits=model(**inputs).logits
        probs=torch.sigmoid(logits).cpu().numpy()
        return np.stack([cv2.resize(p,(rgb.shape[1],rgb.shape[0])) for p in probs])
    for n,row in enumerate(selected):
        rgb=np.asarray(Image.open(dataset/row["file"]).convert("RGB"))
        probs=predict(rgb)
        cap.set(cv2.CAP_PROP_POS_MSEC,(row["timestamp_s"]+.20)*1000)
        ok,neighbor=cap.read()
        if not ok: continue
        nrgb=cv2.cvtColor(neighbor,cv2.COLOR_BGR2RGB)
        other=predict(nrgb)
        gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        ngray=cv2.cvtColor(nrgb,cv2.COLOR_RGB2GRAY)
        flow=cv2.calcOpticalFlowFarneback(gray,ngray,None,.5,3,15,3,5,1.2,0)
        yy,xx=np.mgrid[:rgb.shape[0],:rgb.shape[1]].astype(np.float32)
        warped=np.stack([cv2.remap(p,xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT) for p in other])
        positive=(probs.min(0)>.65)&(warped.min(0)>.65)
        negative=(probs.max(0)<.15)&(warped.max(0)<.15)
        mask=np.full(gray.shape,255,np.uint8)
        mask[negative]=0; mask[positive]=1
        # Exclude HUD; this is source-specific label QC, not runtime screen coordinates.
        mask[:int(mask.shape[0]*.15)]=255
        mask[int(mask.shape[0]*.91):]=255
        mask[:,:int(mask.shape[1]*.10)]=255
        mask[:,int(mask.shape[1]*.91):]=255
        fraction=float((mask==1).mean())
        disagreement=float(np.abs(probs-warped).mean())
        accepted=.01<=fraction<=.6 and disagreement<.12
        name=f"{n:04d}"
        Image.fromarray(mask).save(output/f"{name}.png")
        record=dict(row,mask=f"{name}.png",label_status="pseudo",teacher=MODEL,
                    teacher_revision=revision,prompts=PROMPTS,positive_fraction=fraction,
                    temporal_disagreement=disagreement,accepted=accepted,
                    reject_reason=None if accepted else "insufficient_agreed_surface_or_temporal_disagreement")
        manifest.append(record)
        overlay=rgb.copy()
        overlay[mask==1]=(overlay[mask==1]*.4+np.array([20,230,80])*.6).astype(np.uint8)
        pic=Image.fromarray(overlay); pic.thumbnail((180,320))
        tile=Image.new("RGB",(180,350),"#101918"); tile.paste(pic,(0,0))
        ImageDraw.Draw(tile).text((3,322),f'{row["timestamp_s"]:.0f}s {"ACCEPT" if accepted else "REJECT"} {fraction:.2f}',fill="white")
        panels.append(tile)
        print(f'{n+1}/{len(selected)} {row["split"]} accepted={accepted} positive={fraction:.3f}',flush=True)
        (output/"labels.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    cap.release()
    for offset in range(0,len(panels),24):
        group=panels[offset:offset+24]
        sheet=Image.new("RGB",(6*180,((len(group)+5)//6)*350),"#101918")
        for i,p in enumerate(group): sheet.paste(p,((i%6)*180,(i//6)*350))
        sheet.save(output/f"audit-{offset//24}.jpg")
    report=dict(teacher=MODEL,revision=revision,selected=len(manifest),accepted=sum(x["accepted"] for x in manifest),
                elapsed_seconds=time.perf_counter()-start,ground_truth_count=0,test_used=False,
                limitation="Prompt/flow agreement is not calibrated accuracy and cannot certify safe paths.")
    (output/"report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("video",type=Path); p.add_argument("dataset",type=Path)
    p.add_argument("output",type=Path); p.add_argument("--count",type=int,default=60)
    a=p.parse_args(); run(a.video,a.dataset,a.output,a.count)
