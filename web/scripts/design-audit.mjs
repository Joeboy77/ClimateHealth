import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join } from "node:path";

const SOURCE_ROOT = "src";
const SOURCE_EXTENSIONS = new Set([".ts", ".tsx", ".css"]);

const BANNED_PATTERNS = [
  {
    name: "emoji used as an icon",
    pattern: /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u,
    remedy: "Use a lucide-react icon instead.",
  },
  {
    name: "gradient",
    pattern: /gradient-to-|bg-gradient|linear-gradient/,
    remedy: "Use a flat token colour with semantic meaning.",
  },
  {
    name: "glassmorphism",
    pattern: /backdrop-blur|backdrop-filter/,
    remedy: "Use a solid surface with a one-pixel border.",
  },
  {
    name: "oversized radius",
    pattern: /rounded-(2xl|3xl)\b/,
    remedy: "Use --radius-sm, --radius-md or --radius-lg.",
  },
  {
    name: "default heavy shadow",
    pattern: /shadow-(lg|xl|2xl)\b/,
    remedy: "Use --shadow-1, --shadow-2 or --shadow-3.",
  },
  {
    name: "raw Tailwind palette",
    pattern:
      /\b(?:bg|text|border|ring|fill|stroke)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b/,
    remedy: "Use a project token from globals.css.",
  },
  {
    name: "placeholder copy",
    pattern: /Welcome back|Lorem ipsum|Your dashboard|placeholder text/i,
    remedy: "Write real domain copy.",
  },
];

function sourceFiles(directory) {
  return readdirSync(directory).flatMap((entry) => {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) return sourceFiles(path);
    return SOURCE_EXTENSIONS.has(extname(path)) ? [path] : [];
  });
}

const violations = [];

for (const file of sourceFiles(SOURCE_ROOT)) {
  const lines = readFileSync(file, "utf8").split("\n");
  lines.forEach((line, index) => {
    for (const { name, pattern, remedy } of BANNED_PATTERNS) {
      if (pattern.test(line)) {
        violations.push({ file, line: index + 1, name, remedy });
      }
    }
  });
}

if (violations.length > 0) {
  console.error(`Design audit failed — ${violations.length} violation(s):\n`);
  for (const { file, line, name, remedy } of violations) {
    console.error(`  ${file}:${line}  ${name}\n    ${remedy}`);
  }
  process.exit(1);
}

console.log("Design audit passed — no banned patterns found.");
