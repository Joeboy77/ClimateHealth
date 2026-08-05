import { geoArea, geoBounds, geoMercator, geoPath } from "d3-geo";
import { readFileSync, writeFileSync } from "node:fs";

const VIEWBOX_WIDTH = 760;
const VIEWBOX_HEIGHT = 720;
// Ghana is projected into the left portion; the right margin is the label column.
const LAND_EXTENT = [
  [16, 16],
  [470, 704],
];

const GHANA_EXTENT = { west: -3.3, east: 1.3, south: 4.6, north: 11.3 };

/**
 * d3-geo reads polygons as spherical, so a ring wound the wrong way is read as
 * the whole globe minus the shape. Source data does not agree on winding, so
 * reverse any ring that covers more than half the sphere.
 */
function rewind(collection) {
  return {
    type: "FeatureCollection",
    features: collection.features.map((feature) => {
      const covered = geoArea(feature) > 2 * Math.PI;
      if (!covered) return feature;
      return {
        ...feature,
        geometry: {
          ...feature.geometry,
          coordinates: feature.geometry.coordinates.map((ring) =>
            [...ring].reverse(),
          ),
        },
      };
    }),
  };
}

const collection = rewind(
  JSON.parse(readFileSync("src/data/ghana-regions.json", "utf8")),
);

const [[west, south], [east, north]] = geoBounds(collection);
if (
  west < GHANA_EXTENT.west ||
  east > GHANA_EXTENT.east ||
  south < GHANA_EXTENT.south ||
  north > GHANA_EXTENT.north
) {
  console.error(
    `Geometry covers ${west.toFixed(2)},${south.toFixed(2)} to ${east.toFixed(2)},${north.toFixed(2)} — that is not Ghana. Check ring winding.`,
  );
  process.exit(1);
}

const projection = geoMercator().fitExtent(LAND_EXTENT, collection);

const toPath = geoPath(projection);
const [scale, [translateX, translateY]] = [
  projection.scale(),
  projection.translate(),
];

// Sub-pixel precision is invisible at this viewBox and triples the payload.
function roundPath(d) {
  return d.replace(/-?\d+\.\d+/g, (value) => String(Math.round(Number(value))));
}

// Rounding collapses neighbouring vertices onto each other; drop the repeats.
function dropRepeatedPoints(d) {
  return d.replace(/M([^MZ]*)/g, (_full, body) => {
    const kept = [];
    for (const point of body.split("L")) {
      if (point && point !== kept[kept.length - 1]) kept.push(point);
    }
    return `M${kept.join("L")}`;
  });
}

const regions = collection.features.map((feature) => ({
  name: feature.properties.name,
  d: dropRepeatedPoints(roundPath(toPath(feature))),
}));

// The runtime projects district coordinates without shipping d3-geo or the
// source geometry. Verify that reimplementation against d3 before emitting.
function projectPoint(longitude, latitude) {
  const lambda = (longitude * Math.PI) / 180;
  const phi = (latitude * Math.PI) / 180;
  return [
    scale * lambda + translateX,
    translateY - scale * Math.log(Math.tan(Math.PI / 4 + phi / 2)),
  ];
}

const SAMPLES = [
  [-0.1676, 5.6837],
  [-2.5057, 10.0601],
  [-0.187, 5.6037],
  [-0.8393, 9.4008],
  [-1.6244, 6.6885],
  [-1.2466, 5.1053],
  [-0.8514, 10.7856],
];

let worstDelta = 0;
for (const [longitude, latitude] of SAMPLES) {
  const [expectedX, expectedY] = projection([longitude, latitude]);
  const [actualX, actualY] = projectPoint(longitude, latitude);
  worstDelta = Math.max(
    worstDelta,
    Math.abs(expectedX - actualX),
    Math.abs(expectedY - actualY),
  );
}

if (worstDelta > 1e-6) {
  console.error(`Projection mismatch of ${worstDelta}px — refusing to emit.`);
  process.exit(1);
}

const output = {
  viewBox: { width: VIEWBOX_WIDTH, height: VIEWBOX_HEIGHT },
  landExtent: LAND_EXTENT,
  projection: { scale, translateX, translateY },
  regions,
};

writeFileSync("src/data/ghana-map.json", JSON.stringify(output));
const sizeKb = (JSON.stringify(output).length / 1024).toFixed(1);
console.log(
  `Map built: ${regions.length} regions, ${sizeKb} KB, projection verified to ${worstDelta.toExponential(1)}px`,
);
