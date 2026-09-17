# Architecture

## 1. System overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLOUD INFRASTRUCTURE                        │
│              (AWS CloudWatch API — simulated)                    │
└───────────────────────────────┬───────────────────────────────────┘
                                 │  CPU / Memory / Storage / Network / Energy
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                            │
│  ┌───────────┐ ┌───────────┐ ┌────────────────┐ ┌─────────────┐ │
│  │   Auth    │ │  Cloud    │ │ Carbon Engine   │ │  Prediction │ │
│  │  (JWT)    │ │ Monitoring│ │ (region-aware)  │ │  API (ML)   │ │
│  └───────────┘ └───────────┘ └────────────────┘ └─────────────┘ │
│  ┌────────────────────┐  ┌──────────────────────────────────┐   │
│  │  GreenOps Engine    │  │  AI Assistant (rules + RAG hook) │   │
│  └────────────────────┘  └──────────────────────────────────┘   │
└───────────────┬───────────────────────────────┬─────────────────┘
                │                                │
                ▼                                ▼
      ┌───────────────────┐            ┌──────────────────────┐
      │  MongoDB           │            │   ML Engine           │
      │  (or mongomock      │           │  Random Forest         │
      │   in-memory fallback)│          │  XGBoost                │
      └───────────────────┘            │  LSTM (optional)       │
                                        └──────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   React Dashboard      │
                     │  Carbon Analytics      │
                     │  Forecast Charts       │
                     │  Green Score Gauge     │
                     │  Optimization Reports  │
                     │  AI Assistant Chat     │
                     └───────────────────────┘
```

## 2. Request flow example — "Forecast my emissions"

1. React `Analytics` page collects current telemetry (CPU, memory, energy, region) via a form.
2. `POST /api/predict/` hits `app/routes/prediction.py`.
3. The route calls `app/ml/predict.py::predict_emission()`, which:
   - Loads the trained Random Forest / XGBoost model (`joblib`) — training happens
     automatically on first use if artifacts are missing (`_ensure_trained()`).
   - Computes a same-day carbon proxy via `carbon_engine.calculate_carbon()` as a lag feature.
   - Projects the base prediction forward across `horizon_days` using a mild growth factor.
4. The prediction is stored in the `predictions` MongoDB collection and returned to the client.
5. The frontend renders the predicted kg CO₂, model used, and confidence bar.

## 3. Why mongomock fallback?

MongoDB is the specified database, but a final-year project demo should not fail because a
grader's machine doesn't have MongoDB installed. `app/database/db.py` attempts a real
connection with a 1.2s timeout; on failure it transparently swaps in `mongomock`, an
in-memory engine implementing the same PyMongo collection API (`find`, `insert_one`,
`update_one`, `distinct`, ...). No route code branches on which backend is active — the
same code path works against Atlas, a local Docker Mongo, or the mock.

## 4. Carbon calculation model

```
emission (kg CO2) = energy_consumed (kWh) × region_carbon_factor (kg CO2/kWh)
```

Region factors (`REGION_CARBON_FACTORS` in `app/ml/carbon_engine.py`) are illustrative grid
averages per cloud region — replace with a live feed (e.g. Electricity Maps, WattTime) for
production accuracy.

## 5. GreenOps recommendation engine

A transparent, explainable rule engine (`app/ml/greenops_engine.py`) inspects recent telemetry
and fires rules for:

- **Idle/underutilized resources** (avg CPU < 20%) → downsizing suggestion
- **Overloaded resources** (avg CPU/memory > 88%) → autoscaling suggestion
- **High energy + carbon-intensive region** → migration to a greener region
- **High storage, low compute** → stale data cleanup
- **High energy overall** → workload scheduling to off-peak / lower-carbon hours

Each rule attaches an estimated energy/carbon reduction percentage and a cost saving estimate,
so recommendations are explainable to both engineering and finance stakeholders — unlike a
black-box ML recommender.

## 6. ML pipeline

```
Synthetic dataset (correlated CPU/memory/storage/network → energy → carbon,
with weekly seasonality and long-term growth trend)
        │
        ▼
Data cleaning (bounds checks on percentages, drop NaNs, drop negative emissions)
        │
        ▼
Feature engineering (region label-encoding, previous-emission lag feature)
        │
        ▼
Train/test split (80/20)
        │
        ▼
Train Random Forest (250 trees) + XGBoost (300 rounds)
        │
        ▼
Evaluate (MAE, R²) → both models achieve R² ≈ 0.97 on held-out data
        │
        ▼
Save model.pkl + encoder.pkl + training_metrics.json
```

An optional LSTM module (`app/ml/lstm_model.py`) is included for sequence-based forecasting
over a 14-day rolling window, demonstrating awareness of temporal models per the project
brief, without adding a hard TensorFlow dependency to the core API.

## 7. AI Assistant (GreenOps chatbot)

```
User question
     │
     ▼
Retrieve last 14 telemetry records for the relevant server (RAG-style context)
     │
     ▼
[ If OPENAI_API_KEY / GEMINI_API_KEY set → real LLM call with context injected ]
[ Else → deterministic rule-based answer grounded in the same retrieved context ]
     │
     ▼
Answer (+ persisted to chat_history collection)
```

This means the assistant works out of the box with zero external API cost for a demo, while
the exact same context-retrieval code path is what a real LangChain/RAG pipeline would need —
only the final generation call changes.

## 8. Deployment

`docker-compose.yml` runs three containers:

- `mongo` — official MongoDB 7 image with a persisted volume
- `backend` — FastAPI app; Dockerfile pre-trains ML models at build time
- `frontend` — Vite production build served by Nginx, proxying `/api` to the backend

For cloud deployment, push the backend/frontend images to a registry and deploy to
AWS EC2 / ECS, Azure Container Apps, or GCP Cloud Run, pointing `MONGO_URI` at MongoDB Atlas.
