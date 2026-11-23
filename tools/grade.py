"""
Booklog 디버깅 자동 채점기

사용법 (프로젝트의 가상환경을 켠 상태에서, 레포 루트에서 실행):
    python tools/grade.py skeleton
    python tools/grade.py practice

- 프로젝트의 db.sqlite3는 건드리지 않습니다. 임시 DB를 만들고 fixtures로 채운 뒤 검사합니다.
- 각 검사는 트랜잭션 안에서 실행 후 되돌리므로, 검사 순서와 상관없이 항상 같은 초기 데이터로 시작합니다.
"""
import io
import logging
import os
import shutil
import sys
import tempfile
import traceback

GREEN, RED, YELLOW, DIM, RESET = '\033[32m', '\033[31m', '\033[33m', '\033[2m', '\033[0m'
if os.name == 'nt':
    os.system('')  # Windows 터미널에서 ANSI 색상 활성화
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def setup(project_dir):
    sys.path.insert(0, project_dir)
    os.chdir(project_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'booklog_pjt.settings'

    from django.conf import settings
    tmp_dir = tempfile.mkdtemp(prefix='booklog_grade_')
    settings.DATABASES['default']['NAME'] = os.path.join(tmp_dir, 'grade.sqlite3')
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

    import django
    django.setup()
    logging.getLogger('django.request').disabled = True

    from django.core.management import call_command
    out = io.StringIO()
    call_command('migrate', verbosity=0, stdout=out)
    call_command('loaddata', 'books.json', 'comments.json', verbosity=0, stdout=out)
    return tmp_dir


class Fail(Exception):
    pass


def expect(cond, msg):
    if not cond:
        raise Fail(msg)


def body(r):
    try:
        return r.json()
    except Exception:
        return None


def run_checks():
    from django.db import transaction
    from rest_framework.test import APIClient
    from books.models import Book, Comment

    c = APIClient()

    def status_is(r, code):
        expect(r.status_code == code, f'상태 코드 {r.status_code} (기대값 {code}) · 응답: {str(body(r))[:160]}')

    def p01():
        r = c.get('/api/v1/books/')
        status_is(r, 200)
        data = body(r)
        expect(isinstance(data, list) and data, '응답이 도서 리스트가 아님')
        keys = set(data[0].keys())
        expect(keys == {'id', 'title', 'author', 'num_of_comments'}, f'응답 필드 {sorted(keys)}')

    def p02():
        r = c.post('/api/v1/books/', {'title': '어린 왕자', 'author': '생텍쥐페리', 'content': '가장 중요한 것은 눈에 보이지 않는다.'}, format='json')
        status_is(r, 201)
        expect('id' in (body(r) or {}), '응답에 생성된 도서 id가 없음')

    def p03():
        book = Book.objects.first()
        r = c.post(f'/api/v1/books/{book.pk}/comments/', {'content': '다시 읽어도 좋은 책'}, format='json')
        status_is(r, 201)
        data = body(r) or {}
        expect(data.get('book') == book.pk, f"응답의 book 값 {data.get('book')!r} (기대값 {book.pk})")
        expect(Comment.objects.filter(book=book, content='다시 읽어도 좋은 책').exists(), 'DB에 댓글이 저장되지 않음')

    def p04():
        book = Book.objects.get(pk=2)
        before = Book.objects.count()
        r = c.put(f'/api/v1/books/{book.pk}/', {'title': '클린 코드 (개정판)'}, format='json')
        status_is(r, 200)
        expect(Book.objects.count() == before, '도서 개수가 늘어남 (수정이 아니라 생성됨)')
        book.refresh_from_db()
        expect(book.title == '클린 코드 (개정판)', 'DB의 title이 바뀌지 않음')
        expect(book.author == '로버트 C. 마틴', '보내지 않은 author가 바뀜')

    def p05():
        r = c.delete('/api/v1/books/5/')
        status_is(r, 204)
        expect(not Book.objects.filter(pk=5).exists(), '도서가 삭제되지 않음')

    def p06():
        r = c.get('/api/v1/books/1/')
        status_is(r, 200)
        data = body(r) or {}
        expect('comment_set' in data, f'응답에 comment_set 키가 없음 · 키: {sorted(data.keys())}')
        cs = data['comment_set']
        expect(isinstance(cs, list) and cs and isinstance(cs[0], dict), f'comment_set 형식이 객체 리스트가 아님: {str(cs)[:80]}')
        expect(set(cs[0].keys()) == {'id', 'content'}, f'댓글 필드 {sorted(cs[0].keys())} (기대값 id, content)')
        expect(len(cs) == Comment.objects.filter(book_id=1).count(), '댓글 개수가 DB와 다름')

    def p07():
        r = c.get('/api/v1/books/')
        status_is(r, 200)
        for item in body(r) or []:
            real = Comment.objects.filter(book_id=item['id']).count()
            expect(item.get('num_of_comments') == real, f"도서 {item['id']}의 num_of_comments {item.get('num_of_comments')!r} (기대값 {real})")

    def p08():
        r = c.delete('/api/v1/comments/2/')
        status_is(r, 204)
        expect(not Comment.objects.filter(pk=2).exists(), '댓글이 삭제되지 않음')

    def p09():
        r = c.put('/api/v1/comments/1/', {'content': '두 번째 읽으니 더 좋네요.', 'book': 1}, format='json')
        status_is(r, 200)
        expect((body(r) or {}).get('content') == '두 번째 읽으니 더 좋네요.', '응답에 수정 전 내용이 담김')
        expect(Comment.objects.get(pk=1).content == '두 번째 읽으니 더 좋네요.', 'DB에 저장되지 않음')

    def extra_comment_list():
        r = c.get('/api/v1/comments/')
        status_is(r, 200)
        expect(isinstance(body(r), list), '응답이 리스트가 아님')

    def extra_comment_get():
        r = c.get('/api/v1/comments/3/')
        status_is(r, 200)

    checks = [
        ('01', '도서 목록 응답 필드', 15, p01),
        ('02', '도서 생성 201', 10, p02),
        ('03', '댓글 생성 (content만)', 10, p03),
        ('04', '도서 부분 수정', 10, p04),
        ('05', '도서 삭제 204', 10, p05),
        ('06', '상세 조회 comment_set', 10, p06),
        ('07', '도서별 댓글 개수', 5, p07),
        ('08', '댓글 삭제 204', 5, p08),
        ('09', '댓글 수정 저장', 5, p09),
        ('++', '전체 댓글 목록 GET (회귀 확인)', 0, extra_comment_list),
        ('++', '댓글 단건 GET (회귀 확인)', 0, extra_comment_get),
    ]

    total = got = 0
    failed = []
    for no, name, pts, fn in checks:
        total += pts
        try:
            with transaction.atomic():
                try:
                    fn()
                finally:
                    transaction.set_rollback(True)
            got += pts
            print(f'  {GREEN}PASS{RESET}  [{no}] {name}')
        except Fail as e:
            failed.append(no)
            print(f'  {RED}FAIL{RESET}  [{no}] {name}\n        {DIM}{e}{RESET}')
        except Exception as e:
            failed.append(no)
            print(f'  {RED}500 {RESET}  [{no}] {name}\n        {DIM}{type(e).__name__}: {str(e).splitlines()[0][:200] if str(e) else ""}{RESET}')
    return got, total, failed


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'skeleton'
    project_dir = os.path.abspath(target)
    if not os.path.exists(os.path.join(project_dir, 'manage.py')):
        print(f'{RED}manage.py를 찾을 수 없습니다: {project_dir}{RESET}')
        sys.exit(2)

    print(f'\n채점 대상: {project_dir}\n')
    tmp_dir = None
    try:
        tmp_dir = setup(project_dir)
        # runserver 전에 하는 시스템 체크와 URLConf(views/serializers import) 로딩 확인
        from django.core.management import call_command
        from django.urls import get_resolver
        call_command('check', verbosity=0)
        get_resolver().url_patterns
    except Exception:
        print(f'{RED}서버를 실행할 수 없는 상태입니다. 시험에서는 전체 감점 또는 0점입니다.{RESET}\n')
        traceback.print_exc(limit=3)
        sys.exit(1)

    got, total, failed = run_checks()
    color = GREEN if not failed else YELLOW
    print(f'\n  코드 문항 점수: {color}{got} / {total}{RESET}  (서술형 20점, 주석 감점은 따로 확인)')
    if failed:
        print(f'  다시 볼 문제: {", ".join(failed)}')
    print()
    from django.db import connections
    connections.close_all()
    if tmp_dir:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
