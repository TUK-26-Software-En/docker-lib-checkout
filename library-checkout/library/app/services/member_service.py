from sqlalchemy.orm import Session
from app.models.member import Member
from app.repositories.member_repository import MemberRepository


class MemberService:
    def __init__(self, db: Session):
        self.repo = MemberRepository(db)

    def get_all_members(self) -> list[Member]:
        return self.repo.find_all()

    def get_member(self, member_id: int) -> Member:
        member = self.repo.find_by_id(member_id)
        if not member:
            raise ValueError(f"회원 ID {member_id}를 찾을 수 없습니다.")
        return member

    def create_member(self, name: str, email: str) -> Member:
        if self.repo.find_by_email(email):
            raise ValueError(f"이미 등록된 이메일입니다: {email}")
        member = Member(name=name, email=email)
        return self.repo.save(member)

    def delete_member(self, member_id: int) -> None:
        member = self.get_member(member_id)
        self.repo.delete(member)
