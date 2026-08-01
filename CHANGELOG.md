# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- `critique-accessibility` 0.1.1: findings now name the element they are about with its `id` (or a
  bounded CSS selector when it has none) instead of a bare line number, in both the scripted lane
  (`scripts/checks.py`) and the judged lane (`SKILL.md`, "Naming a location"). No criterion was
  added, removed, or weakened. See ADR 0027 (accessibility location-emission calibration) in
  `docs/internal/decisions/`.

### Added
- Initial repo scaffold: `library.json`, generated `.claude-plugin/plugin.json`, the conformance
  gate wrapper (`scripts/check.mjs`), the manifest generator (`scripts/gen-plugin-manifest.mjs`),
  `LICENSE` (Apache-2.0), `AGENTS.md`, `README.md`, `RELEASE-NOTES.md`, and the Diataxis docs tree.
