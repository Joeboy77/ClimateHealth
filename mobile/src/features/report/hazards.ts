import type { ReportType } from "@/lib/api/types";

type Hazard = {
  readonly type: ReportType;
  readonly label: string;
  readonly help: string;
};

/**
 * What a citizen can report, in their words rather than the engine's.
 *
 * Each one maps to a signal the Signal-to-Syndrome Engine already weighs, which is what
 * makes Community Watch more than a suggestion box: a verified report of stagnant water
 * raises the district's malaria and dengue score the same way a rain gauge would.
 */
export const HAZARDS: readonly Hazard[] = [
  {
    type: "stagnant_water",
    label: "Standing water",
    help: "Pools, gutters, containers holding water",
  },
  {
    type: "flooding",
    label: "Flooding",
    help: "Water over roads, yards or homes",
  },
  {
    type: "unsafe_water",
    label: "Unsafe water",
    help: "Dirty, smelly or discoloured drinking water",
  },
  {
    type: "waste_dumping",
    label: "Waste dumping",
    help: "Rubbish piles, blocked drains, open dumping",
  },
  {
    type: "dust_haze",
    label: "Dust or smoke",
    help: "Heavy dust, burning waste, thick haze",
  },
  {
    type: "illness_cluster",
    label: "People falling ill",
    help: "Several people nearby with the same symptoms",
  },
];

export function hazardLabel(type: ReportType): string {
  return HAZARDS.find((hazard) => hazard.type === type)?.label ?? "Hazard";
}
