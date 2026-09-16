# Third-party components and data

- Android / AndroidX / Compose: Android Open Source Project, Apache 2.0 unless
  otherwise noted in the distributed component notices.
- Kotlin: JetBrains, Apache 2.0.
- ONNX Runtime: Microsoft and contributors, MIT.
- PyTorch / torchvision: their respective BSD-style licenses; research tooling.
- CLIPSeg: [CIDAS model](https://huggingface.co/CIDAS/clipseg-rd64-refined),
  [original project](https://github.com/timojl/clipseg). Used offline to propose
  uncertain semantic masks. The large teacher is not bundled in the Android app.
- MobileNetV3 initialized from torchvision was evaluated but not selected. Its
  weights are not bundled. The packaged CNN was trained from random initialization.
- Public gameplay is attributed in DATASET.md. It is locally analyzed, not
  redistributed as raw video, an image dataset or Android artwork.

BrimBot's original icon uses code-defined vector shapes. It does not copy SYBO
artwork. Source-code licensing does not grant rights to the Blades of Brim brand
or third-party footage.

The APK includes the ONNX Runtime v1.20.0 license and third-party notices, obtained
from that release's source tag, and the Apache 2.0 license in `assets/licenses/`.
