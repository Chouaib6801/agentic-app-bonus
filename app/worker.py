"""
RQ Worker for processing research jobs.
Run with: python -m app.worker
"""

import os
from redis import Redis
from rq import Worker, Queue, Connection

# Redis connection configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def run_worker():
    """Start the RQ worker to process jobs."""
    redis_conn = Redis.from_url(REDIS_URL)
    
    # Listen on the tasks queue
    queues = [Queue("tasks", connection=redis_conn)]
    
    print("Starting worker...")
    print(f"Connected to Redis at {REDIS_URL}")
    print("Listening on queue: tasks")
    
    worker = Worker(queues, connection=redis_conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    run_worker()

