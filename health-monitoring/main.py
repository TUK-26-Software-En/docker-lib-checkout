import asyncio
import os
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

LIBRARY_URL   = os.environ.get("LIBRARY_URL", "http://library-checkout:8000")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "30"))
MAX_HISTORY   = int(os.environ.get("MAX_HISTORY", "20"))

# ── Health check history ──────────────────────────────────────────────────────
history: deque = deque(maxlen=MAX_HISTORY)

# ── Failure tracking state ────────────────────────────────────────────────────
@dataclass
class FailureEvent:
    id: int
    started_at: str
    recovered_at: Optional[str] = None
    duration_seconds: Optional[float] = None


failure_events: list[FailureEvent] = []
monitoring_started_at: Optional[str] = None
_is_currently_failing: bool = False
_failure_start_time: Optional[datetime] = None
_prev_healthy: bool = True  # assume healthy before first poll


# ── Core functions ────────────────────────────────────────────────────────────
async def _fetch_health() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{LIBRARY_URL}/health")
            data = resp.json()
            data["_checked_at"] = checked_at
            data["_http_status"] = resp.status_code
            return data
    except httpx.ConnectError:
        return {"status": "unreachable", "error": "Cannot connect to library-checkout", "_checked_at": checked_at}
    except Exception as e:
        return {"status": "error", "error": str(e), "_checked_at": checked_at}


def _update_failure_tracking(data: dict) -> None:
    global _is_currently_failing, _failure_start_time, _prev_healthy

    now = datetime.now(timezone.utc)
    curr_healthy = data.get("status") == "healthy"

    if _prev_healthy and not curr_healthy:
        # healthy → unhealthy : failure begins
        _is_currently_failing = True
        _failure_start_time = now
        failure_events.append(FailureEvent(
            id=len(failure_events) + 1,
            started_at=now.isoformat(),
        ))

    elif not _prev_healthy and curr_healthy:
        # unhealthy → healthy : recovery
        _is_currently_failing = False
        if failure_events and failure_events[-1].recovered_at is None and _failure_start_time:
            dur = (now - _failure_start_time).total_seconds()
            failure_events[-1].recovered_at = now.isoformat()
            failure_events[-1].duration_seconds = round(dur, 1)
        _failure_start_time = None

    _prev_healthy = curr_healthy


def calculate_metrics() -> dict:
    now = datetime.now(timezone.utc)

    if monitoring_started_at is None:
        return {"status": "not_started"}

    start = datetime.fromisoformat(monitoring_started_at)
    total_time = (now - start).total_seconds()

    # --- downtime ---
    total_downtime = 0.0
    for ev in failure_events:
        if ev.duration_seconds is not None:
            total_downtime += ev.duration_seconds
        elif _is_currently_failing and _failure_start_time and ev.recovered_at is None:
            total_downtime += (now - _failure_start_time).total_seconds()

    total_uptime = max(0.0, total_time - total_downtime)
    availability = max(0.0, min(1.0, total_uptime / total_time)) if total_time > 0 else 1.0
    num_failures = len(failure_events)

    if num_failures == 0:
        return {
            "monitoring_started_at": monitoring_started_at,
            "total_time_seconds": round(total_time),
            "total_uptime_seconds": round(total_uptime),
            "total_downtime_seconds": 0,
            "failure_count": 0,
            "mtbf_seconds": None,
            "mttr_seconds": None,
            "mttf_seconds": None,
            "availability": round(availability, 6),
            "availability_percent": round(availability * 100, 4),
            "is_currently_failing": _is_currently_failing,
            "current_failure_duration_seconds": None,
            "failure_events": [],
        }

    # --- MTTF: avg uptime between (monitoring-start / last-recovery) → next failure ---
    uptime_periods: list[float] = []
    prev = start
    for ev in failure_events:
        fail_at = datetime.fromisoformat(ev.started_at)
        uptime_periods.append(max(0.0, (fail_at - prev).total_seconds()))
        prev = datetime.fromisoformat(ev.recovered_at) if ev.recovered_at else now

    mttf = sum(uptime_periods) / len(uptime_periods) if uptime_periods else None

    # --- MTTR: avg duration of *completed* failures ---
    completed = [ev for ev in failure_events if ev.duration_seconds is not None]
    mttr = (sum(ev.duration_seconds for ev in completed) / len(completed)) if completed else None

    # --- MTBF = MTTF + MTTR ---
    if mttf is not None and mttr is not None:
        mtbf = mttf + mttr
    else:
        mtbf = total_time / num_failures  # fallback estimate

    # --- current failure duration (ongoing) ---
    cur_dur = None
    if _is_currently_failing and _failure_start_time:
        cur_dur = round((now - _failure_start_time).total_seconds(), 1)

    return {
        "monitoring_started_at": monitoring_started_at,
        "total_time_seconds": round(total_time),
        "total_uptime_seconds": round(total_uptime),
        "total_downtime_seconds": round(total_downtime, 1),
        "failure_count": num_failures,
        "mtbf_seconds": round(mtbf, 1),
        "mttr_seconds": round(mttr, 1) if mttr is not None else None,
        "mttf_seconds": round(mttf, 1) if mttf is not None else None,
        "availability": round(availability, 6),
        "availability_percent": round(availability * 100, 4),
        "is_currently_failing": _is_currently_failing,
        "current_failure_duration_seconds": cur_dur,
        "failure_events": [asdict(ev) for ev in failure_events],
    }


