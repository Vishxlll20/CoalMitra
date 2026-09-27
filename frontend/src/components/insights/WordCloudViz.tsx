import { useMemo } from "react";
import type { WordStat } from "../../types";

/**
 * Custom SVG word cloud — no react-wordcloud dependency (incompatible with React 19).
 * Generates a pseudo-random scatter layout seeded on word frequency.
 * Gold palette — words grow bigger and bolder with higher count.
 */

const PALETTE = [
  "#E8A33D", "#B7791F", "#0B1B2B", "#1a3a5c",
  "#5E9EDB", "#8B5CF6", "#46A758", "#6D6A5C",
];

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

export function WordCloudViz({ words, maxWords = 60 }: { words: WordStat[]; maxWords?: number }) {
  const layout = useMemo(() => {
    const top = words
      .slice()
      .sort((a, b) => b.count - a.count)
      .slice(0, maxWords);

    if (top.length === 0) return [];

    const maxCount = top[0].count;
    const minCount = top[top.length - 1].count;
    const rng = seededRandom(42);

    return top.map((w, i) => {
      const t = maxCount > minCount ? (w.count - minCount) / (maxCount - minCount) : 0.5;
      // Font size: 11px (small) → 32px (large)
      const fontSize = 11 + t * 21;
      // Opacity: 0.45 → 1.0
      const opacity = 0.45 + t * 0.55;
      // Pseudo-random position in a cloud-ish area
      const angle = rng() * Math.PI * 2;
      const radius = rng() * 0.42 + 0.08;
      const cx = 50 + Math.cos(angle) * radius * 100;
      const cy = 50 + Math.sin(angle) * radius * 80;
      // Slight rotation for organic feel
      const rotate = (rng() - 0.5) * 8 * t;
      const color = PALETTE[i % PALETTE.length];
      return { ...w, fontSize, opacity, cx, cy, rotate, color };
    });
  }, [words, maxWords]);

  if (layout.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-[13px] text-ink/40">
        No word data available
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-[4/3]">
      <svg viewBox="0 0 100 100" className="h-full w-full" preserveAspectRatio="xMidYMid meet">
        {layout.map((w) => (
          <text
            key={w.word}
            x={`${w.cx}%`}
            y={`${w.cy}%`}
            textAnchor="middle"
            dominantBaseline="central"
            fill={w.color}
            opacity={w.opacity}
            fontSize={w.fontSize * 0.36} // scale down from px to viewBox units
            fontWeight={w.fontSize > 22 ? 700 : w.fontSize > 16 ? 600 : 500}
            fontFamily="Inter Variable, Inter, sans-serif"
            transform={`rotate(${w.rotate} ${w.cx} ${w.cy})`}
            className="transition-opacity duration-200 hover:opacity-100"
          >
            {w.word}
          </text>
        ))}
      </svg>
    </div>
  );
}