"""
Booklog 디버깅 연습 문제 생성기

exam/(없으면 skeleton/)을 복사한 뒤 views.py와 serializers.py를 "정답 코드"로 되돌리고,
그 위에 버그를 심어 연습용 프로젝트를 만듭니다. 원본 폴더는 수정하지 않습니다.
DB(db.sqlite3)는 fixtures로 새로 만들어 두므로 바로 runserver 할 수 있습니다.

사용법 (레포 루트에서):
    python tools/make_practice.py                     # 시험과 같은 버그 9개 (기본: practice/)
    python tools/make_practice.py --mode random       # 변형 버그 5개를 무작위로
    python tools/make_practice.py --mode random --count 7 --seed 42 --out practice2

만든 뒤:
    1) practice/PRACTICE.md 의 증상을 보고 views.py / serializers.py 를 고친다
    2) python tools/grade.py practice 로 채점한다
    3) 막히면 practice/ANSWERS.md 를 연다 (정답이 들어 있음)
"""
import argparse
import os
import random
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# 정답 코드 (주석 포함). 사이트의 "정답 코드" 탭과 같은 내용입니다.
# ---------------------------------------------------------------------------
SERIALIZERS = '''from rest_framework import serializers
from .models import Book, Comment


# 도서 목록 조회용 serializer
class BookListSerializer(serializers.ModelSerializer):
    num_of_comments = serializers.SerializerMethodField()

    class Meta:
        model = Book
        # [01] 목록 조회에는 id, title, author, num_of_comments만 응답
        fields = ('id', 'title', 'author', 'num_of_comments')

    def get_num_of_comments(self, obj):
        # [07] obj(현재 직렬화 중인 도서)에 달린 댓글만 역참조로 세어 반환
        return obj.comment_set.count()


# 도서 생성 / 수정용 serializer
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


# 도서 상세 조회용 serializer (댓글 목록 포함)
class BookDetailSerializer(serializers.ModelSerializer):
    class CommentDetailSerializer(serializers.ModelSerializer):
        class Meta:
            model = Comment
            # [06] 상세 조회에 포함할 댓글 정보는 id, content만 지정
            fields = ('id', 'content')

    # [06] related_name이 없으므로 역참조 이름은 comment_set
    comment_set = CommentDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = '__all__'


# 댓글 serializer
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        # [03] book은 URL의 book_pk로 views에서 save(book=book)로 넣어 주므로
        # 입력 검증에서는 제외하고 응답에만 포함되도록 읽기 전용으로 지정
        read_only_fields = ('book',)
'''

VIEWS = '''from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.shortcuts import get_object_or_404, get_list_or_404
from .models import Book, Comment
from .serializers import (
    BookListSerializer,
    BookSerializer,
    BookDetailSerializer,
    CommentSerializer,
)


@api_view(['GET', 'POST'])
def book_list(request):
    if request.method == 'GET':
        books = get_list_or_404(Book)
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # [02] 생성에 성공하면 201 Created 상태 코드로 응답
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def book_detail(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)

    if request.method == 'GET':
        serializer = BookDetailSerializer(book)
        return Response(serializer.data)

    elif request.method == 'PUT':
        # [04] partial=True: 요청에 담긴 필드만 검증하고 수정하는 부분 수정
        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        book.delete()
        # [05] 삭제에 성공하면 응답 본문 없이 204 No Content로 응답
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def comment_list(request):
    comments = get_list_or_404(Comment)
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


# [08] 댓글 단건 조회·수정에 더해 삭제(DELETE) 요청도 허용
@api_view(['GET', 'PUT', 'DELETE'])
def comment_detail(request, comment_pk):
    comment = get_object_or_404(Comment, pk=comment_pk)

    if request.method == 'GET':
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            # [09] 검증된 데이터를 DB에 저장(instance가 있으므로 update 수행)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def comment_create(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(book=book)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
'''

S, V = 'serializers.py', 'views.py'

