# REST API 명세서

---

## 1. library-checkout (포트 8000)

Base URL: `http://localhost:8000`

---

### 1.1 도서 관리 (Books)

> 응답 형식: HTML (Jinja2 렌더링). 폼 제출은 POST → 303 Redirect 패턴.

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/books/` | 도서 목록 조회 (keyword 검색 지원) |
| GET | `/books/new` | 도서 등록 폼 |
| POST | `/books/new` | 도서 등록 처리 → 303 `/books/` |
| GET | `/books/{book_id}/edit` | 도서 수정 폼 |
| POST | `/books/{book_id}/edit` | 도서 수정 처리 → 303 `/books/` |
| POST | `/books/{book_id}/delete` | 도서 삭제 처리 → 303 `/books/` |

#### GET `/books/`

| 파라미터 | 위치 | 타입 | 설명 |
|---------|------|------|------|
| `keyword` | Query | string | 제목 또는 저자 검색 키워드 (선택) |

**응답 예시** — HTML 테이블, 도서 목록 렌더링

---

#### POST `/books/new`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `title` | Form string | O | 도서 제목 |
| `author` | Form string | O | 저자 |
| `publisher` | Form string | O | 출판사 |

**성공**: 303 Redirect → `/books/`

---

#### POST `/books/{book_id}/edit`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `title` | Form string | O | 도서 제목 |
| `author` | Form string | O | 저자 |
| `publisher` | Form string | O | 출판사 |

**성공**: 303 Redirect → `/books/`

---

#### POST `/books/{book_id}/delete`

**성공**: 303 Redirect → `/books/`  
**실패**: 200 HTML — 도서가 대출 중인 경우 오류 메시지 표시

---

### 1.2 회원 관리 (Members)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/members/` | 회원 목록 조회 |
| GET | `/members/new` | 회원 등록 폼 |
| POST | `/members/new` | 회원 등록 처리 → 303 `/members/` |
| POST | `/members/{member_id}/delete` | 회원 삭제 → 303 `/members/` |

#### POST `/members/new`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | Form string | O | 회원 이름 |
| `email` | Form string | O | 이메일 (UNIQUE 제약) |

**성공**: 303 Redirect → `/members/`  
**실패**: 200 HTML — 이메일 중복 시 오류 메시지

---

### 1.3 대출 관리 (Loans)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/loans/` | 대출 현황 목록 |
| GET | `/loans/new` | 대출 처리 폼 (대출 가능 도서·회원 목록 포함) |
| POST | `/loans/new` | 대출 처리 → 303 `/loans/` |
| POST | `/loans/{loan_id}/return` | 반납 처리 → 303 `/loans/` |

#### POST `/loans/new`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `member_id` | Form integer | O | 대출 회원 ID |
| `book_id` | Form integer | O | 대출 도서 ID |

**성공**: 303 Redirect → `/loans/`  
**실패**: 200 HTML — 이미 대출 중인 도서일 경우 오류 메시지

---

### 1.4 헬스 체크 (Health)

#### `POST /health`

도서 대출 시스템의 헬스 상태를 확인한다. health-monitoring 컨테이너가 주기적으로 호출하며, Docker Healthcheck에도 사용된다.

**요청**: 바디 없음

**응답 (healthy)**

```json
{
  "status": "healthy",
  "timestamp": "2025-05-12T10:00:00+00:00",
  "uptime_seconds": 3620,
  "services": {
    "database": {
      "status": "healthy",
      "latency_ms": 1.24
    }
  },
  "statistics": {
    "books_total": 10,
    "books_available": 7,
    "members_total": 5,
    "active_loans": 3
  }
}
```

**응답 (unhealthy — 장애 주입 활성)**

```json
{
  "status": "unhealthy",
  "timestamp": "2025-05-12T10:05:00+00:00",
  "uptime_seconds": 3920,
  "services": {
    "fault_injection": {
      "status": "unhealthy",
      "message": "장애 주입 활성화 상태입니다."
    }
  },
  "statistics": {}
}
```

| 상태 코드 | 조건 |
|-----------|------|
| 200 | 항상 200 반환 (상태는 `status` 필드로 구분) |

---

#### `GET /health/ui`

헬스 체크 상태를 웹 UI로 확인하는 HTML 페이지.

