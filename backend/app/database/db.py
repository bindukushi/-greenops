"""
Database connection layer.

Tries to connect to a real MongoDB instance (Atlas, Docker, local server)
using the MONGO_URI from settings. If that server is unreachable within a
short timeout -- which is expected when running this project standalone
without `docker-compose up` -- it transparently falls back to `mongomock`,
an in-memory MongoDB-compatible engine. This means the exact same PyMongo
API (find, insert_one, update_one, aggregate, ...) works in both cases and
the codebase never has to branch on which backend is active.

For a real production deployment, simply set MONGO_URI to a MongoDB Atlas
connection string and this module will use it automatically.
"""
import sys
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from app.core.config import settings

logger = logging.getLogger("greenai.database")

_client = None
_db = None
_using_mock = False


def _connect():
    global _client, _db, _using_mock
    try:
        client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=1200)
        client.admin.command("ping")
        _client = client
        _db = client[settings.mongo_db_name]
        _using_mock = False
        logger.info("Connected to real MongoDB at %s", settings.mongo_uri)
    except Exception as exc:  # noqa: BLE001 - broad on purpose for graceful fallback
        logger.warning(
            "Could not reach MongoDB at %s (%s). Falling back to in-memory "
            "mongomock database for this session.",
            settings.mongo_uri,
            exc,
        )
        import mongomock

        _client = mongomock.MongoClient()
        _db = _client[settings.mongo_db_name]
        _using_mock = True


_connect()


def get_db():
    """Return the active database handle (real Mongo or mongomock)."""
    return _db


def is_using_mock() -> bool:
    return _using_mock


# Convenience collection handles used across routes
def users_collection():
    return get_db()["users"]


def cloud_metrics_collection():
    return get_db()["cloud_metrics"]


def predictions_collection():
    return get_db()["predictions"]


def recommendations_collection():
    return get_db()["recommendations"]


def chat_history_collection():
    return get_db()["chat_history"]


def alerts_collection():
    return get_db()["alerts"]


def daily_reports_collection():
    return get_db()["daily_reports"]


def forecast_accuracy_collection():
    return get_db()["forecast_accuracy"]


def budgets_collection():
    return get_db()["budgets"]