# ---------------------------------------------------------------------------
# 버그 목록: (id, 파일, [(정답 조각, 버그 조각), ...], 증상, 정답 설명)
# 정답 조각의 주석까지 함께 지워 힌트가 남지 않게 합니다.
# ---------------------------------------------------------------------------
BUGS = [
    # ---- 시험 원본 9문제 ----
    ('E01', S, [("        # [01] 목록 조회에는 id, title, author, num_of_comments만 응답\n        fields = ('id', 'title', 'author', 'num_of_comments')",
                 "        fields = '__all__'")],
     'GET /api/v1/books/ 목록에 content, finished, created_at 등 모든 필드가 응답됩니다. id, title, author, num_of_comments만 나와야 합니다.',
     "BookListSerializer.Meta.fields = ('id', 'title', 'author', 'num_of_comments')"),
    ('E02', V, [("            # [02] 생성에 성공하면 201 Created 상태 코드로 응답\n            return Response(serializer.data, status=status.HTTP_201_CREATED)",
                 "            return Response(serializer.data)")],
     'POST /api/v1/books/ 로 도서는 생성되지만 200 OK가 응답됩니다. 201 Created여야 합니다.',
     'book_list POST: Response(serializer.data, status=status.HTTP_201_CREATED)'),
    ('E03', S, [("        # [03] book은 URL의 book_pk로 views에서 save(book=book)로 넣어 주므로\n        # 입력 검증에서는 제외하고 응답에만 포함되도록 읽기 전용으로 지정\n        read_only_fields = ('book',)\n",
                 "")],
     'POST /api/v1/books/<book_pk>/comments/ 에 content만 보내면 400 "book: This field is required."가 응답됩니다. 응답에는 book이 포함되어야 합니다.',
     "CommentSerializer.Meta에 read_only_fields = ('book',)"),
    ('E04', V, [("        # [04] partial=True: 요청에 담긴 필드만 검증하고 수정하는 부분 수정\n        serializer = BookSerializer(book, data=request.data, partial=True)",
                 "        serializer = BookSerializer(book, data=request.data)")],
     'PUT /api/v1/books/<book_pk>/ 에 title만 보내면 400 (author, content 필수)이 응답됩니다. 보낸 필드만 수정되어야 합니다. (views.py에서 수정)',
     'book_detail PUT: BookSerializer(book, data=request.data, partial=True)'),
    ('E05', V, [("        book.delete()\n        # [05] 삭제에 성공하면 응답 본문 없이 204 No Content로 응답\n        return Response(status=status.HTTP_204_NO_CONTENT)",
                 "        book.delete()\n        return Response(status=status.HTTP_200_OK)")],
     'DELETE /api/v1/books/<book_pk>/ 로 도서는 삭제되지만 200 OK가 응답됩니다. 204 No Content여야 합니다.',
     'book_detail DELETE: Response(status=status.HTTP_204_NO_CONTENT)'),
    ('E06', S, [("            # [06] 상세 조회에 포함할 댓글 정보는 id, content만 지정\n            fields = ('id', 'content')",
                 "            fields = '__all__'"),
                ("    # [06] related_name이 없으므로 역참조 이름은 comment_set\n    comment_set = CommentDetailSerializer(many=True, read_only=True)",
                 "    comments = CommentDetailSerializer(many=True, read_only=True)")],
     'GET /api/v1/books/<book_pk>/ 응답에 오류는 없지만 댓글 목록이 없습니다. comment_set 키에 댓글(id, content) 목록이 나와야 합니다.',
     "필드 이름을 comment_set으로, CommentDetailSerializer.Meta.fields = ('id', 'content')"),
    ('E07', S, [("        # [07] obj(현재 직렬화 중인 도서)에 달린 댓글만 역참조로 세어 반환\n        return obj.comment_set.count()",
                 "        return Comment.objects.count()")],
     'GET /api/v1/books/ 의 num_of_comments가 모든 도서에서 전체 댓글 수로 같습니다. 도서별 댓글 수여야 합니다.',
     'get_num_of_comments: return obj.comment_set.count()'),
    ('E08', V, [("# [08] 댓글 단건 조회·수정에 더해 삭제(DELETE) 요청도 허용\n@api_view(['GET', 'PUT', 'DELETE'])\ndef comment_detail",
                 "@api_view(['GET', 'PUT'])\ndef comment_detail")],
     'DELETE /api/v1/comments/<comment_pk>/ 요청이 405 Method Not Allowed입니다. 삭제 후 204여야 합니다.',
     "comment_detail: @api_view(['GET', 'PUT', 'DELETE'])"),
    ('E09', V, [("            # [09] 검증된 데이터를 DB에 저장(instance가 있으므로 update 수행)\n            serializer.save()\n",
                 "")],
     'PUT /api/v1/comments/<comment_pk>/ 가 200이지만 응답에 수정 전 내용이 담기고 DB도 그대로입니다.',
     'comment_detail PUT: is_valid() 블록 안에 serializer.save()'),

    # ---- 변형 버그 (재시험 대비) ----
    ('V01', V, [("        serializer = BookListSerializer(books, many=True)",
                 "        serializer = BookListSerializer(books)")],
     "GET /api/v1/books/ 가 500 (AttributeError ... 'list' object has no attribute ...)입니다.",
     'book_list GET: BookListSerializer(books, many=True)'),
    ('V02', V, [("        serializer.save(book=book)",
                 "        serializer.save()")],
     '댓글 생성 POST가 500 (IntegrityError: NOT NULL constraint failed: books_comment.book_id)입니다.',
     'comment_create: serializer.save(book=book)'),
    ('V03', V, [("        # [04] partial=True: 요청에 담긴 필드만 검증하고 수정하는 부분 수정\n        serializer = BookSerializer(book, data=request.data, partial=True)",
                 "        serializer = BookSerializer(data=request.data, partial=True)")],
     'PUT /api/v1/books/<book_pk>/ 가 200인데 응답 id가 새 번호이고 원래 도서는 그대로입니다.',
     'book_detail PUT: 첫 번째 인자로 instance(book)를 넘김'),
    ('V04', S, [("    def get_num_of_comments(self, obj):",
                 "    def get_comments_count(self, obj):")],
     "GET /api/v1/books/ 가 500 (AttributeError: ... has no attribute 'get_num_of_comments')입니다.",
     '메서드 이름을 get_num_of_comments로 (get_ + 필드명)'),
    ('V05', V, [("    if request.method == 'GET':\n        books = get_list_or_404(Book)",
                 "    if request.method == 'Get':\n        books = get_list_or_404(Book)")],
     "GET /api/v1/books/ 가 500 (AssertionError: Expected a `Response` ... received a `<class 'NoneType'>`)입니다.",
     "book_list: request.method == 'GET' (대문자)"),
    ('V06', S, [("        # [01] 목록 조회에는 id, title, author, num_of_comments만 응답\n        fields = ('id', 'title', 'author', 'num_of_comments')",
                 "        fields = ('id', 'title', 'author')")],
     "GET /api/v1/books/ 가 500 (AssertionError: The field 'num_of_comments' was declared ... not been included in the 'fields' option)입니다.",
     "BookListSerializer.Meta.fields에 'num_of_comments' 포함"),
    ('V07', S, [("        fields = '__all__'\n        # [03] book은 URL의 book_pk로 views에서 save(book=book)로 넣어 주므로\n        # 입력 검증에서는 제외하고 응답에만 포함되도록 읽기 전용으로 지정\n        read_only_fields = ('book',)",
                 "        exclude = ('book',)")],
     '댓글 생성·수정·조회 응답에 book 키가 없습니다. 응답에는 book이 포함되어야 합니다.',
     "exclude 대신 fields = '__all__' + read_only_fields = ('book',)"),
    ('V08', V, [("@api_view(['GET'])\ndef comment_list",
                 "def comment_list")],
     'GET /api/v1/comments/ 가 500 (AssertionError: .accepted_renderer not set on Response)입니다.',
     "comment_list에 @api_view(['GET']) 데코레이터"),
    ('V09', S, [("    comment_set = CommentDetailSerializer(many=True, read_only=True)",
                 "    comment_set = CommentDetailSerializer(read_only=True)")],
     'GET /api/v1/books/<book_pk>/ 가 500 (AttributeError ... RelatedManager ...)입니다.',
     'comment_set = CommentDetailSerializer(many=True, read_only=True)'),
    ('V10', V, [("        comment.delete()\n        return Response(status=status.HTTP_204_NO_CONTENT)",
                 "        comment.delete()\n        return Response(status=status.HTTP_200_OK)")],
     'DELETE /api/v1/comments/<comment_pk>/ 로 댓글은 삭제되지만 200 OK가 응답됩니다.',
     'comment_detail DELETE: Response(status=status.HTTP_204_NO_CONTENT)'),
    ('V11', S, [("        return obj.comment_set.count()",
                 "        return obj.comment_set")],
     'GET /api/v1/books/ 가 500 (TypeError: Object of type RelatedManager is not JSON serializable)입니다.',
     'return obj.comment_set.count()'),
]


