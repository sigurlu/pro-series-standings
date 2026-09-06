const base =
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export async function serverApi<T>(path: string): Promise<T> {
  const res = await fetch(`${base}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

/** Pro Series points map roughly 1:1 to seconds of course time. */
export function pointsAsDuration(points: number): string {
  const s = Math.max(0, Math.round(points));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return m > 0 ? `${h}h ${m}m` : `${h}h`;
  if (m > 0) return m < 5 && sec > 0 ? `${m}m ${sec}s` : `${m}m`;
  return `${sec}s`;
}

export interface Standing {
  rank: number;
  rank_diff: number | null;
  name: string;
  slug: string;
  country_code: string | null;
  official_points: number;
  computed_points: number;
  ceiling_points: number;
  ceiling_delta: number;
}

export interface AthleteResult {
  event: string;
  points: number | null;
  distance: string;
  counts_toward_total: boolean;
}

export interface RemainingRace {
  slug: string;
  title: string;
  max_points: number;
}

export interface AthleteDetail {
  name: string;
  slug: string;
  gender: string;
  current_points: number;
  ceiling_points: number;
  results: AthleteResult[];
  remaining: RemainingRace[];
}
