import type { Metadata } from "next";
import Link from "next/link";
import { pointsAsDuration, serverApi, type Standing } from "../lib/api";
import { Tooltip } from "./tooltip";

const n = (v: number) => v.toLocaleString("en-US");

type Sort = "ceiling" | "current";

export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<{ gender?: string }>;
}): Promise<Metadata> {
  const { gender: genderParam } = await searchParams;
  const gender = genderParam === "M" ? "M" : "W";
  const label = gender === "M" ? "Men's" : "Women's";
  const title = `${label} Standings`;
  const description = `2026 IRONMAN Pro Series ${label.toLowerCase()} standings with each athlete's ceiling — the most points they could still finish the season with.`;
  // Both genders live at "/" behind a query param, and every ?gender=M
  // variant should canonicalize to the same URL as the default view — Next's
  // URL resolver also collapses any query string once the pathname is
  // exactly "/" (resolveAbsoluteUrlWithPathname), so a distinct canonical
  // per gender isn't achievable here anyway.
  const canonical = "https://www.improseries.com/";

  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      title,
      description,
      url: canonical,
      siteName: "Pro Series Standings",
      type: "website",
    },
    twitter: { card: "summary_large_image", title, description },
  };
}

const COLUMN_HELP = {
  current:
    "Official 2026 Pro Series points from the standings — best five results, at most three full IRONMAN.",
  ceiling:
    "The most points the athlete could finish 2026 with: full points in every remaining race they're on the start list for, still capped at best five / three IRONMAN.",
  behind:
    "How far behind the #1 athlete on the sorted column, expressed as course time (1 point ≈ 1 second).",
  headroom:
    "Ceiling minus current — how many points are still on the table.",
  meter:
    "Current points as a share of the ceiling — how much of the best-case total is already banked.",
} as const;

function SortHeader({
  label,
  col,
  gender,
  active,
}: {
  label: string;
  col: Sort;
  gender: string;
  active: boolean;
}) {
  return (
    <th className="num">
      <Link
        href={`/?gender=${gender}&sort=${col}`}
        className={`sort ${active ? "active" : ""}`}
        aria-sort={active ? "descending" : "none"}
      >
        <span className="th-label">{label}</span>
        <span className="caret">{active ? "▾" : ""}</span>
      </Link>
      <Tooltip text={COLUMN_HELP[col]}>
        <span className="th-info" aria-label={`About ${label}`}>
          ?
        </span>
      </Tooltip>
    </th>
  );
}

export default async function StandingsPage({
  searchParams,
}: {
  searchParams: Promise<{ gender?: string; sort?: string }>;
}) {
  const { gender: genderParam, sort: sortParam } = await searchParams;
  const gender = genderParam === "M" ? "M" : "W";
  const sort: Sort = sortParam === "current" ? "current" : "ceiling";

  let standings: Standing[] = [];
  let failed = false;
  try {
    standings = await serverApi<Standing[]>(
      `/api/standings?season=2026&gender=${gender}`,
    );
  } catch {
    failed = true;
  }

  const hasData = !failed && standings.length > 0;

  const rows = [...standings].sort((a, b) =>
    sort === "current"
      ? b.official_points - a.official_points ||
        b.ceiling_points - a.ceiling_points
      : b.ceiling_points - a.ceiling_points ||
        b.official_points - a.official_points,
  );

  return (
    <>
      <div className="page-head">
        <h1>Ceiling standings</h1>
        <p className="lede">
          A projection of how the 2026 season could finish. Each athlete&rsquo;s{" "}
          <em>ceiling</em> is the most points they could still score — full
          points in every remaining race they&rsquo;re on the start list for,
          keeping the best-five / max-three-IRONMAN rule.
        </p>
      </div>

      <div className="toolbar">
        <nav className="segmented" aria-label="Gender">
          <Link
            href={`/?gender=W&sort=${sort}`}
            className={gender === "W" ? "active" : ""}
          >
            Women
          </Link>
          <Link
            href={`/?gender=M&sort=${sort}`}
            className={gender === "M" ? "active" : ""}
          >
            Men
          </Link>
        </nav>
        {hasData && (
          <span className="count-hint">{standings.length} athletes</span>
        )}
      </div>

      {!hasData ? (
        <div className="card">
          <p className="empty">
            <strong>No standings loaded</strong>
            Run the scrape command: <code>python -m app.cli scrape</code>
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th className="col-rank">#</th>
                  <th>Athlete</th>
                  <SortHeader
                    label="Ceiling"
                    col="ceiling"
                    gender={gender}
                    active={sort === "ceiling"}
                  />
                  <th className="num">
                    <span className="th-label">Behind #1</span>
                    <Tooltip text={COLUMN_HELP.behind}>
                      <span className="th-info" aria-label="About Behind #1">
                        ?
                      </span>
                    </Tooltip>
                  </th>
                  <SortHeader
                    label="Current"
                    col="current"
                    gender={gender}
                    active={sort === "current"}
                  />
                  <th className="num">
                    <span className="th-label">Headroom</span>
                    <Tooltip text={COLUMN_HELP.headroom}>
                      <span className="th-info" aria-label="About Headroom">
                        ?
                      </span>
                    </Tooltip>
                  </th>
                  <th>
                    <span className="th-label">Locked in</span>
                    <Tooltip text={COLUMN_HELP.meter}>
                      <span className="th-info" aria-label="About Locked in">
                        ?
                      </span>
                    </Tooltip>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s, i) => {
                  const pct =
                    s.ceiling_points > 0
                      ? Math.round(
                          (s.official_points / s.ceiling_points) * 100,
                        )
                      : 0;
                  const headroom = s.ceiling_points - s.official_points;
                  const leader = rows[0];
                  const behind =
                    sort === "current"
                      ? leader.official_points - s.official_points
                      : leader.ceiling_points - s.ceiling_points;
                  return (
                    <tr key={s.slug}>
                      <td className="col-rank">
                        <span className={`rank ${i < 3 ? "top" : ""}`}>
                          <span className="pos">{i + 1}</span>
                        </span>
                      </td>
                      <td>
                        <span className="athlete-cell">
                          <Link
                            href={`/athletes/${s.slug}`}
                            className="name"
                          >
                            {s.name}
                          </Link>
                          <span className="country">
                            {s.country_code ?? "—"}
                          </span>
                        </span>
                      </td>
                      <td
                        className={`num ${sort === "ceiling" ? "sorted" : ""}`}
                      >
                        {n(s.ceiling_points)}
                      </td>
                      <td className="num behind">
                        {behind <= 0 ? "—" : pointsAsDuration(behind)}
                      </td>
                      <td
                        className={`num ${sort === "current" ? "sorted" : ""}`}
                      >
                        {n(s.official_points)}
                      </td>
                      <td className="num">
                        <span
                          className={`headroom ${headroom === 0 ? "flat" : ""}`}
                        >
                          {headroom === 0 ? "—" : `+${n(headroom)}`}
                        </span>
                      </td>
                      <td>
                        <span
                          className="meter"
                          style={
                            { "--pct": `${pct}%` } as React.CSSProperties
                          }
                        >
                          <span />
                        </span>
                        <span className="meter-label">{pct}%</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <p className="note">
        Ranked by ceiling by default — tap <strong>Current</strong> or{" "}
        <strong>Ceiling</strong> to re-sort; <strong>Behind #1</strong> tracks
        whichever column is active, at 1 point ≈ 1 second. Ceiling assumes best
        five results and at most three full IRONMAN races, and only adds
        a remaining race once the athlete appears on its published pro start list.
      </p>
    </>
  );
}
