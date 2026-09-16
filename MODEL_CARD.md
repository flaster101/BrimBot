# BrimBot surface candidate model card

## Intended use

Offline research and on-device **observation only**. It is not a safety, hazard,
navigation, state, player, enemy or full gameplay model. No automatic controls
are authorized by its output.

## Training scope

CLIPSeg ground/grass prompt agreement with adjacent-frame flow checks produces
partial pseudo masks. Training samples come from green-surface portions of the
supplied expert run; validation is a separate contiguous gameplay interval.
Unknown pixels are ignored. The teacher's mistakes and source bias may transfer
to both candidate students.

Training completed on 2026-09-16, using 30 accepted training frames and 19
validation frames. There are **zero independently annotated ground-truth frames**.
The selected custom CNN has 9,161 parameters and a 38,980-byte ONNX export.
MobileNetV3-small was also fitted; its higher pseudo-validation loss excluded it.
No pretrained MobileNet weights are included in the APK.

| Candidate | Pseudo precision | Pseudo recall | Pseudo IoU | Validation loss | Desktop median / p95 |
| --- | --- | --- | --- | --- | --- |
| Custom CNN (selected) | 94.89% | 98.93% | 93.93% | 0.034905 | 4.56 / 6.28 ms |
| Partial MobileNetV3-small | 97.65% | 90.17% | 88.26% | 0.130078 | 4.40 / 6.34 ms |

These are pixel agreement scores on confidently labeled parts of grass-biased
frames. They exclude unknown pixels and **do not measure safe paths or gameplay
accuracy**. Latency covers desktop ONNX inference only, excludes decoding and
preprocessing, and is not a phone benchmark. Selected-model PyTorch/ONNX maximum
absolute output error was 2.39e-7. Full histories and confusion counts are in
[the experiment report](docs/experiments/surface-training.json).

## Interface

ONNX, opset 17. Input `rgb`, float32 `[1,3,192,192]`, RGB [0,1], aspect-preserving
nearest-pixel letterbox with padding 114/255. Output `surface_probability`,
`[1,1,192,192]`. Scores are **uncalibrated**. Input layout is inspected on Android;
the preprocessing component also supports NHWC for independently declared models.

## Known failure modes

- Grass is not proof of safe movement; it can be off-path or on an unreachable
  ledge. Stone paths, stairs and other worlds may be missed entirely.
- Enemies, pet wings, effects, HUD overlays and perspective changes obscure ground.
- Paused game backgrounds may look traversable; the model does not distinguish
  pause/menu/loading/death from active gameplay.
- No gap width, jump reach, landing plane, wall-running affordance or time-to-impact
  prediction is supplied by this model.
- No independently audited critical-class dataset or measured gameplay survival.

## Release status

**Not qualified for autonomous gameplay.** Any packaged version is a diagnostic
asset inside an explicitly labeled observation preview. It must not be described
as a trained Blades of Brim bot. Future models require independent labels,
hazard/path/state metrics, device parity and closed-loop gameplay evaluation.
