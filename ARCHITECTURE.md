# Architecture and current boundaries

## Device data flow

`MainActivity → Android consent → CaptureService → PerceptionEngine → World → DecisionEngine → GestureService`

- Kotlin and Material 3 Compose, Android 8+ (API 26), target API 35.
- One session entry point requests missing accessibility / notification access
  and fresh screen-sharing consent. Android 14 full-display capture is selected
  explicitly; its window coordinate relationship is known.
- A foreground service owns one projection, one virtual display, and a two-image
  reader. It consumes the latest frame, throttles to at most 10 Hz, closes images,
  handles row padding and resizes the existing display when captured content changes.
- The model input shape is inspected. RGB nearest-pixel letterboxing supports
  explicit NCHW and NHWC. Ambiguous shapes fail. Pixels are normalized to [0,1].
- The current model candidate estimates a semantic surface, not safe movement.
  It cannot supply state, player pose, hazards, landing geometry or lane safety.
  `PerceptionEngine` therefore returns UNKNOWN and `perceptionValidated=false`.
- `DecisionEngine` is deterministic and independently tested using injected
  observations. Its availability does not imply an integrated gameplay bot.
- `GestureService` independently checks session qualification, frame age, active
  game package, active window bounds and in-flight input. It contains normalized
  swipe/tap/double-tap dispatch but the preview never permits these commands.

## Qualification is not a setting

The build is observation-only. Both runtime qualification and generated world
qualification are false. Developer diagnostics cannot override them. Production
autonomy requires implemented estimators and independent evidence, followed by
an engineering change; editing a JSON boolean alone is intentionally insufficient.

## Temporal and objective components

The core includes greedy, one-to-one short-lived tracking with velocity estimates;
this is a baseline and is not robust to occlusion, camera rotation or crossings.
The policy does not update player lane merely because a command was issued.
`GoalManager` requires three distinct, consistent high-confidence OCR reads and
rejects unsupported or impossible progress. An OCR provider is not integrated.

## Offline data flow

`public video → source hash + time split → scene/motion/diversity selection →
teacher prompt agreement + optical-flow consistency → explicit pseudo labels →
student comparison → ONNX export → parity → held-out recorded-frame replay`

Training agreement and desktop inference speed are research metrics. Neither is
a substitute for critical-class recall, safe-path precision, physical-device
latency or closed-loop survival.

## Privacy and platform boundaries

No INTERNET permission, storage permission, game memory, hooks, injection or game
APK modifications. Captured images exist only in memory and are not logged or
uploaded. Package checks use accessibility window information; content is not
retained. The user controls Android consent and the persistent notification stop
action. Screen sharing can end at any time; service restart does not reuse tokens.

## Important remaining engineering risks

- Capture/source viewport mapping for gesture decisions must be independently
  tested across cutouts, letterboxing, rotation and multiwindow before autonomy.
- A surface score cannot establish reachable height or a safe swept movement.
- Pausing input is conservative, but doing nothing can still lose a running game.
- Recorded expert actions do not show what would happen after a bot's different action.
