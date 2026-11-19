# CareerLens (AI Bootcamp Innovation Challenger 2026)

개인 경험 기반 AI 커리어 탐색 Agent. 경험 수집 → 경험 카드 → 직무 추천 → 채용공고 연결 → 교육과정 추천.

## 역할 분담

- **세부 로직·처리 방법 설계**: 통계학 전공 팀원들이 Notion에 정리한다. 명세(P0~P7)는 아직 작성 중이며 계속 바뀐다.
- **구현**: 이 저장소 사용자 혼자 한다. 이 저장소는 구현용이다.
- 명세가 비어 있거나 서로 어긋나면 임의로 정하지 말고 사용자에게 알린다.
- 코드 밖의 일(팀원에게 전달·부탁할 것, 대회 측에 확인할 것, 발표 담당에게 넘길 기술 자료)은 `docs/TEAM.md`에서 관리한다. 작업 중 그런 일이 생기면 바로 거기에 적고, 끝난 항목은 지우지 말고 상태를 `완료`로 바꾼다.

- 발표에 쓰거나 피해야 할 사실(규모 숫자, 검증 결과, 틀리기 쉬운 표현, 한계, 바뀐 점수)은 `docs/PRESENTATION_FACTS.md`에 모은다. 비개발자 팀원이 읽는다. 구현 중 그런 사실이 생기거나 숫자가 바뀌면 같은 작업 안에서 바로 고치고 맨 위 "마지막 갱신" 날짜를 바꾼다. 팀 공유본은 Claude Docs 문서 "CareerLens 발표 참고 사실"(https://claude.ai/artifact/XFrff8GQPAeivpfH6iqNuT)이다. 이 파일을 고치면 그 문서의 해당 섹션도 Docs 커넥터로 고친다(새로 만들지 않는다). 원본은 이 파일이다.
- 나중에 할 구현 작업과 결정을 기다리는 작업은 `docs/BACKLOG.md`에 적는다. 미루거나 보류하기로 한 일은 그 자리에서 바로 적고, 끝나면 지우지 않고 `완료`로 바꾼다. 작업을 시작할 때 관련 항목이 있는지 먼저 본다.

## 설계 문서

- `docs/DESIGN.md`: 어떤 기능을 어떤 로직으로 만드는지 팀원에게 설명하는 문서. 비개발자인 팀원이 읽는다. **로직·범위·일정이 바뀌면 코드와 같은 작업 안에서 이 문서도 고치고**, "바뀐 결정 기록"에 한 줄 남긴다. `[기본값]` 표시는 명세가 없어 임시로 정한 규칙이다.
- 구현 범위, 기술 구성, 일정, 우선순위의 기준은 이 문서다.

## 코드 구조와 명령

- `backend/vendor/`: 로직팀 코드 원본(엔진 `engine/src/`, P1 참조 구현 `p1/`). **수정 금지**. 바꿀 동작은 `backend/careerlens/`에서 감싼다.
- `backend/careerlens/paths.py`: vendor 코드는 import할 때 환경 변수로 DB를 열고 형제 모듈을 최상위 이름으로 import한다. 그래서 vendor 모듈보다 이 모듈을 먼저 import한다. 우리 모듈 이름을 `common`, `knowledge` 등 vendor와 겹치게 짓지 않는다.
- `backend/careerlens/experience_rules.py`: 경험 규칙 보정본(엔진·경험 카드 공용).
- `backend/careerlens/cards.py`: 문장 → 역량·근거 등급(시뮬레이션 07의 카드 코드). `recommend.py`: 엔진을 상속한 `Recommender`(시뮬레이션 6·7·8번, 경험 종류 보정). 엔진 준비 약 1.5초, 추천 한 번 약 0.15초.
- 화면 시안: `docs/design/CareerLens v2.dc.html`이 최종본(사용자가 Claude Design으로 수정을 거친 것). `CareerLens.dc.html`은 이전 판. `docs/design/uploads/`(참고 캡처)는 git 밖.
- 큰 데이터(`backend/data/careerlens.db`, `courses.json`)와 엔진 입력(`backend/vendor/engine/out|work/`)은 git 밖이다. 원본은 `docs/context/assets/drive/`.
- 준비: `python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt`
- 엔진 입력 만들기: `cd backend && ../.venv/bin/python scripts/build_engine_inputs.py` (공고 40,479 / 공고별 역량 120,186)
- 공고 분석(P2 규칙 처리) 전량: `cd backend && ../.venv/bin/python scripts/analyze_postings.py` → `backend/data/derived/posting_analysis.jsonl`(git 밖, 약 3분, 63MB). 구절 목록은 파일에 없으니 필요하면 `posting_analysis.analyze()`로 다시 계산.
- LLM(Bedrock)은 `careerlens/llm.py` 한 곳에서만 부른다. LLM 결과는 코드가 검사하고(`interview.quote_ok`·`safe_question`, 숫자 검사), 실패하면 None → 호출한 쪽이 규칙 대체를 쓴다. 시험은 `llm.converse`를 가짜로 바꿔 끼워 실제 호출 없이 돈다(`tests/test_api_interview.py`). 실제 연결 확인은 `AWS_PROFILE=tae ../.venv/bin/python scripts/smoke_llm.py`(호출 약 6번).
- 서버: `cd backend && ../.venv/bin/uvicorn careerlens.api:app --reload` (준비 약 3.5초, 메모리 약 700MB). 단계별 API는 `careerlens/api.py`, 목록은 DESIGN.md 5절.
- 화면: `frontend/`(Vite + React + Tailwind v4, JSX). 상태와 서버 호출은 모두 `src/store.js`(브라우저 저장소에 저장), 단계 화면은 `src/steps.jsx`, 첫 화면·공고 분석·재취업 이야기는 `src/pages.jsx`. 준비 `cd frontend && npm install`. 개발 `npm run dev`(5173, `/api`는 8000으로 넘김), 배포용 `npm run build` → `frontend/dist/`(git 밖)를 FastAPI가 `/`에서 낸다. 글꼴은 Google Fonts 나눔고딕(TTF는 파일당 4.5MB라 안 씀).
- 화면 확인은 헤드리스 브라우저로 한다: 스크래치 폴더에 `npm install playwright` 후 스크립트로 흐름을 돌려 1280·1024px 캡처. LLM 없이 보려면 서버를 `AWS_PROFILE=none-offline AWS_EC2_METADATA_DISABLED=true`로 띄운다(규칙 대체로 돎, 비용 없음).
- 시험: `cd backend && ../.venv/bin/pytest -q`. 로직팀 미해결 건은 `xfail(strict=True)`로 고정한다(고쳐지면 시험이 알려 줌).

## Git

- 커밋과 푸시는 사용자가 직접 한다. Claude는 `git commit`, `git push`를 실행하지 않고, 변경을 스테이징하고 커밋 메시지를 제안하는 데까지만 한다.
- 커밋 메시지에 Claude 관련 문구(`Co-Authored-By`, 세션 링크 등)를 넣지 않는다. 기여자 목록에 Claude가 남으면 안 된다.

## 세션 방식

하나의 세션을 compact하며 길게 끌지 않는다. 세션마다 handoff를 남기고 새 세션에서 이어 간다.

- 세션 시작: `docs/HANDOFF.md`가 있으면 가장 먼저 읽는다.
- 세션 종료(사용자가 handoff를 요청할 때): `docs/HANDOFF.md`를 덮어쓴다. 내용은 지금 상태, 이번에 결정한 것과 이유, 다음에 할 일, 막힌 것·팀원에게 물어볼 것. 이전 버전은 git 기록에 남으므로 파일을 늘리지 않는다.
- 여러 세션에 걸쳐 유효한 사실(구조, 명령어, 규칙)은 handoff가 아니라 이 파일에 적는다.

## 맥락 자료 (`docs/context/`)

팀 Notion과 Google Drive를 2026-11-17에 가져온 스냅샷이다(07은 같은 날 오후 갱신분, 08은 같은 날 밤 회의 결과). 원본이 바뀌었을 수 있으니 오래됐다 싶으면 다시 가져올지 사용자에게 묻는다. Notion과 Drive는 읽기 전용으로만 다룬다.

| 파일 | 내용 |
| --- | --- |
| `00-ai-bootcamp-innovation-challenger-2026.md` | 서비스 한 장 요약 (5단계 흐름, 사용 예시) |
| `01-세부-로직-및-처리-방법.md` | 팀 역할 정의, P0~P7 명세 계획, 투트랙(A 대학생·취준생 / B 중장년·경력단절 여성) 비교표 |
| `02-aws-계정-제원.md` | 대회 제공 AWS 샌드박스 계정, CLI 프로필, 할당량, 주의점 |
| `03-json형식.md` | 경험 카드 / 채용공고 JSON 템플릿 |
| `04-케글데이터-정돈.md` | 트랙 A용 Kaggle 공고 정제 기준과 진행 상황 |
| `05-google-drive-ai-경진대회.md` | Drive 파일 목록, 178개 역량 키워드 사전, DB 구조, 팀원 추천 엔진 점수식 |
| `06-교육과정-전처리-과정.md` | 고용24 교육과정 전처리, `courses.json` 구조 |
| `07-노션-갱신-1117.md` | 11/17 오후 Notion 갱신(P1 역량 사전 182개·규칙서, P3 경험카드·인터뷰 명세, P4 트랙 A 점수식, 시뮬레이션)과 팀 대화 요지. 명세 원문은 `assets/notion-1117/` |
| `08-회의-1117.md` | 11/17 팀 회의 결과(트랙 A 제외, 마감 11/22 등)와 P2 서울시 공고 분석 명세 요약. 첨부(P1 최종 사전, P1 참조 구현, P2 원문)는 `assets/notion-1118/` |

`assets/drive/`에는 팀원이 만든 데이터와 파이썬 코드(추천 엔진 포함) 사본이 있다. 10MB 넘는 파일 4개(`careerlens.db` 등)는 받지 않았다.

## AWS

- 대회 대여 계정(Innovation Sandbox)이다. 예산 초과 시 동결·정리될 수 있고 대여 종료 시 리소스가 전부 삭제된다.
- 리소스를 만들거나 비용이 드는 명령은 실행 전에 사용자 확인을 받는다. GPU 할당량은 0이다.
- 자세한 내용은 `docs/context/02-aws-계정-제원.md`.
