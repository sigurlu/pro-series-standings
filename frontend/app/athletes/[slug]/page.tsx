import type { Metadata } from "next";
import Link from "next/link";
import { serverApi, type AthleteDetail } from "../../../lib/api";

const n = (v: number) => v.toLocaleString("en-US");

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;

  let athlete: AthleteDetail | null = null;
  try {
    athlete = await serverApi<AthleteDetail>(
      `/api/athletes/${slug}?season=2026`,
    );
  } catch {
    athlete = null;
  }

  if (!athlete) {
    return { title: "Athlete", robots: { index: false, follow: true } };
  }

  const title = athlete.name;
  const description = `${athlete.name}'s 2026 IRONMAN Pro Series results: ${n(
    athlete.current_points,
  )} points so far, with a ceiling of ${n(athlete.ceiling_points)} points if they take full points in every remaining race they're eligible for.`;
  const canonical = `/athletes/${slug}`;

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

export default async function AthletePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let athlete: AthleteDetail | null = null;
  try {
    athlete = await serverApi<AthleteDetail>(
      `/api/athletes/${slug}?season=2026`,
    );
  } catch {
    athlete = null;
  }

  if (!athlete) {
    return (
      <>
        <Link href="/" className="backlink">
          ← Standings
        </Link>
        <div className="card">
          <p className="empty">
            <strong>No data for this athlete</strong>
            Run the scrape command to load results.
          </p>
        </div>
      </>
    );
  }

  const headroom = athlete.ceiling_points - athlete.current_points;
  const pct =
    athlete.ceiling_points > 0
      ? Math.round((athlete.current_points / athlete.ceiling_points) * 100)
      : 0;
  const shownPoints = athlete.results.reduce((sum, r) => sum + (r.points ?? 0), 0);
  const hiddenPoints = athlete.current_points - shownPoints;

  return (
    <>
      <Link href="/" className="backlink">
        ← Standings
      </Link>

      <div className="athlete-head">
        <h1>{athlete.name}</h1>
        <span className="tag">{athlete.gender === "M" ? "Men" : "Women"}</span>
      </div>

      <div className="stats">
        <div className="stat">
          <span className="label">Current</span>
          <span className="value">{n(athlete.current_points)}</span>
        </div>
        <div className="stat">
          <span className="label">Ceiling</span>
          <span className="value">{n(athlete.ceiling_points)}</span>
        </div>
        <div className="stat accent">
          <span className="label">Headroom</span>
          <span className="value">
            {headroom === 0 ? "—" : `+${n(headroom)}`}
          </span>
        </div>
      </div>

      <div className="ceiling-bar">
        <div className="track">
          <div className="fill" style={{ width: `${pct}%` }} />
        </div>
        <p className="caption">
          Current points are {pct}% of the theoretical ceiling.
        </p>
      </div>

      <h2 className="section-title">Results</h2>
      {hiddenPoints > 50 && (
        <p className="note">
          Current total includes {n(hiddenPoints)} points from earlier 2026
          races not shown here — the source only lists an athlete&rsquo;s ten
          most recent events.
        </p>
      )}
      {athlete.results.length === 0 ? (
        <div className="card">
          <p className="empty">No completed results yet.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Distance</th>
                  <th className="num">Points</th>
                  <th>Counts</th>
                </tr>
              </thead>
              <tbody>
                {athlete.results.map((r) => (
                  <tr key={r.event} className={r.counts_toward_total ? "counts" : ""}>
                    <td>{r.event}</td>
                    <td>
                      <span
                        className={`pill ${r.distance === "im" ? "im" : ""}`}
                      >
                        {r.distance === "im" ? "IRONMAN" : "70.3"}
                      </span>
                    </td>
                    <td className="num">
                      {r.points === null ? (
                        <span className="dash">—</span>
                      ) : (
                        n(r.points)
                      )}
                    </td>
                    <td>
                      {r.counts_toward_total ? (
                        <span className="check">✓</span>
                      ) : (
                        <span className="dash">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <h2 className="section-title">
        Remaining races · on the start list · assumed max points
      </h2>
      {athlete.remaining.length === 0 ? (
        <div className="card">
          <p className="empty">
            Not on the published start list for any remaining race, so the
            ceiling equals the current total.
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Event</th>
                  <th className="num">Max points</th>
                </tr>
              </thead>
              <tbody>
                {athlete.remaining.map((r) => (
                  <tr key={r.slug}>
                    <td>{r.title}</td>
                    <td className="num">{n(r.max_points)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
