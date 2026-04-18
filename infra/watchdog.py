"""Watchdog service for system health monitoring."""

import logging
from datetime import datetime, timedelta, timezone

from db.runs import list_runs, transition_run

LOGGER = logging.getLogger("infra.watchdog")

STALE_THRESHOLD = timedelta(minutes=10)

def cleanup_stale_runs() -> int:
    """Find and fail runs stuck in 'pending' or 'running' for too long.
    
    Returns:
        Number of runs cleaned up.
    """
    now = datetime.now(timezone.utc)
    stale_count = 0
    
    runs = list_runs()
    for run in runs:
        if run.status in ("pending", "running"):
            # Check if the run has been updated recently
            # updated_at is refreshed on every state transition
            elapsed = now - run.updated_at
            if elapsed > STALE_THRESHOLD:
                LOGGER.warning(
                    f"Cleaning up stale run {run.run_id} (status: {run.status}, elapsed: {elapsed})"
                )
                try:
                    transition_run(run.run_id, "failed", error_code="AE-SYS-001")
                    stale_count += 1
                except Exception as e:
                    LOGGER.error(f"Failed to cleanup run {run.run_id}: {e}")
                    
    if stale_count > 0:
        LOGGER.info(f"Watchdog cleanup complete. Resolved {stale_count} stale runs.")
    
    return stale_count
