from app.ml.carbon_engine import calculate_carbon, get_carbon_factor, green_score


def test_get_carbon_factor_known_region():
    assert get_carbon_factor("ap-south-1") == 0.82


def test_get_carbon_factor_unknown_region_uses_default():
    assert get_carbon_factor("mars-north-1") == 0.82


def test_calculate_carbon_basic():
    # 500 kWh * 0.82 factor = 410 kg CO2 (matches project brief example)
    assert calculate_carbon(500, "ap-south-1") == 410.0


def test_calculate_carbon_low_carbon_region():
    emission = calculate_carbon(500, "eu-north-1")
    assert emission == 10.0  # 500 * 0.02


def test_green_score_within_bounds():
    score = green_score(cpu_usage=50, memory_usage=55, carbon_emission=100, energy_kwh=200)
    assert 0 <= score <= 100


def test_green_score_penalizes_idle_waste():
    idle_score = green_score(cpu_usage=5, memory_usage=8, carbon_emission=50, energy_kwh=100)
    healthy_score = green_score(cpu_usage=55, memory_usage=60, carbon_emission=50, energy_kwh=100)
    assert healthy_score > idle_score
