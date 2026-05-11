# 다이어그램 생성 상세 문서

---

## 1. 사용 라이브러리

### 1.1 pyreverse (pylint 내장)

| 항목 | 내용 |
|------|------|
| 패키지 | `pylint` |
| 설치 | `pip install pylint` |
| 실행 파일 | `.venv/bin/pyreverse` |
| 역할 | Python 소스 코드를 AST로 파싱해 클래스·의존 관계를 `.dot` 파일로 추출 |
| 출력 형식 | DOT (Graphviz), PlantUML |
| 공식 문서 | https://pylint.readthedocs.io/en/latest/pyreverse.html |

**주요 옵션**

| 옵션 | 설명 |
|------|------|
| `--output dot` | DOT 형식으로 출력 |
| `--project <name>` | 출력 파일명 접두사 지정 |
| `--colorized` | 클래스 종류(모델/서비스 등)에 따라 색상 자동 부여 |
| `--only-classnames` | 클래스명만 표시 (속성·메서드 생략) — 미사용 시 전체 표시 |

**적용 범위**

- `app/models/`, `app/services/`, `app/repositories/` 세 패키지를 대상으로 실행
- 출력된 `classes_library.dot`을 graphviz Python 패키지로 PNG 렌더링

---

### 1.2 graphviz (Python 패키지)

| 항목 | 내용 |
|------|------|
| 패키지 | `graphviz` |
| 설치 | `pip install graphviz` |
| 시스템 의존 | Graphviz CLI (`dot`, `neato`) — `apt install graphviz` |
| 역할 | DOT 소스를 받아 PNG/SVG 렌더링, `graphviz.Source` 로 직접 DOT 기술 가능 |
| 공식 문서 | https://graphviz.readthedocs.io |

**주요 API**

```python
import graphviz

# DOT 문자열 직접 렌더링
src = graphviz.Source(dot_string)
src.render(filename="output", format="png", cleanup=True)

# pyreverse 출력 파일 렌더링
src = graphviz.Source(Path("classes_library.dot").read_text())
src.render(filename="class_diagram", format="png", cleanup=True)
```

**사용 레이아웃 엔진**

| 엔진 | 특징 | 적용 다이어그램 |
|------|------|----------------|
| `dot` (기본) | 계층적 TB/LR 레이아웃, rank 정렬 지원 | class, er, layer, package, sequence |
| `neato` | 절대 좌표(`pos`) 기반 자유 배치 | sequence_borrow (lifeline 수동 배치) |

---

## 2. 다이어그램별 구성 방법

### 2.1 class_diagram.png — 클래스 다이어그램

**생성 방식:** pyreverse → DOT → graphviz PNG

```
pyreverse --output dot --project library --colorized \
  app/models app/services app/repositories
→ classes_library.dot
→ graphviz.Source(dot).render("class_diagram", format="png")
```

**표현 내용**

- `Book`, `Member`, `Loan`, `LoanStatus` 도메인 모델 (속성 포함)
- `BookService`, `MemberService`, `LoanService` 서비스 (메서드 시그니처 포함)
- `BookRepository`, `MemberRepository`, `LoanRepository` (메서드 포함)
- 클래스 간 의존 관계(집합, 연관)를 화살표로 표시

**특이사항**

- pyreverse가 Python 타입 어노테이션(`list[Book]`, `Loan | None`)을 읽어 반환 타입까지 표시
- `--colorized` 옵션으로 Service(초록), Repository(파랑), Model(보라) 자동 색상 부여

---

### 2.2 package_diagram.png — 패키지 의존성 다이어그램

**생성 방식:** graphviz DOT 직접 기술 → PNG

> pyreverse로 생성 시 개별 모듈 단위까지 모두 노출되어 엣지 37개 이상 교차,
> 시인성이 매우 나빠지므로 실제 import를 분석해 직접 DOT으로 작성했다.

**import 분석 방법**

```bash
grep -rn "^from app\|^import app" app/ --include="*.py"
```

위 명령으로 추출한 실제 import 관계를 DOT에 반영했다.

**레이아웃 구성 핵심 기법**

| 기법 | 설명 |
|------|------|
| `newrank=true` | 클러스터 내부 노드에도 `rank=same` 적용 가능하게 함 (기본값은 클러스터 경계에서 무시됨) |
| `rank=min` | `main.py`를 항상 최상단에 고정 |
| `rank=max` | `database.py`를 항상 최하단에 고정 |
| `rank=same` | 동일 레이어의 노드를 같은 수평선에 정렬 |
| `subgraph cluster_*` | 레이어를 시각적으로 묶는 배경 박스, `style=filled`로 배경색 적용 |

