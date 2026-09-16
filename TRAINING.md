# Reproducible training

The implemented experiment compares a small convolutional segmentation network
against a MobileNetV3-small feature extractor initialized from torchvision weights.
It uses only accepted training pseudo masks, validation-based early stopping,
AdamW, class-balanced binary loss, ignored uncertain pixels and mild brightness
augmentation. Geometry-destroying rotations/crops are not used.

The seed is 17. Model history, selected epoch, parameters, teacher metadata,
desktop CPU latency and PyTorch/ONNX output error are recorded. ONNX uses opset 17
with fixed batch-one RGB NCHW input and an explicit surface-probability output.
No quantization is selected without validated gameplay-critical recall.

The completed comparison and all epoch histories are in
[surface-training.json](docs/experiments/surface-training.json). The custom CNN
was selected at epoch 13; MobileNet's best checkpoint was epoch 6. Both use the
same 30 training / 19 validation frames. The selected model is 38,980 bytes.
Model selection was frozen before separate-source replay.

## Developer reproduction

Use Python 3.12 and the recorded dependency lock, then:

```sh
python -m dataset_tools.sample data/reference.webm --output data/reference-diverse --max-frames 800
python -m dataset_tools.path_teacher data/reference.webm data/reference-diverse data/path-labels --count 48
python -m dataset_tools.teacher_probe
python -m dataset_tools.path_teacher data/reference.webm data/reference-diverse data/path-labels-ground --count 64 --prompts ground grass
python -m dataset_tools.refine_surface_split
python -m dataset_tools.path_teacher data/reference.webm data/surface-candidates data/path-labels-selected --count 80 --prompts ground grass
python -m dataset_tools.path_teacher data/reference.webm data/surface-candidates data/path-labels-extra-val --count 800 --prompts ground grass --only-split val
python -m dataset_tools.merge_labels data/path-labels-final data/path-labels-selected data/path-labels-extra-val
python -m training.path_student data/surface-candidates data/path-labels-final artifacts/training
```

These commands are for engineering reproduction, not normal app operation.
Training refuses fewer than 12 accepted train or four accepted validation frames.
Test rows supplied to the teacher or student trigger an error.

The CPU torch/torchvision versions in the Windows lock are available from the
official `https://download.pytorch.org/whl/cpu` index. Cache directories are local
and ignored by Git. The teacher revision is pinned in the labeling source.

## Scope

This experiment trains a semantic appearance candidate, **not a complete game
perception model**. There is no trained enemy detector, critical hazard detector,
reliable gameplay-state classifier or calibrated safe-path estimator. Pseudo-label
precision/recall/IoU measure agreement with the teacher; they are not game accuracy.

Object-detection mAP50/mAP50–95, per-enemy recall and a true confusion matrix
cannot be honestly reported without an object detector and independent labels.