**응답**: HTML (Jinja2 템플릿 `health/dashboard.html`)

---

### 1.5 장애 주입 (Fault Injection)

인위적으로 헬스 상태를 `unhealthy`로 전환하는 기능. `state.py`의 전역 플래그로 구현되어 있으며, health-monitoring이 이를 프록시한다.

#### `POST /fault/inject`

장애 주입을 활성화한다. 이후 `POST /health` 요청에서 `unhealthy`를 반환한다.

**응답**

```json
{
  "fault_active": true,
  "message": "장애가 주입되었습니다."
}
```

---

#### `POST /fault/recover`

장애 주입을 비활성화한다. 이후 `POST /health` 요청에서 정상 응답을 반환한다.

**응답**

```json
{
  "fault_active": false,
  "message": "시스템이 복구되었습니다."
}
```

---

#### `GET /fault/status`

현재 장애 주입 상태를 조회한다.

**응답**

```json
{
  "fault_active": false
}
```

---

## 2. health-monitoring (포트 8001)

Base URL: `http://localhost:8001`

---

### 2.1 대시보드 UI

#### `GET /`

3탭 모니터링 대시보드 HTML을 반환한다.

- **탭 1 현황**: 최신 헬스 상태, 이력 차트 (자동 새로고침)
- **탭 2 장애 주입**: 장애 주입·복구 버튼, 즉시 헬스 체크
- **탭 3 신뢰성 지표**: MTBF·MTTR·MTTF·가용성 대시보드, 장애 이벤트 표

**응답**: HTML

---

### 2.2 상태·이력 API

#### `GET /api/status`

가장 최근에 수행된 헬스 체크 결과를 반환한다.

**응답**

```json
{
  "status": "healthy",
  "timestamp": "2025-05-12T10:00:00+00:00",
  "uptime_seconds": 3620,
  "services": { "database": { "status": "healthy", "latency_ms": 1.24 } },
  "statistics": { "books_total": 10, "books_available": 7, "members_total": 5, "active_loans": 3 },
  "_checked_at": "2025-05-12T10:00:01+00:00",
  "_http_status": 200
}
```

이력이 없을 경우 `{"status": "initializing"}` 반환.

---

#### `GET /api/history`

저장된 헬스 체크 이력 전체를 배열로 반환한다 (최대 `MAX_HISTORY`개).

**응답**

```json
[
  { "status": "healthy", "_checked_at": "...", ... },
  { "status": "unhealthy", "_checked_at": "...", ... }
]
```

---

#### `POST /api/check/now`

배경 폴링 주기를 기다리지 않고 즉시 헬스 체크를 수행한다. 장애 주입 후 즉각 피드백에 사용된다.

**응답**: `GET /api/status` 와 동일한 단일 결과 객체

---

### 2.3 신뢰성 지표 API

#### `GET /api/metrics`

모니터링 시작 이후 누적된 신뢰성 지표를 반환한다.

**응답 (장애 없음)**

```json
{
  "monitoring_started_at": "2025-05-12T09:00:00+00:00",
  "total_time_seconds": 3600,
  "total_uptime_seconds": 3600,
  "total_downtime_seconds": 0,
  "failure_count": 0,
  "mtbf_seconds": null,
  "mttr_seconds": null,
  "mttf_seconds": null,
  "availability": 1.0,
  "availability_percent": 100.0,
  "is_currently_failing": false,
  "current_failure_duration_seconds": null,
  "failure_events": []
}
```

**응답 (장애 발생 후)**

```json
{
  "monitoring_started_at": "2025-05-12T09:00:00+00:00",
  "total_time_seconds": 7200,
  "total_uptime_seconds": 7020,
  "total_downtime_seconds": 180.0,
  "failure_count": 2,
  "mtbf_seconds": 3600.0,
  "mttr_seconds": 90.0,
  "mttf_seconds": 3510.0,
  "availability": 0.975,
  "availability_percent": 97.5,
  "is_currently_failing": false,
  "current_failure_duration_seconds": null,
  "failure_events": [
    {
      "id": 1,
      "started_at": "2025-05-12T09:30:00+00:00",
      "recovered_at": "2025-05-12T09:31:30+00:00",
      "duration_seconds": 90.0
    },
    {
      "id": 2,
      "started_at": "2025-05-12T10:30:00+00:00",
      "recovered_at": "2025-05-12T10:32:00+00:00",
      "duration_seconds": 120.0
    }
  ]
}
```

