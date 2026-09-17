"""
Background scheduler for the daily monitoring cycle.

Uses APScheduler's BackgroundScheduler (a dedicated thread, independent of
request handling and independent of the asyncio Live Mode engine). In
production this ticks once every 24 hours. For demos, use
POST /api/monitoring/run-daily-job to trigger the exact same cycle instantly
rather than waiting for a real day boundary.
"""
from apscheduler.schedulers.background import BackgroundScheduler

from app.services.daily_job import run_daily_cycle

_scheduler = BackgroundScheduler()
_started = False


def start():
    global _started
    if not _started:
        _scheduler.add_job(
            run_daily_cycle, "interval", hours=24,
            id="daily_monitoring_cycle", next_run_time=None,
        )
        _scheduler.start()
        _started = True


def shutdown():
    global _started
    if _started:
        _scheduler.shutdown(wait=False)
        _started = False


def status() -> dict:
    job = _scheduler.get_job("daily_monitoring_cycle") if _started else None
    return {
        "running": _started,
        "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "interval": "every 24 hours (production) — use /run-daily-job to trigger on demand",
    }
