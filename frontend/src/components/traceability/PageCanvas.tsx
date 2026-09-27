import { BboxOverlay } from "./BboxOverlay";
import { usePageImage } from "./usePageImage";
import { Skeleton } from "../shared/LoadingSkeleton";

/**
 * Renders a page PNG with a normalized bbox overlay.
 * Container adapts; the page scales within it maintaining aspect ratio.
 */
export function PageCanvas({
  documentId,
  pageNumber,
  bbox,
  className,
}: {
  documentId: string;
  pageNumber: number;
  bbox?: { x0: number; y0: number; x1: number; y1: number };
  className?: string;
}) {
  const { img, dims, loading } = usePageImage(documentId, pageNumber);

  return (
    <div className={`relative overflow-hidden rounded-md bg-slate-100 ${className ?? ""}`}>
      {loading && (
        <div className="flex items-center justify-center aspect-[595/842]">
          <Skeleton className="h-16 w-16 rounded-xl" />
        </div>
      )}
      {img && (
        <div className="relative">
          {/* The page image scales naturally in the container via width 100% */}
          <img
            src={img.src}
            alt={`Page ${pageNumber}`}
            className="block w-full rounded-md"
            style={{ display: loading ? "none" : "block" }}
            onLoad={() => {}}
          />
          {/* Overlay sits on top at the same scale */}
          {bbox && (
            <BboxOverlay bbox={bbox} pageW={dims.width} pageH={dims.height} />
          )}
        </div>
      )}
      {!loading && !img && (
        <div className="flex aspect-[595/842] items-center justify-center text-[12px] text-ink/40">
          Page preview unavailable
        </div>
      )}
    </div>
  );
}