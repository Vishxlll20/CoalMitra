import { motion } from "framer-motion";
import type { BBox } from "../../types";

/**
 * Draws a normalized bbox over a rendered page. On mount it does the
 * 2× gold "flash" pulse then settles into a soft amber highlight.
 */
export function BboxOverlay({ bbox, pageW, pageH }: { bbox: BBox; pageW: number; pageH: number }) {
  const x = bbox.x0 * pageW;
  const y = bbox.y0 * pageH;
  const w = Math.max((bbox.x1 - bbox.x0) * pageW, 14);
  const h = Math.max((bbox.y1 - bbox.y0) * pageH, 14);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.25 }}
      className="pointer-events-none absolute z-20 animate-flash rounded-[3px] border-2 border-gold-500 bg-gold-400/25"
      style={{
        left: x - 3,
        top: y - 3,
        width: w + 6,
        height: h + 6,
        boxShadow: "0 0 0 1px rgba(255,255,255,0.55) inset",
      }}
    />
  );
}