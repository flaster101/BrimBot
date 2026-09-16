"""Decode training/validation only; reserve untouched test time before sampling.

python -m dataset_tools.sample data/reference.webm --output data/reference
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw


def split_at(t: float, duration: float, embargo: float = 15.0) -> str:
    if duration <= 0 or not 0 <= t <= duration:
        raise ValueError("Invalid timestamp or duration")
    a, b = duration * .70, duration * .85
    if abs(t - a) < embargo or abs(t - b) < embargo:
        return "embargo"
    return "train" if t < a else "val" if t < b else "test"


def dhash(frame: np.ndarray) -> int:
    gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (9, 8))
    result = 0
    for bit in (gray[:, 1:] > gray[:, :-1]).flat:
        result = (result << 1) | int(bit)
    return result


def contact_sheet(rows: list[dict], root: Path, output: Path, limit: int = 48) -> None:
    selected = rows[:limit]
    if not selected:
        return
    canvas = Image.new("RGB", (6 * 180, ((len(selected) + 5)//6) * 345), "#101820")
    draw = ImageDraw.Draw(canvas)
    for i, row in enumerate(selected):
        pic = Image.open(root / row["file"]).convert("RGB")
        pic.thumbnail((176, 312))
        x, y = (i % 6)*180, (i//6)*345
        canvas.paste(pic, (x, y))
        draw.text((x+3, y+314), f'{row["timestamp_s"]:.2f}s {row["reason"]}', fill="white")
    canvas.save(output)


def sample(video: Path, output: Path, source_url: str, max_frames: int = 1200) -> dict:
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if not cap.isOpened() or fps <= 0 or count <= 0:
        raise ValueError("Video has no decodable frames or valid timing")
    duration = count / fps
    output.mkdir(parents=True, exist_ok=True)
    (output / "frames").mkdir(exist_ok=True)
    source_sha = hashlib.file_digest(video.open("rb"), "sha256").hexdigest()
    source_id = source_sha[:16]
    # Each candidate retains a temporal neighborhood. Scene/motion/novelty decide
    # whether it becomes a sample; this is not fixed-interval extraction alone.
    stride = max(1, round(fps * .5))
    rows, hashes, previous, last_saved, segment = [], {}, None, -10.0, 0
    frame_id = 0
    spacing = duration * .85 / max_frames
    while frame_id < int(duration*.85*fps):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ok, frame = cap.read()
        if not ok:
            break
        t = frame_id / fps
        split = split_at(t, duration)
        small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (64, 64))
        motion = 0.0 if previous is None else float(np.abs(small.astype(float)-previous).mean()/255)
        scene = motion > .26
        if scene:
            segment += 1
        digest = dhash(frame)
        seen = hashes.setdefault(split, [])
        novelty = min(((digest ^ h).bit_count() for h in seen[-200:]), default=64)
        reason = "scene" if scene else "motion" if motion > .12 else "diversity" if novelty >= 16 else "coverage"
        keep = split in {"train", "val"} and t-last_saved >= spacing and novelty >= 7 and (scene or motion > .12 or novelty >= 16 or t-last_saved > 8)
        if keep:
            filename = f"frames/{source_id}_{frame_id:08d}.jpg"
            cv2.imwrite(str(output/filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 94])
            rows.append(dict(id=f"{source_id}:{frame_id}", file=filename, source=source_url,
                             source_sha256=source_sha, source_id=source_id, run_id=source_id,
                             segment_id=f"{source_id}:{segment}", timestamp_s=t,
                             frame_id=frame_id, fps=fps, split=split,
                             neighbors=[max(0, frame_id-stride), min(count-1, frame_id+stride)],
                             hash=f"{digest:016x}", motion=motion, novelty=novelty, reason=reason))
            seen.append(digest)
            last_saved=t
        previous=small
        frame_id += stride
    cap.release()
    (output/"frames.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows), encoding="utf-8")
    plan = dict(source=source_url, source_sha256=source_sha, fps=fps, duration_s=duration,
                train=[0, duration*.70-15], val=[duration*.70+15, duration*.85-15],
                test=[duration*.85+15, duration], embargo_s=15,
                test_decoded=False, selected=len(rows), max_frames=max_frames,
                warning="One source/run; temporal holdout is not cross-device or cross-run validation.")
    (output/"split.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    contact_sheet(rows, output, output/"contact-sheet.jpg")
    return plan


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", default="https://www.youtube.com/watch?v=FPrG-8yTrBE")
    parser.add_argument("--max-frames", type=int, default=1200)
    args=parser.parse_args()
    print(json.dumps(sample(args.video,args.output,args.source,args.max_frames),indent=2))
