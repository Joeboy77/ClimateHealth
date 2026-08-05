import mapData from "@/data/ghana-map.json";

export const GHANA_MAP = mapData as {
  viewBox: { width: number; height: number };
  projection: { scale: number; translateX: number; translateY: number };
  regions: { name: string; d: string }[];
};

export function projectPoint(
  longitude: number,
  latitude: number,
): { x: number; y: number } {
  const { scale, translateX, translateY } = GHANA_MAP.projection;
  const lambda = (longitude * Math.PI) / 180;
  const phi = (latitude * Math.PI) / 180;
  return {
    x: scale * lambda + translateX,
    y: translateY - scale * Math.log(Math.tan(Math.PI / 4 + phi / 2)),
  };
}

export function GhanaOutline({
  className,
  fill = "var(--color-raised)",
  stroke = "var(--color-border)",
  strokeWidth = 0.75,
}: {
  className?: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
}) {
  return (
    <g className={className}>
      {GHANA_MAP.regions.map((region) => (
        <path
          key={region.name}
          d={region.d}
          fill={fill}
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeLinejoin="round"
        />
      ))}
    </g>
  );
}
