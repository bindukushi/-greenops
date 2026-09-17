#
Restart the backend, then use the "Real AWS CloudWatch Sync" panel on the Dashboard (or
`POST /api/cloud/aws/sync?instance_ids=i-0123456789abcdef0`) to pull real `CPUUtilization` data
for your own EC2 instances. Honesty note: CloudWatch's default EC2 metrics only expose CPU —
memory/disk require the CloudWatch Agent, and energy consumption isn't directly exposed by AWS,
so it's estimated from CPU via a simple power model (documented in
`app/integrations/aws_cloudwatch.py`). Everything downstream (carbon calc, ML forecasting,
GreenOps recommendations) works identically on this real data with zero code changes, since it's
stored in the same schema as the simulated data.

## 9. Daily Monitoring in depth

The Monitoring page (`/monitoring`) is the closest thing in this project to a real production
MLOps setup:

1. **Scheduled forecasting** — `app/services/scheduler.py` runs a background job every 24 hours
   (production) that forecasts next-day emissions per server using the trained Random Forest
   model. For demos, click **Run Daily Job Now** instead of waiting for a real day to pass.
2. **Genuine accuracy tracking** — each run scores the *previous* run's forecast against what
   actually happened since, storing predicted-vs-actual pairs. This is why the Forecast Accuracy
   chart needs at least two runs of the daily job before it shows data — the first run has
   nothing to compare against yet.
3. **Anomaly detection** — a transparent z-score check (`app/ml/anomaly_engine.py`) flags any
   server whose latest reading deviates sharply from its own recent baseline. Explainable by
   design: an alert says "3.1 standard deviations above the 14-day average," not just "anomaly."
4. **Carbon budget alerts** — set a daily fleet-wide limit on the Monitoring page; exceeding it
   raises a budget alert on the next run.
5. **Digest compilation** — every run produces a summary (total emission, top offender, alert
   counts, average forecast error) stored in `daily_reports` and shown as history on the page.

Use the **"Test the Alerting Pipeline"** button on the Monitoring page to inject a deliberate
spike reading and immediately see it caught — useful for a live demo since organic random
variance in simulated data won't reliably produce a real anomaly on demand.

## 10. Extending this project

- **Real cloud data**: replace `POST /api/cloud/simulate` with a `boto3` CloudWatch client
  pulling real `CPUUtilization`, `MemoryUtilization`, `NetworkIn/Out` metrics.
- **Real LLM assistant**: set `OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env` — the code path
  in `app/ml/assistant.py::_llm_answer` is ready to wire up a LangChain/RAG pipeline over
  the same MongoDB telemetry used by the rule-based fallback.
- **L GreenAI

**Cloud-Based AI System for Carbon Emission Forecasting and GreenOps Optimization**

A final-year engineering project: an intelligent sustainability platform that monitors cloud
resource usage, calculates carbon emissions, forecasts future emissions with machine learning,
and generates GreenOps optimization recommendations — with an AI assistant on top.

![status](https://img.shields.io/badge/status-demo--ready-3DDC84) ![python](https://img.shields.io/badge/python-3.12-blue) ![react](https://img.shields.io/badge/react-18-61DAFB)

---

## 1. What's inside

| Layer         | Technology                                              |
|---------------|-----------------------------------------------------------|
| Frontend      | React 18, Vite, Tailwind CSS, Recharts                    |
| Backend       | Python, FastAPI, JWT auth                                  |
| Database      | MongoDB (falls back automatically to an in-memory `mongomock` instance if no real Mongo is reachable — **so the whole project runs standalone with zero setup**) |
| Machine Learning | scikit-learn (Random Forest), XGBoost, optional LSTM (TensorFlow) |
| Cloud         | AWS CloudWatch API simulation (swap for real `boto3` calls in production) |
| Deployment    | Docker + Docker Compose (Mongo + FastAPI + Nginx/React)     |

Full details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), API reference: [`docs/API.md`](docs/API.md),
testing strategy: [`docs/TESTING.md`](docs/TESTING.md).

## 2. What's new in this update

- **Daily Monitoring (scheduled forecasting + MLOps-style tracking)** — a new `/monitoring` page
  and background job that: forecasts next-day emissions for every server, **scores each previous
  forecast against what actually happened** (genuine accuracy tracking, not just re-predicting),
  runs statistical anomaly detection (z-score based, explainable), checks a configurable daily
  carbon budget, and compiles a digest — all runnable on a real 24-hour schedule or on demand via
  "Run Daily Job Now". Includes a "Test the Alerting Pipeline" utility to inject a deliberate
  spike and watch it get caught. See section 9 below.
- **Live Mode (genuine real-time streaming)** — click **Start Live Mode** on the Dashboard and a
  background task streams one new simulated reading per server every few seconds, with the
  dashboard auto-polling and updating on its own — no page refresh needed.
- **Real AWS CloudWatch sync (optional add-on)** — a genuinely real data path, inert by default.
  Install `boto3` and set AWS credentials to pull actual `CPUUtilization` data for your own EC2
  instances — see `app/integrations/aws_cloudwatch.py`.
- **Server drill-down page** — a new `/servers` list (with quick KPIs per server) that links
  through to `/servers/:id`, showing that server's full carbon/energy history, sustainability
  score, and tailored GreenOps recommendations in one view.
- **Multi-Cloud page** — dedicated AWS vs Azure vs GCP comparison with per-provider efficiency
  ranking, plus a region-level carbon breakdown chart (`/multi-cloud` in the sidebar).
