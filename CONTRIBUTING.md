# Contributing

Use Kotlin Multiplatform, Compose, Kotlin DSL and the existing project modules. Keep features small, constructor-injected and testable. Match the version catalog; prefer compatible stable dependencies. Do not copy third-party code or assets without license review. The repository owner has not selected a project-wide license yet; public hosting alone does not grant a redistribution license.

Start with a clean tree, fetch origin, fast-forward local main, and branch from main using `feature/`, `fix/`, `refactor/`, `research/` or `chore/`. Never overwrite another contributor's uncommitted work. Use Conventional Commits, push only the feature branch, open a PR to main with implementation details, tests and limitations, then wait for review. Never merge automatically.

Run the commands in [README.md](README.md) and the applicable [testing checklist](docs/TESTING.md). CI checks configuration, shared/Android compilation, host tests and iOS builds. Describe skipped or unavailable checks honestly; no simulated or compile-only result counts as hardware validation.

Keep BLE changes discovery-only until a separate reviewed feature authorizes connection behavior. Never invent protocol values, reset/unpair a device, flash firmware, send undocumented commands, hardcode keys, or log private notification content. Preserve official-app pairing. Redact identifiers and private advertisement names before sharing screenshots.

Do not add bypasses or weaken main protection. Required CI check names must match successful published checks. No mandatory external reviewer approval is required for this solo repository.
