"""Training-only prompt sensitivity audit. Does not generate accepted labels."""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
import torch
from transformers import CLIPSegProcessor,CLIPSegForImageSegmentation

if __name__=="__main__":
    torch.set_num_threads(3)
    root=Path("data/reference-diverse")
    rows=[json.loads(x) for x in (root/"frames.jsonl").read_text().splitlines()]
    row=next(r for r in rows if r["timestamp_s"]>82 and r["split"]=="train")
    image=Image.open(root/row["file"]).convert("RGB")
    prompts=["ground","grass","floor","path","road","sky","wall","the ground path in a video game"]
    revision="999e0328d9e10b484360c477313983f9afdd7050"
    processor=CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined",revision=revision)
    model=CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined",revision=revision).eval()
    inputs=processor(text=prompts,images=[image]*len(prompts),padding=True,return_tensors="pt")
    with torch.inference_mode(): logits=model(**inputs).logits
    probs=torch.sigmoid(logits).numpy()
    sheet=Image.new("RGB",(180*4,350*2),"#101918")
    report=[]
    for i,(prompt,prob) in enumerate(zip(prompts,probs)):
        heat=cv2.applyColorMap((cv2.resize(prob,(180,320))*255).astype(np.uint8),cv2.COLORMAP_TURBO)
        pic=Image.fromarray(cv2.cvtColor(heat,cv2.COLOR_BGR2RGB))
        overlay=Image.blend(image.resize((180,320)),pic,.6)
        x,y=i%4*180,i//4*350;sheet.paste(overlay,(x,y));ImageDraw.Draw(sheet).text((x+3,y+323),prompt,fill="white")
        report.append(dict(prompt=prompt,max=float(prob.max()),mean=float(prob.mean()),p95=float(np.quantile(prob,.95))))
    sheet.save("artifacts/teacher-probe.jpg")
    Path("artifacts/teacher-probe.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
