"""Compare compact surface students against teacher pseudo labels, not truth."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import random
from pathlib import Path
import time
import cv2
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.nn import functional as F
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
import onnxruntime as ort
from perception.geometry import prepare_rgb,Letterbox

SIZE=192


class TinySurface(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers=nn.Sequential(nn.Conv2d(3,16,3,padding=1,stride=2),nn.ReLU(),
            nn.Conv2d(16,24,3,padding=1,stride=2),nn.ReLU(),nn.Conv2d(24,24,3,padding=1),nn.ReLU(),nn.Conv2d(24,1,1))
    def forward(self,x):
        return torch.sigmoid(F.interpolate(self.layers(x),size=(SIZE,SIZE),mode="bilinear",align_corners=False))


class MobileSurface(nn.Module):
    def __init__(self,pretrained=True):
        super().__init__()
        model=mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT if pretrained else None)
        self.features=nn.Sequential(*list(model.features.children())[:4])
        self.decoder=nn.Sequential(nn.Conv2d(24,24,3,padding=1),nn.ReLU(),nn.Conv2d(24,1,1))
        self.register_buffer("mean",torch.tensor([.485,.456,.406]).view(1,3,1,1))
        self.register_buffer("std",torch.tensor([.229,.224,.225]).view(1,3,1,1))
    def forward(self,x):
        x=self.features((x-self.mean)/self.std)
        return torch.sigmoid(F.interpolate(self.decoder(x),size=(SIZE,SIZE),mode="bilinear",align_corners=False))


def load(rows,root,masks):
    xs,ys=[],[]
    for row in rows:
        rgb=np.asarray(Image.open(root/row["file"]).convert("RGB"))
        x,tr=prepare_rgb(rgb,[1,3,SIZE,SIZE])
        raw=np.asarray(Image.open(masks/row["mask"]))
        yy,xx=np.mgrid[:SIZE,:SIZE]
        sx=(xx+.5-tr.padding[0])/tr.scale
        sy=(yy+.5-tr.padding[1])/tr.scale
        valid=(sx>=0)&(sx<rgb.shape[1])&(sy>=0)&(sy<rgb.shape[0])
        y=np.full((SIZE,SIZE),255,dtype=np.float32)
        y[valid]=raw[np.floor(sy[valid]).astype(int),np.floor(sx[valid]).astype(int)]
        xs.append(x[0]); ys.append(y[None])
    return torch.tensor(np.stack(xs)),torch.tensor(np.stack(ys))


def masked_loss(pred,target):
    valid=target!=255
    if not valid.any(): raise ValueError("No supervised pixels")
    p=pred[valid]; y=target[valid]
    # Equal importance per pseudo class; imbalance must not reward all-background.
    positive=y==1; negative=y==0
    losses=[]
    for mask in (positive,negative):
        if mask.any(): losses.append(F.binary_cross_entropy(p[mask],y[mask]))
    return sum(losses)/len(losses)


def fit(dataset: Path,masks: Path,output: Path,epochs=15):
    random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.set_num_threads(4)
    output.mkdir(parents=True,exist_ok=True)
    rows=json.loads((masks/"labels.json").read_text())
    if any(r["split"]=="test" for r in rows): raise ValueError("Test contamination")
    train=[r for r in rows if r["accepted"] and r["split"]=="train"]
    val=[r for r in rows if r["accepted"] and r["split"]=="val"]
    if len(train)<12 or len(val)<4: raise ValueError("Insufficient clean pseudo labels; refuse training")
    xt,yt=load(train,dataset,masks); xv,yv=load(val,dataset,masks)
    reports=[]
    for name,model in [("tiny",TinySurface()),("mobilenet",MobileSurface())]:
        optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
        best=float("inf"); best_state=None; history=[]; patience=0; started=time.perf_counter()
        for epoch in range(epochs):
            model.train(); permutation=torch.randperm(len(xt)); training=[]
            for indexes in permutation.split(8):
                x=xt[indexes]
                # Photometric changes only; preserve path geometry and padding layout.
                brightness=.9+torch.rand(1).item()*.2
                prediction=model((x*brightness).clamp(0,1))
                loss=masked_loss(prediction,yt[indexes]); optimizer.zero_grad(); loss.backward(); optimizer.step()
                training.append(loss.item())
            model.eval()
            with torch.inference_mode(): loss=masked_loss(model(xv),yv).item()
            history.append(dict(epoch=epoch+1,train_loss=float(np.mean(training)),pseudo_val_loss=loss))
            print(name,history[-1],flush=True)
            if loss<best-.0001: best=loss; best_state=copy.deepcopy(model.state_dict()); patience=0
            else: patience+=1
            if patience>=4: break
        model.load_state_dict(best_state); model.eval()
        torch.save(dict(state_dict=best_state,architecture=name,seed=17,history=history),output/f"{name}.pt")
        with torch.inference_mode():
            prediction=model(xv)
            valid=yv!=255; positives=yv==1; guesses=prediction>=.5
            tp=int((guesses&positives&valid).sum()); fp=int((guesses&~positives&valid).sum())
            fn=int((~guesses&positives&valid).sum()); tn=int((~guesses&~positives&valid).sum())
        onnx_path=output/f"{name}.onnx"
        torch.onnx.export(model,xt[:1],str(onnx_path),input_names=["rgb"],output_names=["surface_probability"],
                          opset_version=17,dynamo=False)
        options=ort.SessionOptions(); options.intra_op_num_threads=2
        session=ort.InferenceSession(str(onnx_path),sess_options=options,providers=["CPUExecutionProvider"])
        a=xv[:1].numpy(); actual=session.run(None,{"rgb":a})[0]
        parity=float(np.max(np.abs(actual-prediction[:1].numpy())))
        latencies=[]
        for i in range(35):
            begin=time.perf_counter(); session.run(None,{"rgb":a})
            if i>=5: latencies.append((time.perf_counter()-begin)*1000)
        reports.append(dict(name=name,train_frames=len(train),validation_frames=len(val),ground_truth_frames=0,
            pseudo_precision=tp/max(1,tp+fp),pseudo_recall=tp/max(1,tp+fn),pseudo_iou=tp/max(1,tp+fp+fn),
            pseudo_confusion=[[tn,fp],[fn,tp]],pseudo_val_loss=best,history=history,
            desktop_median_ms=float(np.median(latencies)),desktop_p95_ms=float(np.percentile(latencies,95)),
            bytes=onnx_path.stat().st_size,torch_onnx_max_abs_error=parity,elapsed_s=time.perf_counter()-started))
        if parity>1e-4: raise ValueError("Export parity failed")
    winner=min(reports,key=lambda x:x["pseudo_val_loss"])
    report=dict(candidates=reports,selected=winner["name"],qualified=False,
                warning="All agreement metrics use pseudo labels. None measures gap/hazard recall or safe path accuracy.",test_used=False)
    (output/"report.json").write_text(json.dumps(report,indent=2))
    selected=(output/f'{winner["name"]}.onnx').read_bytes()
    (output/"path-candidate.onnx").write_bytes(selected)
    (output/"manifest.json").write_text(json.dumps(dict(schema=1,qualified=False,sha256=hashlib.sha256(selected).hexdigest(),
        input=dict(name="rgb",shape=[1,3,SIZE,SIZE],layout="NCHW",dtype="float32",range=[0,1],padding=114),
        output=dict(name="surface_probability",shape=[1,1,SIZE,SIZE]),
        limitation="Semantic surface candidate only. No state, enemy, edge, gap, landing or safe-lane recognition."),indent=2))
    # Golden input + output permits Android runtime parity; no private data.
    rgb=np.zeros((37,19,3),np.uint8)
    yy,xx=np.mgrid[:37,:19]
    rgb[:,:,0]=(xx*13)%256; rgb[:,:,1]=(yy*7)%256; rgb[:,:,2]=((xx+yy)*5)%256
    Image.fromarray(rgb).save(output/"parity.png")
    x,_=prepare_rgb(rgb,[1,3,SIZE,SIZE])
    session=ort.InferenceSession(str(output/"path-candidate.onnx"),providers=["CPUExecutionProvider"])
    golden=session.run(None,{"rgb":x})[0].reshape(-1)
    (output/"parity.json").write_text(json.dumps(dict(input_shape=[1,3,SIZE,SIZE],expected=golden.tolist(),max_absolute_error=.0001)))
    print(json.dumps({k:v for k,v in report.items() if k!="candidates"},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("dataset",type=Path); p.add_argument("masks",type=Path); p.add_argument("output",type=Path)
    p.add_argument("--epochs",type=int,default=15); a=p.parse_args(); fit(a.dataset,a.masks,a.output,a.epochs)
