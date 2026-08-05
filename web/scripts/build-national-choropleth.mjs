import { geoArea, geoBounds, geoMercator, geoPath } from "d3-geo";
import { readFileSync, writeFileSync } from "node:fs";

const VIEWBOX = { width: 620, height: 720 };
const EXTENT = [
  [14, 14],
  [606, 706],
];
const OUTPUT = "public/ghana-choropleth.json";

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

function tidy(d) {
  const rounded = d.replace(/-?\d+\.\d+/g, (v) => String(Math.round(Number(v))));
  return rounded.replace(/M([^MZ]*)/g, (_f, body) => {
    const kept = [];
    for (const point of body.split("L")) {
      if (point && point !== kept[kept.length - 1]) kept.push(point);
    }
    return `M${kept.join("L")}`;
  });
}

const seeded = JSON.parse(
  readFileSync("../backend/climahealth/infrastructure/seed/data/districts.json", "utf8"),
);
const idByShape = new Map(seeded.map((d) => [d.shape_name, d.district_id]));

const adm2 = JSON.parse(readFileSync("/tmp/gha-adm2.geojson", "utf8")).features.map(rewind);
const adm1 = JSON.parse(readFileSync("/tmp/gha.geojson", "utf8")).features.map(rewind);

const all = { type: "FeatureCollection", features: adm2 };
const [[west, south], [east, north]] = geoBounds(all);
if (west < -3.3 || east > 1.3 || south < 4.6 || north > 11.3) {
  console.error("Geometry is not Ghana — check winding.");
  process.exit(1);
}

const projection = geoMercator().fitExtent(EXTENT, all);
const toPath = geoPath(projection);

const districts = [];
for (const feature of adm2) {
  const districtId = idByShape.get(feature.properties.shapeName.trim());
  if (!districtId) {
    console.error(`No seeded district for shape "${feature.properties.shapeName}"`);
    process.exit(1);
  }
  districts.push({ id: districtId, d: tidy(toPath(feature)) });
}

const output = {
  viewBox: VIEWBOX,
  projection: {
    scale: projection.scale(),
    translateX: projection.translate()[0],
    translateY: projection.translate()[1],
  },
  districts,
  regions: adm1.map((f) => ({
    name: (f.properties.name ?? f.properties.shapeName).replace(" Region", ""),
    d: tidy(toPath(f)),
  })),
};

writeFileSync(OUTPUT, JSON.stringify(output));
console.log(
  `Choropleth built: ${districts.length} districts + ${output.regions.length} regions, ${(JSON.stringify(output).length / 1024).toFixed(0)} KB`,
);
