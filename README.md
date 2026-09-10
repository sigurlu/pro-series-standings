# IRONMAN Pro Series Standings

Scrapes the 2026 IRONMAN Pro Series standings, computes each athlete's **ceiling**
(theoretical maximum points if they take full points in every remaining race they
are eligible for — best five results, at most three full IRONMAN), and serves a
standings table plus per-athlete detail pages.

Stack: FastAPI + SQLAlchemy 2 + Alembic + Postgres 16 (backend), Next.js 15 App
Router + TypeScript + Tailwind (frontend), Docker Compose for local dev.

> Scrapes public data from ironman.com for personal, non-commercial use. Not
> affiliated with, authorized, or endorsed by The IRONMAN Group. Review
> IRONMAN's Terms of Service before running the scraper or deploying this, and
> keep the built-in 1 request/second rate limit.

## 1. Run locally

```sh
cp .env.example .env
docker compose up --build
```

This starts Postgres (5432), the API (8000), and the frontend (3000). The backend
waits for Postgres, runs `alembic upgrade head`, then serves uvicorn.

## 2. Load data (hits ironman.com)

With the compose stack up, run the scrape job. **This makes live requests to
`www.ironman.com`**, rate-limited to 1 request/second:

```sh
docker compose exec backend python -m app.cli scrape --season 2026
```

Add `--pages-only` to skip the per-athlete pages while debugging. You can also
`POST /api/scrape` with header `X-Scrape-Token: dev-scrape-token`.

### How the scrape reads the site

- The standings pager is **0-indexed** (`?page=0` is ranks 1-10).
- Scraped events are matched to the seeded calendar by their
  `/proseries/races/<slug>` URL, falling back to fuzzy title tokens (live
  titles carry sponsor prefixes / championship suffixes).
- A race is **completed** (and drops out of every ceiling) once its calendar
  date has passed, or once any athlete has scored points for it — whichever
  comes first. The date is the primary signal: Pro Series points can lag the
  race by several days, and a race that already happened is not still winnable.
- **Start lists:** the scrape also reads the published pro start lists for the
  remaining World Championship races (`START_LISTS` in `calendar_2026.py`) and
  matches names to athletes. Once a race has a start list, it only enters the
  ceiling of athletes who are on it — a top-ranked athlete who is skipping Kona
  gets no Kona points in their ceiling. Names are matched accent-insensitively
  with a first-name nickname fallback (Matt / Matthew); unmatched names (almost
  all non–Pro Series or age-group entrants) are logged.
- **Known limitation:** each athlete page only serves its 10 most recent
  results (the rest are behind an infinite-scroll "Load More", which is out of
  scope). An athlete with a long 2025/2024 history can have a 2026 result
  missing, so `computed_points` falls below `official_points` — the scrape logs
  a warning, and the ceiling folds the unseen points back in so headroom never
  goes negative. `official_points` and `rank` come straight from the standings
  table and are exact.

## 3. Open the app

<http://localhost:3000> — before the first scrape it shows
"No standings loaded. Run the scrape command."

## 4. Tests

```sh
cd backend
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/pytest
```

Scoring and parser tests need no Postgres and no network.

## 5. Railway deploy

Deployed as four services in one project, all from this repo:

| Service | Source | Notes |
|---|---|---|
| `Postgres` | Railway PostgreSQL | private-network only |
| `backend` | `backend/` · Dockerfile | healthcheck `/health`, binds `$PORT` |
| `frontend` | `frontend/` · Dockerfile | `next start`, public domain |
| `scrape` | `backend/` · Dockerfile | cron `0 5 * * *`, start command `python -m app.cli scrape --season 2026` |

- **Isolated monorepo**: each service sets a root directory (`backend` / `frontend`)
  and a watch pattern so a push only redeploys the service it touched.
- **backend / scrape vars**:
  `DATABASE_URL=postgresql+psycopg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}`,
  `PORT=8000`, `SCRAPE_TOKEN` (backend only), `FRONTEND_ORIGIN` = the frontend URL.
- **frontend var**: `API_URL=http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8000`
  (the browser never calls the API directly, so `NEXT_PUBLIC_API_URL` is unused).
- Bind `0.0.0.0`, not `::` — Railway's healthcheck is IPv4.
- First data load: the daily cron, or `railway ssh --service backend
  "python -m app.cli scrape --season 2026"`. A one-off `POST /api/scrape` also
  works but the HTTP call 502s at Railway's 5-minute edge timeout while the
  scrape keeps running server-side.

## License

MIT — see [LICENSE](LICENSE). The license covers this project's source only; it
grants no rights to IRONMAN's data, trademarks, or website content.
