from sqlalchemy.orm import Session
from app.models.member import Member


class MemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[Member]:
        return self.db.query(Member).all()

    def find_by_id(self, member_id: int) -> Member | None:
        return self.db.query(Member).filter(Member.id == member_id).first()

    def find_by_email(self, email: str) -> Member | None:
        return self.db.query(Member).filter(Member.email == email).first()

    def save(self, member: Member) -> Member:
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def delete(self, member: Member) -> None:
        self.db.delete(member)
        self.db.commit()
