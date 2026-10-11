export const inCity = ([lng, lat]) =>
  Number.isFinite(lng) &&
  Number.isFinite(lat) &&
  lng >= -122.525 &&
  lng <= -122.345 &&
  lat >= 37.706 &&
  lat <= 37.835;

export const normalize = (value) =>
  String(value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\bsan francisco\b|\bsf\b|\bca\b|\b94\d{3}\b/g, "")
    .replace(/['’]/g, "")
    .replace(/&/g, " and ")
    .replace(/\bstreet\b/g, "st")
    .replace(/\bavenue\b/g, "ave")
    .replace(/\bboulevard\b/g, "blvd")
    .replace(/\bdrive\b/g, "dr")
    .replace(/\broad\b/g, "rd")
    .replace(/\b0+(\d)/g, "$1")
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

export function createSearch(addressRows, placeRows) {
  const addresses = addressRows
    .map((r) => ({
      id: `address:${r.eas_address_id}`,
      label: r.address,
      coordinates: [+r.longitude, +r.latitude],
      neighborhood: r.nhood || "San Francisco",
      kind: "address",
    }))
    .filter((p) => inCity(p.coordinates));
  const landmarks = addressRows
    .filter((r) => r.complete_landmark_name)
    .map((r) => ({
      id: `landmark:${r.eas_address_id}`,
      label: r.complete_landmark_name,
      coordinates: [+r.longitude, +r.latitude],
      neighborhood: r.nhood || "San Francisco",
      address: r.address,
      aliases: [r.landmark_aliases || ""],
      kind: "landmark",
    }));
  const named = [...landmarks, ...placeRows].filter((p) =>
    inCity(p.coordinates),
  );
  const entries = [...named, ...addresses].map(
    ({ aliases = [], ...place }) => ({
      place,
      names: [place.label, ...aliases].map(normalize).filter(Boolean),
      key: normalize([place.label, ...aliases, place.address || ""].join(" ")),
    }),
  );

  function search(input) {
    const q = normalize(String(input).slice(0, 200));
    if (q.length < 2) return [];
    const words = q.split(" ");
    const numbered = /^\d+\s/.test(q);
    const scores = [];
    for (const entry of entries) {
      if (!words.every((word) => entry.key.includes(word))) continue;
      const { place, names } = entry;
      const score = names.includes(q)
        ? 0
        : names.some((name) => name.endsWith(" " + q))
          ? 1
          : names.some((name) => name.startsWith(q))
            ? 2
            : names.some((name) =>
                  words.every((word) =>
                    name.split(" ").some((part) => part.startsWith(word)),
                  ),
                )
              ? 3
              : 4;
      const preference = numbered
        ? place.kind === "address"
          ? 0
          : 1
        : place.kind === "landmark"
          ? 0
          : place.kind === "place"
            ? 1
            : 2;
      scores.push({ place, score, preference });
    }
    scores.sort(
      (a, b) =>
        a.score - b.score ||
        a.preference - b.preference ||
        a.place.label.length - b.place.label.length ||
        a.place.label.localeCompare(b.place.label),
    );
    const result = [];
    const seenAddresses = new Set();
    const canonical = (p) =>
      normalize(p.label.split(",")[0]).replace(/^the /, "");
    for (const { place } of scores) {
      if (place.kind === "address") {
        const key = normalize(place.label);
        if (seenAddresses.has(key)) continue;
        seenAddresses.add(key);
      } else if (
        result.some(
          (other) =>
            other.kind !== "address" &&
            canonical(other) === canonical(place) &&
            Math.hypot(
              (other.coordinates[0] - place.coordinates[0]) * 88000,
              (other.coordinates[1] - place.coordinates[1]) * 111000,
            ) < 80,
        )
      )
        continue;
      result.push(place);
      if (result.length === 7) break;
    }
    return result;
  }
  return { search, addressCount: addresses.length, placeCount: named.length };
}
