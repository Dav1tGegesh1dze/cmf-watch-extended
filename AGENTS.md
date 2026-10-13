# Repository engineering rules

- Work only in this repository; inspect `git status`, branch, remotes and existing changes first. Preserve uncommitted user work.
- Fetch origin and fast-forward main before each new feature. Branch from main with `feature/*`, `fix/*`, `refactor/*`, `research/*` or `chore/*`.
- One coherent feature per PR. Use Conventional Commits, run applicable tests/builds, push only the feature branch, open a PR to main, then stop for review. Never push to main or merge PRs. The initial baseline bootstrap exception was one-time only.
- Preserve the existing KMP modules and Gradle Kotlin DSL. Use compatible stable dependencies, Coroutines, StateFlow, MVVM and constructor injection. Avoid speculative abstractions and unnecessary DI frameworks.
- Phase 1 is discovery only: no connections, authentication, commands, GATT writes, reset, unpairing or firmware operations. Later device behavior requires pinned documentation, license review, offline tests and separately recorded hardware verification.
- Never invent UUIDs, packets, checksums or keys. Never hardcode secrets or log private notification contents. Logs must be bounded and exclude device identifiers. Preserve official-app pairing and document possible interaction with it.
- Firmware flashing/modification and unpairing require separate explicit user approval.
- Session authorization recorded 2026-10-13: the owner explicitly authorized opening and merging subsequent implementation PRs after required checks pass. This overrides the default stop-for-review/no-merge rule for this ongoing implementation. Never bypass protections or push directly to main; firmware and pairing approvals remain separate.
- Maintain English/Georgian phone UI, but do not claim phone localization fixes watch glyphs. Keep research confidence levels distinct.
- Maintain README, architecture, roadmap, BLE research and Georgian support docs. Report executed versus unexecuted tests and builds accurately, including iOS.
- Inspect existing rulesets before changes. Never weaken protection, grant bypasses, or require an unpublished/unsuccessful check. Require PRs without mandatory external approval for this solo repository.
- Stop and explain if external authentication is needed. Do not expose tokens or include unrelated repositories in Git operations.