**지표 정의**

| 지표 | 공식 | 설명 |
|------|------|------|
| MTTF | avg(장애 시작 전 가동 시간) | Mean Time To Failure |
| MTTR | avg(완료된 장애 지속 시간) | Mean Time To Repair |
| MTBF | MTTF + MTTR | Mean Time Between Failures |
| Availability | 총 가동 시간 / 총 관측 시간 | 가용성 |

모니터링 미시작 시: `{"status": "not_started"}`

---

#### `POST /api/monitoring/reset`

모니터링 데이터(장애 이벤트, 이력, 시작 시각)를 초기화한다.

**응답**

```json
{
  "message": "모니터링 데이터가 초기화되었습니다.",
  "started_at": "2025-05-12T10:10:00+00:00"
}
```

---

### 2.4 장애 주입 프록시 API

health-monitoring이 library-checkout의 `/fault/*` 엔드포인트를 프록시하는 API.
대시보드에서 단일 Origin을 통해 장애 주입을 제어할 수 있다.

#### `POST /api/fault/inject`

library-checkout의 `POST /fault/inject` 를 프록시한다.

**응답**: library-checkout의 응답을 그대로 전달

```json
{ "fault_active": true, "message": "장애가 주입되었습니다." }
```

| 상태 코드 | 조건 |
|-----------|------|
| 200 | 정상 프록시 |
| 503 | library-checkout 연결 실패 |

---

#### `POST /api/fault/recover`

library-checkout의 `POST /fault/recover` 를 프록시한다.

**응답**

```json
{ "fault_active": false, "message": "시스템이 복구되었습니다." }
```

---

#### `GET /api/fault/status`

library-checkout의 `GET /fault/status` 를 프록시한다.

**응답**

```json
{ "fault_active": false }
```

---

## 3. 엔드포인트 요약

### library-checkout (port 8000)

| 메서드 | 경로 | 형식 | 설명 |
|--------|------|------|------|
| GET | `/` | HTML | → 302 `/books/` |
| GET | `/books/` | HTML | 도서 목록 |
| GET | `/books/new` | HTML | 도서 등록 폼 |
| POST | `/books/new` | Redirect | 도서 등록 |
| GET | `/books/{id}/edit` | HTML | 도서 수정 폼 |
| POST | `/books/{id}/edit` | Redirect | 도서 수정 |
| POST | `/books/{id}/delete` | Redirect/HTML | 도서 삭제 |
| GET | `/members/` | HTML | 회원 목록 |
| GET | `/members/new` | HTML | 회원 등록 폼 |
| POST | `/members/new` | Redirect/HTML | 회원 등록 |
| POST | `/members/{id}/delete` | Redirect | 회원 삭제 |
| GET | `/loans/` | HTML | 대출 현황 |
| GET | `/loans/new` | HTML | 대출 폼 |
| POST | `/loans/new` | Redirect/HTML | 대출 처리 |
| POST | `/loans/{id}/return` | Redirect/HTML | 반납 처리 |
| POST | `/health` | JSON | 헬스 체크 |
| GET | `/health/ui` | HTML | 헬스 UI |
| POST | `/fault/inject` | JSON | 장애 주입 활성화 |
| POST | `/fault/recover` | JSON | 장애 복구 |
| GET | `/fault/status` | JSON | 장애 상태 조회 |

### health-monitoring (port 8001)

| 메서드 | 경로 | 형식 | 설명 |
|--------|------|------|------|
| GET | `/` | HTML | 3탭 대시보드 |
| GET | `/api/status` | JSON | 최신 헬스 상태 |
| GET | `/api/history` | JSON | 헬스 체크 이력 |
| POST | `/api/check/now` | JSON | 즉시 헬스 체크 |
| GET | `/api/metrics` | JSON | 신뢰성 지표 |
| POST | `/api/monitoring/reset` | JSON | 모니터링 초기화 |
| POST | `/api/fault/inject` | JSON | 장애 주입 (프록시) |
| POST | `/api/fault/recover` | JSON | 장애 복구 (프록시) |
| GET | `/api/fault/status` | JSON | 장애 상태 (프록시) |
