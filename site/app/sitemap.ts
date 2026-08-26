import type { MetadataRoute } from "next";

const SITE_URL = "https://synthetic.heartlandprotocol.org";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: SITE_URL,
      lastModified: new Date("2026-08-23T00:00:00Z"),
      changeFrequency: "monthly",
      priority: 1,
    },
    {
      url: `${SITE_URL}/dataset`,
      lastModified: new Date("2026-08-26T00:00:00Z"),
      changeFrequency: "yearly",
      priority: 0.9,
    },
  ];
}
