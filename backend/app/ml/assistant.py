"""
GreenOps AI Assistant.

Uses:
- Actual GreenAI telemetry as grounding context
- GreenAI project knowledge
- Groq LLM for natural-language answers
- Rule-based fallback if Groq is unavailable
"""

from statistics import mean
from app.core.config import settings


GREENAI_KNOWLEDGE = """
You are the AI Assistant inside GreenAI, a Cloud Sustainability Platform.

GREENAI FEATURES:

1. DASHBOARD
The Dashboard provides an overview of cloud sustainability including:
- CPU utilization
- Energy consumption
- Carbon emissions
- Sustainability/Green Score
- Carbon emission trends
- Energy consumption trends
- Resource usage by server
- Live monitoring
- CloudWatch telemetry ingestion

2. SERVERS
The Servers page provides:
- List of monitored servers
- Server-specific KPIs
- CPU and memory utilization
- Energy consumption
- Carbon emissions
- Historical telemetry
- Sustainability score
- Server-specific GreenOps recommendations

3. MONITORING
The Monitoring page provides:
- Daily emission forecasting
- Forecast accuracy tracking
- Predicted vs actual emissions
- Statistical anomaly detection
- Z-score based anomaly detection
- Carbon budget monitoring
- Daily sustainability reports
- Alert history
- Alert testing through deliberate spike injection

4. ANALYTICS
The Analytics page provides:
- Carbon emission forecasting
- Random Forest forecasting
- XGBoost forecasting
- Historical trends
- Prediction charts
- Analytical reports
- CSV/PDF export where available

5. MULTI-CLOUD
The Multi-Cloud page compares:
- AWS
- Azure
- GCP

It provides:
- Cloud provider efficiency comparison
- Region-level carbon analysis
- Carbon efficiency ranking

6. OPTIMIZATION
The Optimization page provides GreenOps recommendations such as:
- Reducing unnecessary resource usage
- Optimizing underutilized servers
- Improving workload scheduling
- Reducing energy consumption
- Reducing carbon emissions

7. AI ASSISTANT
The AI Assistant answers questions using:
- GreenAI project knowledge
- Actual telemetry retrieved from the application
- Carbon and energy metrics
- Server information when available
- Forecasting information when available

IMPORTANT:
Never invent telemetry values.
If a requested value is not present in the supplied context, clearly say that
the information is not available in the current context.

The assistant should answer questions specifically rather than returning
the same generic telemetry snapshot for every question.
"""


def _build_context_summary(history: list[dict]) -> dict:
    if not history:
        return {}

    return {
        "avg_cpu": round(mean(m.get("cpu_usage", 0) for m in history), 1),
        "avg_memory": round(mean(m.get("memory_usage", 0) for m in history), 1),
        "avg_energy": round(
            mean(m.get("energy_consumption", 0) for m in history), 1
        ),
        "avg_carbon": round(
            mean(m.get("carbon_emission", 0) for m in history), 1
        ),
        "latest_carbon": history[0].get("carbon_emission", 0),
        "oldest_carbon": history[-1].get("carbon_emission", 0),
        "n_records": len(history),
    }


