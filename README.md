# CMF Watch Extended

Experimental Kotlin Multiplatform companion application for the **CMF Watch Pro 2 by Nothing**, using Compose Multiplatform on Android and iOS. This is an unofficial project, unaffiliated with or endorsed by Nothing/CMF.

## Current scope: BLE device discovery

- Bluetooth capability, power and permission handling.
- User-initiated foreground BLE scans, manual stop and automatic 15-second timeout.
- Nearby device names, platform identifiers and RSSI; deduplicated results.
- Recoverable scan errors and bounded, in-memory diagnostic logs.
- Responsive Material UI with system light/dark themes and English/Georgian text.
- Shared state/repository tests and GitHub Actions for Android and iOS.

The app discovers all nearby BLE advertisers. A listed name does **not** verify that a device is a CMF watch. No pairing, connection, authentication, watch commands, GATT access, notification forwarding or firmware transfer is implemented. Discovery on the intended physical watch/iPhone remains unverified.

Your watch may not advertise while connected to the official CMF application. Preserve the existing pairing; do not reset or unpair it for this phase. Future connection work may conflict with the official app and requires separate testing.

## Platforms and build

The existing wizard modules are `shared` (common UI/domain and native BLE controllers), `androidApp`, and `iosApp`. Android minimum is API 24, compile/target SDK 37. The iOS app deployment target remains 18.2; Kotlin targets are `iosArm64` and `iosSimulatorArm64` (Apple Silicon simulator).

Use JDK 21 (the Gradle daemon criteria select Zulu), Android SDK 37 and Xcode 26.4.1 or a compatible version. Existing Gradle/AGP/Kotlin/Compose versions are preserved in the version catalog; Material 3 uses its latest verified stable release instead of the wizard alpha. Configure `local.properties` with your Android SDK path or set `ANDROID_HOME`; do not commit machine-specific settings.

```sh
./gradlew help
./gradlew :shared:compileCommonMainKotlinMetadata :shared:testAndroidHostTest :androidApp:assembleDebug
```

The debug APK is `androidApp/build/outputs/apk/debug/androidApp-debug.apk`. Install it through Android Studio or `adb install -r` on your own test device. On Android 12+ grant Nearby Devices permission; Android 7–11 requires fine location permission and Location services enabled. The app does not infer physical location. Android's `neverForLocation` setting can filter some beacon advertisements.

On an Apple Silicon Mac:

```sh
./gradlew :shared:linkDebugFrameworkIosArm64 :shared:linkDebugFrameworkIosSimulatorArm64 :shared:iosSimulatorArm64Test
xcodebuild -project iosApp/iosApp.xcodeproj -scheme iosApp -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath build/ios-local CODE_SIGNING_ALLOWED=NO build
```

For an iPhone, open `iosApp/iosApp.xcodeproj`, select your signing team and physical phone, and run `iosApp`. Follow the detailed [iPhone installation and acceptance checklist](docs/TESTING.md). Simulator builds and fake-transport tests do not validate radio behavior.

## Compatibility and limitations

CMF Watch Pro 2 is the research target; no firmware-specific compatibility is claimed yet. Other BLE advertisers may appear. iOS identifiers are UUIDs, Android identifiers are addresses, and neither should be treated as universal stable identity. Scans are foreground-only and retain at most 200 devices; logs retain 80 events and are lost when the controller is destroyed. No log export or persistence is implemented.

Georgian localization and preview text affect the phone only. Watch font coverage, Unicode notification handling, custom watchfaces and transfers remain research topics. An ordinary iOS companion app cannot read arbitrary third-party app notifications.

## Development and research

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [BLE research, pinned sources and attribution](docs/BLE_RESEARCH.md)
- [Georgian support and confidence levels](docs/GEORGIAN_SUPPORT.md)
- [Tests and physical-device checklist](docs/TESTING.md)
- [Executed local validation](docs/VALIDATION.md)
- [Contributing](CONTRIBUTING.md) and [agent instructions](AGENTS.md)

Each feature uses a separate branch and PR to protected `main`. CI runs for PRs to main and feature-branch pushes. Required checks are configured only after successful runs. No automatic merges.

No third-party implementation, font or proprietary brand artwork is copied. The repository owner has not yet selected a project-wide open-source license; public source availability alone does not grant reuse rights.
