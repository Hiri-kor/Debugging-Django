# Booklog API · 디버깅 시험 (재현본)

Django REST Framework로 만든 독서 기록(도서·댓글) API입니다. 9개 API에 버그가 하나씩 들어 있습니다.
**`books/views.py`와 `books/serializers.py`만 고쳐서** 아래 9문제를 해결하세요. 서술형 2문제는 [`problem_10_11.md`](problem_10_11.md)에 답합니다.

- 시험 시간 기준: 50분 (서술형 포함)
- 총점 100점 = 코드 80점 + 서술형 20점

## 1. 환경 준비

레포 루트(`Debugging-Django/`)에서:

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

`exam/` 폴더에서 DB를 만들고 서버를 켭니다:

```bash
cd exam
python manage.py migrate
python manage.py loaddata books.json comments.json
python manage.py runserver
```

- 요청은 Postman 등으로 보냅니다. **URL 끝에 반드시 `/`를 붙입니다.** (예: `http://127.0.0.1:8000/api/v1/books/`)
- DB를 처음 상태로 되돌리려면 `db.sqlite3`를 지우고 위의 `migrate`, `loaddata`를 다시 실행합니다.
- 처음부터 다시 풀려면 레포 루트에서 `git checkout -- exam/`

## 2. 문제 (코드 80점)

| # | 요청 | 수정 파일 | 현재 증상 | 정상 동작 | 배점 |
|---|------|-----------|-----------|-----------|-----|
| 01 | `GET /api/v1/books/` | serializers.py | 각 도서의 모든 필드(content, finished, created_at 등)가 응답됨 | 각 도서의 `id`, `title`, `author`, `num_of_comments`만 응답 | 15 |
| 02 | `POST /api/v1/books/` | views.py | 도서는 생성되지만 `200 OK`로 응답 | 생성된 도서 정보와 함께 `201 Created` | 10 |
| 03 | `POST /api/v1/books/<book_pk>/comments/` | serializers.py | `content`만 보내면 `400` + `"book: This field is required."` | 도서는 URL의 book_pk로 정해지므로 content만 보내도 `201 Created`. **응답에는 book 포함** | 10 |
| 04 | `PUT /api/v1/books/<book_pk>/` | views.py | `title`만 보내면 `400` + author, content 필수 | 일부 필드만 보내도 보낸 필드만 수정되어 `200 OK` | 10 |
| 05 | `DELETE /api/v1/books/<book_pk>/` | views.py | 삭제는 되지만 `200 OK`로 응답 | `204 No Content` | 10 |
| 06 | `GET /api/v1/books/<book_pk>/` | serializers.py | 오류는 없지만 댓글 목록이 응답에 없음 | `comment_set` 필드에 해당 도서의 댓글 목록(`id`, `content`) 포함 | 10 |
| 07 | `GET /api/v1/books/` | serializers.py | `num_of_comments`가 모든 도서에서 같은 값(전체 댓글 수) | 각 도서에 달린 댓글 개수 | 5 |
| 08 | `DELETE /api/v1/comments/<comment_pk>/` | views.py | `405 Method Not Allowed` | 댓글이 삭제되고 `204 No Content` | 5 |
| 09 | `PUT /api/v1/comments/<comment_pk>/` | views.py | `200 OK`지만 응답에 수정 전 내용, 다시 조회해도 그대로 | 요청한 내용으로 저장되고 수정된 댓글 정보가 `200 OK` | 5 |

요청 예시 (Body는 raw · JSON):

```jsonc
// 02  POST /api/v1/books/
{ "title": "어린 왕자", "author": "생텍쥐페리", "content": "가장 중요한 것은 눈에 보이지 않는다." }

// 03  POST /api/v1/books/4/comments/
{ "content": "싱클레어의 성장이 인상 깊었어요." }

// 04  PUT /api/v1/books/2/
{ "title": "클린 코드 (개정판)" }

// 09  PUT /api/v1/comments/1/
{ "content": "두 번째 읽으니 더 좋네요.", "book": 1 }
```

## 3. 규칙 (실제 시험과 동일)

- 문제에 지정된 파일 외의 파일을 고치면 기능이 맞아도 오답입니다. `models.py`는 수정하지 않습니다.
- 정의된 파일명·함수명을 바꾸지 않습니다. (예: `def book_detail(request, book_pk)` → `def detail(request, pk)` 금지)
- 고친 줄에는 무엇을 왜 바꿨는지 **주석**을 답니다. 없거나 미흡하면 감점입니다.
- 한 문제를 고치다 다른 문제를 깨뜨리면 감점입니다.
- 출력에 정답과 무관한 내용(디버깅용 `print` 등)을 남기지 않습니다.
- 제출 시점에 `runserver`가 반드시 켜져야 합니다. 못 푼 문제는 주석 처리해서라도 서버가 뜨게 둡니다.

## 4. 채점

레포 루트에서:

```bash
python tools/grade.py exam
```

임시 DB에서 9개 요청을 보내 PASS/FAIL과 점수를 출력합니다. (`exam/db.sqlite3`는 건드리지 않음)
풀이와 해설은 학습 사이트의 "문제 01–09" 탭을 참고하세요.

---

## 참고: API 목록

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/v1/books/` | 도서 목록 조회 |
| POST | `/api/v1/books/` | 도서 생성 |
| GET | `/api/v1/books/<book_pk>/` | 도서 상세 조회 (댓글 목록 포함) |
| PUT | `/api/v1/books/<book_pk>/` | 도서 수정 |
| DELETE | `/api/v1/books/<book_pk>/` | 도서 삭제 |
| GET | `/api/v1/comments/` | 전체 댓글 목록 조회 |
| GET | `/api/v1/comments/<comment_pk>/` | 댓글 단건 조회 |
| PUT | `/api/v1/comments/<comment_pk>/` | 댓글 수정 |
| DELETE | `/api/v1/comments/<comment_pk>/` | 댓글 삭제 |
| POST | `/api/v1/books/<book_pk>/comments/` | 특정 도서에 댓글 작성 |

API 문서: `/api/schema/swagger-ui/`, `/api/schema/redoc/`

## 참고: 모델

| 모델 | 필드 |
|------|------|
| Book | id, title, author, content, finished(완독 여부), created_at, updated_at |
| Comment | id, book(FK → Book), content, created_at, updated_at |

- Book : Comment = 1 : N
- Comment의 `book` 필드에는 `related_name`이 지정되어 있지 않습니다.
- 초기 데이터: Book 5개, Comment 6개 (`books/fixtures/`)
