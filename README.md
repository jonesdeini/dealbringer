# Dealbringer

A privacy-first, self-hosted grocery coupon tool. Milestone 1 implements an entirely
local fake retailer. Wegmans is a disabled placeholder pending research into a
permitted integration and authorization workflow. No accounts or browser are needed.

## Run locally

Install Python 3.12+ and uv, then:

```sh
uv sync --locked
uv run dealbringer stores
uv run dealbringer run fake --dry-run
uv run dealbringer run fake
uv run dealbringer run fake
uv run dealbringer history
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The fixture contains four offers: two eligible, one already clipped, and one
ineligible. A dry-run reports three skipped offers and changes no coupon state;
it still saves a run summary. The first normal run clips two offers; subsequent
runs find three already clipped. JSON summaries include counts, UTC start time,
duration, and actionable errors. Exit codes: 0 success, 1 workflow failure,
2 configuration/storage error or unavailable adapter. Discovery failures appear
in `errors`; `failed` counts individual offers whose clipping failed.

`DEALBRINGER_DATA_DIR` defaults to `./data`. Set it in your shell to change storage;
`.env.example` documents the setting (the CLI does not load `.env` automatically).
SQLite stores summaries only; `fake-state.json` stores fixture coupon IDs.
Files are local and ignored by Git. Run one job at a time against a data directory.

## Container

```sh
docker compose build
docker compose run --rm dealbringer
# Inspect persistent history or run without clipping:
docker compose run --rm dealbringer history
docker compose run --rm dealbringer run fake --dry-run
```

Compose uses a persistent named volume at `/data`, a non-root user (UID 10001),
process reaping, no network, no inbound ports, and no automatic restart. The image
uses Debian glibc. Playwright and Chromium are deliberately deferred until the
retailer feasibility milestone; there is no browser version to coordinate yet.

For Unraid, replace the named mount with
`/mnt/user/appdata/dealbringer:/data` and make that directory writable by UID 10001
before running. Schedule the short-lived `docker compose run --rm dealbringer`
command using the host scheduler. Restarting a fake job discovers saved state and
skips prior clips. Back up `/data` while no job is running; restore it to the same
mount with the same ownership. There are no sessions to expire in this milestone.
If a job fails, inspect its exit code and JSON errors, check volume ownership and
available disk space, then retry. Do not delete the volume to troubleshoot unless
you intend to discard history and reset the fake retailer.

## Architecture and scope

`cli.py` parses commands and coordinates storage; `config.py` resolves the data
path. `runner.py` discovers, filters, clips, verifies, and summarizes via the small
`Store` protocol. Typed dataclasses live in `models.py`, SQLite in `history.py`,
and retailer behavior in `stores/`. The fake adapter uses atomic file replacement
for persistent state. Expected adapter errors and timeouts allow other offers to
continue; raw exception details are not included in summaries.

Runtime dependencies are standard library only. Pytest and Ruff are development
dependencies; uv_build builds the package. `uv.lock` pins dependencies for local
development. The container installs the dependency-free package with pip.

Next: Milestone 2 must establish Wegmans' permitted access and authorization path
before adding login, session storage, Playwright, selectors, or live clipping.
Production retries, hard timeout enforcement, and browser sandbox/shared-memory
configuration remain for later milestones.
