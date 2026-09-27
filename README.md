# CoalMitra

An AI-powered document intelligence platform for CMPDI/CIL — turning scanned geological & mining documents into auto-generated reports, topic/word-cloud insights, and a cited AI query system with Hindi voice support.

Built for **Smart India Hackathon**. Demo mode has been smoke-tested end-to-end against the seeded SQLite corpus.

## What's inside

- **Traceability centerpiece**: every report number, extraction chip, chat citation, and anomaly is a clickable ref → the source page slides in, the normalized bbox pulses gold, confidence counts up, "Open original" serves the source PDF.
- Role-aware dashboards (**Geologist / Ministry Official / Auditor**), live landing KPIs and metrics with trends, word cloud + topic drift with clickable document filters, anomaly consistency dashboard, AI query with citations in EN + HI, Hindi voice query with browser TTS read-back.
- **Demo-first pipeline**: `DEMO_MODE=1` (default) plays back a deterministic seeded corpus instantly — no Tesseract/Chroma/Whisper/API keys needed. Flip to `DEMO_MODE=0` for the real OCR/RAG/ASR paths.

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

The app boots to a **landing screen**; the corpus (15 docs, 195 fields, 13 anomalies, 19 reports, 120 word entries across 6 topics) seeds on first startup. Landing KPIs load from the live health and metrics endpoints. Storage paths resolve relative to `backend/`, independent of the shell's current directory. Follow the judge script in `DEMO_SCRIPT.md`.

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

- **`DEMO_MODE=1`** (default): deterministic seeded pipeline — instant credible OCR/RAG/voice results from the seeded corpus. No heavy deps.
- **`DEMO_MODE=0`**: real paths — PyMuPDF word-level extraction + Tesseract OCR for scans, ChromaDB + fastembed RAG, faster-whisper ASR. Install the optional packages commented out in `backend/requirements.txt` and the system Tesseract binary first. Model downloads and hardware affect first-run latency. OpenAI credentials are optional for LLM answers/embeddings.

## Project layout

```
CoalMitra/
├── backend/           FastAPI + SQLAlchemy 2.0 (psycopg2 / SQLite)
│   ├── app/routers/   documents, extraction, reports, insights, anomalies,
│   │                  chat, metrics, dashboard
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

The typed frontend client in `frontend/src/lib/api.ts` mirrors the backend response payloads. The demo API includes `/api/health`; `/api/documents` and `/{id}`, `/{id}/status|pages|fields|emissions|file`, `/upload`, and `/coalfields`; `/api/reports` and `/{id}`, `/generate`, and `/{id}/export.pdf`; `/api/insights/{wordcloud,topics,topic-drift}` and `/api/insights/topics/{id}/documents`; `/api/anomalies` and `/{id}/ack`; `/api/metrics/{summary,trends}`; `/api/dashboard/{role}`; and `/api/chat/sessions` with message, query, and voice routes. Topic selection loads linked documents, which open in document detail.

## Checks

There is no automated test suite in the repository yet. From `frontend/`, run `npm run build` and `npm run lint`. From `backend/`, run `python -m compileall -q app`. Demo-mode API and browser smoke checks use the seeded SQLite corpus.