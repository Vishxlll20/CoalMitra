# CoalMitra — Demo Script (judge walk)

Everything below uses the **seeded demo corpus** (15 documents across 7 CMPDI coalfields, real PyMuPDF-rendered page images, real bboxes, 13 anomalies, 15 auto-reports). No external services or API keys are required.

> Start both servers first:
> ```bash
> cd backend  && DATABASE_URL="sqlite:///./coalmitra.db" DEMO_MODE=1 uvicorn app.main:app --port 8000
> cd frontend && npm run dev
> ```
> Open **http://localhost:5173**

---

## 1. Landing screen (first impression)

Hero: "Turning coal-field papers into decision-ready intelligence." Feature cards, seeded stats strip (documents processed, extraction accuracy, anomaly flags), subsidiary logos. All numbers are live `GET /api/health` + `/api/metrics/summary`.

## 2. Role-aware dashboard

Switch role from the topbar (**Geologist / Ministry Official / Auditor**). Each tab loads `GET /api/dashboard/{role}`:
- **Geologist** — raw data: recent documents, extraction confidence, field-level feed.
- **Ministry Official** — summaries: report count, open anomalies, ready answers.
- **Auditor** — governance: audit trail, anomaly counts, confidence distribution.

Each stat card counts up on mount; all values live.

## 3. Documents + extraction

Open **Documents**. Cards show category, coalfield, block, status, confidence. Click one →
**Document detail**: field table with confidence chips + the page viewer. Note a chip →
the **source panel slides in** from the right; the page PNG swaps to the right page; the
field's **bounding box pulses gold**, then settles into a highlight; a corner chip counts
up the extraction confidence; footer shows doc title, page, and **Open original** (serves the source PDF).

**Upload** a PDF (even a non-PDF file works in demo mode): the stepper animates
Upload → OCR → Extract → Index → Ready on the seeded deterministic progress; the new
doc appears in the list.

## 4. Reports — the traceability centerpiece

Open **Reports**, pick one. The narrative mixes paragraphs and data tables. The numbers are
**SourcePills** — each one is a clickable ref to the exact source line. Click any number →
same slide-in panel → page swap → gold pulse on the bbox → confidence count-up.

Click **Generate** in the header → a fresh report is produced (`POST /api/reports/generate`)
and appears in the list. Click **Export PDF** → downloads a reportlab-rendered PDF.

## 5. Insights

**Word cloud** (120 terms, EN + Devanagari, sized by frequency). **Topic drift** — quarterly
stacked area of 6 topics (Exploration / Reserves / Seam Quality / Environment / Production /
Compliance). Click a topic chip → the doc list filters to documents in that topic.

## 6. Anomalies

Consistency dashboard: severity cards (Critical/High/Medium), deviation bars vs coalfield
baseline, rationale text. Click **Review** → ack → the card flips to reviewed inline
(`POST /api/anomalies/{id}/ack`). Each anomaly deep-links its primary and baseline documents.

## 7. AI query — EN + HI with citations

Open **Query**. Pick or create a session. Ask in English or Hindi (the demo corpus answers
in Devanagari for Hindi prompts). Every answer carries a **confidence gauge** and citation
chips; click a citation → the source panel opens on the exact page region. The response is
styled as an "official response" (TemplateResponder — no LLM key needed).

## 8. Hindi voice query

Press the mic button, speak, and the waveform animates while recording. On stop, the pure-JS
WAV encoder ships the audio to `POST /api/chat/sessions/{id}/voice`; demo mode plays back a
deterministic Hindi/English transcript; the answer renders with citations, and the browser
**reads it back** via `speechSynthesis` (`hi-IN` when Hindi).

## 9. Metrics

Metric tiles: report-prep reduction %, extraction accuracy %, automation %, query resolution %,
each with an upward-trending sparkline from `GET /api/metrics/trends`. Open-anomaly count and
avg response time also live here.

---

## Fail-safe / notes

- **No PostgreSQL needed for the demo**: point `DATABASE_URL` at SQLite (as above) and the
  corpus seeds identically. PostgreSQL only changes the storage engine.
- **Batteries included**: page images, bboxes, citations, anomalies are all real data seeded
  into the database — nothing is hard-coded in the UI layer.