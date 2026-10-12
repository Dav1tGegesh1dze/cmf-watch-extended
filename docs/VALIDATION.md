# Phase 1 validation

Local validation on 2026-10-12, Apple Silicon macOS, Xcode 26.4.1 (17E202), Gradle 9.5.1 / Zulu JDK 21.

| Check | Result |
| --- | --- |
| Gradle `help` and shared task configuration | Passed |
| `:shared:compileCommonMainKotlinMetadata` | Passed |
| `:shared:compileAndroidMain` | Passed |
| `:androidApp:assembleDebug` | Passed; debug APK generated |
| `:androidApp:lintDebug` | Passed, 0 errors / 10 warnings |
| `:shared:testAndroidHostTest` | 13 tests passed, 0 failed/skipped |
| `:shared:linkDebugFrameworkIosArm64` | Passed; device framework linked, not installed on hardware |
| `:shared:linkDebugFrameworkIosSimulatorArm64` | Passed |
| `:shared:iosSimulatorArm64Test` | 13 tests passed, 0 failed/skipped |
| Xcode `iosApp` simulator Debug build, signing disabled | Passed |
| Physical iPhone / Android / watch BLE reception | Not executed |

Each test runner executes the 11 new discovery tests and two existing wizard tests. New coverage includes availability gating, duplicate scan requests, deduplication/RSSI/name updates, late events, timeout and cancellation, power loss, permission/error recovery, bounded logs/devices, repository/ViewModel delegation, and Georgian UTF-8 strings.

Lint warnings are: existing toolchain update suggestions (5), wizard launcher/resource suggestions (3), the intentional API-31-only permission flag (1), and a Kotlin URI convenience-method suggestion (1). No lint baseline or blanket error suppression was added. The stable existing toolchain is preserved to keep the feature focused.

An initial native compilation found two incorrect Kotlin/Native imports, which were corrected. An overlapping Xcode build timed out waiting for Gradle's configuration-cache lock; sequential validation completed successfully. Run Gradle and Xcode checks sequentially in the same checkout.

The workflow records independent GitHub-hosted checks and uploads test/lint reports. Only successful published checks may be made required. Simulator results do not prove Bluetooth hardware behavior or watch font support. Follow [TESTING.md](TESTING.md) for real-device acceptance.
