# Dealbringer — repository instructions for Codex

## Project in one paragraph

**Dealbringer** is a privacy-first, self-hosted application for managing digital grocery coupons. Its initial use case is discovering and clipping eligible coupons on a user's own Wegmans account, without relying on a Chrome extension, a hosted third-party service, or an always-on desktop. The coupon-clipping component may be called **Clipbringer**. The name is inspired by *Oathbringer*; keep the code and product approachable rather than turning the theme into an architectural constraint.

This is a personal project and also an opportunity to learn production-quality Python, Playwright, containerization, and operating a service on owned hardware. The developer is experienced in Ruby on Rails, backend architecture, Selenium, and CI/CD, but is newer to Python browser automation and self-hosted operations.

## What success looks like

A user can authorize a retailer account through a legitimate, permitted workflow; run a headless job on their own server; discover eligible coupons; clip those not already clipped; and view a clear summary of what happened. Jobs should be repeatable, observable, safe to retry, and respectful of the retailer's service rules.

Start with **one user and one retailer (Wegmans)**. Design for additional retailer adapters later, but do not implement speculative integrations.

## First principles

- **Privacy first.** No third-party browser extensions, analytics SDKs, external telemetry, or hosted credential vaults are required.
- **Permission first.** Check retailer terms and available official/supported integration mechanisms before attempting live automation. Do not assume that personal-account access authorizes scraping or bot use. If automated access is prohibited or unclear, implement mock/local flows and document the blocker rather than work around it.
- **Never bypass authentication or abuse controls.** Do not defeat CAPTCHA, MFA, bot detection, rate limits, paywalls, or access restrictions. Don't build stealth/fingerprint-spoofing or proxy-rotation features.
- **Keep credentials private.** Never commit passwords, cookies, tokens, Playwright storage-state files, or live account data. Prefer interactive manual sign-in and reusable, locally protected session state when permitted. Support straightforward manual reauthentication.
- **Reliable over clever.** Bounded retries, clear failures, conservative request volume, idempotent operations, and verification of successful clipping are more important than speed.
- **Simple deployment.** A single container should be enough for the first version. Avoid extra infrastructure until there is a concrete need.

## Proposed technology choices

These are starting preferences, not mandates. If there's a compelling alternative, explain the tradeoff before making a major architectural change.

- Python 3.12+; use modern type annotations.
- `uv` for environment/dependency management and reproducible lockfiles.
- Official **Python Playwright** API, preferably async where it meaningfully helps. Chromium, headless for scheduled runs and headed for interactive setup/debugging.
- `pytest` for tests, `ruff` for linting/formatting. Use type checking if it proves useful, without overengineering the initial scaffold.
- SQLite for local run history and simple metadata; files/volumes for browser session state. Do not store authentication material in SQLite unless there is a clear need and protection model.
- Python standard library logging or another small structured-logging solution. Mask sensitive values.
- Docker/Compose for packaging. Choose a **Debian/Ubuntu glibc base, not Alpine**, for browser compatibility. Pin matching Playwright package/browser image versions. If using Microsoft's Playwright image, note its testing-oriented defaults and follow its guidance on running untrusted sites with a non-root sandboxed browser.
- No Rails service, Kubernetes, Redis, Celery, RabbitMQ, web frontend, or public API in v1.

## Hosting context

- Target host: **Unraid on an HPE DL380 Gen9** (2× Xeon E5-2699 v4, 128 GB RAM with a planned upgrade to 256 GB). No GPU is needed for coupon clipping.
- Run as its own project, separate from other applications on the host.
- Persist data on an Unraid SSD-backed appdata share, for example `/mnt/user/appdata/dealbringer/`, mapped to a predictable container path such as `/data`.
- Favor a **short-lived, scheduled container run** (host cron/User Scripts or equivalent) instead of a continuously running application scheduler for v1.
- Expose **no inbound network ports** unless a later feature demonstrably needs them. Never expose browser debugging ports publicly.
- Run with a non-root user, sensible file permissions, clean process reaping (`init: true`), and sufficient Chromium shared memory. Don't use `privileged: true` as a shortcut.
- Document backups, session expiry, restart behavior, and how to troubleshoot a failed job.

## Product behavior — MVP

1. Discover supported retailer adapters (initially Wegmans, pending permitted access).
2. Provide a separate, explicit account-authorization/setup workflow. Never silently collect credentials.
3. Discover available coupon offers using a supported/authorized mechanism. Handle lazy loading or pagination only where permitted, with limits to prevent infinite loops.
4. Identify offers that are already clipped vs. offers requiring action.
5. Clip the remaining offers, verifying the result when possible. Avoid re-clipping and duplicate side effects.
6. Produce a run summary: offers found, previously clipped, newly clipped, skipped, failed, duration, and actionable errors.
7. Support a **dry-run** that discovers and reports without changing anything.
8. Save minimal run history locally. Make logs useful for debugging without leaking personal or session information.

