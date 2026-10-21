// News pins are geocoded to a fixed town/district centre (see backend
// api/news/places.py) rather than the actual crime scene, so every
// story about the same place shares one exact coordinate — with years of
// archived news that stacks dozens of pins on a single point and only the
// topmost one is tappable. This spreads each pin deterministically (same
// seed always lands in the same spot) ~450 m–1.1 km around its centre, so
// every story gets its own tappable position while still reading as
// "near that town".
export function jitterCoordinate(seed, latitude, longitude) {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  const angle = ((hash % 360) * Math.PI) / 180;
  const radiusDegrees = 0.004 + ((Math.abs(hash) % 100) / 100) * 0.006;
  return {
    latitude: latitude + radiusDegrees * Math.cos(angle),
    longitude: longitude + (radiusDegrees * Math.sin(angle)) / Math.cos((latitude * Math.PI) / 180),
  };
}
