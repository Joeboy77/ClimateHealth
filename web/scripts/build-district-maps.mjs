import { geoArea, geoBounds, geoMercator, geoPath } from "d3-geo";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const SOURCE = "/tmp/gha-adm2.geojson";
const OUTPUT_DIR = "public/district-maps";

const VIEWBOX = { width: 460, height: 400 };
const EXTENT = [
  [24, 24],
  [436, 376],
];

/** Every seeded district, keyed by id, read from the backend's own data file. */
const SEEDED = JSON.parse(
  readFileSync("../backend/climahealth/infrastructure/seed/data/districts.json", "utf8"),
);
const SHAPE_BY_DISTRICT = Object.fromEntries(
  SEEDED.map((district) => [district.district_id, district.shape_name]),
);

/** d3-geo reads rings spherically; a ring wound the wrong way becomes the globe. */
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

function tidyPath(d) {
  const rounded = d.replace(/-?\d+\.\d+/g, (value) =>
    String(Math.round(Number(value) * 10) / 10),
  );
  return rounded.replace(/M([^MZ]*)/g, (_full, body) => {
    const kept = [];
    for (const point of body.split("L")) {
      if (point && point !== kept[kept.length - 1]) kept.push(point);
    }
    return `M${kept.join("L")}`;
  });
}

const source = JSON.parse(readFileSync(SOURCE, "utf8"));
const byName = new Map(
  source.features.map((feature) => [feature.properties.shapeName, feature]),
);

const districts = {};

for (const [districtId, shapeName] of Object.entries(SHAPE_BY_DISTRICT)) {
  const raw = byName.get(shapeName);
  if (!raw) {
    console.error(`No ADM2 shape named "${shapeName}" for district "${districtId}".`);
    process.exit(1);
  }

  const feature = rewind(raw);
  const [[west, south], [east, north]] = geoBounds(feature);
  const spanDegrees = Math.max(east - west, north - south);
  if (spanDegrees > 3) {
    console.error(
      `"${shapeName}" spans ${spanDegrees.toFixed(2)}° — too large for a district. Check winding.`,
    );
    process.exit(1);
  }

  const projection = geoMercator().fitExtent(EXTENT, feature);
  const scale = projection.scale();
  const [translateX, translateY] = projection.translate();

  const project = (longitude, latitude) => [
    scale * ((longitude * Math.PI) / 180) + translateX,
    translateY -
      scale * Math.log(Math.tan(Math.PI / 4 + (latitude * Math.PI) / 360)),
  ];

  const [expectedX, expectedY] = projection([
    (west + east) / 2,
    (south + north) / 2,
  ]);
  const [actualX, actualY] = project((west + east) / 2, (south + north) / 2);
  if (
    Math.abs(expectedX - actualX) > 1e-6 ||
    Math.abs(expectedY - actualY) > 1e-6
  ) {
    console.error(`Projection mismatch for "${districtId}" — refusing to emit.`);
    process.exit(1);
  }

  districts[districtId] = {
    shapeName,
    viewBox: VIEWBOX,
    projection: { scale, translateX, translateY },
    bounds: { west, south, east, north },
    d: tidyPath(geoPath(projection)(feature)),
  };
}

mkdirSync(OUTPUT_DIR, { recursive: true });
let totalBytes = 0;
let largest = { id: "", kb: 0 };
for (const [districtId, entry] of Object.entries(districts)) {
  const body = JSON.stringify(entry);
  totalBytes += body.length;
  const kb = body.length / 1024;
  if (kb > largest.kb) largest = { id: districtId, kb };
  writeFileSync(`${OUTPUT_DIR}/${districtId}.json`, body);
}

console.log(
  `District maps built: ${Object.keys(districts).length} files, ${(totalBytes / 1024).toFixed(0)} KB total, largest ${largest.id} at ${largest.kb.toFixed(1)} KB`,
);
