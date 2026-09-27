# CoalMitra

An AI-powered document intelligence platform for CMPDI/CIL — turning scanned geological & mining documents into auto-generated reports, topic/word-cloud insights, and a cited AI query system with Hindi voice support.

Built for CMPDI/CIL geological and mining-report workflows. Demo mode has been smoke-tested end-to-end against the seeded SQLite corpus.

## What's inside

- **Traceability centerpiece**: extracted fields and numeric report-table values link to source pages; chat citations and anomalies open the cited source region; generated PDFs are downloadable.
- Role-aware dashboards (**Geologist / Ministry Official / Auditor**), live landing KPIs and metrics with trends, bilingual word frequencies, keyword-weighted topic drift with clickable document filters, historical anomaly comparisons, AI query with citations in EN + HI, and browser TTS read-back.
- **Authentication and RBAC**: HTTP-only, revocable sessions; new registrations receive the Geologist role; server-side route and action checks; role-specific navigation and dashboards.
- **Document ingestion**: PDF, common image formats, CSV, and XLSX inputs normalize into searchable PDFs; selectable text is extracted directly, while scanned pages use Tesseract OCR when installed. Processing status and errors are shown on the Documents page.
- **Demo-first pipeline**: `DEMO_MODE=1` (default) starts from a deterministic seeded corpus without Chroma, Whisper, or API keys. Scanned uploads still require the Tesseract system binary and English/Hindi language data.

## Quickstart (demo, no PostgreSQL required)

```bash
# 1) Backend (SQLite fallback — seeds the full demo corpus automatically at startup)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL="sqlite:///./coalmitra.db" DEMO_MODE=1 uvicorn app.main:app --port 8000

# 2) Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

The app boots to a **landing screen**; the corpus (15 docs, 195 fields, 13 anomalies, 19 reports, 120 word entries across 6 topics) seeds on first startup. Landing KPIs load from the public health and aggregate-metrics endpoints. Storage paths resolve relative to `backend/`, independent of the shell's current directory. Follow the walkthrough in `DEMO_SCRIPT.md`.

Open **http://localhost:5173**, choose **Open app**, and sign in. Demo mode offers persona shortcuts on the sign-in page; all three demo accounts use the password `CoalMitraDemo2026!`:

| Role | Demo email |
|---|---|
| Geologist | `geologist@coalmitra.demo` |
| Ministry Official | `ministry@coalmitra.demo` |
| Auditor | `auditor@coalmitra.demo` |

New sign-ups are Geologists and cannot select or elevate their own role. In non-demo deployments, provision Ministry Official and Auditor roles through trusted database administration. For HTTPS deployments set `AUTH_COOKIE_SECURE=1`; local HTTP development defaults to a non-Secure cookie.

### Role permissions

- **Geologist**: dashboard, documents, extraction data, reports, insights, anomalies, and AI query; may upload documents and generate reports.
- **Ministry Official**: summary dashboard, ready reports, insights, metrics, and cited AI queries. Source-page click-through remains available, but raw field/emission data and document management are restricted.
- **Auditor**: read-only document/source and report review, insights, metrics, and anomaly review; may acknowledge anomalies. Chat/query access is restricted.

The backend enforces these permissions in addition to hiding unavailable navigation and actions. The dashboard endpoint uses the signed-in account's assigned role rather than trusting a role supplied by the client. Chat sessions created after sign-in are private to their owner; seeded sample conversations are available as starter history.

## PostgreSQL (optional, closer to production)

```bash
# Once — unlock the postgres superuser and create the app role+db
bash backend/scripts/init_db.sh

