# API Reference

Base URL: `http://localhost:8000`. Interactive docs at `/docs` (Swagger) and `/redoc`.

All routes except `/`, `/api/health`, `/api/auth/register`, `/api/auth/login` require:

```
Authorization: Bearer <access_token>
```

## Authentication

| Method | Path                | Description                          |
|--------|---------------------|--------------------------------------|
| POST   | `/api/auth/register`| Create an account, returns a token   |
| POST   | `/api/auth/login`   | Log in, returns a token              |
| GET    | `/api/auth/me`      | Current user profile                 |

**Register / Login request body**
```json
{ "name": "Ada", "email": "ada@example.com", "password": "secret123", "role": "viewer" }
```

**Response**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "...", "name": "Ada", "email": "ada@example.com", "role": "viewer" }
}
```

## Cloud Monitoring

| Method | Path                     | Description                                       |
|--------|--------------------------|----------------------------------------------------|
| POST   | `/api/cloud/metrics`     | Ingest a single telemetry reading                   |
| GET    | `/api/cloud/metrics`     | List recent readings (`?server_id=&limit=`)         |
| GET    | `/api/cloud/servers`     | List distinct servers currently reporting           |
| GET    | `/api/cloud/servers/overview` | One row per server with quick KPIs (for the Servers list page) |
| GET    | `/api/cloud/servers/{server_id}/detail` | Full drill-down: averages, latest reading, totals |
| POST   | `/api/cloud/live/start`  | Start real-time simulated streaming (`?interval_seconds=`) |
| POST   | `/api/cloud/live/stop`   | Stop the live-streaming background task            |
| GET    | `/api/cloud/live/status` | `{running, interval_seconds, tick_count, server_count}` |
| POST   | `/api/cloud/aws/sync`    | Pull REAL CloudWatch data (`?instance_ids=&region=`), requires `boto3` + AWS credentials |
| GET    | `/api/cloud/aws/status`  | `{configured: bool}` — whether real AWS sync is available |
| GET    | `/api/cloud/summary`     | Dashboard KPIs (total emission, energy, green score)|
| POST   | `/api/cloud/simulate`    | Simulate `?days=N` of CloudWatch history for demo   |
| GET    | `/api/cloud/resource-usage` | Average CPU/memory/energy per server (chart data) |
| GET    | `/api/cloud/export/csv`  | Download raw telemetry as CSV (`?server_id=`)       |

## Carbon Engine

| Method | Path                              | Description                              |
|--------|------------------------------------|-------------------------------------------|
| POST   | `/api/carbon/calculate`           | `{ energy_kwh, region }` → emission (kg)   |
| GET    | `/api/carbon/trend`               | Daily emission trend (`?server_id=&days=`) |
| GET    | `/api/carbon/energy-trend`         | Daily energy consumption trend (`?server_id=&days=`) |
| GET    | `/api/carbon/multi-cloud-comparison` | Region-by-region carbon efficiency ranking |
| GET    | `/api/carbon/provider-comparison` | AWS vs Azure vs GCP carbon efficiency ranking |
| GET    | `/api/carbon/report/pdf`          | Downloadable PDF carbon footprint report   |

## Prediction (ML)

| Method | Path                    | Description                                   |
|--------|-------------------------|------------------------------------------------|
| POST   | `/api/predict/`         | Forecast emission from live telemetry           |
| GET    | `/api/predict/metrics`  | Model MAE / R² / confidence (RF + XGBoost)      |
| GET    | `/api/predict/history`  | Past predictions (`?server_id=&limit=`)         |

**Predict request body**
```json
{
  "server_id": "AWS001",
  "cpu_usage": 80,
  "memory_usage": 70,
  "storage": 400,
  "network_traffic": 50,
  "energy_consumption": 300,
  "temperature": 24,
  "region": "ap-south-1",
  "horizon_days": 7,
  "model_name": "random_forest"
}
```

## GreenOps

| Method | Path                          | Description                                |
|--------|-------------------------------|----------------------------------------------|
| GET    | `/api/greenops/recommendations` | Rule-based recommendations (`?server_id=`)  |

## AI Assistant

| Method | Path              | Description                                  |
|--------|-------------------|-------------------------------------------------|
| POST   | `/api/chat/ask`   | `{ message, server_id? }` → grounded answer      |
| GET    | `/api/chat/history` | Past questions/answers for the current user    |

## Daily Monitoring

| Method | Path                                | Description                                       |
|--------|-------------------------------------|-----------------------------------------------------|
| POST   | `/api/monitoring/run-daily-job`     | Runs the full cycle now: forecast, score accuracy, detect anomalies, check budget, compile digest |
| GET    | `/api/monitoring/daily-reports`     | Recent digest history (`?limit=`)                   |
| GET    | `/api/monitoring/alerts`            | Recent alerts (`?limit=&alert_type=anomaly\|budget`) |
| GET    | `/api/monitoring/forecast-accuracy` | Predicted vs. actual emission pairs (`?server_id=&limit=`) |
| GET    | `/api/monitoring/budget`            | Current daily carbon budget                          |
| PUT    | `/api/monitoring/budget`            | `{ daily_limit_kg }` → update the budget              |
| GET    | `/api/monitoring/scheduler/status`  | Whether the 24h background scheduler is active       |
| POST   | `/api/monitoring/inject-test-anomaly` | Demo utility: inserts a deliberate spike reading (`?server_id=`) |
