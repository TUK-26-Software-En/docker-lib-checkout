import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.database import engine, Base
import app.models  # noqa: F401 — register all ORM models before create_all
from app.routers import book_router, member_router, loan_router, health_router, fault_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=os.environ.get("APP_TITLE", "도서 대출 관리 시스템"),
    debug=os.environ.get("APP_ENV", "production") == "development",
)

app.include_router(book_router)
app.include_router(member_router)
app.include_router(loan_router)
app.include_router(health_router)
app.include_router(fault_router)


@app.get("/")
def root():
    return RedirectResponse("/books/")
