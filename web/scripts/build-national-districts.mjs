import { geoArea, geoBounds, geoCentroid, geoContains } from "d3-geo";
import { readFileSync, writeFileSync } from "node:fs";

const ADM1 = "/tmp/gha.geojson";
const ADM2 = "/tmp/gha-adm2.geojson";
const BACKEND_OUT = "../backend/climahealth/infrastructure/seed/data/districts.json";

/**
 * The African meningitis belt covers Ghana's five northern regions. Membership is
 * a property of the region, not something to infer from a latitude cut-off that
 * would slice districts in half.
 */
const MENINGITIS_BELT_REGIONS = new Set([
  "Upper East",
  "Upper West",
  "Northern",
  "North East",
  "Savannah",
]);

function rewind(feature) {
  if (geoArea(feature) <= 2 * Math.PI) return feature;
  const flip = (rings) => rings.map((ring) => [...ring].reverse());
  return {
    ...feature,
    geometry: {
      ...feature.geometry,
      coordinates:
        feature.geometry.type === "MultiPolygon"
          ? feature.geometry.coordinates.map(flip)
          : flip(feature.geometry.coordinates),
    },
  };
}

/**
 * Short, stable ids for the districts the demo and seeded data already reference.
 * Names stay official; only the internal identifier is shortened.
 */
const PREFERRED_IDS = new Map([
  ["La-nkwantanang-madina", "madina"],
  ["Wa Municipal", "wa"],
  ["Accra Metropolis", "accra-metropolitan"],
  ["Tamale Metropolitan", "tamale"],
  ["Kumasi Metropolitan", "kumasi"],
  ["Cape Coast Metropolitan", "cape-coast"],
  ["Bolgatanga Municipal", "bolgatanga"],
]);

function slugify(name) {
  return name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

const regions = JSON.parse(readFileSync(ADM1, "utf8")).features.map((feature) => ({
  name: feature.properties.name ?? feature.properties.shapeName.replace(" Region", ""),
  feature: rewind(feature),
}));

const districts = JSON.parse(readFileSync(ADM2, "utf8")).features.map(rewind);

const seeded = [];
const unassigned = [];
const usedIds = new Set();

for (const feature of districts) {
  const name = feature.properties.shapeName.trim();
  const centroid = geoCentroid(feature);
  const [longitude, latitude] = centroid;

  let region = regions.find((candidate) =>
    geoContains(candidate.feature, centroid),
  )?.name;

  // A centroid can fall just outside its own polygon on concave shapes; fall back
  // to the region whose bounding box contains it and whose centre is nearest.
  if (!region) {
    const nearest = regions
      .map((candidate) => {
        const [[west, south], [east, north]] = geoBounds(candidate.feature);
        const inside =
          longitude >= west &&
          longitude <= east &&
          latitude >= south &&
          latitude <= north;
        const [centreLon, centreLat] = geoCentroid(candidate.feature);
        return {
          name: candidate.name,
          inside,
          distance: Math.hypot(centreLon - longitude, centreLat - latitude),
        };
      })
      .filter((candidate) => candidate.inside)
      .sort((first, second) => first.distance - second.distance)[0];
    region = nearest?.name;
    if (region) unassigned.push(`${name} -> ${region} (bbox fallback)`);
  }

  if (!region) {
    console.error(`Could not place "${name}" in any region.`);
    process.exit(1);
  }

  let districtId = PREFERRED_IDS.get(name) ?? slugify(name);
  if (usedIds.has(districtId)) districtId = `${districtId}-${slugify(region)}`;
  usedIds.add(districtId);

  seeded.push({
    district_id: districtId,
    name,
    region,
    latitude: Number(latitude.toFixed(4)),
    longitude: Number(longitude.toFixed(4)),
    in_meningitis_belt: MENINGITIS_BELT_REGIONS.has(region),
    shape_name: name,
  });
}

seeded.sort((first, second) =>
  first.region.localeCompare(second.region) || first.name.localeCompare(second.name),
);

writeFileSync(BACKEND_OUT, `${JSON.stringify(seeded, null, 1)}\n`);

const byRegion = new Map();
for (const district of seeded) {
  byRegion.set(district.region, (byRegion.get(district.region) ?? 0) + 1);
}

console.log(`Seeded ${seeded.length} districts across ${byRegion.size} regions.`);
for (const [region, count] of [...byRegion].sort()) {
  const belt = MENINGITIS_BELT_REGIONS.has(region) ? " (meningitis belt)" : "";
  console.log(`  ${region.padEnd(16)} ${String(count).padStart(3)}${belt}`);
}
if (unassigned.length > 0) {
  console.log(`\n${unassigned.length} placed by bounding-box fallback:`);
  for (const entry of unassigned) console.log(`  ${entry}`);
}
