import pytest
from app.services.member_service import MemberService


def test_create_member(db):
    svc = MemberService(db)
    member = svc.create_member("홍길동", "hong@example.com")
    assert member.id is not None
    assert member.name == "홍길동"
    assert member.email == "hong@example.com"


def test_get_member(db):
    svc = MemberService(db)
    created = svc.create_member("홍길동", "hong@example.com")
    found = svc.get_member(created.id)
    assert found.id == created.id


def test_get_member_not_found_raises(db):
    with pytest.raises(ValueError):
        MemberService(db).get_member(9999)


def test_get_all_members(db):
    svc = MemberService(db)
    svc.create_member("홍길동", "hong@example.com")
    svc.create_member("김철수", "kim@example.com")
    assert len(svc.get_all_members()) == 2


def test_create_duplicate_email_raises(db):
    svc = MemberService(db)
    svc.create_member("홍길동", "hong@example.com")
    with pytest.raises(ValueError, match="이미 등록된"):
        svc.create_member("김철수", "hong@example.com")


def test_delete_member(db):
    svc = MemberService(db)
    member = svc.create_member("삭제할 회원", "delete@example.com")
    svc.delete_member(member.id)
    with pytest.raises(ValueError):
        svc.get_member(member.id)
