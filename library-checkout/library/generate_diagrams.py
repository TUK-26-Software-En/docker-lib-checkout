"""
pyreverse(pylint) + graphviz 를 사용해 코드 기반 UML 다이어그램을 생성한다.

생성 대상:
  1. class_diagram.png       — 전체 클래스 다이어그램 (models + services + repositories)
  2. package_diagram.png     — 패키지(모듈) 의존성 (구버전)
  3. er_diagram.png          — SQLAlchemy ORM 모델 ER 다이어그램
  4. layer_diagram.png       — 3-계층 구조 (구버전)
  5. sequence_borrow.png     — 도서 대출 시퀀스
  6. package_diagram_v2.png  — 패키지 의존성 (health/fault/state 포함)
  7. layer_diagram_v2.png    — 3-계층 구조 (PostgreSQL·health/fault 포함)
  8. container_diagram.png   — Docker 3-컨테이너 아키텍처
  9. sequence_fault.png      — 장애 주입 시퀀스
"""

import subprocess
import sys
from pathlib import Path
import graphviz

ROOT = Path(__file__).parent
APP = ROOT / "app"
OUT = ROOT / "docx" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

_venv_pyreverse = ROOT / ".venv" / "bin" / "pyreverse"
PYREVERSE = _venv_pyreverse if _venv_pyreverse.exists() else Path("pyreverse")


# ── 1. pyreverse: Class Diagram ───────────────────────────────────────────────

