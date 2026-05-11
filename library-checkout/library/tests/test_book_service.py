import pytest
from app.services.book_service import BookService
from app.services.member_service import MemberService
from app.services.loan_service import LoanService


def test_create_book(db):
    svc = BookService(db)
    book = svc.create_book("파이썬 완전 정복", "김철수", "한빛미디어")
    assert book.id is not None
    assert book.title == "파이썬 완전 정복"
    assert book.author == "김철수"
    assert book.available is True


def test_get_book(db):
    svc = BookService(db)
    created = svc.create_book("테스트 도서", "저자", "출판사")
    found = svc.get_book(created.id)
    assert found.id == created.id
    assert found.title == created.title


def test_get_book_not_found_raises(db):
    with pytest.raises(ValueError):
        BookService(db).get_book(9999)


def test_get_all_books(db):
    svc = BookService(db)
    svc.create_book("도서1", "저자1", "출판사1")
    svc.create_book("도서2", "저자2", "출판사2")
    assert len(svc.get_all_books()) == 2


def test_search_books_by_title(db):
    svc = BookService(db)
    svc.create_book("파이썬 프로그래밍", "김철수", "한빛미디어")
    svc.create_book("자바 프로그래밍", "이영희", "생능출판")
    results = svc.search_books("파이썬")
    assert len(results) == 1
    assert results[0].title == "파이썬 프로그래밍"


def test_search_books_by_author(db):
    svc = BookService(db)
    svc.create_book("도서A", "홍길동", "출판사")
    svc.create_book("도서B", "김철수", "출판사")
    results = svc.search_books("홍길동")
    assert len(results) == 1


def test_update_book(db):
    svc = BookService(db)
    book = svc.create_book("원본 제목", "원본 저자", "원본 출판사")
    updated = svc.update_book(book.id, "수정된 제목", "수정된 저자", "수정된 출판사")
    assert updated.title == "수정된 제목"
    assert updated.author == "수정된 저자"
    assert updated.publisher == "수정된 출판사"


def test_delete_book(db):
    svc = BookService(db)
    book = svc.create_book("삭제할 도서", "저자", "출판사")
    svc.delete_book(book.id)
    with pytest.raises(ValueError):
        svc.get_book(book.id)


def test_delete_loaned_book_raises(db):
    book = BookService(db).create_book("대출중 도서", "저자", "출판사")
    member = MemberService(db).create_member("홍길동", "hong@test.com")
    LoanService(db).borrow_book(member.id, book.id)
    with pytest.raises(ValueError, match="대출 중"):
        BookService(db).delete_book(book.id)
