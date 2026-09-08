import type { MetadataRoute } from "next";
import { serverApi, type Standing } from "../lib/api";

const SITE_URL = "https://www.improseries.com";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base: MetadataRoute.Sitemap = [
    {
      url: SITE_URL,
      changeFrequency: "daily",
      priority: 1,
    },
  ];

  let athletes: Standing[] = [];
  try {
    const [women, men] = await Promise.all([
      serverApi<Standing[]>("/api/standings?season=2026&gender=W"),
      serverApi<Standing[]>("/api/standings?season=2026&gender=M"),
    ]);
    athletes = [...women, ...men];
  } catch {
    return base;
  }

  return [
    ...base,
    ...athletes.map((a) => ({
      url: `${SITE_URL}/athletes/${a.slug}`,
      changeFrequency: "daily" as const,
      priority: 0.6,
    })),
  ];
}