def run_pyreverse_class():
    """models / services / repositories 대상 클래스 다이어그램"""
    targets = [
        str(APP / "models"),
        str(APP / "services"),
        str(APP / "repositories"),
    ]
    result = subprocess.run(
        [
            str(PYREVERSE),
            "--output", "dot",
            "--project", "library",
            "--colorized",
            *targets,
        ],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    if result.returncode != 0:
        print("[WARN] pyreverse stderr:", result.stderr[:300])

    dot_path = ROOT / "classes_library.dot"
    if not dot_path.exists():
        print("[ERROR] classes_library.dot 생성 실패")
        print(result.stdout, result.stderr)
        return

    src = graphviz.Source(dot_path.read_text())
    src.render(
        filename=str(OUT / "class_diagram"),
        format="png",
        cleanup=True,
    )
    dot_path.unlink(missing_ok=True)
    print(f"[OK] class_diagram.png → {OUT / 'class_diagram.png'}")


# ── 2. pyreverse: Package Diagram ─────────────────────────────────────────────

def run_package_diagram():
    """
    실제 import 관계를 기반으로 패키지 다이어그램을 작성한다.
    pyreverse 는 개별 모듈까지 모두 노출해 엣지가 교차하므로,
    graphviz DOT 로 직접 기술한다.

    레이어 구성 (TB):
      main (rank=min)
      Presentation : routers
      Business     : services
      Data         : repositories / models
      database.py  (rank=max)
    """
    dot_src = r"""
digraph PackageDiagram {
    graph [rankdir=TB, newrank=true, fontname="Helvetica",
           nodesep=0.55, ranksep=0.85, pad=0.5]
    node  [fontname="Helvetica", fontsize=11, style="filled,rounded",
           shape=box, width=1.65, height=0.42]
    edge  [fontname="Helvetica", fontsize=9]

    main     [label="main.py",     fillcolor="#D5D8DC"]
    database [label="database.py", fillcolor="#BFC9CA", shape=cylinder, height=0.6]

    subgraph cluster_routers {
        label="app.routers  ·  Presentation Layer"
        style=filled; fillcolor="#D6EAF8"; color="#2471A3"; penwidth=2
        fontcolor="#1A5276"; fontname="Helvetica Bold"; fontsize=11
        book_router   [label="book_router",   fillcolor="#AED6F1"]
        member_router [label="member_router", fillcolor="#AED6F1"]
        loan_router   [label="loan_router",   fillcolor="#AED6F1"]
    }

    subgraph cluster_services {
        label="app.services  ·  Business Layer"
        style=filled; fillcolor="#D5F5E3"; color="#1E8449"; penwidth=2
        fontcolor="#1D6A3F"; fontname="Helvetica Bold"; fontsize=11
        book_service   [label="book_service",   fillcolor="#A9DFBF"]
        member_service [label="member_service", fillcolor="#A9DFBF"]
        loan_service   [label="loan_service",   fillcolor="#A9DFBF"]
    }

    subgraph cluster_repos {
        label="app.repositories  ·  Data Layer"
        style=filled; fillcolor="#FDEBD0"; color="#CA6F1E"; penwidth=2
        fontcolor="#784212"; fontname="Helvetica Bold"; fontsize=11
        book_repo   [label="book_repository",   fillcolor="#FAD7A0"]
        member_repo [label="member_repository", fillcolor="#FAD7A0"]
        loan_repo   [label="loan_repository",   fillcolor="#FAD7A0"]
    }

    subgraph cluster_models {
        label="app.models  ·  Data Layer"
        style=filled; fillcolor="#FDEDEC"; color="#B03A2E"; penwidth=2
        fontcolor="#7B241C"; fontname="Helvetica Bold"; fontsize=11
        book_model   [label="book.py",   fillcolor="#F1948A"]
        member_model [label="member.py", fillcolor="#F1948A"]
        loan_model   [label="loan.py",   fillcolor="#F1948A"]
    }

    { rank=min;  main }
    { rank=same; book_router; member_router; loan_router }
    { rank=same; book_service; member_service; loan_service }
    { rank=same; book_repo; member_repo; loan_repo }
    { rank=same; book_model; member_model; loan_model }
    { rank=max;  database }

    main -> book_router    [style=dashed, color="#888888", arrowhead=open]
    main -> member_router  [style=dashed, color="#888888", arrowhead=open]
    main -> loan_router    [style=dashed, color="#888888", arrowhead=open]

    book_router   -> book_service   [color="#2471A3", penwidth=1.5]
    member_router -> member_service [color="#2471A3", penwidth=1.5]
    loan_router   -> loan_service   [color="#2471A3", penwidth=1.5]
    loan_router   -> book_service   [color="#888888", style=dashed]
    loan_router   -> member_service [color="#888888", style=dashed]

    book_service   -> book_repo   [color="#1E8449", penwidth=1.5]
    member_service -> member_repo [color="#1E8449", penwidth=1.5]
    loan_service   -> loan_repo   [color="#1E8449", penwidth=1.5]
    loan_service   -> book_repo   [color="#888888", style=dashed]
    loan_service   -> member_repo [color="#888888", style=dashed]

    book_service   -> book_model   [color="#AAAAAA", style=dashed, arrowhead=open]
    member_service -> member_model [color="#AAAAAA", style=dashed, arrowhead=open]
    loan_service   -> loan_model   [color="#AAAAAA", style=dashed, arrowhead=open]

    book_repo   -> book_model   [color="#CA6F1E", penwidth=1.5]
    member_repo -> member_model [color="#CA6F1E", penwidth=1.5]
    loan_repo   -> loan_model   [color="#CA6F1E", penwidth=1.5]

    book_model   -> database [color="#B03A2E", penwidth=1.5]
    member_model -> database [color="#B03A2E", penwidth=1.5]
    loan_model   -> database [color="#B03A2E", penwidth=1.5]
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "package_diagram"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] package_diagram.png → {OUT / 'package_diagram.png'}")


# ── 3. graphviz: ER Diagram (SQLAlchemy 모델 수동 반영) ──────────────────────

def run_er_diagram():
    """
    SQLAlchemy ORM 모델 3개(Book / Member / Loan)의 관계를
    graphviz DOT로 직접 기술해 ER 다이어그램을 생성한다.
    pyreverse는 ORM 관계를 해석하지 못하므로 별도로 작성한다.
    """
    dot_src = """
digraph ER {
    graph [rankdir=LR, fontname="Helvetica", splines=ortho]
    node  [shape=record, fontname="Helvetica", fontsize=11]
    edge  [fontname="Helvetica", fontsize=10]

    Book [label="{Book|id : INTEGER PK\\ltitle : VARCHAR\\lauthor : VARCHAR\\lpublisher : VARCHAR\\lavailable : BOOLEAN\\l}"]
    Member [label="{Member|id : INTEGER PK\\lname : VARCHAR\\lemail : VARCHAR UNIQUE\\l}"]
    Loan [label="{Loan|id : INTEGER PK\\lbook_id : INTEGER FK\\lmember_id : INTEGER FK\\lloan_date : DATE\\lreturn_date : DATE\\lstatus : ENUM(ACTIVE,RETURNED)\\l}"]

    Book -> Loan [label="1 : N", arrowhead=crow, arrowtail=none, dir=both]
    Member -> Loan [label="1 : N", arrowhead=crow, arrowtail=none, dir=both]
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "er_diagram"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] er_diagram.png → {OUT / 'er_diagram.png'}")


# ── 4. graphviz: 3 Layer Architecture Diagram ────────────────────────────────

def run_layer_diagram():
    dot_src = """
digraph LayerArch {
    graph [rankdir=TB, fontname="Helvetica", splines=ortho, nodesep=0.5]
    node  [fontname="Helvetica", fontsize=11, style=filled]
    edge  [fontname="Helvetica", fontsize=10]

    subgraph cluster_presentation {
        label="Presentation Layer"
        style=filled; fillcolor="#D6EAF8"
        Templates [label="Jinja2 Templates\\n(View)", fillcolor="#AED6F1"]
        Routers   [label="book_router\\nmember_router\\nloan_router", fillcolor="#AED6F1"]
    }

    subgraph cluster_business {
        label="Business Layer"
        style=filled; fillcolor="#D5F5E3"
        BookSvc   [label="BookService",   fillcolor="#A9DFBF"]
        MemberSvc [label="MemberService", fillcolor="#A9DFBF"]
        LoanSvc   [label="LoanService",   fillcolor="#A9DFBF"]
    }

    subgraph cluster_data {
        label="Data Layer"
        style=filled; fillcolor="#FDEBD0"
        BookRepo   [label="BookRepository",   fillcolor="#FAD7A0"]
        MemberRepo [label="MemberRepository", fillcolor="#FAD7A0"]
        LoanRepo   [label="LoanRepository",   fillcolor="#FAD7A0"]
        DB         [label="SQLite DB", shape=cylinder, fillcolor="#E59866"]
    }

    User [label="User / Admin", shape=ellipse, fillcolor="#D7BDE2"]

    User     -> Templates
    Templates -> Routers
    Routers  -> BookSvc
    Routers  -> MemberSvc
    Routers  -> LoanSvc
    BookSvc   -> BookRepo
    MemberSvc -> MemberRepo
    LoanSvc   -> BookRepo
    LoanSvc   -> MemberRepo
    LoanSvc   -> LoanRepo
    BookRepo   -> DB
    MemberRepo -> DB
    LoanRepo   -> DB
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "layer_diagram"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] layer_diagram.png → {OUT / 'layer_diagram.png'}")


# ── 5. graphviz: Sequence Diagram (대출 흐름) ─────────────────────────────────

def run_sequence_diagram():
    """
    graphviz로 시퀀스 다이어그램을 표현한다.
    참가자(lifeline)를 열로, 각 메시지를 행(rank)으로 배치해
    UML 시퀀스 다이어그램과 유사한 레이아웃을 구성한다.
    """
    actors = ["User", "LoanRouter", "LoanService", "BookRepository", "LoanRepository", "SQLite_DB"]
    labels = {
        "User":           "User",
        "LoanRouter":     "LoanRouter",
        "LoanService":    "LoanService",
        "BookRepository": "BookRepository",
        "LoanRepository": "LoanRepository",
        "SQLite_DB":      "SQLite DB",
    }
    colors = {
        "User":           "#D7BDE2",
        "LoanRouter":     "#AED6F1",
        "LoanService":    "#A9DFBF",
        "BookRepository": "#FAD7A0",
        "LoanRepository": "#FAD7A0",
        "SQLite_DB":      "#F9E79F",
    }

    messages = [
        ("User",           "LoanRouter",     "POST /loans/new\\n(member_id, book_id)", False),
        ("LoanRouter",     "LoanService",    "borrow_book(member_id, book_id)", False),
        ("LoanService",    "BookRepository", "find_by_id(book_id)", False),
        ("BookRepository", "SQLite_DB",      "SELECT * FROM books", False),
        ("SQLite_DB",      "BookRepository", "Book", True),
        ("BookRepository", "LoanService",    "Book", True),
        ("LoanService",    "BookRepository", "save(book, available=False)", False),
        ("BookRepository", "SQLite_DB",      "UPDATE books SET available=0", False),
        ("LoanService",    "LoanRepository", "save(Loan, status=ACTIVE)", False),
        ("LoanRepository", "SQLite_DB",      "INSERT INTO loans", False),
        ("LoanService",    "LoanRouter",     "Loan", True),
        ("LoanRouter",     "User",           "303 Redirect /loans/", True),
    ]

    # 열 위치
    col = {a: i for i, a in enumerate(actors)}
    n_cols = len(actors)
    n_rows = len(messages)
    col_w, row_h = 2.2, 0.7

    lines = ['digraph Seq {']
    lines += ['  graph [rankdir=TB, splines=false, nodesep=0, ranksep=0, pad=0.4]']
    lines += ['  node  [shape=box, style=filled, fontname="Helvetica", fontsize=10]']
    lines += ['  edge  [fontname="Helvetica", fontsize=9]']

    # ── 헤더 노드 ──────────────────────────────────────────────
    for a in actors:
        x = col[a] * col_w
        lines.append(
            f'  H_{a} [label="{labels[a]}", fillcolor="{colors[a]}",'
            f' pos="{x},0!", width=1.8, height=0.5]'
        )

    # ── lifeline 점선 ──────────────────────────────────────────
    for a in actors:
        x = col[a] * col_w
        for r in range(n_rows + 1):
            y = -(r + 0.8) * row_h
            lines.append(
                f'  L_{a}_{r} [shape=point, width=0.01, style=invis,'
                f' pos="{x},{y}!"]'
            )
        # lifeline edge (점선)
        for r in range(n_rows):
            lines.append(
                f'  L_{a}_{r} -> L_{a}_{r+1}'
                f' [style=dashed, arrowhead=none, color="#AAAAAA"]'
            )

    # ── 메시지 화살표 ──────────────────────────────────────────
    for r, (frm, to, lbl, ret) in enumerate(messages):
        style = 'dashed' if ret else 'solid'
        arrow = 'open' if ret else 'normal'
        lines.append(
            f'  L_{frm}_{r} -> L_{to}_{r}'
            f' [label="{lbl}", style={style}, arrowhead={arrow},'
            f' color="{"#555555" if ret else "#1A5276"}"]'
        )

    lines.append('}')
    dot_src = '\n'.join(lines)

    src = graphviz.Source(dot_src, engine="neato")
    src.render(
        filename=str(OUT / "sequence_borrow"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] sequence_borrow.png → {OUT / 'sequence_borrow.png'}")


# ── 6. graphviz: Package Diagram v2 (health/fault/state 포함) ─────────────────

def run_package_diagram_v2():
    """
    health_router, fault_router, state.py 가 추가된 최신 패키지 의존성 다이어그램.
    """
    dot_src = r"""
digraph PackageDiagramV2 {
    graph [rankdir=TB, newrank=true, fontname="Helvetica",
           nodesep=0.55, ranksep=0.9, pad=0.5]
    node  [fontname="Helvetica", fontsize=11, style="filled,rounded",
           shape=box, width=1.8, height=0.42]
    edge  [fontname="Helvetica", fontsize=9]

    main     [label="main.py",     fillcolor="#D5D8DC"]
    database [label="database.py", fillcolor="#BFC9CA", shape=cylinder, height=0.6]
    state    [label="state.py\n(fault flag)", fillcolor="#F9E79F", shape=note]

    subgraph cluster_routers {
        label="app.routers  ·  Presentation Layer"
        style=filled; fillcolor="#D6EAF8"; color="#2471A3"; penwidth=2
        fontcolor="#1A5276"; fontname="Helvetica Bold"; fontsize=11
        book_router   [label="book_router",   fillcolor="#AED6F1"]
        member_router [label="member_router", fillcolor="#AED6F1"]
        loan_router   [label="loan_router",   fillcolor="#AED6F1"]
        health_router [label="health_router", fillcolor="#85C1E9"]
        fault_router  [label="fault_router",  fillcolor="#85C1E9"]
    }

    subgraph cluster_services {
        label="app.services  ·  Business Layer"
        style=filled; fillcolor="#D5F5E3"; color="#1E8449"; penwidth=2
        fontcolor="#1D6A3F"; fontname="Helvetica Bold"; fontsize=11
        book_service   [label="book_service",   fillcolor="#A9DFBF"]
        member_service [label="member_service", fillcolor="#A9DFBF"]
        loan_service   [label="loan_service",   fillcolor="#A9DFBF"]
    }

    subgraph cluster_repos {
        label="app.repositories  ·  Data Layer"
        style=filled; fillcolor="#FDEBD0"; color="#CA6F1E"; penwidth=2
        fontcolor="#784212"; fontname="Helvetica Bold"; fontsize=11
        book_repo   [label="book_repository",   fillcolor="#FAD7A0"]
        member_repo [label="member_repository", fillcolor="#FAD7A0"]
        loan_repo   [label="loan_repository",   fillcolor="#FAD7A0"]
    }

    subgraph cluster_models {
        label="app.models  ·  Data Layer"
        style=filled; fillcolor="#FDEDEC"; color="#B03A2E"; penwidth=2
        fontcolor="#7B241C"; fontname="Helvetica Bold"; fontsize=11
        book_model   [label="book.py",   fillcolor="#F1948A"]
        member_model [label="member.py", fillcolor="#F1948A"]
        loan_model   [label="loan.py",   fillcolor="#F1948A"]
    }

    { rank=min;  main }
    { rank=same; book_router; member_router; loan_router; health_router; fault_router }
    { rank=same; book_service; member_service; loan_service }
    { rank=same; book_repo; member_repo; loan_repo }
    { rank=same; book_model; member_model; loan_model }
    { rank=max;  database }

    main -> book_router    [style=dashed, color="#888888", arrowhead=open]
    main -> member_router  [style=dashed, color="#888888", arrowhead=open]
    main -> loan_router    [style=dashed, color="#888888", arrowhead=open]
    main -> health_router  [style=dashed, color="#2471A3", arrowhead=open]
    main -> fault_router   [style=dashed, color="#2471A3", arrowhead=open]

    book_router   -> book_service   [color="#2471A3", penwidth=1.5]
    member_router -> member_service [color="#2471A3", penwidth=1.5]
    loan_router   -> loan_service   [color="#2471A3", penwidth=1.5]
    loan_router   -> book_service   [color="#888888", style=dashed]
    loan_router   -> member_service [color="#888888", style=dashed]
    health_router -> database       [color="#2471A3", penwidth=1.5, label="SELECT 1"]
    health_router -> state          [color="#E67E22", penwidth=1.5]
    fault_router  -> state          [color="#E67E22", penwidth=1.5]

    book_service   -> book_repo   [color="#1E8449", penwidth=1.5]
    member_service -> member_repo [color="#1E8449", penwidth=1.5]
    loan_service   -> loan_repo   [color="#1E8449", penwidth=1.5]
    loan_service   -> book_repo   [color="#888888", style=dashed]
    loan_service   -> member_repo [color="#888888", style=dashed]

    book_repo   -> book_model   [color="#CA6F1E", penwidth=1.5]
    member_repo -> member_model [color="#CA6F1E", penwidth=1.5]
    loan_repo   -> loan_model   [color="#CA6F1E", penwidth=1.5]

    book_model   -> database [color="#B03A2E", penwidth=1.5]
    member_model -> database [color="#B03A2E", penwidth=1.5]
    loan_model   -> database [color="#B03A2E", penwidth=1.5]
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "package_diagram_v2"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] package_diagram_v2.png → {OUT / 'package_diagram_v2.png'}")


# ── 7. graphviz: Layer Diagram v2 (PostgreSQL·health/fault 포함) ──────────────

def run_layer_diagram_v2():
    dot_src = """
digraph LayerArchV2 {
    graph [rankdir=TB, fontname="Helvetica", nodesep=0.5, ranksep=0.7]
    node  [fontname="Helvetica", fontsize=11, style=filled]
    edge  [fontname="Helvetica", fontsize=10]

    subgraph cluster_presentation {
        label="Presentation Layer"
        style=filled; fillcolor="#D6EAF8"
        Templates   [label="Jinja2 Templates\\n(View)", fillcolor="#AED6F1"]
        Routers     [label="book_router\\nmember_router\\nloan_router", fillcolor="#AED6F1"]
        HealthFault [label="health_router\\nfault_router", fillcolor="#85C1E9"]
    }

    subgraph cluster_business {
        label="Business Layer"
        style=filled; fillcolor="#D5F5E3"
        BookSvc   [label="BookService",   fillcolor="#A9DFBF"]
        MemberSvc [label="MemberService", fillcolor="#A9DFBF"]
        LoanSvc   [label="LoanService",   fillcolor="#A9DFBF"]
    }

    subgraph cluster_data {
        label="Data Layer"
        style=filled; fillcolor="#FDEBD0"
        BookRepo   [label="BookRepository",   fillcolor="#FAD7A0"]
        MemberRepo [label="MemberRepository", fillcolor="#FAD7A0"]
        LoanRepo   [label="LoanRepository",   fillcolor="#FAD7A0"]
        StateMod   [label="state.py\\n(fault flag)", fillcolor="#F9E79F", shape=note]
        DB         [label="PostgreSQL 16", shape=cylinder, fillcolor="#E59866"]
    }

    User    [label="Browser / Admin", shape=ellipse, fillcolor="#D7BDE2"]
    Monitor [label="health-monitoring\\n(external container)", shape=ellipse, fillcolor="#E8DAEF"]

    User    -> Templates
    Monitor -> HealthFault  [style=dashed, label="POST /health\\nGET /fault/status"]
    Templates -> Routers
    Routers  -> BookSvc
    Routers  -> MemberSvc
    Routers  -> LoanSvc
    HealthFault -> StateMod [color="#E67E22", penwidth=1.5]
    HealthFault -> DB       [color="#2471A3", style=dashed]
    BookSvc   -> BookRepo
    MemberSvc -> MemberRepo
    LoanSvc   -> BookRepo
    LoanSvc   -> MemberRepo
    LoanSvc   -> LoanRepo
    BookRepo   -> DB
    MemberRepo -> DB
    LoanRepo   -> DB
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "layer_diagram_v2"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] layer_diagram_v2.png → {OUT / 'layer_diagram_v2.png'}")


# ── 8. graphviz: Container Architecture Diagram ───────────────────────────────

def run_container_diagram():
    """
    Docker Compose 3-컨테이너 아키텍처를 graphviz DOT으로 직접 기술한다.
    """
    dot_src = """
digraph ContainerArch {
    graph [rankdir=TB, fontname="Helvetica",
           nodesep=0.8, ranksep=1.0, pad=0.6]
    node  [fontname="Helvetica", fontsize=11, style="filled,rounded", shape=box]
    edge  [fontname="Helvetica", fontsize=10]

    // ── 외부 접근 ──
    browser [label="Browser\\n/ Admin", shape=ellipse,
             fillcolor="#D7BDE2", style=filled]

    // ── library-net 내부 ──

    subgraph cluster_net {
        label="Docker Network: library-net  (bridge)"
        style=filled; fillcolor="#F0F3F4"; color="#5D6D7E"; penwidth=2.5

        subgraph cluster_monitor {
            label="health-monitoring  ·  :8001"
            style=filled; fillcolor="#D6EAF8"; color="#2471A3"; penwidth=2
            fontcolor="#1A5276"
            mon_app   [label="FastAPI\\nmain.py", fillcolor="#AED6F1"]
            mon_tmpl  [label="dashboard.html\\n(3-tab UI)", fillcolor="#AED6F1"]
            mon_poll  [label="asyncio\\npoll loop (30s)", fillcolor="#85C1E9", shape=ellipse]
        }

        subgraph cluster_checkout {
            label="library-checkout  ·  :8000"
            style=filled; fillcolor="#D5F5E3"; color="#1E8449"; penwidth=2
            fontcolor="#1D6A3F"
            co_app    [label="FastAPI\\nmain.py", fillcolor="#A9DFBF"]
            co_pytest [label="pytest\\n(startup)", fillcolor="#58D68D", shape=ellipse]
            co_state  [label="state.py\\n(fault flag)", fillcolor="#F9E79F", shape=note]
        }

        subgraph cluster_pg {
            label="library-postgres  ·  :5432"
            style=filled; fillcolor="#FDEBD0"; color="#CA6F1E"; penwidth=2
            fontcolor="#784212"
            pg_db  [label="PostgreSQL 16\\n(library)", shape=cylinder, fillcolor="#FAD7A0"]
            pg_vol [label="postgres_data\\n(named volume)", shape=note, fillcolor="#FDEBD0"]
        }
    }

    // ── 포트 노출 ──
    browser -> mon_app  [label=":8001", color="#2471A3", penwidth=1.5]
    browser -> co_app   [label=":8000", color="#1E8449", penwidth=1.5]

    // ── 컨테이너 간 통신 ──
    mon_poll -> co_app  [label="POST /health\\n(30s)", color="#2471A3", penwidth=1.5]
    mon_app  -> co_app  [label="POST /fault/*\\n(proxy)", color="#E74C3C",
                         style=dashed, penwidth=1.5]

    // ── App → DB ──
    co_app -> pg_db [label="SQLAlchemy\\nPostgreSQL", color="#CA6F1E", penwidth=1.5]

    // ── 볼륨 ──
    pg_db -> pg_vol [style=dashed, arrowhead=none, color="#888888"]

    // ── 내부 관계 ──
    mon_app -> mon_tmpl  [style=invis]
    mon_app -> mon_poll  [style=invis]
    co_app  -> co_pytest [style=invis]
    co_app  -> co_state  [style=invis]

    // ── 시작 의존성 ──
    pg_db  -> co_app  [label="depends_on\\n(healthy)", style=dotted,
                       color="#777777", arrowhead=open, constraint=false]
    co_app -> mon_app [label="depends_on\\n(healthy)", style=dotted,
                       color="#777777", arrowhead=open, constraint=false]
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "container_diagram"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] container_diagram.png → {OUT / 'container_diagram.png'}")


# ── 9. graphviz: Sequence Diagram (장애 주입 흐름) ────────────────────────────

def run_sequence_fault_injection():
    """
    장애 주입 → 감지 → 복구 전체 시퀀스를 neato 절대좌표로 표현한다.
    """
    actors = ["User", "Dashboard", "MonitorAPI", "CheckoutFault", "CheckoutHealth", "StateModule"]
    labels = {
        "User":          "User",
        "Dashboard":     "Dashboard\\n(browser)",
        "MonitorAPI":    "health-monitoring\\nFastAPI",
        "CheckoutFault": "library-checkout\\nfault_router",
        "CheckoutHealth":"library-checkout\\nhealth_router",
        "StateModule":   "state.py",
    }
    colors = {
        "User":          "#D7BDE2",
        "Dashboard":     "#AED6F1",
        "MonitorAPI":    "#85C1E9",
        "CheckoutFault": "#A9DFBF",
        "CheckoutHealth":"#A9DFBF",
        "StateModule":   "#F9E79F",
    }

    messages = [
        ("User",          "Dashboard",     "[Inject Fault] click", False),
        ("Dashboard",     "MonitorAPI",    "POST /api/fault/inject", False),
        ("MonitorAPI",    "CheckoutFault", "POST /fault/inject (proxy)", False),
        ("CheckoutFault", "StateModule",   "set_fault(True)", False),
        ("StateModule",   "CheckoutFault", "fault_active = True", True),
        ("CheckoutFault", "MonitorAPI",    "{fault_active: true}", True),
        ("MonitorAPI",    "Dashboard",     "{fault_active: true}", True),
        ("MonitorAPI",    "CheckoutHealth","POST /health (poll)", False),
        ("CheckoutHealth","StateModule",   "is_fault_active()", False),
        ("StateModule",   "CheckoutHealth","True", True),
        ("CheckoutHealth","MonitorAPI",    "{status: unhealthy}", True),
        ("MonitorAPI",    "MonitorAPI",    "_update_failure_tracking()\\nFailureEvent created", False),
        ("Dashboard",     "MonitorAPI",    "GET /api/metrics (auto-refresh)", False),
        ("MonitorAPI",    "Dashboard",     "MTBF / MTTF / MTTR\\nAvailability", True),
        ("User",          "Dashboard",     "[Recover] click", False),
        ("Dashboard",     "MonitorAPI",    "POST /api/fault/recover", False),
        ("MonitorAPI",    "CheckoutFault", "POST /fault/recover (proxy)", False),
        ("CheckoutFault", "StateModule",   "set_fault(False)", False),
        ("StateModule",   "CheckoutFault", "fault_active = False", True),
        ("CheckoutFault", "MonitorAPI",    "{fault_active: false}", True),
        ("MonitorAPI",    "CheckoutHealth","POST /health (poll)", False),
        ("CheckoutHealth","MonitorAPI",    "{status: healthy}", True),
        ("MonitorAPI",    "MonitorAPI",    "record duration\\nrecalc Availability", False),
    ]

    col = {a: i for i, a in enumerate(actors)}
    n_rows = len(messages)
    col_w, row_h = 2.4, 0.65

    lines = ['digraph SeqFault {']
    lines += ['  graph [rankdir=TB, splines=false, nodesep=0, ranksep=0, pad=0.5]']
    lines += ['  node  [shape=box, style=filled, fontname="Helvetica", fontsize=9]']
    lines += ['  edge  [fontname="Helvetica", fontsize=8]']

    for a in actors:
        x = col[a] * col_w
        lines.append(
            f'  H_{a} [label="{labels[a]}", fillcolor="{colors[a]}",'
            f' pos="{x},0!", width=2.0, height=0.55]'
        )

    for a in actors:
        x = col[a] * col_w
        for r in range(n_rows + 1):
            y = -(r + 1.0) * row_h
            lines.append(
                f'  L_{a}_{r} [shape=point, width=0.01, style=invis,'
                f' pos="{x},{y}!"]'
            )
        for r in range(n_rows):
            lines.append(
                f'  L_{a}_{r} -> L_{a}_{r+1}'
                f' [style=dashed, arrowhead=none, color="#CCCCCC"]'
            )

    for r, (frm, to, lbl, ret) in enumerate(messages):
        style = 'dashed' if ret else 'solid'
        arrow = 'open'   if ret else 'normal'
        color = '#888888' if ret else '#1A5276'
        lines.append(
            f'  L_{frm}_{r} -> L_{to}_{r}'
            f' [label="{lbl}", style={style}, arrowhead={arrow}, color="{color}"]'
        )

    lines.append('}')
    dot_src = '\n'.join(lines)

    src = graphviz.Source(dot_src, engine="neato")
    src.render(
        filename=str(OUT / "sequence_fault"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] sequence_fault.png → {OUT / 'sequence_fault.png'}")


if __name__ == "__main__":
    print("=== UML 다이어그램 생성 시작 (pyreverse + graphviz) ===\n")
    run_pyreverse_class()
    run_package_diagram()
    run_er_diagram()
    run_layer_diagram()
    run_sequence_diagram()
    print()
    print("--- 추가 다이어그램 (v2) ---")
    run_package_diagram_v2()
    run_layer_diagram_v2()
    run_container_diagram()
    run_sequence_fault_injection()
    print(f"\n=== 완료 — 출력 위치: {OUT} ===")
