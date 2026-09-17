"""
Carbon Calculation Engine.

Converts raw energy consumption into an estimated CO2 footprint using
region-aware grid carbon-intensity factors (kg CO2 per kWh). Falls back to
a configurable default factor for unknown regions.

Region factors are illustrative averages (kg CO2e / kWh) commonly cited for
national/regional electricity grids, and can be swapped for live figures
from a provider such as Electricity Maps or WattTime in production.
"""
from app.core.config import settings

REGION_CARBON_FACTORS = {
    "ap-south-1": 0.82,      # Mumbai, India - coal-heavy grid
    "ap-southeast-1": 0.51,  # Singapore
    "us-east-1": 0.38,       # N. Virginia, USA
    "us-west-2": 0.14,       # Oregon, USA - hydro heavy
    "eu-west-1": 0.32,       # Ireland
    "eu-north-1": 0.02,      # Stockholm - near-100% renewable grid
    "sa-east-1": 0.09,       # Sao Paulo - hydro heavy
}


def get_carbon_factor(region: str) -> float:
    """Return kg CO2 per kWh for a given cloud region."""
    return REGION_CARBON_FACTORS.get(region, settings.default_carbon_factor)


def calculate_carbon(energy_kwh: float, region: str = "ap-south-1") -> float:
    """
    Core carbon calculation:
        emission (kg CO2) = energy_consumed (kWh) * region_carbon_factor
    """
    factor = get_carbon_factor(region)
    return round(energy_kwh * factor, 3)


def green_score(cpu_usage: float, memory_usage: float, carbon_emission: float,
                 energy_kwh: float) -> int:
    """
    Composite sustainability score (0-100). Higher is better.

    Combines resource utilization efficiency (penalizes very low or very
    high utilization -> waste or risk of throttling) with carbon efficiency
    (emission per unit of energy actually used).
    """
    # Utilization efficiency: ideal band is 40-75% usage
    utilization = (cpu_usage + memory_usage) / 2
    if utilization < 20:
        util_score = 40  # heavily underutilized / idle waste
    elif 40 <= utilization <= 75:
        util_score = 100
    elif utilization > 90:
        util_score = 55  # overloaded, risk of inefficiency
    else:
        util_score = 75

    # Carbon efficiency: lower emission per kWh is better
    factor_ratio = min(carbon_emission / max(energy_kwh, 0.001), 1.0)
    carbon_score = round((1 - factor_ratio) * 100)

    score = round(0.5 * util_score + 0.5 * carbon_score)
    return max(0, min(100, score))


def estimate_cost_savings(energy_kwh: float, reduction_pct: float = 0.3,
                           price_per_kwh: float = 0.12) -> dict:
    """Estimate cost + carbon savings from a proposed workload reduction."""
    saved_energy = energy_kwh * reduction_pct
    return {
        "energy_saved_kwh": round(saved_energy, 2),
        "cost_saved_usd": round(saved_energy * price_per_kwh, 2),
        "carbon_saved_kg": round(saved_energy * settings.default_carbon_factor, 2),
    }
