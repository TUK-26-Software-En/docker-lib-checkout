from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.state import is_fault_active, set_fault

router = APIRouter(prefix="/fault", tags=["fault"])


@router.post("/inject", response_class=JSONResponse)
def inject_fault():
    set_fault(True)
    return {"fault_active": True, "message": "장애가 주입되었습니다."}


@router.post("/recover", response_class=JSONResponse)
def recover_fault():
    set_fault(False)
    return {"fault_active": False, "message": "시스템이 복구되었습니다."}


@router.get("/status", response_class=JSONResponse)
def fault_status():
    return {"fault_active": is_fault_active()}
