from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import (
    Coalfield,
    Document,
    DocCategory,
    DocStatus,
    DocumentPage,
    DocumentTopic,
    FieldExtraction,
    QuantMetric,
    Role,
    Topic,
    User,
)
from app.models.chat import AuditEvent
from app.models.report import Anomaly, AnomalySeverity, AnomalyStatus, Report
from app.routers.extraction import FieldCorrection, correct_field
from app.services.anomaly_service import severity_for
from app.services.extraction_service import extract_fields_from_pages
from app.services.ingestion import (
    _assign_topics_and_detect_anomalies,
    _populate_document_metadata,
    migrate_legacy_field_units,
)
from app.services.insight_service import infer_topic_weights
from app.services.pdf_service import PageTextResult


class PlanWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db: Session = self.session_factory()
        self.coalfield = Coalfield(
            name="Test Field", subsidiary="Test", state="Test", baseline_gcv=4000,
            baseline_ash=20, baseline_ob_ratio=2, reserve_mt=100,
        )
        self.user = User(name="Test Geologist", role=Role.GEOLOGIST, title="Geologist", subsidiary="Test")
        self.db.add_all([self.coalfield, self.user])
        self.db.add_all([
            Topic(key=key, label=key, color="#123456")
            for key in ("exploration", "seam-quality", "reserves", "production", "environment", "compliance")
        ])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_severity_order_and_content_topic_ranking(self) -> None:
        self.assertEqual(severity_for(25), AnomalySeverity.HIGH)
        self.assertEqual(severity_for(35), AnomalySeverity.CRITICAL)
        topics = infer_topic_weights("Production output and dispatch. GCV and coal quality.")
        self.assertEqual(topics[0][0], "production")
        self.assertIn("seam-quality", dict(topics))

    def test_extractor_handles_colon_labels_without_neighbor_units(self) -> None:
        text = (
            "Ash Content: 18 %\nMoisture: 9 %\nGrade: G8\n"
            "Proved Reserve: 350 Mt\nReport Date: 2025-04-10"
        )
        lines = []
        cursor = 0
        for line in text.splitlines():
            start = text.find(line, cursor)
            lines.append({"text": line, "bbox": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
                          "conf": 0.99, "char_start": start, "char_end": start + len(line)})
            cursor = start + len(line)
        page = PageTextResult(text, lines, 595, 842, 0.99)
        hits = extract_fields_from_pages([(page, 1)], {})
        values = {hit.field_key: (hit.value, hit.unit) for hit in hits}
        self.assertEqual(values["ash_content"], ("18", "%"))
        self.assertEqual(values["moisture"], ("9", "%"))
        self.assertEqual(values["grade"], ("G8", ""))
        self.assertEqual(values["proved_reserve_mt"], ("350", "MT"))
        self.assertEqual(values["report_date"], ("2025-04-10", ""))

    def test_metadata_and_live_historical_anomaly_link(self) -> None:
        prior = Document(title="Prior", category=DocCategory.PRODUCTION, coalfield=self.coalfield,
                         block_name="Block A", status=DocStatus.READY, report_date="2024-01-10")
        current = Document(title="Current", category=DocCategory.PRODUCTION, coalfield=self.coalfield,
                           status=DocStatus.READY)
        self.db.add_all([prior, current])
        self.db.flush()
        page = DocumentPage(
            document_id=current.id,
            page_number=1,
            text="Block: Block A\nDistrict: North\nCoalfield: Test Field\nReport Date: 2025-04-10",
        )
        self.db.add(page)
        self.db.flush()
        _populate_document_metadata(self.db, current, [SimpleNamespace(text=page.text)])
        self.assertEqual(current.block_name, "Block A")
        self.assertEqual(current.district, "North")
        self.assertEqual(current.coalfield_id, self.coalfield.id)
        self.assertEqual(current.report_date, "2025-04-10")

        prior_metric = QuantMetric(document_id=prior.id, metric_key="gcv", label="GCV", value=4000, unit="kcal/kg")
        current_metric = QuantMetric(document_id=current.id, metric_key="gcv", label="GCV", value=5000, unit="kcal/kg")
        field = FieldExtraction(
            document_id=current.id, page_id=page.id, page_number=1, field_key="gcv",
            field_label="GCV", value="5000", unit="kcal/kg", numeric_value=5000,
            confidence=0.7, bbox={}, matched_text="GCV 5000",
        )
        self.db.add_all([prior_metric, current_metric, field])
        self.db.commit()
        with patch("app.services.ingestion.create_report", lambda _: None):
            _assign_topics_and_detect_anomalies(self.db, current.id)
        anomaly = self.db.query(Anomaly).filter_by(document_id=current.id).one()
        self.assertEqual(anomaly.severity, AnomalySeverity.HIGH)
        self.assertEqual(anomaly.baseline_document_id, prior.id)
        self.assertGreater(self.db.query(DocumentTopic).filter_by(document_id=current.id).count(), 0)

    def test_human_correction_updates_metric_and_audit_log(self) -> None:
        doc = Document(title="Correction", category=DocCategory.GEOLOGICAL_REPORT,
                       coalfield=self.coalfield, block_name="Block B", status=DocStatus.READY)
        self.db.add(doc)
        self.db.flush()
        page = DocumentPage(document_id=doc.id, page_number=1, text="GCV 4200")
        self.db.add(page)
        self.db.flush()
        field = FieldExtraction(
            document_id=doc.id, page_id=page.id, page_number=1, field_key="gcv",
            field_label="GCV", value="4200", unit="kcal/kg", numeric_value=4200,
            confidence=0.7, bbox={}, matched_text="GCV 4200",
        )
        metric = QuantMetric(document_id=doc.id, metric_key="gcv", label="GCV", value=4200, unit="kcal/kg")
        self.db.add_all([field, metric])
        self.db.add(Anomaly(
            document_id=doc.id,
            coalfield_id=self.coalfield.id,
            block_name=doc.block_name,
            metric_key="gcv",
            label="GCV",
            expected_value="4,000 kcal/kg",
            actual_value="4,200 kcal/kg",
            deviation_pct=5,
            severity=AnomalySeverity.MEDIUM,
            status=AnomalyStatus.OPEN,
        ))
        self.db.commit()
        with patch("app.services.ingestion.create_report", lambda _: None):
            result = correct_field(doc.id, field.id, FieldCorrection(value="4300"), self.db, self.user)
        self.assertEqual(result["method"], "human")
        self.assertEqual(result["numeric_value"], 4300)
        self.assertEqual(self.db.query(QuantMetric).filter_by(document_id=doc.id).one().value, 4300)
        self.assertEqual(self.db.query(AuditEvent).filter_by(action="corrected_field").count(), 1)
        refreshed_anomaly = self.db.query(Anomaly).filter_by(document_id=doc.id, status=AnomalyStatus.OPEN).one()
        self.assertTrue(refreshed_anomaly.actual_value.startswith("4,300"))

    def test_legacy_unit_migration_updates_stored_report_refs_idempotently(self) -> None:
        doc = Document(title="Legacy", category=DocCategory.GEOLOGICAL_REPORT,
                       coalfield=self.coalfield, block_name="Block C", status=DocStatus.READY)
        self.db.add(doc)
        self.db.flush()
        page = DocumentPage(document_id=doc.id, page_number=1, text="Grade: G8")
        self.db.add(page)
        self.db.flush()
        field = FieldExtraction(
            document_id=doc.id, page_id=page.id, page_number=1, field_key="grade",
            field_label="Grade", value="G8", unit="MT", numeric_value=None,
            confidence=0.9, bbox={}, matched_text="Grade: G8",
        )
        metric = QuantMetric(document_id=doc.id, metric_key="ob_ratio", label="OB ratio",
                             value=5.9, unit="MT")
        baseline = Document(title="Baseline", category=DocCategory.GEOLOGICAL_REPORT,
                            coalfield=self.coalfield, block_name="Other Block", status=DocStatus.READY)
        self.db.add(baseline)
        self.db.flush()
        self.db.add(QuantMetric(document_id=baseline.id, metric_key="gcv", label="GCV",
                                value=4000, unit="kcal/kg"))
        anomaly = Anomaly(
            document_id=doc.id, coalfield_id=self.coalfield.id, block_name=doc.block_name,
            metric_key="gcv", label="GCV", expected_value="4,000 kcal/kg",
            actual_value="4,200 kcal/kg", deviation_pct=5, severity=AnomalySeverity.MEDIUM,
            status=AnomalyStatus.OPEN, baseline_document_id="",
        )
        report = Report(
            document_id=doc.id,
            title="Legacy report",
            sections=[{"kind": "table", "refs": [{"value": "G8", "display": "G8 MT", "page": 1}]}],
            pdf_path="old-report.pdf",
        )
        self.db.add_all([field, metric, anomaly, report])
        self.db.commit()

        self.assertGreater(migrate_legacy_field_units(self.db), 0)
        self.assertEqual(field.unit, "")
        self.assertEqual(metric.unit, ":1")
        self.assertEqual(report.sections[0]["refs"][0]["display"], "G8")
        self.assertEqual(report.pdf_path, "")
        self.assertEqual(anomaly.baseline_document_id, baseline.id)
        self.assertEqual(migrate_legacy_field_units(self.db), 0)


if __name__ == "__main__":
    unittest.main()