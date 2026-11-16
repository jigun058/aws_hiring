# Handoff (2026-11-17 작성)

## 지금 상태

- **코드는 아직 한 줄도 없다.** 이번 세션은 자료 수집과 설계 합의(grilling)만 했다.
- 팀 Notion과 Google Drive를 `docs/context/`로 가져왔다.
- 구현 범위·로직·기술·일정·우선순위를 사용자와 합의했다. **기준 문서는 `docs/DESIGN.md`** 이니 구현 전에 반드시 읽는다.
- 코드 밖의 일(팀원·대회 측 소통)은 `docs/TEAM.md`에 있다. 전부 `대기` 상태(C2만 완료)이며, 사용자가 팀원에게 아직 전달하지 않았다.
- 문서의 커밋과 푸시는 사용자가 직접 한다. 원격 저장소는 비공개다.

## 다음에 할 일 (11/17~18 목표: 로컬에서 5단계가 끝까지 도는 뼈대)

1. 팀원 엔진을 저장소 제자리로 복사한다: `docs/context/assets/drive/서울시데이터/careerlens_db_outputs/`의 `src/*.py`와 `out/*.csv`. **수정하지 않는다.** `python src/recommend_cli.py "..."`가 도는지부터 확인한다(pandas, scikit-learn 필요. `kiwipiepy`는 README의 설치 목록에 있으나 추천에 실제로 필요한지는 미확인).
2. 받지 않은 `cleaned_job_postings.csv`(56MB)를 받는다. 공고를 보여 주는 `postings_for`에 필요할 가능성이 높다(코드로 확인할 것). Drive 파일 ID `1q-4KXCzjSjkmSqOFVzwgUEyCVXp7FPc2`, 큰 파일은 `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t`로 받는다. git에는 넣지 않는다.
3. FastAPI 서버: 에이전트(Bedrock Converse + 도구 4개: 역량 추출, 직무 추천, 공고 검색, 교육과정 검색)와 단계별 API.
4. React 화면(Tailwind + shadcn/ui): `DESIGN.md`의 화면 배치대로 구조와 동작부터. 디자인 시안은 사용자가 Claude Design으로 만들어 `docs/design/`에 넣을 예정(11/19 목표). 오기 전에는 기본 부품 모습으로 둔다.
5. 교육과정 추천은 `docs/context/assets/drive/고용24_교육과정데이터/courses.json`을 쓴다. 구조는 `docs/context/06-교육과정-전처리-과정.md`.

그다음은 `DESIGN.md` 6절의 일정을 따른다. 시간이 남으면 뒤 날짜 목표를 당겨서 한다.

## 환경

- AWS CLI: `~/.local/bin/aws` (v2, 이번 세션에 설치). 프로필 `tae`, 리전 `ap-northeast-2`, 설정은 `~/.aws/config`.
- 로그인이 만료되면 사용자에게 `! aws sso login --profile tae --use-device-code` 실행을 부탁한다. 브라우저가 자동으로 열리지 않으므로 출력된 주소와 코드를 사용자가 직접 입력해야 한다.
- Bedrock 호출 확인됨(서울 리전, 추론 프로필 ID로 호출):
  - 되는 것: `global.anthropic.claude-sonnet-4-6`, `global.anthropic.claude-sonnet-4-5-20250929-v1:0`, `global.anthropic.claude-haiku-4-5-20251001-v1:0`, `apac.amazon.nova-lite-v1:0`, `apac.amazon.nova-pro-v1:0`, `global.amazon.nova-2-lite-v1:0`
  - 안 되는 것: Claude 5 계열(목록에는 보이지만 "이 계정에서 사용 불가"로 거부됨)
- 계정 권한은 AdministratorAccess. 역할·EC2·S3·DynamoDB 생성이 정책 모의 평가에서 허용으로 나왔으나 실제 생성은 아직 안 했다. S3 버킷, DynamoDB 테이블, 인스턴스 프로필은 현재 하나도 없다.
- 이 컴퓨터: Python 3.12(pandas·scikit-learn 미설치), Node·npm·Docker 있음, `unzip` 없음.

## 주의

- **비용이 드는 AWS 명령은 실행 전에 사용자 승인을 받는다.** 예산 한도를 모른다(`TEAM.md` C1). Kaggle 전량 추출 전에는 표본 300건으로 잰 실측 비용을 보고하고 승인받기로 했다.
- 사용자는 코드 구조를 React 경험자로서 직접 검토한다. 화면은 "급조된 데모"가 아니라 실제 서비스처럼 보여야 한다(`DESIGN.md`의 화면 품질 기준 여섯 가지).
- 확인하지 않고 정한 것:
  - Bedrock이 파일(PDF, Word, 이미지)을 직접 받는다는 것과 크기 한도(약 4MB)는 기억에 의존했다. 파일 업로드 구현 첫날 문서로 확인한다.
  - 모델 단가와 추출 비용(Kaggle 전량 약 10달러)은 추정이다.
  - 응답을 글자 단위로 흘려보내는 방식이 CloudFront를 거쳐 동작하는지는 배포 때 확인한다.
- `DESIGN.md`에서 `[기본값]`으로 표시한 규칙 세 가지(인터뷰 멈춤 기준, 근거 등급, 트랙 A 공고 일치도)는 구현 담당이 임시로 정한 것이라 팀원이 바꿀 수 있다. 한곳에 모아 갈아 끼우기 쉽게 만든다.

## 사용자가 할 일

- `docs/TEAM.md`의 T1~T7을 팀원에게 전달하고, C1·C3·C4를 대회 측에 확인(또는 팀원에게 부탁).
- `docs/design/claude-design-prompt.md`의 프롬프트로 Claude Design 시안 제작.
