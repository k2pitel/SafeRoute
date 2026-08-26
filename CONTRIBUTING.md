# Contributing to SafeRoute

Thanks for your interest in contributing! This is a student software
engineering project, but PRs and suggestions are welcome.

## Getting set up
See **Getting Started** in the [README](README.md) for local dev setup
(Docker Compose, backend, mobile app).

## Workflow
1. Fork/branch from `main`.
2. Keep PRs focused — one feature/fix per PR where possible.
3. Run backend tests (`pytest`) and lint (`ruff check .`) before opening a PR.
4. For mobile changes, run `npm run lint` in `mobile/`.
5. Open a PR against `main`; CI (`.github/workflows/ci.yml`) must pass.

## Code style
- Python: formatted per `ruff`/PEP8 defaults.
- JS/React Native: standard ESLint rules (see `mobile/.eslintrc` once added).

## Reporting issues
Use GitHub Issues. Include steps to reproduce, expected vs. actual behavior,
and screenshots for UI issues where relevant.
