"""Consistency / anomaly detection.

Compares a document's numeric QuantMetrics against historical baselines for
the same coalfield. Deviation % = (actual - expected) / expected.
Severity buckets: <5% LOW, 5–15% MEDIUM, 15–30% HIGH, >30% CRITICAL.
"""
from __future__ import annotations

from app.models.report import Anomaly, AnomalySeverity, AnomalyStatus


def severity_for(deviation_pct: float) -> AnomalySeverity:
    p = abs(deviation_pct)
    if p > 30:
        return AnomalySeverity.CRITICAL
    if p > 15:
        return AnomalySeverity.HIGH
    if p > 5:
        return AnomalySeverity.MEDIUM
    return AnomalySeverity.LOW


def detect(doc, quant_metrics: list, coalfield, proof_fields: dict, db,
           min_severity: AnomalySeverity = AnomalySeverity.MEDIUM) -> list[Anomaly]:
    """Run deviation analysis for a document.

    quant_metrics: list of QuantMetric (metric_key, label, value, unit, conf).
    coalfield: the document's Coalfield (has baseline_gcv, baseline_ash,
    baseline_ob_ratio, reserve_mt).
    proof_fields: {metric_key: FieldExtraction} to carry bbox/page/confidence
    (used for click-through to the source line).
    min_severity: only surface anomalies at or above this severity (LOW
    sub-threshold deviations are expected noise, not "anomalies").
    Returns list of unsaved Anomaly objects.
    """
    anomalies: list[Anomaly] = []

    baseline_map = {
        "gcv": (coalfield.baseline_gcv, "kcal/kg"),
        "ash_content": (coalfield.baseline_ash, "%"),
        "ob_ratio": (coalfield.baseline_ob_ratio, ""),
        "proved_reserve_mt": (coalfield.reserve_mt, "MT"),
    }

    for m in quant_metrics:
        baseline, unit = baseline_map.get(m.metric_key, (None, m.unit))
        if baseline is None or baseline <= 0 or m.value is None:
            continue
        deviation = ((m.value - baseline) / baseline) * 100
        sev = severity_for(deviation)
        # Sub-threshold drift (LOW) is expected variance — don't flood the QA
        # screen with noise. Only MEDIUM+ becomes a clickable anomaly.
        if sev.value < min_severity.value:
            continue

        proof = proof_fields.get(m.metric_key)
        expected = f"{baseline:,.2f}{(' ' + unit) if unit else ''}"
        actual = f"{m.value:,.2f}{(' ' + unit) if unit else ''}"

        anomalies.append(Anomaly(
            document_id=doc.id,
            coalfield_id=doc.coalfield_id,
            block_name=doc.block_name,
            metric_key=m.metric_key,
            label=m.label,
            expected_value=expected,
            actual_value=actual,
            deviation_pct=round(deviation, 2),
            severity=sev,
            status=AnomalyStatus.OPEN,
            rationale=(
                f"{m.label} for {doc.block_name or 'this block'} deviates "
                f"{deviation:+.1f}% from the {coalfield.name} baseline "
                f"({expected}). Threshold for scrutiny exceeded; verify the "
                f"source figure before publication."
            ),
            page_number=proof.page_number if proof else 1,
            bbox=proof.bbox if proof else {},
            confidence=proof.confidence if proof else 0,
            baseline_document_id="",
        ))

    return anomalies