**엣지 표현 규칙**

| 엣지 종류 | 색상 | 스타일 | 의미 |
|-----------|------|--------|------|
| 실선 (진한) | 레이어 색 | solid, penwidth=1.5 | 주요 의존 (서비스→레포 등) |
| 점선 (회색) | `#888888` | dashed | 부가 의존 (loan_service→book_repo 등) |
| 점선 (연한) | `#AAAAAA` | dashed, open | 모델 직접 import (서비스→모델) |

---

### 2.3 er_diagram.png — ER 다이어그램

**생성 방식:** graphviz DOT 직접 기술 → PNG

> pyreverse는 SQLAlchemy `relationship()`을 ORM 관계로 해석하지 못하므로
> DB 테이블 구조를 직접 DOT으로 작성했다.

**구성 요소**

```dot
node [shape=record]   // 테이블을 레코드 형태로 표현
Book -> Loan          // arrowhead=crow (1:N 관계)
Member -> Loan        // arrowhead=crow (1:N 관계)
```

- `shape=record`의 `{테이블명|컬럼 목록}` 문법으로 테이블 스키마 표현
- `arrowhead=crow`, `arrowtail=none`, `dir=both` 조합으로 IE 표기법(까마귀발 표기) 구현

---

### 2.4 layer_diagram.png — 3 Layer Architecture 다이어그램

**생성 방식:** graphviz DOT 직접 기술 → PNG

**구성 요소**

- `subgraph cluster_*` 3개로 Presentation / Business / Data 계층 표현
- 각 노드에 실제 클래스명 기재 (`BookService`, `LoanRepository` 등)
- `shape=cylinder`로 DB 노드 구분
- `shape=ellipse`로 사용자(Actor) 노드 구분

---

### 2.5 sequence_borrow.png — 시퀀스 다이어그램 (도서 대출)

**생성 방식:** graphviz DOT 직접 기술 (`neato` 엔진, 절대 좌표) → PNG

> pyreverse는 시퀀스 다이어그램을 지원하지 않는다.
> graphviz의 `dot` 엔진은 시퀀스 다이어그램의 교차선 없는 배치가 어려워
> `neato` 엔진 + `pos="x,y!"` 절대 좌표 방식을 사용했다.

**핵심 구성 방식**

```python
actors = ["User", "LoanRouter", "LoanService", "BookRepository", ...]
col_w, row_h = 2.2, 0.7   # 열 간격, 행 간격

# 참가자 헤더 노드: pos="col*col_w, 0!"
# lifeline 포인트 노드: pos="col*col_w, -(row+0.8)*row_h!"
# lifeline 연결: point → point (style=dashed, arrowhead=none)
# 메시지 화살표: L_frm_r → L_to_r (같은 row, 다른 col)
```

**표현 규칙**

| 요소 | 표현 방식 |
|------|----------|
| 참가자(lifeline) | 열 단위 헤더 노드 + 수직 point 노드 체인 |
| lifeline 수직선 | point→point 점선, `arrowhead=none` |
| 요청 메시지 | 실선 화살표 (`style=solid`, `arrowhead=normal`) |
| 반환 메시지 | 점선 화살표 (`style=dashed`, `arrowhead=open`) |

---

## 3. 재생성 방법

```bash
cd library
source .venv/bin/activate
python generate_diagrams.py
```

출력 위치: `docx/diagrams/*.png`

---

## 4. 라이브러리 선택 근거 요약

| 다이어그램 | 선택 방법 | 근거 |
|-----------|----------|------|
| 클래스 | pyreverse + graphviz | 코드 직접 파싱 → 속성·메서드·의존관계 자동 추출 |
| 패키지 | graphviz DOT 직접 기술 | pyreverse는 모듈 단위 노출로 가독성 불량 → import 분석 후 수동 작성 |
| ER | graphviz DOT 직접 기술 | pyreverse가 SQLAlchemy ORM 관계 미해석 |
| 3 Layer | graphviz DOT 직접 기술 | 아키텍처 개념 표현은 코드 추출 불가, 직접 기술이 정확 |
| 시퀀스 | graphviz DOT (neato) 직접 기술 | pyreverse 미지원, neato 절대좌표로 lifeline 구조 구현 |
