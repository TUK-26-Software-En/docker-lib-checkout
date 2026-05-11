from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["books"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def list_books(request: Request, keyword: str = "", db: Session = Depends(get_db)):
    service = BookService(db)
    books = service.search_books(keyword) if keyword else service.get_all_books()
    return templates.TemplateResponse("books/list.html", {
        "request": request, "books": books, "keyword": keyword
    })


@router.get("/new", response_class=HTMLResponse)
def new_book_form(request: Request):
    return templates.TemplateResponse("books/form.html", {"request": request, "book": None, "error": None})


@router.post("/new")
def create_book(
    title: str = Form(...),
    author: str = Form(...),
    publisher: str = Form(...),
    db: Session = Depends(get_db),
):
    BookService(db).create_book(title, author, publisher)
    return RedirectResponse("/books/", status_code=303)


@router.get("/{book_id}/edit", response_class=HTMLResponse)
def edit_book_form(book_id: int, request: Request, db: Session = Depends(get_db)):
    book = BookService(db).get_book(book_id)
    return templates.TemplateResponse("books/form.html", {"request": request, "book": book, "error": None})


@router.post("/{book_id}/edit")
def update_book(
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    publisher: str = Form(...),
    db: Session = Depends(get_db),
):
    BookService(db).update_book(book_id, title, author, publisher)
    return RedirectResponse("/books/", status_code=303)


@router.post("/{book_id}/delete")
def delete_book(book_id: int, request: Request, db: Session = Depends(get_db)):
    service = BookService(db)
    try:
        service.delete_book(book_id)
    except ValueError as e:
        books = service.get_all_books()
        return templates.TemplateResponse("books/list.html", {
            "request": request, "books": books, "keyword": "", "error": str(e)
        })
    return RedirectResponse("/books/", status_code=303)
