# Debugging-Django

Django REST Framework **디버깅 시험 대비** 자료입니다. (SSAFY 16기 5회차 월말평가 · 파이썬 트랙 유형)
도서·댓글 API 9곳에 심어진 버그를 찾아 고치고, 서술형 2문제에 답합니다.

## 바로 시작하기

### A. 설치 없이 — 학습 사이트

**https://hiri-kor.github.io/Debugging-Django/**

- 문제 카드의 편집기에서 버그 코드를 고치고 **채점** 버튼으로 확인 (주석 유무까지 체크)
- 힌트 → 정답 diff → 해설 → 변형 포인트 순서로 학습
- 개념 정리, 변형 퀴즈 14문항, 에러 메시지 사전, 제출 체크리스트

### B. 실제 시험처럼 — 레포에서 풀기

```bash
git clone https://github.com/Hiri-kor/Debugging-Django.git
cd Debugging-Django
python -m venv venv
venv\Scripts\activate              # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

cd exam
python manage.py migrate
python manage.py loaddata books.json comments.json
python manage.py runserver
```

1. [`exam/README.md`](exam/README.md)의 문제를 보고 `exam/books/views.py`, `exam/books/serializers.py`를 고칩니다.
2. Postman으로 요청을 보내 확인합니다. (URL 끝에 `/` 필수)
3. 레포 루트에서 채점합니다.

```bash
python tools/grade.py exam
```

처음부터 다시 풀려면 `git checkout -- exam/`

## 변형 문제로 더 연습하기

```bash
python tools/make_practice.py                                   # 원본 9문제를 practice/ 에 새로 생성
python tools/make_practice.py --mode random --count 6 --force   # 변형 버그 20개 중 6개를 무작위로
python tools/grade.py practice
```

- 증상은 `practice/PRACTICE.md`, 정답은 `practice/ANSWERS.md`
- DB까지 만들어 두므로 `cd practice && python manage.py runserver`로 바로 실행됩니다.

## 구성

```
Debugging-Django/
├── exam/                     # 시험 재현 프로젝트 (버그 9개, 여기서 직접 풀기)
│   ├── README.md             # 문제 · 규칙 · 요청 예시
│   ├── problem_10_11.md      # 서술형 답안지
│   └── books/                # views.py, serializers.py 수정 대상
├── site/index.html           # 학습 사이트 (GitHub Pages 배포 대상)
├── tools/
│   ├── grade.py              # 자동 채점기 (임시 DB에서 9개 요청 검사)
│   └── make_practice.py      # 연습 문제 생성기
├── requirements.txt          # Django 5.2, DRF 3.18, drf-spectacular
└── .github/workflows/deploy-pages.yml
```

채점기는 지정 파일 외 수정 여부, 주석 유무, 서술형 답안은 확인하지 않습니다. 실제 시험 채점 기준과 같다는 보장은 없습니다.

## 사이트 배포 (레포 관리자용)

`master`에 `site/` 변경이 push되면 GitHub Actions가 Pages로 배포합니다.
최초 1회: **Settings → Pages → Source**를 **GitHub Actions**로 지정한 뒤 Actions 탭에서 `Deploy study site`를 실행합니다.
무료 계정은 공개(public) 레포만 Pages를 쓸 수 있습니다.
