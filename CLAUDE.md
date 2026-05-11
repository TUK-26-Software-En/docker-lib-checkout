# 도서 대출 관리 시스템 — Claude 가이드

## 프로젝트 개요
대학교 4학년 1학기 AI 과목 프로젝트. FastAPI + SQLite 기반 도서관 대출 관리 웹 애플리케이션.

## 디렉토리 구조
```
library-checkout/
├── library/                  # 메인 앱 루트 (uvicorn 실행 위치)
│   ├── app/
│   │   ├── main.py           # FastAPI 앱 진입점
│   │   ├── database.py       # SQLAlchemy 엔진/세션/Base
│   │   ├── models/           # ORM 모델 (book, member, loan)
│   │   ├── repositories/     # DB 접근 계층
│   │   ├── services/         # 비즈니스 로직 계층
│   │   ├── routers/          # HTTP 라우터 (FastAPI APIRouter)
│   │   └── templates/        # Jinja2 HTML 템플릿
│   ├── library.db            # SQLite DB 파일
│   └── requirements.txt
└── meterials/                # 강의 자료
    ├── se/                   # 소프트웨어 공학 강의 (1~6장)
    ├── chat1.md
    └── pre_architecture.md
```

## 실행 방법

### Docker (권장)
```bash
# 프로젝트 루트(G:\project\Univ\4-1\ai)에서
docker-compose up --build
# library-checkout → http://localhost:8000
# health-monitoring → http://localhost:8001
```

### 로컬 개발
```bash
cd library-checkout/library
pip install -r requirements.txt
uvicorn app.main:app --reload   # → http://localhost:8000
pytest tests/ -v                # 단위 테스트 실행
```

## 아키텍처 원칙
계층을 엄격히 분리한다: **Router → Service → Repository → Model**

- **Router**: HTTP 요청/응답만 담당. 비즈니스 로직 없음.
- **Service**: 비즈니스 규칙 처리. DB에 직접 접근하지 않음.
- **Repository**: DB 쿼리만 담당. `find_*`, `save`, `delete` 메서드 패턴 사용.
- **Model**: SQLAlchemy ORM 정의만. 로직 없음.

## 도메인 모델
| 클래스 | 테이블 | 핵심 필드 |
|--------|--------|-----------|
| `Book` | `books` | `id`, `title`, `author`, `publisher`, `available: bool` |
| `Member` | `members` | `id`, `name`, `email (unique)` |
| `Loan` | `loans` | `id`, `book_id`, `member_id`, `loan_date`, `return_date`, `status: ACTIVE\|RETURNED` |

## 비즈니스 규칙
- 대출(`borrow_book`): `book.available=True`인 경우만 가능 → 대출 후 `available=False`
- 반납(`return_book`): `status=ACTIVE`인 경우만 가능 → `available=True` 복원
- 도서 삭제: `available=False`(대출 중)이면 불가

## 코드 컨벤션
- 에러는 `ValueError`로 발생시키고 router에서 catch하여 템플릿에 `error` 변수로 전달
- DB 세션은 `Depends(get_db)`로 주입
- 새 모델 추가 시 `app/models/__init__.py`에 import 등록 필요 (Base.metadata.create_all 트리거)
- 템플릿 경로: `app/templates/{도메인}/{list|form|...}.html`

## Docker 컨테이너 구성 (3개)
| 컨테이너 | 이미지/빌드 | 포트 | 역할 |
|----------|------------|------|------|
| `library-postgres` | postgres:16-alpine | 내부 only | PostgreSQL DB |
| `library-checkout` | ./library-checkout/library | 8000 | FastAPI 앱 + 단위 테스트 실행 후 기동 |
| `health-monitoring` | ./health-monitoring | 8001 | library-checkout 헬스 모니터링 대시보드 |

- 시작 순서: postgres → library-checkout (tests 통과 후) → health-monitoring
- `library-checkout` 기동 시 `entrypoint.sh`가 pytest 실행 → 통과하면 uvicorn 기동

## Health Check 엔드포인트
| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `POST /health` | POST | JSON으로 DB·통계 상태 반환 (REST API) |
| `GET /health/ui` | GET | 웹 헬스 대시보드 (library-checkout 내장) |
| `GET /` (port 8001) | GET | health-monitoring 모니터링 대시보드 |
| `GET /api/status` (port 8001) | GET | 최신 헬스 데이터 JSON |
| `GET /api/history` (port 8001) | GET | 최근 20건 이력 JSON |

## 단위 테스트 구조 (tests/)
- SQLite in-memory 사용 (PostgreSQL 불필요)
- `conftest.py`: `db` fixture (각 테스트마다 새 in-memory DB)
- `test_book_service.py`: 도서 CRUD + 대출 중 삭제 방지
- `test_member_service.py`: 회원 CRUD + 중복 이메일
- `test_loan_service.py`: 대출/반납 + 예외 케이스

## 기술 스택 버전
- Python 3.11+
- FastAPI 0.115.5 / uvicorn 0.32.1
- SQLAlchemy 2.0.36 (DeclarativeBase, `db.query()` 스타일)
- PostgreSQL 16 (Docker), SQLite (로컬/테스트)
- psycopg2-binary 2.9.10
- Jinja2 3.1.4
- pytest 8.3.4 / httpx 0.28.1
