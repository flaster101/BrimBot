"""Frame-by-frame surface candidate replay; abstention is not successful play."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
import cv2
import numpy as np
import onnxruntime as ort
from perception.geometry import prepare_rgb
from perception.policy import Policy,World


def replay(video: Path, model: Path, split_file: Path, output: Path, seconds: float | None=None, max_fps: float=10):
    if not 0<max_fps<=120: raise ValueError("Invalid replay rate")
    cv2.setNumThreads(1)
    output.mkdir(parents=True,exist_ok=True)
    split=json.loads(split_file.read_text())
    start,end=split["test"]
    if seconds is not None: end=min(end,start+seconds)
    cap=cv2.VideoCapture(str(video)); source_fps=cap.get(cv2.CAP_PROP_FPS)
    if not cap.isOpened() or source_fps<=0: raise RuntimeError("Cannot decode input video")
    stride=max(1,int(np.ceil(source_fps/max_fps))); fps=source_fps/stride
    cap.set(cv2.CAP_PROP_POS_MSEC,start*1000)
    options=ort.SessionOptions(); options.intra_op_num_threads=2
    session=ort.InferenceSession(str(model),sess_options=options,providers=["CPUExecutionProvider"])
    shape=session.get_inputs()[0].shape
    policy=Policy(); frames=0; decoded=0; latencies=[]; writer=None; actions={}; start_time=time.perf_counter()
    projection=None; previous_shape=None
    with (output/"events.jsonl").open("w",encoding="utf-8") as log:
        while True:
            ok,bgr=cap.read()
            if not ok: break
            timestamp=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if timestamp>end: break
            decoded+=1
            if (decoded-1)%stride: continue
            rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
            tensor,tr=prepare_rgb(rgb,shape)
            begin=time.perf_counter(); probability=session.run(None,{session.get_inputs()[0].name:tensor})[0][0,0]
            latency=(time.perf_counter()-begin)*1000; latencies.append(latency)
            world=World(timestamp_ms=round(timestamp*1000))
            decision=policy.decide(world)
            actions[decision.action]=actions.get(decision.action,0)+1
            record=dict(timestamp_s=timestamp,detections=[],hazards=[],state="unknown",target=None,
                action=decision.action,reason=decision.reason,surface_fraction=float((probability>.85).mean()),
                latency_ms=latency,qualified=False)
            log.write(json.dumps(record)+"\n")
            if previous_shape!=bgr.shape:
                yy,xx=np.mgrid[:bgr.shape[0],:bgr.shape[1]].astype(np.float32)
                projection=(xx*tr.scale+tr.padding[0],yy*tr.scale+tr.padding[1])
                previous_shape=bgr.shape
            px,py=projection
            projected=cv2.remap(probability,px,py,cv2.INTER_LINEAR)
            mask=projected>.85
            bgr[mask]=(bgr[mask]*.6+np.array([70,210,50])*.4).astype(np.uint8)
            cv2.rectangle(bgr,(0,0),(bgr.shape[1],78),(15,25,24),-1)
            for n,text in enumerate(["RESEARCH REPLAY - NOT AUTONOMOUS PLAY",f"t={timestamp:.2f}  action=NONE", "Surface candidates only; safety UNKNOWN"]):
                cv2.putText(bgr,text,(7,18+n*22),cv2.FONT_HERSHEY_SIMPLEX,.34,(220,235,220),1,cv2.LINE_AA)
            if writer is None:
                writer=cv2.VideoWriter(str(output/"annotated.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),fps,(bgr.shape[1],bgr.shape[0]))
                if not writer.isOpened(): raise RuntimeError("Video encoder unavailable")
            writer.write(bgr); frames+=1
            if frames%500==0: print(f"Analyzed {frames} frames through {timestamp:.1f}s",flush=True)
    cap.release()
    if writer: writer.release()
    if not frames: raise RuntimeError("Replay processed no frames")
    report=dict(frames=frames,decoded_frames=decoded,analysis_fps=fps,source_fps=source_fps,
        start_s=start,end_s=end,actions=actions,
        desktop_median_ms=float(np.median(latencies)) if latencies else None,
        desktop_p95_ms=float(np.percentile(latencies,95)) if latencies else None,
        elapsed_s=time.perf_counter()-start_time,autonomous_gameplay_success=False,
        survival_duration=None,detector_map50=None,detector_map50_95=None,hazard_recall=None,
        failure="No qualified state, enemy, player or safe-path estimator. All controls withheld.",
        evaluation_kind="recorded-frame integration and abstention test, not closed-loop gameplay")
    (output/"report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("video",type=Path);p.add_argument("model",type=Path)
    p.add_argument("split",type=Path);p.add_argument("output",type=Path);p.add_argument("--seconds",type=float)
    p.add_argument("--max-fps",type=float,default=10,help="Match the Android capture analysis ceiling (10 Hz)")
    a=p.parse_args();replay(a.video,a.model,a.split,a.output,a.seconds,a.max_fps)
