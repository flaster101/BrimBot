# Evaluation

**Autonomous gameplay is not demonstrated.** This page separates passing software
checks from missing gameplay evidence. A successful APK build or a fast inference
result does not establish survival.

## Checks and evidence

On 2026-09-16: **45 Python tests, 12 Kotlin/JVM tests and four Android
instrumentation tests passed**, with zero failures in their final runs.
Android used an x86_64 Android 15 / API 35 emulator. The model parity test compares
every output pixel to Python-generated golden values at absolute tolerance 1e-4.
Capture testing uses Android's actual system consent, checks receipt of a frame,
rotates the activity and invokes the notification's Stop pending intent.

- Python tests exercise policy priorities, abstention, unsafe reward avoidance,
  pet conservation, cooldowns, oscillation, stale frames, malformed observations,
  label quarantine, coordinate transforms and event-log auditing.
- Kotlin/JVM tests exercise policy, tensor layouts, six geometry cases, tracking
  and conservative parsing of objective text.
- Android 15 emulator tests exercise onboarding, normal screens, permission
  cancellation, rejection of missing capture consent and projection lifecycle.
- Candidate training, export parity, desktop performance and Android output
  parity are recorded separately in experiment reports.
- Recorded-frame replay must be described as replay. Human actions in the video
  cannot establish the outcome of different bot decisions.

## Metrics that are not available

Object-detection mAP50/mAP50–95, real per-class enemy/hazard precision and recall,
safe-path reliability, rare-mechanic reliability, physical-device thermal/FPS
measurements and autonomous survival time have **not** been established.
Pseudo-label agreement is not substituted for these metrics.

## Release qualification

`evaluation/release_gate.py` rejects absent or nonfinite metrics, missing independent
ground truth, missing critical-class counts, missing Android parity/lifecycle
evidence and insufficient closed-loop runs/devices. Proposed engineering gates
include lower 95% confidence bounds of 98% critical-hazard recall and 99.5% safe-path
and active-state precision. These targets are design criteria, not achieved results
or guarantees of safe play. The preview remains blocked regardless of cosmetic
changes to its release-status manifest.

## Test screen geometry

Numerical round-trip cases: 720×1280, 1080×1920, 1080×2400, 1440×3200, 2208×1840,
1920×1080. Both NCHW and NHWC preprocessing layouts are exercised. These tests do
not establish live control accuracy for every cutout, app letterbox or OEM window.

## Why no gameplay gestures are released

The integrated perception engine lacks validated game-state, player-lane, lethal
hazard and traversability outputs. It returns UNKNOWN, and both the policy and
the gesture service reject automatic action. This is intentional abstention;
doing nothing during a run is not successful autonomous play.
