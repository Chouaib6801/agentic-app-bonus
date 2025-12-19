"""
Redis Queue configuration and connection utilities.
Supports both real Redis and fakeredis for local development.
"""

import os
from rq import Queue

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
USE_FAKE_REDIS = os.getenv("USE_FAKE_REDIS", "false").lower() == "true"

# Singleton for fakeredis connection (must be shared between API and worker)
_fake_redis_conn = None


def get_redis_connection():
    """
    Get a Redis connection instance.
    Uses fakeredis if USE_FAKE_REDIS=true, otherwise real Redis.
    """
    global _fake_redis_conn
    
    if USE_FAKE_REDIS:
        if _fake_redis_conn is None:
            import fakeredis
            _fake_redis_conn = fakeredis.FakeRedis()
            print("[Queue] Using fakeredis for local development")
        return _fake_redis_conn
    else:
        from redis import Redis
        return Redis.from_url(REDIS_URL)


def get_task_queue() -> Queue:
    """Get the main task queue."""
    conn = get_redis_connection()
    return Queue("tasks", connection=conn, is_async=not USE_FAKE_REDIS)
