# CoalMitra — Demo Script (judge walk)

Everything below uses the **seeded demo corpus** (15 documents across 7 CMPDI coalfields, real PyMuPDF-rendered page images, real bboxes, 13 anomalies, 19 reports). No external services or API keys are required.

> Start both servers first:
> ```bash
> cd backend  && DATABASE_URL="sqlite:///./coalmitra.db" DEMO_MODE=1 uvicorn app.main:app --port 8000
> cd frontend && npm run dev
> ```
> Open **http://localhost:5173**

---

## 1. Landing screen (first impression)

Hero: "Turning coal-field papers into decision-ready intelligence." Feature cards, seeded stats strip (documents processed, extraction accuracy, anomaly flags), subsidiary logos. All numbers are live `GET /api/health` + `/api/metrics/summary`.

## 2. Sign-in and role access

Click **Open app** and choose a demo account on the sign-in page. All demo roles use `CoalMitraDemo2026!`:
- Geologist — `geologist@coalmitra.demo`
- Ministry Official — `ministry@coalmitra.demo`
- Auditor — `auditor@coalmitra.demo`

The role shown in the topbar is assigned by the server; there is no client-side role switch. New registrations receive the Geologist role.

## 3. Role-aware dashboard

Each signed-in account loads its own `GET /api/dashboard/{role}` view:
- **Geologist** — raw data: recent documents, extraction confidence, field-level feed.
- **Ministry Official** — summaries: report count, open anomalies, ready answers.
- **Auditor** — governance: audit trail, anomaly counts, confidence distribution.

Each stat card counts up on mount; all values live.

## 4. Documents + extraction

Open **Documents**. Cards show category, coalfield, block, status, confidence. Click one →
**Document detail**: field table with confidence chips + the page viewer. Note a chip →
the **source panel slides in** from the right; the page PNG swaps to the right page; the
field's **bounding box pulses gold**, then settles into a highlight; a corner chip counts
up the extraction confidence; footer shows doc title, page, and **Open original** (serves the source PDF).

**Upload** a selectable-text PDF, image, CSV, or XLSX as a Geologist. The Documents table shows ingestion status while conversion, extraction, indexing, and report generation run. A scanned-only PDF or image requires Tesseract with English/Hindi language packs; without it the document is marked failed with an explanatory message.

For a lower-confidence field, select **Correct**, enter the reviewed value, and save. The extraction and numeric metric update, the action is added to the audit trail, and a fresh report is generated.

Document management is available to Geologists; Auditors can inspect source records read-only. Ministry Officials can open source pages through report and answer citations, but do not get raw field/emission views.

## 5. Reports — the traceability centerpiece

Open **Reports**, pick one. The narrative mixes paragraphs and data tables. The numbers are
**SourcePills** — each one is a clickable ref to the exact source line. Click any number →
same slide-in panel → page swap → gold pulse on the bbox → confidence count-up.

As a Geologist, click **Generate** in the header → a fresh report is produced (`POST /api/reports/generate`)
and appears in the list. Click **Export PDF** → downloads a reportlab-rendered PDF.

## 6. Insights

**Word cloud** (120 terms, EN + Devanagari, sized by frequency). **Topic drift** — quarterly
stacked area of 6 keyword-scored topics (Exploration / Reserves / Seam Quality / Environment / Production /
Compliance). Click a topic chip → the doc list filters to documents in that topic.

## 7. Anomalies

Consistency dashboard: severity cards (Critical/High/Medium), deviation bars vs historical
same-block filings when present (coalfield baseline otherwise), rationale text. As an Auditor, click **Ack** → the card flips to reviewed inline
(`POST /api/anomalies/{id}/ack`). Each anomaly deep-links its primary and baseline documents.

## 8. AI query — EN + HI with citations

Open **Query**. Pick or create a session. Ask in English or Hindi (the demo corpus answers
in Devanagari for Hindi prompts). Every answer carries a **confidence gauge** and citation
chips; click a citation → the source panel opens on the exact page region. The response is
styled as an "official response" (TemplateResponder — no LLM key needed).

## 9. Hindi voice query

Press the mic button, speak, and the waveform animates while recording. On stop, the pure-JS
WAV encoder ships the audio to `POST /api/chat/sessions/{id}/voice`; demo mode uses a
deterministic mock Hindi/English transcript, while real mode uses faster-whisper when installed. The answer renders with citations, and the browser
**reads it back** via `speechSynthesis` (`hi-IN` when Hindi).

## 10. Metrics

Metric tiles: report-prep reduction %, extraction accuracy %, automation %, query resolution %,
each with an upward-trending sparkline from `GET /api/metrics/trends`. Open-anomaly count and
avg response time also live here.

---

## Fail-safe / notes

- **No PostgreSQL needed for the demo**: point `DATABASE_URL` at SQLite (as above) and the
  corpus seeds identically. PostgreSQL only changes the storage engine.
- **Batteries included**: page images, bboxes, citations, anomalies are all real data seeded
  into the database — nothing is hard-coded in the UI layer.