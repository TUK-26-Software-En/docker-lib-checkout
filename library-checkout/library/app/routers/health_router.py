import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.state import is_fault_active

router = APIRouter(prefix="/health", tags=["health"])
templates = Jinja2Templates(directory="app/templates")

_start_time = time.time()


@router.post("", response_class=JSONResponse)
def health_check(db: Session = Depends(get_db)):
    if is_fault_active():
        return JSONResponse(content={
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - _start_time),
            "services": {
                "fault_injection": {
                    "status": "unhealthy",
                    "message": "장애 주입 활성화 상태입니다.",
                }
            },
            "statistics": {},
        })

    result = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _start_time),
        "services": {},
        "statistics": {},
    }

    t0 = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        result["services"]["database"] = {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as e:
        result["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        result["status"] = "unhealthy"

    try:
        from app.models.book import Book
        from app.models.member import Member
        from app.models.loan import Loan, LoanStatus

        result["statistics"] = {
            "books_total": db.query(Book).count(),
            "books_available": db.query(Book).filter(Book.available == True).count(),
            "members_total": db.query(Member).count(),
            "active_loans": db.query(Loan).filter(Loan.status == LoanStatus.ACTIVE).count(),
        }
    except Exception as e:
        result["statistics_error"] = str(e)

    return result


@router.get("/ui", response_class=HTMLResponse)
def health_ui(request: Request):
    return templates.TemplateResponse("health/dashboard.html", {"request": request})
