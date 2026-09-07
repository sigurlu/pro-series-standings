from __future__ import annotations

import argparse
import logging
import sys

from app.db import SessionLocal
from app.scrape.persist import run_scrape


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    scrape = sub.add_parser("scrape", help="Scrape the IRONMAN Pro Series standings")
    scrape.add_argument("--season", type=int, default=2026)
    scrape.add_argument("--pages-only", action="store_true")
    args = parser.parse_args(argv)

    # Log to stdout — platforms (Railway, Docker, GCP…) tag anything on stderr
    # as ERROR, which made every INFO line show up red.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    # httpx logs one INFO line per request (~500 per scrape) — too noisy
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if args.command == "scrape":
        if args.season != 2026:
            parser.error("only season 2026 is supported")
        logging.getLogger("app.cli").warning(
            "this command makes live requests to www.ironman.com "
            "(rate limited to 1 req/sec)"
        )
        with SessionLocal() as db:
            athletes, races = run_scrape(db, pages_only=args.pages_only)
        print(f"scraped {athletes} athletes, {races} races")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
