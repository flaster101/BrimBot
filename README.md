# BrimBot

An Android visual player for **Blades of Brim**, designed around survival first.

**Development status: not yet validated for autonomous gameplay.** A working
APK build is not evidence that a bot can survive a run. See [EVALUATION.md](EVALUATION.md)
for measured results and release gates. No game assets, modified game APKs,
memory access, or hooks are used.

## Product

One start button, permission guidance, on-device screen analysis, and a persistent
stop control. The application must withhold gestures when the game is not active,
the screen mapping is uncertain, or the installed perception package has not
passed the release gate. No model or coordinate configuration belongs in the
normal user interface.

## Repository

| Directory | Responsibility |
| --- | --- |
| `android/` | Kotlin app, capture, gestures, Material interface |
| `perception/` | Model contracts, transforms, tracking and baseline analysis |
| `dataset_tools/` | Provenance, temporal splits, diverse sampling and label QC |
| `training/` | Reproducible training and candidate comparison |
| `evaluation/` | Replay, metrics and release qualification |
| `models/` | Model manifest and validation status |
| `tests/` | Offline regression tests |
| `docs/` | Research and implementation records |

## Engineering documentation

[Game knowledge](GAME_KNOWLEDGE.md) · [Architecture](ARCHITECTURE.md) ·
[Dataset](DATASET.md) · [Training](TRAINING.md) · [Evaluation](EVALUATION.md) ·
[Android](ANDROID.md) · [Model card](MODEL_CARD.md)

BrimBot is an independent project and is not affiliated with SYBO.
