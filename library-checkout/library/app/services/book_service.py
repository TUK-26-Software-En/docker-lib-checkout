from sqlalchemy.orm import Session
from app.models.book import Book
from app.repositories.book_repository import BookRepository


class BookService:
    def __init__(self, db: Session):
        self.repo = BookRepository(db)

    def get_all_books(self) -> list[Book]:
        return self.repo.find_all()

    def get_book(self, book_id: int) -> Book:
        book = self.repo.find_by_id(book_id)
        if not book:
            raise ValueError(f"도서 ID {book_id}를 찾을 수 없습니다.")
        return book

    def search_books(self, keyword: str) -> list[Book]:
        return self.repo.find_by_keyword(keyword)

    def create_book(self, title: str, author: str, publisher: str) -> Book:
        book = Book(title=title, author=author, publisher=publisher, available=True)
        return self.repo.save(book)

    def update_book(self, book_id: int, title: str, author: str, publisher: str) -> Book:
        book = self.get_book(book_id)
        book.title = title
        book.author = author
        book.publisher = publisher
        return self.repo.save(book)

    def delete_book(self, book_id: int) -> None:
        book = self.get_book(book_id)
        if not book.available:
            raise ValueError("대출 중인 도서는 삭제할 수 없습니다.")
        self.repo.delete(book)
