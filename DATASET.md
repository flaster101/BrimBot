# Dataset provenance and separation

Raw media and extracted images stay outside Git. Public availability is not a
blanket redistribution license; no raw gameplay is included with the app.

Primary reference: [foolish gamer's supplied record run](https://www.youtube.com/watch?v=FPrG-8yTrBE).
Acquired locally at 360×640; 6,682.06 seconds, approximately 29.88 fps.
SHA-256: `d8a8466650e0a44c9c5ecf619e59be595272ae75fc6e538a2d80a761bae5cc66`.

Secondary research reference: [TheGamerStep tutorial](https://www.youtube.com/watch?v=s_a4RqhULyo),
650 seconds, 360×480 encoded canvas. It is older footage, not evidence that
today's Android UI and mechanics are identical.

## Temporal holdout

The primary source is split before teacher execution:

| Partition | Seconds |
| --- | --- |
| Train | 0–4662.443 |
| Excluded boundary | 4662.443–4692.443 |
| Validation | 4692.443–5664.752 |
| Excluded boundary | 5664.752–5694.752 |
| Test | 5694.752–6682.062 |

One run cannot establish generalization across devices, versions, loadouts and
worlds. This is a contiguous-time test, not a cross-run test. The test partition
is not decoded during sampling, prompt selection or teacher-label creation.

## Sampling

The sampler evaluates temporal candidates using gray-frame motion, scene changes
and perceptual hash novelty. A temporal budget prevents dense early gameplay
from consuming the whole sample set. It selected 702 source-linked frames across
train/validation. Each row preserves source SHA, URL, source/run ID, contiguous
scene ID, frame/time, fps, neighboring frame IDs, hash and selection reason.
Contact sheets expose duplicates, menus, effects and world changes for audit.

The first development sampler reached its budget too early. Its output is not
used by the final diverse pipeline. The corrected sampling procedure scans the
entire train/validation interval.

## Label quality

The first CLIPSeg prompt pair accepted 0/60 samples. Rejection is recorded; these
frames are not silently converted into negatives or used for training.
A training-only prompt audit motivated a narrower ground/grass experiment.
Agreement requires both prompts and an optical-flow-aligned neighboring frame.
Unknown pixels are ignored, HUD margins are excluded, and implausible mask areas
or disagreement cause sample rejection. The model revision and prompts are saved.

These are **pseudo labels**, even after QC. Model scores are not calibrated
probabilities of safe traversability. A ground/grass experiment excludes stone
surfaces and can confuse vegetation, walls, effects and unreachable terrain.
No independent human-verified hazard test set exists yet.

Final QC accepted 30 of 80 selected training frames and 19 of 72 validation
frames. Expanding validation processed all eligible candidates without relaxing
the acceptance thresholds. Overlapping batches were deduplicated before fitting.
The original prompt experiment accepted 0/60; the first broad ground/grass batch
accepted 5/80. These failed/limited experiments remain part of the record.

## Content-aware correction before student fitting

The broad contact sheet revealed that approximately the final third of the
supplied video is loot/chest UI. The initial validation interval therefore
contained no accepted ground masks. Before fitting any student, the surface
experiment was refined to train 80–2700 s and validate 2730–3990 s, with a 30-second
gap. Candidate selection uses visible green-area coverage to target the limited
grass-surface task. All selection decisions and reject counts remain recorded.
This biases coverage intentionally; it is not a general gameplay dataset.

The original final test interval remains reserved. Additionally, the entirety
of [this separate tutorial source](https://www.youtube.com/watch?v=Hd_l5lOFtZQ)
was reserved for final recorded-frame replay. It is not used for teacher prompts,
pseudo labels, student fitting or checkpoint selection. Its age and device
differences limit what any result can establish about current Android gameplay.
