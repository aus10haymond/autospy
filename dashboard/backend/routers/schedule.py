"""
Schedule router — read and update the in-process async scheduler.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/schedule", tags=["schedule"])


class ScheduleRequest(BaseModel):
    enabled:        bool
    interval_hours: int       = Field(default=24, ge=1, le=8760)
    profile_ids:    list[str] = []   # empty list = run all profiles
    schedule_time:  str       = ""   # "HH:MM" local time, empty = interval-only


@router.get("")
def get_schedule():
    """Return current scheduler status."""
    from dashboard.backend import app_scheduler
    return app_scheduler.get_status()


@router.post("")
async def update_schedule(req: ScheduleRequest):
    """Enable/disable or reconfigure the scheduler. Takes effect immediately."""
    from dashboard.backend import app_scheduler
    await app_scheduler.apply_settings(
        req.enabled, req.interval_hours, req.profile_ids, req.schedule_time
    )
    return app_scheduler.get_status()


@router.post("/run-now")
async def run_now():
    """Fire an immediate run using the current schedule's profile_ids."""
    from dashboard.backend import app_scheduler
    from dashboard.backend.job_manager import list_jobs

    active = [j for j in list_jobs() if j.status in ("pending", "running")]
    if active:
        raise HTTPException(409, f"A run is already in progress (job_id={active[0].job_id})")

    job_id = await app_scheduler.run_now()
    return {"job_id": job_id}
