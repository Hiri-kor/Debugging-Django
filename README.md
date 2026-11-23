# Debugging-Django

SSAFY 16기 5회차 월말평가(파이썬 트랙 · DRF 디버깅) 재시험 대비 자료입니다.

> 시험 원본(`skeleton/`)과 시험지 PDF는 `.gitignore`로 제외되어 있습니다.
> 아래 도구는 레포 루트에 `skeleton/`이 있다고 가정합니다.

## 구성

| 경로 | 내용 |
|------|------|
| [`site/index.html`](site/index.html) | 학습 사이트. 브라우저로 바로 열기. 문제 01–09 풀이, 서술형, 변형 퀴즈, 개념 정리, 정답 코드, 에러 사전, 제출 체크리스트 |
| [`tools/make_practice.py`](tools/make_practice.py) | 연습 문제 생성기. `skeleton/`을 복사해 시험 원본 버그 9개 또는 변형 버그를 무작위로 심음 |
| [`tools/grade.py`](tools/grade.py) | 자동 채점기. 임시 DB에서 9개 요청을 보내 PASS/FAIL과 점수(80점 만점) 출력 |

## 사이트 배포 (GitHub Pages)

`site/` 폴더가 그대로 사이트가 됩니다. `master`에 `site/` 변경이 push되면 [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)이 자동 배포합니다.

최초 1회 설정:

1. 레포 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 지정
2. **Actions** 탭에서 `Deploy study site` 워크플로를 **Run workflow**로 한 번 실행
3. 배포 주소: `https://hiri-kor.github.io/Debugging-Django/`

> 무료 계정에서는 **공개(public) 레포만** Pages를 쓸 수 있습니다. 비공개로 두려면 GitHub Pro 이상이 필요합니다.

```
Debugging-Django/
├── .github/workflows/deploy-pages.yml   # site/ → GitHub Pages
├── site/index.html                      # 학습 사이트 (배포 대상)
├── tools/
│   ├── make_practice.py                 # 연습 문제 생성기
│   └── grade.py                         # 자동 채점기
├── skeleton/        (gitignore)         # 시험 원본 프로젝트
├── practice*/       (gitignore)         # 생성된 연습 프로젝트
└── venv/            (gitignore)
```

## 사용법

```bash
# 준비 (처음 한 번)
python -m venv venv
venv\Scripts\activate
pip install -r skeleton/requirements.txt

# 연습 문제 만들기 → practice/PRACTICE.md 의 증상을 보고 고치기
python tools/make_practice.py                                # 시험 원본 9문제
python tools/make_practice.py --mode random --count 6 --force   # 변형 6문제

# 채점
python tools/grade.py practice
python tools/grade.py skeleton
```

- 정답은 `practice/ANSWERS.md`에 있습니다. 다 풀고 나서 여세요.
- 두 스크립트 모두 원본 `skeleton/` 코드와 `db.sqlite3`를 수정하지 않습니다.
- 채점기는 지정 파일 외 수정 여부, 주석, 서술형 답안은 확인하지 않습니다.
