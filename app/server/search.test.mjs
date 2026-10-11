import test from "node:test";
import assert from "node:assert/strict";
import { createSearch, inCity } from "./search.mjs";

const addresses = [
  {
    eas_address_id: "1",
    address: "1 DR CARLTON B GOODLETT PL",
    longitude: -122.4193,
    latitude: 37.7793,
    complete_landmark_name: "San Francisco City Hall",
    landmark_aliases: "Civic Center City Hall",
  },
  {
    eas_address_id: "2",
    address: "100 VAN NESS AVE",
    longitude: -122.4195,
    latitude: 37.7767,
  },
  {
    eas_address_id: "3",
    address: "100 VAN NESS AVE",
    longitude: -122.4195,
    latitude: 37.7767,
  },
  {
    eas_address_id: "4",
    address: "1100 VAN NESS AVE",
    longitude: -122.42,
    latitude: 37.78,
  },
];
const places = [
  {
    id: "osm:1",
    label: "City Hall",
    coordinates: [-122.4194, 37.7792],
    kind: "place",
    aliases: [],
  },
  {
    id: "osm:2",
    label: "Café Réveille",
    coordinates: [-122.42, 37.77],
    kind: "place",
    address: "610 Long Bridge Street",
    aliases: [],
  },
  {
    id: "osm:3",
    label: "Blue Bottle Coffee",
    coordinates: [-122.4, 37.78],
    kind: "place",
    address: "1 Market Street",
    aliases: [],
  },
  {
    id: "osm:4",
    label: "Blue Bottle Coffee",
    coordinates: [-122.43, 37.76],
    kind: "place",
    address: "2 Valencia Street",
    aliases: [],
  },
  {
    id: "osm:5",
    label: "Mission Dolores Park",
    coordinates: [-122.426, 37.759],
    kind: "place",
    aliases: ["Dolores Park"],
  },
  {
    id: "outside",
    label: "Outside SF",
    coordinates: [-122.2, 37.8],
    kind: "place",
  },
];
const { search } = createSearch(addresses, places);

test("numbered addresses retain exact priority, street abbreviations and deduplication", () => {
  const matches = search("100 Van Ness Avenue, San Francisco, CA 94102");
  assert.equal(matches[0].id, "address:2");
  assert.equal(matches.filter((p) => p.label === "100 VAN NESS AVE").length, 1);
});
test("landmark names return named destinations with their street address", () => {
  const matches = search("city hall");
  assert.equal(matches.length, 1);
  assert.equal(matches[0].kind, "landmark");
  assert.equal(matches[0].address, "1 DR CARLTON B GOODLETT PL");
});
test("partial names, aliases and accent-insensitive queries work", () => {
  assert.equal(search("cafe reve")[0].id, "osm:2");
  assert.equal(search("dolores park")[0].id, "osm:5");
  assert.equal(search("civic center")[0].kind, "landmark");
});
test("separate branches are retained and may be narrowed by street", () => {
  assert.equal(search("blue bottle").length, 2);
  assert.equal(search("blue bottle valencia")[0].id, "osm:4");
});
test("queries do not alter source casing or disclose index fields", () => {
  const place = search("CAFE REVEILLE")[0];
  assert.equal(place.label, "Café Réveille");
  assert.equal("key" in place, false);
  assert.equal("names" in place, false);
  assert.equal("aliases" in place, false);
});
test("empty queries and locations outside the supported bounds are excluded", () => {
  assert.deepEqual(search(""), []);
  assert.deepEqual(search("sf"), []);
  assert.deepEqual(search("outside"), []);
  assert.equal(inCity([NaN, 37.77]), false);
});
test("autocomplete results are bounded", () => {
  const many = Array.from({ length: 20 }, (_, i) => ({
    ...places[1],
    id: `test:${i}`,
    label: `Cafe ${i}`,
  }));
  assert.equal(createSearch([], many).search("cafe").length, 7);
});