def _rule_based_answer(message: str, ctx: dict) -> str:
    """
    Safe fallback when Groq is unavailable.
    """

    if not ctx:
        return (
            "I don't currently have monitoring data available. "
            "Please ingest cloud telemetry first, then ask me again."
        )

    msg = message.lower()

    delta = ctx["latest_carbon"] - ctx["oldest_carbon"]

    if ctx["oldest_carbon"]:
        pct_change = delta / ctx["oldest_carbon"] * 100
    else:
        pct_change = 0

    if any(
        word in msg
        for word in [
            "hello",
            "hi",
            "hey",
        ]
    ):
        return (
            "Hello! I'm the GreenAI GreenOps Assistant. "
            "I can answer questions about your dashboard, servers, "
            "monitoring, analytics, cloud emissions, forecasts, "
            "optimization recommendations, and sustainability metrics."
        )

    if any(
        word in msg
        for word in [
            "monitoring",
            "monitor",
            "daily job",
            "anomaly",
            "alert",
        ]
    ):
        return (
            "The Monitoring page performs daily carbon-emission forecasting, "
            "compares previous forecasts with actual emissions, detects "
            "statistical anomalies using z-scores, checks the carbon budget, "
            "and generates daily monitoring reports."
        )

    if any(
        word in msg
        for word in [
            "server",
            "servers",
        ]
    ):
        return (
            f"GreenAI currently has telemetry from {ctx['n_records']} "
            "records. The server details page provides server-level CPU, "
            "memory, energy, carbon history, sustainability scores, "
            "and GreenOps recommendations."
        )

    if any(
        word in msg
        for word in [
            "why",
            "increasing",
            "increase",
            "higher",
            "rising",
        ]
    ):
        direction = "increased" if delta > 0 else "decreased"

        return (
            f"Your carbon emission has {direction} by "
            f"{abs(pct_change):.1f}% over the available recorded period. "
            f"Average CPU utilization is {ctx['avg_cpu']}%, while average "
            f"energy consumption is {ctx['avg_energy']} kWh. "
            "Higher compute utilization and energy consumption can increase "
            "the carbon footprint."
        )

    if any(
        word in msg
        for word in [
            "reduce",
            "lower",
            "optimize",
            "improve",
        ]
    ):
        return (
            f"Your current average energy consumption is "
            f"{ctx['avg_energy']} kWh and average carbon emission is "
            f"{ctx['avg_carbon']} kg CO2. Recommended actions include "
            "optimizing underutilized resources, scheduling non-critical "
            "workloads efficiently, and reviewing the Optimization page "
            "for server-specific GreenOps recommendations."
        )

    if any(
        word in msg
        for word in [
            "score",
            "sustainability",
            "green score",
        ]
    ):
        return (
            f"Your current telemetry shows average energy consumption of "
            f"{ctx['avg_energy']} kWh and average carbon emissions of "
            f"{ctx['avg_carbon']} kg CO2. For the exact Green Score, "
            "check the Sustainability Score card on the Dashboard."
        )

    if any(
        word in msg
        for word in [
            "forecast",
            "predict",
            "future",
            "next month",
            "next week",
        ]
    ):
        return (
            "GreenAI supports carbon-emission forecasting using Random Forest "
            "and XGBoost. For the actual forecast, use the Analytics page "
            "because the forecast endpoint contains the model prediction "
            "rather than only historical telemetry."
        )

    if any(
        word in msg
        for word in [
            "multi-cloud",
            "aws",
            "azure",
            "gcp",
            "cloud provider",
        ]
    ):
        return (
            "The Multi-Cloud page compares AWS, Azure, and GCP using "
            "carbon-efficiency and region-level sustainability information."
        )

    if any(
        word in msg
        for word in [
            "analytics",
            "random forest",
            "xgboost",
            "machine learning",
            "ml model",
        ]
    ):
        return (
            "GreenAI uses machine learning for carbon-emission forecasting. "
            "The primary models are Random Forest and XGBoost. "
            "The Analytics page allows you to run forecasts and compare "
            "prediction results."
        )

    if any(
        word in msg
        for word in [
            "optimization",
            "greenops",
        ]
    ):
        return (
            "GreenOps focuses on reducing cloud resource waste, energy "
            "consumption, and carbon emissions. GreenAI generates "
            "server-specific recommendations through the Optimization page."
        )

    return (
        f"Based on the current telemetry, average CPU is "
        f"{ctx['avg_cpu']}%, average energy consumption is "
        f"{ctx['avg_energy']} kWh, and average carbon emission is "
        f"{ctx['avg_carbon']} kg CO2 across {ctx['n_records']} records. "
        "I can answer questions about your Dashboard, Servers, Monitoring, "
        "Analytics, Multi-Cloud, Optimization, forecasts, and emissions."
    )


def _groq_answer(message: str, ctx: dict) -> str:
    """
    Generate a grounded response using Groq.
    """

    from groq import Groq

    api_key = settings.groq_api_key

    if not api_key:
        return _rule_based_answer(message, ctx)

    client = Groq(api_key=api_key)

    system_prompt = f"""
{GREENAI_KNOWLEDGE}

CURRENT GREENAI TELEMETRY:
{ctx}

USER QUESTION:
{message}

INSTRUCTIONS:

1. Answer the user's actual question.
2. Use the telemetry supplied above whenever relevant.
3. Use the GreenAI project knowledge when the user asks how the application works.
4. Do not repeat the generic telemetry snapshot unless the user asks for it.
5. Do not invent numbers, servers, forecasts, scores, alerts, or cloud regions.
6. If a value is unavailable, say so clearly.
7. Keep the response concise but useful.
8. If the user asks for optimization, provide practical GreenOps actions.
9. If the user asks about a GreenAI page, explain that page specifically.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        temperature=0.2,
        max_tokens=500,
    )

    return response.choices[0].message.content.strip()


def _llm_answer(message: str, ctx: dict) -> str:
    """
    LLM entry point.

    Currently uses Groq.
    Falls back to the deterministic assistant if Groq fails.
    """

    try:
        return _groq_answer(message, ctx)

    except Exception as exc:
        print(f"Groq assistant error: {exc}")

        return _rule_based_answer(message, ctx)


def answer_question(
    message: str,
    metrics_history: list[dict],
) -> str:

    ctx = _build_context_summary(metrics_history)

    return _llm_answer(message, ctx)