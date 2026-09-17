"""
Live-streaming engine.

Simulates a real-time CloudWatch push feed: once started, a background
asyncio task inserts one new telemetry reading per server every
`interval_seconds`, with each server's CPU/memory drifting gradually
(a random walk) rather than jumping to a fresh random value each tick —
so a dashboard polling for updates sees a genuinely evolving, organic-looking
stream instead of noise.

This is intentionally separate from POST /api/cloud/simulate (which
backfills a fixed batch of historical days instantly). Live mode is for
demonstrating an always-on monitoring feed.
"""
import asyncio
import random
from datetime import datetime

from app.core.constants import SERVER_IDS, PROVIDERS, PROVIDER_NAMES
from app.database.db import cloud_metrics_collection
from app.ml.carbon_engine import calculate_carbon

_state = {
    "running": False,
    "interval_seconds": 5,
    "tick_count": 0,
    "task": None,
    "baselines": {},  # server_id -> {provider, region, cpu, mem}
}


def _init_baselines():
    _state["baselines"] = {}
    for i, server_id in enumerate(SERVER_IDS):
        provider = PROVIDER_NAMES[i % len(PROVIDER_NAMES)]
        region = random.choice(PROVIDERS[provider]["regions"])
        _state["baselines"][server_id] = {
            "provider": provider,
            "region": region,
            "cpu": random.uniform(25, 70),
            "mem": random.uniform(30, 75),
        }


async def _tick():
    now = datetime.utcnow()
    for server_id, base in _state["baselines"].items():
        # Random-walk the CPU/memory baseline so consecutive ticks drift
        # smoothly instead of jumping — this is what makes it look "live"
        # rather than just re-randomized noise every few seconds.
        cpu = max(1, min(100, base["cpu"] + random.gauss(0, 5)))
        mem = max(1, min(100, base["mem"] + random.gauss(0, 4)))
        storage = random.uniform(150, 900)
        network = max(0, random.gauss(60, 20))
        energy = max(5, 0.9 * cpu + 0.6 * mem + 0.02 * storage + 0.15 * network
                     + random.gauss(0, 6))
        carbon = calculate_carbon(energy, base["region"])

        cloud_metrics_collection().insert_one({
            "server_id": server_id,
            "region": base["region"],
            "cloud_provider": base["provider"],
            "cpu_usage": round(cpu, 2),
            "memory_usage": round(mem, 2),
            "storage": round(storage, 2),
            "network_traffic": round(network, 2),
            "energy_consumption": round(energy, 2),
            "temperature": round(random.gauss(24, 2), 1),
            "timestamp": now,
            "carbon_emission": carbon,
            "source": "live_stream",
        })

        base["cpu"] = cpu
        base["mem"] = mem

    _state["tick_count"] += 1


async def _loop():
    try:
        while _state["running"]:
            await _tick()
            await asyncio.sleep(_state["interval_seconds"])
    except asyncio.CancelledError:
        pass


def start(interval_seconds: int = 5) -> dict:
    """Starts the background live-stream task (idempotent if already running)."""
    if not _state["running"]:
        if not _state["baselines"]:
            _init_baselines()
        _state["running"] = True
        _state["interval_seconds"] = max(2, min(60, interval_seconds))
        loop = asyncio.get_event_loop()
        _state["task"] = loop.create_task(_loop())
    return status()


def stop() -> dict:
    """Stops the background live-stream task."""
    _state["running"] = False
    task = _state["task"]
    if task:
        task.cancel()
        _state["task"] = None
    return status()


def status() -> dict:
    return {
        "running": _state["running"],
        "interval_seconds": _state["interval_seconds"],
        "tick_count": _state["tick_count"],
        "server_count": len(_state["baselines"]),
    }
