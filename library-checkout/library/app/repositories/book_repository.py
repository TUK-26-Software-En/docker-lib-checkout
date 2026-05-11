from sqlalchemy.orm import Session
from app.models.book import Book


class BookRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[Book]:
        return self.db.query(Book).all()

    def find_by_id(self, book_id: int) -> Book | None:
        return self.db.query(Book).filter(Book.id == book_id).first()

    def find_by_keyword(self, keyword: str) -> list[Book]:
        pattern = f"%{keyword}%"
        return self.db.query(Book).filter(
            Book.title.like(pattern) | Book.author.like(pattern)
        ).all()

    def save(self, book: Book) -> Book:
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def delete(self, book: Book) -> None:
        self.db.delete(book)
        self.db.commit()
