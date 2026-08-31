// Place search (city/address autocomplete) via OpenStreetMap's Nominatim.
// Free, no API key — fine for local dev. For production, swap this for a
// paid geocoder (Mapbox/Google) or a self-hosted Nominatim instance, since
// the public one is rate-limited (~1 req/sec) and asks for attribution.
const NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";

// How far around `near` to softly prefer results from, in degrees
// (~0.2 ≈ 20km). Soft bias, not a hard cutoff — distant matches can still
// show up, just ranked lower.
const BIAS_DEGREES = 0.2;

function splitLabel(item) {
  const a = item.address || {};
  const street = [a.road, a.house_number].filter(Boolean).join(" ");
  const primary = street || item.name || item.display_name.split(",")[0];

  // Prefer city/town-level for dedup+display over finer suburb/district
  // detail — multiple OSM way segments of the same street otherwise look
  // like distinct results (e.g. "Nørregade, Midtbyen" vs "Nørregade,
  // Frederiksbjerg" instead of one "Nørregade, Aarhus").
  const locality = a.city || a.town || a.village || a.municipality || a.city_district || a.suburb;
  const secondary = [locality, a.country].filter(Boolean).join(", ") || item.display_name;

  return { primary, secondary };
}

function dedupe(places) {
  const seen = new Set();
  const out = [];
  for (const place of places) {
    const key = `${place.primary}|${place.secondary}`.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(place);
  }
  return out;
}

export async function searchPlaces(query, { limit = 6, near } = {}) {
  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  const params = new URLSearchParams({
    q: trimmed,
    format: "jsonv2",
    addressdetails: "1",
    // Fetch extra so we still have `limit` results left after deduping.
    limit: String(limit * 3),
  });

  if (near) {
    params.set(
      "viewbox",
      [near.longitude - BIAS_DEGREES, near.latitude + BIAS_DEGREES, near.longitude + BIAS_DEGREES, near.latitude - BIAS_DEGREES].join(",")
    );
    // Soft bias (not "bounded=1"), so relevant far-away matches aren't hidden.
  }

  try {
    const res = await fetch(`${NOMINATIM_URL}?${params}`, {
      headers: { "Accept-Language": "en" },
    });
    if (!res.ok) return [];
    const data = await res.json();
    const places = data.map((item) => {
      const { primary, secondary } = splitLabel(item);
      return {
        id: String(item.place_id),
        label: item.display_name,
        primary,
        secondary,
        latitude: parseFloat(item.lat),
        longitude: parseFloat(item.lon),
      };
    });
    return dedupe(places).slice(0, limit);
  } catch {
    return [];
  }
}