- **More dashboard charts** — Energy Consumption Trend and Resource Usage by Server (click a bar
  to jump straight to that server's detail page), alongside the Carbon Emission Trend and gauge.
- **CSV export** — download raw telemetry as CSV from the Dashboard, Analytics, Multi-Cloud, or
  any individual server's detail page (`GET /api/cloud/export/csv`).
- **Polish** — loading skeletons, empty states, retryable error banners, animated count-up KPIs,
  and subtle hover/press micro-interactions throughout the UI.

## 3. Quick start (no Docker — fastest for a demo)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # optional but recommended
pip install -r requirements.txt

cp .env.example .env                                     # edit if you have a real Mongo URI

# Generate the synthetic training dataset and train the ML models
python -m app.ml.generate_dataset
python -m app.ml.train

# Seed a demo admin login (admin@greenai.io / GreenAI@123)
python seed.py

# Run the API
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` — Swagger docs at `http://localhost:8000/docs`.

> No MongoDB running? No problem — the backend automatically falls back to an in-memory
> `mongomock` database so you can demo the entire project without installing anything else.
> Note: mongomock data resets whenever the server restarts. Point `MONGO_URI` at a real
> MongoDB (local or Atlas) in `.env` for persistent storage.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, log in with the seeded demo account, then click
**"Simulate CloudWatch ingest"** on the Dashboard to populate 60 days of sample telemetry
across 6 servers.

## 4. Quick start (Docker — production-style)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000/docs
- MongoDB:  localhost:27017 (persisted in a named volume)

The backend container trains the ML models at build time, so predictions work immediately.
Run `docker compose exec backend python seed.py` once to create the demo login.

## 5. Demo login

```
email:    admin@greenai.io
password: GreenAI@123
```

(created by running `python seed.py` — see step 2 above)

## 6. Demo flow (for your presentation)

1. **Login** with the seeded admin account.
2. On the **Dashboard**, click *Simulate CloudWatch ingest* to load sample cloud telemetry, or
   click *Start Live Mode* to watch it stream in real time.
3. Watch the **Carbon Emission Trend** chart and **Sustainability Score** gauge populate.
4. Go to **Servers** → click into any server for its full history and tailored recommendations.
5. Go to **Monitoring** → click *Run Daily Job Now* twice (to see forecast accuracy appear),
   then *Inject spike* to watch the anomaly alert fire live.
6. Go to **Analytics** → run a forecast (Random Forest / XGBoost) and download the PDF report.
7. Go to **Multi-Cloud** → compare AWS vs Azure vs GCP carbon efficiency ranking.
8. Go to **Optimization** → review GreenOps recommendations per server.
9. Go to **AI Assistant** → ask *"How can I reduce emissions?"*.

## 7. Project structure

```
GreenAI/
├── backend/
│   ├── app/
│   │   ├── routes/        # auth, cloud, carbon, prediction, greenops, chat, monitoring
│   │   ├── models/        # Pydantic schemas
│   │   ├── ml/            # carbon engine, GreenOps engine, anomaly detection,
│   │   │                  # training + prediction, assistant
│   │   ├── services/      # live_engine (real-time streaming), scheduler + daily_job
│   │   │                  # (scheduled forecasting, accuracy tracking, alerts)
│   │   ├── integrations/  # aws_cloudwatch (optional real AWS CloudWatch sync)
│   │   ├── database/      # MongoDB connection (with mongomock fallback)
│   │   ├── core/          # config, security (JWT), shared constants
│   │   └── main.py
│   ├── tests/              # pytest suite (41 tests)
│   ├── seed.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/         # Login, Dashboard, Servers, ServerDetail, Monitoring,
│   │   │                  # Analytics, MultiCloud, Optimization, Assistant
│   │   ├── components/    # AppLayout, StatCard, GreenScoreGauge, PageHeader,
│   │   │                  # Skeleton, States
│   │   ├── hooks/          # useCountUp (animated KPI numbers)
│   │   ├── services/      # axios API client, CSV/blob download helper
│   │   └── context/        # AuthContext
│   └── package.json
├── dataset/                # generated synthetic training data (CSV)
├── docs/                   # architecture, API reference, testing strategy
├── docker-compose.yml
└── README.md
```

## 8. Real-time & real AWS integration

**Is this actually real-time?** Two levels, and it's worth being precise about which is which:

- **The pipeline is 100% real.** Every prediction, recommendation, and chart is computed live
  from whatever's currently in the database — nothing is pre-recorded or faked. Switching
  servers, running a forecast, or asking the AI Assistant all trigger genuine computation.
- **The default data source is simulated**, because a student project can't have production
  cloud infrastructure to monitor. Two ways to make the data itself real-time:

**1. Live Mode (simulated, zero setup)** — click **Start Live Mode** on the Dashboard. A background
`asyncio` task (`app/services/live_engine.py`) pushes one new reading per server every few
seconds, with each server's CPU/memory drifting gradually (a random walk) rather than
re-randomizing — so it looks and behaves like a genuine live monitoring feed. The dashboard polls
and updates on its own while this is running. Verified: starting live mode and waiting 10 seconds
produces real, incrementing tick counts and changing KPIs — this is an actual running background
task, not a UI animation.

**2. Real AWS CloudWatch sync (optional add-on, genuinely real)** — the one part of this project
that talks to real infrastructure:
```bash
pip install boto3
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1        # optional
```STM forecasting**: `app/ml/lstm_model.py` trains a sequence model over 14-day windows
  for trend-aware forecasting; install `tensorflow` to use it (kept optional to keep the
  core API lightweight).
- **Real carbon intensity data**: swap the static `REGION_CARBON_FACTORS` table in
  `app/ml/carbon_engine.py` for a live feed from Electricity Maps or WattTime.
- **Email/Slack alerts**: `app/services/daily_job.py` already creates alert documents in Mongo —
  add a notification sink (SMTP, Slack webhook) that fires when a new alert is inserted.

## 11. License

Provided as a final-year academic project template. Use, modify, and extend freely.
