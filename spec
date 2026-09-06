---
name: Pro Series Ceiling
overview: Zeroshot-ready spec for a FastAPI + Postgres + Next.js app that scrapes 2026 IRONMAN Pro Series data, computes ceiling standings, and is deployable to Railway. No remaining product or stack decisions.
todos:
  - id: scaffold
    content: Create repo at /Users/sigurdlund/code/ironman-pro-standings with Docker Compose, env files, FastAPI+Alembic, Next.js
    status: pending
  - id: models-scoring
    content: Implement SQLAlchemy models, 2026 calendar seed, scoring engine, and pytest scoring tests
    status: pending
  - id: scrape
    content: Implement standings+athlete HTML parsers with fixtures, persist+recompute CLI
    status: pending
  - id: api
    content: Implement FastAPI health, standings, athlete, races, and token-gated scrape endpoints
    status: pending
  - id: frontend
    content: Implement Next.js standings table and athlete detail page against the API
    status: pending
  - id: docker-readme
    content: Add Dockerfiles, compose wiring, and README with local run plus Railway checklist
    status: pending
isProject: false
---

# IRONMAN Pro Series ceiling standings (zeroshot spec)

Implement this entire spec in one pass. Do not ask clarifying questions. Do not expand scope. Do not commit unless asked. Do not deploy to Railway.

Create a **new git repo** at [`/Users/sigurdlund/code/ironman-pro-standings`](/Users/sigurdlund/code/ironman-pro-standings). Put every file there. Do not touch sibling projects under `/Users/sigurdlund/code`.

## Locked decisions

- Stack: Python 3.12 FastAPI + SQLAlchemy 2 + Alembic + Postgres 16; Next.js 15 App Router + TypeScript + Tailwind (no UI kit)
- DB: **Postgres only** via `DATABASE_URL` (no SQLite)
- Ports: Postgres `5432`, API `8000`, frontend `3000`
- Season: **2026 only**
- Ceiling: theoretical max if the athlete takes **full points** in every **remaining** race they are eligible for; **not** gated on start lists
- Scoring: best 5 results; at most 3 full IRONMAN (WC counts as full IM; 70.3 WC counts as 70.3)
- Max points: IM 5000, 70.3 2500, IM WC 6000, 70.3 WC 3000
- Race calendar: **seed in code** (`calendar_2026.py`), not scraped from the schedule page. Overlay `completed` from the standings Race Results table when a winner is present
- Remaining races as of this spec: 70.3 Worlds (gender-specific date) + IM Worlds Kona Oct 10
- Hamburg 2026 is **women only**; Frankfurt 2026 is **men only**; 70.3 Worlds is two rows (W Sep 12, M Sep 13)
- Site never fetches ironman.com; only the backend scrape job does
- CORS: `FRONTEND_ORIGIN` allowlist, not `*`
- HTML cache: optional under `backend/.cache/` (gitignored); not the source of truth
- Rate limit live fetches to 1 request/second; User-Agent `ironman-pro-standings/0.1 (personal project)`

## Repo layout (create exactly these)

```
ironman-pro-standings/
  .gitignore
  .env.example
  docker-compose.yml
  README.md
  backend/
    Dockerfile
    pyproject.toml
    alembic.ini
    alembic/env.py
    alembic/script.py.mako
    alembic/versions/001_initial.py
    app/__init__.py
    app/config.py
    app/db.py
    app/models.py
    app/schemas.py
    app/scoring.py
    app/calendar_2026.py
    app/main.py
    app/cli.py
    app/scrape/__init__.py
    app/scrape/http.py
    app/scrape/standings.py
    app/scrape/athletes.py
    app/scrape/persist.py
    tests/test_scoring.py
    tests/test_parsers.py
    tests/fixtures/standings_snippet.html
    tests/fixtures/athlete_snippet.html
  frontend/
    Dockerfile
    package.json
    tsconfig.json
    next.config.ts
    next-env.d.ts
    postcss.config.mjs
    app/globals.css
    app/layout.tsx
    app/page.tsx
    app/athletes/[slug]/page.tsx
    lib/api.ts
```

## Env

`.env.example` and compose env:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/standings`
- `FRONTEND_ORIGIN=http://localhost:3000`
- `SCRAPE_TOKEN=dev-scrape-token`
- `API_URL=http://backend:8000` (frontend server-side, used in Docker)
- `NEXT_PUBLIC_API_URL=http://localhost:8000` (browser)

Host-run (not Docker) API uses `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/standings`.

## Docker Compose

Services: `postgres` (postgres:16-alpine, db/user/password `standings`/`postgres`/`postgres`, port 5432), `backend` (build `./backend`, command `uvicorn app.main:app --host 0.0.0.0 --port 8000`, depends on postgres healthy, port 8000), `frontend` (build `./frontend`, port 3000, `API_URL=http://backend:8000`). Backend waits for DB then runs `alembic upgrade head` before uvicorn (entrypoint script in Dockerfile).