# Then run the backend against Postgres (seeds identically)
cd backend
DATABASE_URL="postgresql+psycopg2://coalmitra:coalmitra@localhost:5432/coalmitra" DEMO_MODE=1 uvicorn app.main:app --port 8000
```

> If `sudo` needs a password on your box, the manual equivalent:
> `sudo -u postgres psql -c "CREATE ROLE coalmitra LOGIN PASSWORD 'coalmitra'; CREATE DATABASE coalmitra OWNER coalmitra;"`
> The app connects via TCP (`localhost:5432`) with md5 password auth — it never touches the `postgres` superuser.

## Modes

- **`DEMO_MODE=1`** (default): seeded corpus uses pre-rendered page images, bboxes, fields, reports, and keyword retrieval. Uploaded digital PDFs, images, CSVs, and XLSX files use the real extraction/conversion path. Voice input records real audio but uses a deterministic mock transcript.
- **`DEMO_MODE=0`**: enables Chroma/fastembed retrieval and faster-whisper ASR when optional dependencies are installed. OpenAI credentials enable LLM answers; extraction remains rule-based and source-snapped, not schema-constrained LLM extraction. Model downloads and hardware affect first-run latency.

### Scanned-document OCR

Install Tesseract plus English and Hindi language data before uploading image-only PDFs or scans. On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
```

If Tesseract or either language pack is missing, ingestion reports a clear `FAILED` status instead of marking a blank scan as ready. PDF, PNG/JPEG/TIFF/BMP, CSV, and XLSX are supported; spreadsheet pages are rendered to a text-bearing PDF before field extraction.

## Plan Coverage

- **Ingestion and traceability**: implemented for searchable PDFs, scans with Tesseract, common images, CSV, and XLSX. Extraction uses regex/rules over source text and stores page, bbox, and confidence. A Geologist can correct lower-confidence fields; corrections update numeric metrics, are audit-logged, and regenerate the report.
- **Report generation**: narrative/table reports, source refs, numeric table-cell click-through, and PDF export are implemented.
- **Topic and word insights**: bilingual word frequencies and keyword-weighted topics/drift are implemented for live uploads and the seed. This is not BERTopic/LDA model training.
- **Consistency checking**: ingestion checks extracted metrics against a same-block previous filing when available, otherwise uses the coalfield baseline. Severity ranking and source-document links are implemented.
- **AI query and response**: official-format answers and citations are available in demo mode; offline keyword fallback searches the full corpus. Real LLM citations preserve document IDs. Demo voice transcription is deliberately mocked; real transcription requires faster-whisper.
- **Role-based dashboards and access**: authenticated roles have server-enforced permissions.
- **Not implemented yet**: schema-constrained LLM extraction, a correction-training flywheel, and archive digitization-priority ranking. Corrections are audited but do not yet train a model or change future extraction behavior.

## Project layout

```
CoalMitra/
├── backend/           FastAPI + SQLAlchemy 2.0 (psycopg2 / SQLite)
│   ├── app/routers/   authentication, documents, extraction, reports, insights,
│   │                  anomalies, chat, metrics, dashboard
│   ├── app/services/  ingestion, extraction, report, anomaly, insight, chat,
│   │                  pdf, transcribe, answerer, index (Chroma/fastembed)
│   ├── app/seed/      demo corpus generator + startup seeder
│   └── scripts/init_db.sh
├── frontend/          React 19 + TS + Vite + Tailwind v4 + Recharts + framer-motion
│   └── src/           pages, traceability components, typed API client
├── DEMO_SCRIPT.md     the judge walk
└── README.md
```

## API surface

The typed frontend client in `frontend/src/lib/api.ts` mirrors the backend response payloads. Public endpoints are `/api/health`, `/api/seed-state`, aggregate `/api/metrics/summary` and `/api/metrics/trends`, and demo-only `/api/auth/demo-accounts`; authentication endpoints are `/api/auth/register`, `/login`, `/me`, and `/logout`. Document records, role dashboards, chat, raw extraction data, and `/static/*` source files require a valid session. Extraction supports `/api/documents/{id}/fields/{field_id}` `PATCH` for Geologist corrections. Upload is Geologist-only; anomaly acknowledgment is Auditor-only; chat sessions are private to their owner. Topic selection loads linked documents, which open in document detail.

## Checks

From `frontend/`, run `npm run build` and `npm run lint`. From `backend/`, run `python -m compileall -q app` and `DATABASE_URL="sqlite:///./coalmitra.db" python -m unittest discover -s tests -v`. The regression suite covers field parsing/units, metadata, topic assignment, historical anomaly severity/linking, and audited corrections. Live smoke checks also cover auth/RBAC, PDF and spreadsheet upload, generated reports, source downloads, and offline retrieval.