def copy_project(src, dst):
    # DB와 시험용 README는 복사하지 않음 (DB는 아래에서 fixtures로 새로 생성)
    ignore = shutil.ignore_patterns('venv', '.venv', '__pycache__', '*.pyc', 'db.sqlite3', 'README.md')
    shutil.copytree(src, dst, ignore=ignore)


def default_src():
    # 레포에 포함된 exam/을 기본으로 쓰고, 없으면 시험 원본 skeleton/을 사용
    for name in ('exam', 'skeleton'):
        path = os.path.join(ROOT, name)
        if os.path.exists(os.path.join(path, 'manage.py')):
            return path
    return os.path.join(ROOT, 'exam')


def build_db(project_dir):
    import subprocess
    for cmd in (['migrate', '-v', '0'], ['loaddata', 'books.json', 'comments.json', '-v', '0']):
        r = subprocess.run([sys.executable, 'manage.py', *cmd], cwd=project_dir, capture_output=True, text=True)
        if r.returncode != 0:
            print('DB 생성에 실패했습니다. 가상환경을 켜고 pip install -r requirements.txt 를 했는지 확인하세요.')
            print(r.stderr[-800:])
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description='Booklog 디버깅 연습 문제 생성기')
    ap.add_argument('--mode', choices=['exam', 'random'], default='exam', help='exam: 시험 원본 9문제, random: 무작위 변형')
    ap.add_argument('--count', type=int, default=5, help='random 모드에서 심을 버그 수 (기본 5)')
    ap.add_argument('--seed', type=int, default=None, help='같은 문제를 다시 만들고 싶을 때 지정')
    ap.add_argument('--src', default=default_src(), help='복사할 원본 프로젝트 (기본: exam/)')
    ap.add_argument('--out', default=os.path.join(ROOT, 'practice'))
    ap.add_argument('--force', action='store_true', help='출력 폴더가 있으면 지우고 다시 생성')
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    if os.path.exists(out):
        if not args.force:
            print(f'이미 있습니다: {out}\n다시 만들려면 --force 를 붙이세요.')
            sys.exit(1)
        shutil.rmtree(out)
    copy_project(os.path.abspath(args.src), out)

    files = {S: SERIALIZERS, V: VIEWS}
    if args.mode == 'exam':
        chosen = [b for b in BUGS if b[0].startswith('E')]
    else:
        rng = random.Random(args.seed)
        pool = BUGS[:]
        rng.shuffle(pool)
        chosen = []
        for bug in pool:
            if len(chosen) >= args.count:
                break
            _, fname, pairs, _, _ = bug
            text = files[fname]
            if all(good in text for good, _ in pairs):
                for good, bad in pairs:
                    text = text.replace(good, bad, 1)
                files[fname] = text
                chosen.append(bug)
        chosen.sort(key=lambda b: b[0])

    if args.mode == 'exam':
        for _, fname, pairs, _, _ in chosen:
            for good, bad in pairs:
                assert good in files[fname], good
                files[fname] = files[fname].replace(good, bad, 1)

    # 정답 표시용 [NN] 주석은 남은 것도 지워서 버그 위치가 드러나지 않게 함
    import re
    for fname, text in files.items():
        text = re.sub(r'^[ \t]*# \[\d\d\].*\n(?:[ \t]*# (?!\[).*\n)?', '', text, flags=re.M)
        with open(os.path.join(out, 'books', fname), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)

    rel = os.path.relpath(out, ROOT)
    with open(os.path.join(out, 'PRACTICE.md'), 'w', encoding='utf-8') as f:
        f.write(f'# 연습 문제 ({args.mode}, 버그 {len(chosen)}개{"" if args.seed is None else f", seed {args.seed}"})\n\n')
        f.write('수정 파일은 books/views.py, books/serializers.py 뿐입니다. 고친 줄에는 주석을 다세요.\n\n')
        for i, (_, fname, _, symptom, _) in enumerate(chosen, 1):
            f.write(f'{i}. [{fname}] {symptom}\n')
        f.write(f'\n채점: `python tools/grade.py {rel}`\n')
    with open(os.path.join(out, 'ANSWERS.md'), 'w', encoding='utf-8') as f:
        f.write('# 정답 (다 풀고 열어 보세요)\n\n')
        for i, (bid, fname, _, symptom, answer) in enumerate(chosen, 1):
            f.write(f'{i}. ({bid}) {fname} → {answer}\n')

    db_ok = build_db(out)
    print(f'연습 프로젝트를 만들었습니다: {out}')
    print(f'심은 버그 {len(chosen)}개 · 증상은 {rel}/PRACTICE.md')
    if db_ok:
        print(f'서버 실행: cd {rel} && python manage.py runserver')
    print(f'채점: python tools/grade.py {rel}')


if __name__ == '__main__':
    main()
