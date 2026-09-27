"""Bounding-box helpers. All bboxes are normalized 0..1 (fraction of page w/h)."""


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def normalize(x0: float, y0: float, x1: float, y1: float, pw: float, ph: float) -> dict:
    """Convert pixel coords to normalized 0..1 box."""
    if pw <= 0 or ph <= 0:
        return {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
    return {
        "x0": clamp(x0 / pw),
        "y0": clamp(y0 / ph),
        "x1": clamp(x1 / pw),
        "y1": clamp(y1 / ph),
    }


def denormalize(bbox: dict, pw: float, ph: float) -> dict:
    """Convert normalized box back to pixels for overlay rendering."""
    return {
        "x": bbox.get("x0", 0) * pw,
        "y": bbox.get("y0", 0) * ph,
        "w": (bbox.get("x1", 1) - bbox.get("x0", 0)) * pw,
        "h": (bbox.get("y1", 1) - bbox.get("y0", 0)) * ph,
    }


def point_in_box(px: float, py: float, bbox: dict) -> bool:
    return (
        bbox.get("x0", 0) <= px <= bbox.get("x1", 1)
        and bbox.get("y0", 0) <= py <= bbox.get("y1", 1)
    )


def bbox_overlap(a: dict, b: dict) -> float:
    """Intersection over union of two normalized boxes."""
    ix = max(0.0, min(a.get("x1", 1), b.get("x1", 1)) - max(a.get("x0", 0), b.get("x0", 0)))
    iy = max(0.0, min(a.get("y1", 1), b.get("y1", 1)) - max(a.get("y0", 0), b.get("y0", 0)))
    inter = ix * iy
    area_a = (a.get("x1", 1) - a.get("x0", 0)) * (a.get("y1", 1) - a.get("y0", 0))
    area_b = (b.get("x1", 1) - b.get("x0", 0)) * (b.get("y1", 1) - b.get("y0", 0))
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0


def merge_boxes(boxes: list[dict]) -> dict:
    """Union of many normalized boxes."""
    if not boxes:
        return {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
    return {
        "x0": min(b.get("x0", 1) for b in boxes),
        "y0": min(b.get("y0", 1) for b in boxes),
        "x1": max(b.get("x1", 0) for b in boxes),
        "y1": max(b.get("y1", 0) for b in boxes),
    }