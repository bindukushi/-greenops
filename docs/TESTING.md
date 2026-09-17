# Testing Strategy

## 1. Unit tests

`backend/tests/test_carbon_engine.py` — pure function tests for the carbon calculation
engine: region factor lookups, the core `energy × factor` formula, and green score bounds
and behavior (idle utilization should never outscore healthy utilization).

`backend/tests/test_greenops_engine.py` — rule-firing tests for the GreenOps recommendation
engine: idle servers trigger "Resource Optimization", overloaded servers trigger "Workload
Optimization", and healthy servers return a clean "Status: OK" recommendation.

## 2. Integration / API tests

`backend/tests/test_api.py` and `backend/tests/test_prediction.py` use FastAPI's `TestClient`
against the full app (routing, auth middleware, MongoDB layer via `mongomock`), covering:

- Registration, login, duplicate-email rejection, wrong-password rejection
- Unauthenticated requests are rejected with 401
- Cloud metric ingestion computes the correct carbon emission
- GreenOps recommendations reflect ingested telemetry
- The AI assistant responds to a grounded question
- The prediction endpoint returns a valid emission forecast and confidence score
- Model metrics endpoint exposes MAE/R² for both Random Forest and XGBoost

## 3. Running the tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

All 21 tests pass in ~10 seconds (the first prediction test triggers on-demand model
training if `model_random_forest.pkl` isn't already present).

## 4. Manual / exploratory testing checklist

- [ ] Register a new account and log in
- [ ] Simulate CloudWatch ingest and confirm dashboard KPIs update
- [ ] Run a forecast with both Random Forest and XGBoost, compare confidence
- [ ] Download the PDF carbon report and confirm it opens correctly
- [ ] Trigger each GreenOps rule by ingesting metrics with idle CPU, overloaded CPU,
      high storage/low compute, and high energy in a carbon-intensive region
- [ ] Ask the AI Assistant all four suggested questions and confirm grounded answers
- [ ] Confirm behavior with no MongoDB running (mongomock fallback) and with a real
      MongoDB instance (`docker compose up mongo`)

## 5. Suggested future test additions

- Frontend component tests with React Testing Library (form validation, chart rendering)
- Load testing the `/api/predict/` endpoint with `locust` or `k6`
- Model drift monitoring: periodically re-evaluate MAE/R² against fresh data and alert
  if performance degrades below a threshold