**Not in v1:** deal recommendations, purchase-history analysis, shopping lists, price comparison, multi-user support, dashboards, mobile apps, AI agents, and continuously running orchestration. These are possible future directions, not reasons to expand the first milestone.

## Suggested code boundaries

Keep the implementation small and readable. A possible layout:

```text
.
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── compose.yaml
├── .env.example
├── src/dealbringer/
│   ├── cli.py
│   ├── config.py
│   ├── browser.py
│   ├── models.py
│   ├── history.py
│   └── stores/
│       ├── base.py
│       ├── fake.py
│       └── wegmans.py
└── tests/
```

Keep store-specific selectors, page behavior, offer semantics, and any API integration in the individual store adapter. Use a small, explicit contract between orchestration and adapters (e.g. list/discover offers, determine status, clip, verify). Avoid a framework or plugin architecture that only has one real implementation.

## Developer experience / interface

Aim for a simple CLI; refine names if the implemented tool suggests something clearer:

```bash
uv run dealbringer stores
uv run dealbringer run fake --dry-run
uv run dealbringer run wegmans --dry-run
uv run dealbringer run wegmans
uv run dealbringer history
```

An interactive `auth` or `login` command may be useful, but only implement it after deciding on a permitted, secure session workflow. Commands needing a retailer session must fail clearly rather than hanging in a headless container or silently retrying forever.

## Implementation milestones

### Milestone 1: working skeleton (do this first)

- Set up Python package, `uv`, CLI, Ruff, pytest, `.gitignore`, `.env.example`, and a concise README.
- Define small typed offer/result models and the minimal store adapter interface.
- Add a **fake retailer / local test fixture** so the complete discovery → dry-run → clip → summary workflow runs offline, with deterministic tests.
- Add SQLite-backed run history if it remains simple; otherwise defer it and explain why.
- Add a Dockerfile + Compose example that runs the fake adapter in a single container and persists `/data`.
- Make `uv run pytest`, `uv run ruff check .`, and the example container command work.
- Do **not** log in to Wegmans or try live clipping in this milestone.

### Milestone 2: retailer feasibility and authorization

- Research Wegmans' current terms, the official website/account flow, and any supported coupon integration/API. Document conclusions and sources in `docs/wegmans-feasibility.md`.
- Identify what would be required for lawful/permitted interactive sign-in, session persistence, coupon discovery, and clipping. Do not infer private endpoint contracts from guesswork.
- If permitted, implement a small manual/headed proof of concept and then adapt it to headless execution. Keep interactions low-volume and within the authorized account.
- If prohibited or uncertain, stop before live automation. Leave a documented adapter boundary and fixture-based tests rather than implementing evasion.

### Milestone 3: operational reliability

- Add bounded timeouts/retries, meaningful exit codes, failure summaries, and idempotent behavior.
- Verify that a scheduled container run works on Unraid with persistent data and no public ports.
- Document first-time setup, session refresh, schedule configuration, backup/restore, and resource/security settings.
- Add CI for tests/linting and optionally container builds after the core behavior is stable.

## How Codex should work in this repository

- Before writing code, inspect the current repository and reuse existing conventions. These directions describe intent, not proof that files already exist.
- For a substantial task, briefly state a plan, implement the smallest coherent slice, then run relevant tests and report exactly what passed or could not run.
- Keep dependencies minimal; explain additions that aren't obvious.
- Prefer straightforward Python over patterns translated mechanically from Rails.
- Use `pathlib`, type annotations, clear exceptions, and small functions with explicit inputs/outputs.
- Write tests for success, already-clipped, partial failure, timeout, and repeated-run behavior. Prefer fixtures/mocks over brittle live-site tests.
- Never commit secrets or real session data; keep `/data`, `.env`, screenshots, traces, and auth states out of Git. If traces or screenshots are needed for debugging, ensure they are local and may contain sensitive information.
- Do not invent facts about Wegmans DOM selectors, APIs, authentication, or support for automation. Clearly identify unknowns and verify through authorized channels.
- Do not create a public web interface or integrate AI without a specific user request.
- In your final response after making changes, summarize what changed, how it was tested, important open questions, and the most useful next step.

## First task for Codex

**Build Milestone 1 only.** Start by checking whether this repository is empty, propose a minimal file structure, then implement a runnable offline fake-store workflow with tests and Docker support. Keep the Wegmans adapter as an explicit placeholder until its permitted integration path is established. Do not attempt to log in to a retailer or clip real coupons yet.
