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

## 5. Railway checklist (not executed here)

- Add the Postgres plugin; note its connection URL.
- Backend service built from `backend/Dockerfile`.
- Frontend service built from `frontend/Dockerfile`.
- Set env vars per `.env.example`: `DATABASE_URL` (from the plugin, with the
  `postgresql+psycopg://` driver prefix), `FRONTEND_ORIGIN`, `SCRAPE_TOKEN`,
  `API_URL`, `NEXT_PUBLIC_API_URL`.
- Schedule a daily cron running `python -m app.cli scrape --season 2026` or an
  authenticated `POST /api/scrape`.

## License

MIT — see [LICENSE](LICENSE). The license covers this project's source only; it
grants no rights to IRONMAN's data, trademarks, or website content.
