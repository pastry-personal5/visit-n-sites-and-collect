<INSTRUCTIONS>
## Project summary
This repo automates:
1) finding “campaign links” from a few publisher/community sites (collectors like `c1`, `d1`)
2) visiting those campaign links (Selenium + `undetected-chromedriver`)
3) optionally syncing visit history to Google Drive

Primary entry point: `src/visit_n_sites_and_collect/main.py` (also `./1`).

## Local-only config / secrets
- Treat `config/global_config.yaml` as a local secret file (it is gitignored). Do not add or commit credentials.
- Update `config/global_config.yaml.template` when new config keys are required.
- Output/state lives under `data/` (gitignored). Avoid writing tests that depend on real `data/` contents.

## How to run
- Preferred runner: `uv` with Python 3.11.
  - Run: `./1`
  - Tests: `make test`
  - Lint/style (best-effort): `make lint` / `make style`
  - Cleanup visited URLs: `make clean_data`

## Tooling expectations
- Python: >= 3.11 (required for `undetected-chromedriver` in this project).
- Selenium collectors require a working Chrome/Chromium install compatible with `undetected-chromedriver`.
- Cloud storage tests are opt-in:
  - `RUN_CLOUD_STORAGE_TESTS=1 make test` (also requires valid Google credentials/config).

## Code conventions (keep changes minimal)
- Prefer small, testable helpers and typed signatures; match existing module style.
- Logging: use `loguru.logger`; prefer `logger.exception(...)` when catching exceptions.
- Networking: do not add tests that hit real external sites; use stubs/mocks (see `tests/test_publisher.py`, `tests/test_collector_cookie.py` patterns).
- Collectors:
  - Implement as a `LinkFinderImplBase` subclass under `src/visit_n_sites_and_collect/`.
  - Wire via a factory in `src/visit_n_sites_and_collect/main.py` and a toggle in config (`collectors:`).

## Known issues
- See `src/visit_n_sites_and_collect/ISSUES.md` for documented edge cases (cloud-storage guards, cleanup semantics, infinite waits).
</INSTRUCTIONS>
