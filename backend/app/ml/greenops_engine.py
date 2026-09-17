"""
GreenOps Recommendation Engine.

Hybrid rule-based + statistical system that inspects recent cloud metrics
for a server and produces actionable sustainability recommendations:
- Reduce unused / idle resources
- Workload optimization (rebalancing, autoscaling)
- Energy-efficient region migration
- Cost reduction strategies

Rules are intentionally transparent (not a black box) since GreenOps
recommendations need to be explainable to engineering & finance stakeholders.
"""
from statistics import mean
from app.ml.carbon_engine import get_carbon_factor, estimate_cost_savings

IDLE_CPU_THRESHOLD = 20
OVERLOAD_CPU_THRESHOLD = 88
HIGH_ENERGY_THRESHOLD_KWH = 280
LOW_CARBON_REGIONS = ["eu-north-1", "sa-east-1", "us-west-2"]


def generate_recommendations(metrics_history: list[dict], region: str) -> list[dict]:
    """
    metrics_history: list of recent cloud metric documents for one server,
    most-recent-first, e.g. [{cpu_usage, memory_usage, energy_consumption, ...}, ...]
    """
    if not metrics_history:
        return []

    recs = []
    avg_cpu = mean(m["cpu_usage"] for m in metrics_history)
    avg_mem = mean(m["memory_usage"] for m in metrics_history)
    avg_energy = mean(m["energy_consumption"] for m in metrics_history)
    current_factor = get_carbon_factor(region)

    # Rule 1: Idle / underutilized resources
    if avg_cpu < IDLE_CPU_THRESHOLD:
        savings = estimate_cost_savings(avg_energy, reduction_pct=0.35)
        recs.append({
            "category": "Resource Optimization",
            "problem": f"Server is underutilized (avg CPU {avg_cpu:.1f}%).",
            "suggestion": "Downsize the instance type or consolidate workloads onto fewer nodes.",
            "expected_energy_reduction_pct": 30,
            "expected_carbon_reduction_pct": 25,
            "estimated_savings": savings,
            "priority": "high",
        })

    # Rule 2: Overloaded resources risking inefficient throttling
    if avg_cpu > OVERLOAD_CPU_THRESHOLD or avg_mem > OVERLOAD_CPU_THRESHOLD:
        recs.append({
            "category": "Workload Optimization",
            "problem": f"Server is consistently overloaded (avg CPU {avg_cpu:.1f}%, "
                       f"avg memory {avg_mem:.1f}%).",
            "suggestion": "Enable autoscaling or distribute load across additional instances "
                          "to avoid inefficient high-frequency throttling.",
            "expected_energy_reduction_pct": 12,
            "expected_carbon_reduction_pct": 10,
            "estimated_savings": estimate_cost_savings(avg_energy, reduction_pct=0.12),
            "priority": "medium",
        })

    # Rule 3: High energy usage -> suggest greener region
    if avg_energy > HIGH_ENERGY_THRESHOLD_KWH and region not in LOW_CARBON_REGIONS:
        best_region = min(LOW_CARBON_REGIONS, key=get_carbon_factor)
        recs.append({
            "category": "Green Region Migration",
            "problem": f"High energy draw ({avg_energy:.0f} kWh avg) in a carbon-intensive "
                       f"region ({region}, {current_factor} kg CO2/kWh).",
            "suggestion": f"Migrate non-latency-sensitive workloads to {best_region} "
                          f"({get_carbon_factor(best_region)} kg CO2/kWh) for greener compute.",
            "expected_energy_reduction_pct": 0,
            "expected_carbon_reduction_pct": round(
                (1 - get_carbon_factor(best_region) / current_factor) * 100
            ),
            "estimated_savings": estimate_cost_savings(avg_energy, reduction_pct=0.0),
            "priority": "high",
        })

    # Rule 4: Storage growth without corresponding compute activity
    avg_storage = mean(m.get("storage", 0) for m in metrics_history)
    if avg_storage > 500 and avg_cpu < 40:
        recs.append({
            "category": "Storage Cleanup",
            "problem": f"Storage usage is high ({avg_storage:.0f} GB) relative to compute "
                       f"activity, suggesting stale or unused data.",
            "suggestion": "Archive cold data to lower-tier storage and delete unused snapshots.",
            "expected_energy_reduction_pct": 8,
            "expected_carbon_reduction_pct": 8,
            "estimated_savings": estimate_cost_savings(avg_energy, reduction_pct=0.08),
            "priority": "low",
        })

    # Rule 5: Scheduling - suggest shifting batch workloads to off-peak/greener hours
    if avg_energy > 200:
        recs.append({
            "category": "Workload Scheduling",
            "problem": "Significant energy consumption during standard operating hours.",
            "suggestion": "Shift non-critical batch or training jobs to off-peak hours when "
                          "grid carbon intensity is typically lower.",
            "expected_energy_reduction_pct": 5,
            "expected_carbon_reduction_pct": 15,
            "estimated_savings": estimate_cost_savings(avg_energy, reduction_pct=0.05),
            "priority": "medium",
        })

    if not recs:
        recs.append({
            "category": "Status",
            "problem": "No major inefficiencies detected.",
            "suggestion": "Current configuration is well-optimized. Keep monitoring.",
            "expected_energy_reduction_pct": 0,
            "expected_carbon_reduction_pct": 0,
            "estimated_savings": {"energy_saved_kwh": 0, "cost_saved_usd": 0, "carbon_saved_kg": 0},
            "priority": "info",
        })

    return recs
