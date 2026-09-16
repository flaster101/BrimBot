# Android implementation and release engineering

## Platform

Kotlin, Compose Material 3, min API 26, target/compile API 35, Java 17,
Android Gradle Plugin 8.9.1, Gradle 8.11.1. ONNX Runtime Android 1.20.0 performs
local inference. The application requests no internet or file-storage access.

## Permissions and lifecycle

- Accessibility enables game-package/window checks and future gesture dispatch.
  The preview explicitly discloses that dispatch is disabled.
- Notification permission supports a visible stop control.
- MediaProjection consent is requested for every new session. Its foreground
  service starts before obtaining a projection, registers the callback before
  creating the virtual display, and reuses/resizes that display.
- The service is not sticky and does not persist or reuse consent tokens.
- Foreground game checks happen before inference; dispatch separately rechecks
  the active game window and observation freshness.
- Frame objects close on all branches; inference is serialized off the UI thread.
- Process death or projection revocation never resumes autonomous input.

Reference: [Android MediaProjection](https://developer.android.com/media/grow/media-projection)
and [AccessibilityService](https://developer.android.com/reference/android/accessibilityservice/AccessibilityService).

## Screens and scope

Onboarding remembers completion. Play shows a clear preview status and one start/
stop control. Objectives describes the survival policy without fabricated game
progress. About explains privacy, permissions, version and independence from SYBO.
Seven taps on the version reveal diagnostics; the normal interface has no model
selection, confidence sliders, class lists or coordinate fields.

## Build and signing

The release uses a dedicated local signing key. Key material and passwords are
excluded from Git and APK assets. The release APK is named `BrimBot.apk`.
The signing key must remain available for future updates; do not regenerate it
when incrementing the app version. GitHub Actions builds/tests source separately
and does not receive the signing key.

## Verification boundaries

JVM tests cover policy, geometry, tensor layout, tracking and OCR evidence parsing.
Four passing instrumentation tests cover onboarding/UI, permission cancellation,
missing consent, real projection consent/frame receipt/rotation/notification Stop,
and Python-to-Android model output parity with the packaged candidate.
Emulator testing is not physical-phone performance or actual-game validation.
Capture permission revocation, OEM battery behavior, thermal throttling and real
game gesture timing still require broader device testing before autonomy.