# ── Background polling loop ───────────────────────────────────────────────────
async def _poll_loop():
    global monitoring_started_at
    monitoring_started_at = datetime.now(timezone.utc).isoformat()
    while True:
        data = await _fetch_health()
        _update_failure_tracking(data)
        history.append(data)
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_poll_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Library Health Monitor", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "library_url": LIBRARY_URL,
        "poll_interval": POLL_INTERVAL,
        "max_history": MAX_HISTORY,
    })


# ── Status / History ──────────────────────────────────────────────────────────
@app.get("/api/status", response_class=JSONResponse)
async def get_status():
    return JSONResponse(content=history[-1] if history else {"status": "initializing"})


@app.get("/api/history", response_class=JSONResponse)
async def get_history():
    return JSONResponse(content=list(history))


# ── Immediate check (for fault-injection feedback) ────────────────────────────
@app.post("/api/check/now", response_class=JSONResponse)
async def check_now():
    data = await _fetch_health()
    _update_failure_tracking(data)
    history.append(data)
    return JSONResponse(content=data)


# ── Reliability metrics ───────────────────────────────────────────────────────
@app.get("/api/metrics", response_class=JSONResponse)
async def get_metrics():
    return JSONResponse(content=calculate_metrics())


@app.post("/api/monitoring/reset", response_class=JSONResponse)
async def reset_monitoring():
    global monitoring_started_at, _is_currently_failing, _failure_start_time, _prev_healthy
    failure_events.clear()
    history.clear()
    monitoring_started_at = datetime.now(timezone.utc).isoformat()
    _is_currently_failing = False
    _failure_start_time = None
    _prev_healthy = True
    return JSONResponse(content={"message": "모니터링 데이터가 초기화되었습니다.", "started_at": monitoring_started_at})


# ── Fault injection proxy ─────────────────────────────────────────────────────
async def _proxy_post(path: str) -> JSONResponse:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{LIBRARY_URL}{path}")
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=503)


async def _proxy_get(path: str) -> JSONResponse:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{LIBRARY_URL}{path}")
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=503)


@app.post("/api/fault/inject", response_class=JSONResponse)
async def inject_fault():
    return await _proxy_post("/fault/inject")


@app.post("/api/fault/recover", response_class=JSONResponse)
async def recover_fault():
    return await _proxy_post("/fault/recover")


@app.get("/api/fault/status", response_class=JSONResponse)
async def fault_status():
    return await _proxy_get("/fault/status")
