import { useEffect, useState } from "react";

interface PageDims {
  width: number;
  height: number;
}

/**
 * Loads a rendered page PNG from the backend.
 * Backend serves at /static/pages/{docId}/{page}.png
 * Returns the HTMLImageElement + intrinsic dimensions so bbox overlays
 * can be drawn at exact normalized 0–1 scale.
 */
export function usePageImage(documentId: string | undefined, pageNumber: number) {
  const [img, setImg] = useState<HTMLImageElement | null>(null);
  const [dims, setDims] = useState<PageDims>({ width: 595, height: 842 }); // A4 default
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!documentId) return;
    let alive = true;

    setLoading(true);
    setImg(null);

    const im = new Image();
    im.crossOrigin = "anonymous";
    im.onload = () => {
      if (!alive) return;
      setImg(im);
      setDims({ width: im.naturalWidth, height: im.naturalHeight });
      setLoading(false);
    };
    im.onerror = () => {
      if (alive) setLoading(false);
    };
    im.src = `/static/pages/${documentId}/${pageNumber}.png`;

    return () => { alive = false; };
  }, [documentId, pageNumber]);

  return { img, dims, loading };
}