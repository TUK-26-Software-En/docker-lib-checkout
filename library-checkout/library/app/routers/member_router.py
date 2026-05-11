from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.member_service import MemberService

router = APIRouter(prefix="/members", tags=["members"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def list_members(request: Request, db: Session = Depends(get_db)):
    members = MemberService(db).get_all_members()
    return templates.TemplateResponse("members/list.html", {"request": request, "members": members, "error": None})


@router.get("/new", response_class=HTMLResponse)
def new_member_form(request: Request):
    return templates.TemplateResponse("members/form.html", {"request": request, "error": None})


@router.post("/new")
def create_member(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        MemberService(db).create_member(name, email)
    except ValueError as e:
        return templates.TemplateResponse("members/form.html", {"request": request, "error": str(e)})
    return RedirectResponse("/members/", status_code=303)


@router.post("/{member_id}/delete")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    MemberService(db).delete_member(member_id)
    return RedirectResponse("/members/", status_code=303)