## Backend details

### `app/calendar_2026.py`

Export `SEASON = 2026` and `RACES: list[dict]` with keys: `slug`, `title`, `date` (ISO date), `distance` (`im` | `im703`), `is_world_championship` (bool), `max_points` (int), `eligible_gender` (`W` | `M` | `both`).

Seed (slug, date, distance, max, gender):

- `im-new-zealand` — 2026-03-07 — im — 5000 — both — title ANZCO Foods IRONMAN New Zealand
- `im703-geelong` — 2026-03-22 — im703 — 2500 — both
- `im703-oceanside` — 2026-03-28 — im703 — 2500 — both
- `im-texas` — 2026-04-18 — im — 5000 — both
- `im703-aix-en-provence` — 2026-05-17 — im703 — 2500 — both
- `im-hamburg` — 2026-06-07 — im — 5000 — W
- `im703-pennsylvania` — 2026-06-14 — im703 — 2500 — both
- `im703-elsinore` — 2026-06-21 — im703 — 2500 — both
- `im-frankfurt` — 2026-06-28 — im — 5000 — M
- `im703-swansea` — 2026-07-12 — im703 — 2500 — both
- `im-lake-placid` — 2026-07-19 — im — 5000 — both
- `im703-boise` — 2026-07-25 — im703 — 2500 — both
- `im-kalmar` — 2026-08-15 — im — 5000 — both
- `im703-zell-am-see` — 2026-08-30 — im703 — 2500 — both
- `im703-world-championship-w` — 2026-09-12 — im703 — 3000 — W — is_world_championship true
- `im703-world-championship-m` — 2026-09-13 — im703 — 3000 — M — is_world_championship true
- `im-world-championship` — 2026-10-10 — im — 6000 — both — is_world_championship true

On every scrape, upsert these rows for season 2026. Default `status=upcoming`; then set `completed` when the standings race-results table has a winner for that event.

### Models (`app/models.py`)

- `athletes`: id PK, ironman_nid int unique, slug unique, name, country_code (2-letter, nullable), gender (`W`|`M`)
- `races`: id PK, season int, slug unique per season, title, date, distance, is_world_championship bool, max_points int, eligible_gender, status (`completed`|`upcoming`)
- `results`: id PK, athlete_id FK, race_id FK, points int nullable, finish_time str nullable, finish_rank int nullable, unique (athlete_id, race_id)
- `standings`: id PK, athlete_id FK, season int, official_points int, computed_points int, ceiling_points int, rank int, rank_diff int nullable, unique (athlete_id, season)

### Scoring (`app/scoring.py`)

Pure functions, no IO.

`is_full_im(distance, is_world_championship) -> bool`: true when `distance == "im"` (includes IM WC).

`best_legal_total(results: list[ScoredRace]) -> tuple[int, list[ScoredRace]]` where `ScoredRace` has `points`, `is_full_im`, `id`. Enumerate all subsets of size 0..min(5, n) with `sum(is_full_im) <= 3`; pick max sum; return (total, chosen).

`ceiling_total(completed: list[ScoredRace], remaining: list[ScoredRace]) -> int`: call `best_legal_total(completed + remaining)` where remaining races use `points=max_points`.

Remaining for an athlete = calendar races with `status=upcoming` and `eligible_gender` in `{athlete.gender, both}`.

### Parser rules (no live network in unit tests)

**Standings page** `https://www.ironman.com/proseries/standings/2026` and `?page=N` (N starts at 1). Stop when a gender table yields 0 new athlete nids (or fewer than 10 data rows).

- Women container: `.standings-search--female`
- Men container: `.standings-search--male`
- Data rows: `table tbody tr` excluding `.points-breakdown`
- `data-athlete-nid` from `a.toggle-points`
- Profile path from `a[href*="/proseries/triathletes/"]` → slug
- Rank: first numeric cell
- Official points: cell `td.views-field-points` (strip commas)
- Country: `img` under `.country-flag-formatter` — use filename / parent text; store ISO2 if present else null
- Rank diff: `.rank-change--up .number` positive, `--down` negative, missing → 0

**Race results table** on the same HTML (the cols-7 table, not the standings tables): title, date, points, winner columns. If a women’s or men’s winner name is present, mark the matching seed race `completed`. Match titles fuzzily (casefold, ignore `IRONMAN`, `70.3`, punctuation). 70.3 Worlds W/M may be absent from this table — keep seed rows upcoming until matched.

**Athlete page** `https://www.ironman.com/proseries/triathletes/{slug}`:

- Only rows in the 2026 season results table (`views-field-wtc-points`)
- Event title: `.event-title` or `td.views-field-title-1`
- Points: `td.views-field-wtc-points` — skip `—` / empty (DNF: store points null, still insert row if event matches)
- Distance: `div.race-type-logo` class contains `70.3` → im703 else im
- Match to seed race by slug/title fuzzy match + same distance; ignore non-Pro-Series events that do not match a seed race

Live scrape CLI: `python -m app.cli scrape --season 2026` (optional `--pages-only` to skip athlete pages for debugging). `POST /api/scrape` with header `X-Scrape-Token: $SCRAPE_TOKEN` runs the same pipeline.

After persist: for each athlete, compute `computed_points` and `ceiling_points`; set `rank` by `official_points` desc within gender (tie: name). Log warning if `computed_points != official_points`.

### API (`app/main.py`)

Pydantic response models in `schemas.py`.

- `GET /health` → `{ "ok": true }`
- `GET /api/races?season=2026` → list of races sorted by date
- `GET /api/standings?season=2026&gender=W|M` → list sorted by rank: `{ rank, rank_diff, name, slug, country_code, official_points, computed_points, ceiling_points, ceiling_delta }` where `ceiling_delta = ceiling_points - official_points`
- `GET /api/athletes/{slug}?season=2026` → athlete + results (each with `counts_toward_total` bool from scoring chosen set) + remaining races at max points + current/ceiling totals
- `POST /api/scrape` → 401 if token missing/wrong; 200 `{ "athletes": n, "races": n }` after job

### Tests

`test_scoring.py` (no network):

1. Three completed IM at 5000 + upcoming IM WC 6000 → ceiling replaces weakest IM with 6000 (= 16000 if the three were 5000 and two 70.3 slots empty… construct explicitly): completed `[5000 IM, 5000 IM, 5000 IM, 2500 70.3, 2400 70.3]`, remaining `[6000 IM WC]` → ceiling 5000+5000+6000+2500+2400 = 20900, not 4 IMs
2. Completed four results with only two IM; remaining 3000 70.3 WC + 6000 IM WC → both can be added by dropping the two weakest if needed; assert IM count ≤ 3
3. No remaining → ceiling == current
4. Hamburg remaining must not apply to a male athlete (eligible_gender filter in persist/scoring integration test with fixtures)

`test_parsers.py`: parse checked-in fixture snippets (minimal HTML with the CSS classes above) for one woman row and one athlete result row. Do not require a live fetch for tests to pass.

`pyproject.toml` deps: fastapi, uvicorn[standard], sqlalchemy>=2, psycopg[binary], alembic, pydantic-settings, httpx, beautifulsoup4, lxml, pytest. Scripts: none required beyond `python -m app.cli`.

Backend Dockerfile: python:3.12-slim, install deps, copy app, expose 8000, CMD alembic upgrade then uvicorn.

## Frontend details

- `lib/api.ts`: `serverApi(path)` uses `process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"`
- `app/page.tsx`: searchParam `gender` default `W`; links to `?gender=W` / `?gender=M`; table columns Rank, Name (link `/athletes/[slug]`), Country, Current, Ceiling, Headroom (ceiling − current). One-sentence disclaimer: theoretical max if they take full points in remaining Pro Series races (best five, max three IRONMAN).
- `app/athletes/[slug]/page.tsx`: name, current vs ceiling; list results with a check mark if counting; list remaining races with max points assumed
- `app/layout.tsx`: title `Pro Series ceiling standings`; simple header
- Styling: readable table, system font stack, no images required
- If API is empty (no scrape yet), show “No standings loaded. Run the scrape command.”

Frontend Dockerfile: node:22-alpine, `npm ci && npm run build`, `npm start`. `package.json` scripts: `dev`, `build`, `start`. Next config: no extra rewrite required.

## README (must include)

1. `cp .env.example .env` then `docker compose up --build`
2. From host with compose API up: `docker compose exec backend python -m app.cli scrape --season 2026` (warns this hits ironman.com)
3. Open `http://localhost:3000`
4. `cd backend && pytest` (needs no Docker if fixtures-only tests; scoring tests must pass without Postgres)
5. Railway checklist (do not execute): add Postgres plugin; backend service from `backend/Dockerfile`; frontend from `frontend/Dockerfile`; set env vars; cron daily `python -m app.cli scrape --season 2026` or POST `/api/scrape`

## Out of scope (do not implement)

- Railway/Vercel live deploy, custom domain, CI
- Start lists, 2024/2025 seasons, auth, Redis
- Client-side scrape, `/views/ajax`
- Scraping `/proseries/pro-series-schedule` (calendar is seeded)

## Done when

- `pytest` in `backend/` passes
- `docker compose up` starts all three services (or README documents the exact commands if scrape is run separately)
- `GET /health` returns ok
- Standings UI renders empty-state without scrape, and table after scrape
- No SQLite, no scrape on page load, no calls to ironman.com from Next.js
