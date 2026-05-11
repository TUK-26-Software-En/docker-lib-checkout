from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.loan_service import LoanService
from app.services.book_service import BookService
from app.services.member_service import MemberService

router = APIRouter(prefix="/loans", tags=["loans"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def list_loans(request: Request, db: Session = Depends(get_db)):
    loans = LoanService(db).get_all_loans()
    return templates.TemplateResponse("loans/list.html", {"request": request, "loans": loans, "error": None})


@router.get("/new", response_class=HTMLResponse)
def new_loan_form(request: Request, db: Session = Depends(get_db)):
    books = [b for b in BookService(db).get_all_books() if b.available]
    members = MemberService(db).get_all_members()
    return templates.TemplateResponse("loans/form.html", {
        "request": request, "books": books, "members": members, "error": None
    })


@router.post("/new")
def borrow_book(
    request: Request,
    member_id: int = Form(...),
    book_id: int = Form(...),
    db: Session = Depends(get_db),
):
    try:
        LoanService(db).borrow_book(member_id, book_id)
    except ValueError as e:
        books = [b for b in BookService(db).get_all_books() if b.available]
        members = MemberService(db).get_all_members()
        return templates.TemplateResponse("loans/form.html", {
            "request": request, "books": books, "members": members, "error": str(e)
        })
    return RedirectResponse("/loans/", status_code=303)


@router.post("/{loan_id}/return")
def return_book(loan_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        LoanService(db).return_book(loan_id)
    except ValueError as e:
        loans = LoanService(db).get_all_loans()
        return templates.TemplateResponse("loans/list.html", {
            "request": request, "loans": loans, "error": str(e)
        })
    return RedirectResponse("/loans/", status_code=303)
