# Testing Phase 1

## Automated checks

```sh
./gradlew help :shared:tasks --all
./gradlew :shared:compileCommonMainKotlinMetadata :shared:compileAndroidMain :shared:testAndroidHostTest :androidApp:assembleDebug :androidApp:lintDebug
./gradlew :shared:linkDebugFrameworkIosArm64 :shared:linkDebugFrameworkIosSimulatorArm64 :shared:iosSimulatorArm64Test
xcodebuild -project iosApp/iosApp.xcodeproj -scheme iosApp -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath build/ios-local CODE_SIGNING_ALLOWED=NO build
```

iOS tasks require an Apple Silicon Mac with Xcode and an installed iOS simulator runtime. Tests use fake Bluetooth; no watch is contacted. Host test HTML reports are under `shared/build/reports/tests/testAndroidHostTest/`. Native test reports are under `shared/build/reports/tests/iosSimulatorArm64Test/`.

## iPhone installation

1. Check out `feature/ble-device-discovery` and open `iosApp/iosApp.xcodeproj` in Xcode. The existing deployment target is iOS 18.2.
2. In Xcode Settings → Accounts, sign in to your Apple ID. Select the `iosApp` target → Signing & Capabilities, select your Personal Team/development team and enable automatic signing. If needed, set a unique bundle identifier. Keep personal signing changes local. Alternatively fill `TEAM_ID` in `iosApp/Configuration/Config.xcconfig` locally; do not commit your team details.
3. Connect and trust your iPhone, enable Developer Mode in Settings → Privacy & Security if Xcode requests it, and select the physical iPhone as the run destination. Keep your existing watch pairing intact.
4. Run the `iosApp` scheme (Cmd-R). The first build downloads Kotlin/Native dependencies and can take several minutes. If Xcode cannot find Java, install JDK 21 and ensure it is discoverable by the Gradle wrapper; the repository's daemon criteria select Zulu 21.
5. Open **CMF Watch Extended**, tap **Start scan**, and allow Bluetooth access. If the permission dialog interrupted initialization, tap Start scan again. A physical iPhone is required for BLE acceptance; the simulator is for UI/build/tests only.
6. Expect device names (or “Unnamed device”), iOS UUID identifiers and RSSI. Tap **Stop scan** and verify the list stops updating. Start again and verify automatic completion after 15 seconds. New scans clear prior results.
7. Switch to **ქართული** and inspect all four Georgian samples, then test system dark and light appearance and larger text. This checks phone fonts only.

## Hardware acceptance checklist — not yet executed

Record phone model, OS version, watch firmware (from its existing UI), date and result. Do not publish raw nearby-device identifiers or names.

- [ ] Bluetooth disabled: explanatory state; enabling it allows a fresh scan.
- [ ] Permission denied: useful recovery instructions; granting in Settings works after returning.
- [ ] Nearby advertising peripherals appear with usable names/identifiers/RSSI.
- [ ] Repeat advertisements update one row rather than duplicate it.
- [ ] Missing names and unavailable RSSI remain readable.
- [ ] Manual stop and 15-second timeout both stop scan activity.
- [ ] Leaving the foreground stops scanning and does not auto-restart on return.
- [ ] Switching Bluetooth off mid-scan stops scanning cleanly.
- [ ] Android activity recreation does not leak scanning or receivers.
- [ ] Android API 24–30 handles location permission and disabled Location services.
- [ ] Android API 31+ handles Nearby Devices permission, including permanent denial.
- [ ] Georgian text is readable on the phone; no watch-font claim is made.
- [ ] Existing official CMF pairing remains intact.

A watch absent while connected to the official app is a valid limitation, not a reason to reset or unpair. Do not disconnect/unpair it just to complete this checklist. If a later test needs pairing changes, obtain explicit approval first.
