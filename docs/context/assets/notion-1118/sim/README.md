# CareerLens 시뮬레이션 코드 (로직 담당)

11/17에 돌린 시뮬레이션 코드 전체다. 매핑 규칙과 점수식이 의도대로 동작하는지 확인하려고 만든 **검증·분석용 코드**이고, 서비스 코드로 다듬은 것은 아니다. 개발 구현의 참고와 결과 비교용으로 쓴다.

관련 문서: P1 규칙서, P2 서울시 공고 분석 명세, P3 경험 카드·인터뷰 명세, P4 트랙 A 점수식, 「CareerLens 추천 시뮬레이션 결과 (트랙 A·B)」 문서

## 1. 준비

**필요한 것**: Python 3.10 이상, pandas, numpy. 그 밖의 패키지는 쓰지 않는다.

**`data/` 폴더에 넣을 파일** (용량이 커서 묶음에 넣지 않음)

| 파일 이름 (이 이름으로 넣기) | 원본 |
|---|---|
| `careerlens.db` | 팀 careerlens.db (서울시 공고 DB) |
| `courses.json` | 고용24 국비 과정 데이터 |
| `postings_usa_candidates_no_senior_6343.csv` | Kaggle 미국 공고 6,343건 (트랙 A 시뮬레이션에만 필요) |

이미 들어 있는 파일: `P1_competency_dictionary_final.csv`, `P1_skill_layer_final.csv`, `P1_gold_mapping_50.csv`, `P1_validation_30.csv`

다른 위치에 있으면 환경 변수로 알려 준다: `CAREERLENS_DB`, `COURSES_JSON`, `KAGGLE_CSV`(파일 경로), `CL_DATA`, `CL_OUT`(폴더). 경로는 모두 `paths.py`에 모여 있다.

## 2. 실행 순서

| 순서 | 파일 | 하는 일 | 결과 (`out/`) | 필요 데이터 |
|---|---|---|---|---|
| 0 | `run_p1_tests.py` | P1 매핑 자동 시험(정답 50 + 검증 30) | 화면 출력 | db, courses |
| 1 | `01_tag_postings.py` | Kaggle 공고 6,343건에 P1 규칙으로 역량 번호 붙이기 | `posting_kw.json` | db, courses, Kaggle |
| 2 | `02_clean_track_a.py` | Kaggle 공고 보정: 중복·비대상 표시, 직무분류 다시 매기기, 신뢰도 | `track_a_postings_보정본.csv`, `track_a_보정_요약.json` | 1번 결과, Kaggle |
| 3 | `03_build_kaggle_db.py` | 트랙 A용 DB(careerlens.db와 같은 표 구조) | `careerlens_kaggle.db` | 2번 결과, db |
| 4 | `04_build_engine_inputs.py` | 팀원 엔진이 읽는 입력 파일을 careerlens.db에서 만들기 | `engine/out/*.csv`, `engine/work/*.pkl` | db |
| 5 | `05_sim_track_a.py` | 트랙 A 점수식(P4 + 수정안 4가지) 시뮬레이션, 가상 인물 3명 | 화면 출력 | 2번 결과 |
| 6 | `06_sim_track_b_engine.py` | 트랙 B 팀원 엔진 시뮬레이션, 가상 인물 3명 | 화면 출력 | 4번 결과 |
| 7 | `07_sim_full.py` | **통합 시뮬레이션**: P3 경험 카드(역량·근거 등급) → 트랙 A P4 점수 / 트랙 B 엔진(카드 등급을 근거 강도로 넣음) | `sim_full.json` | 2·4번 결과, db, courses |

**트랙 B만 필요하면** `run_p1_tests.py` → `04` → `06` 또는 `07`만 돌리면 된다(Kaggle 파일 없이 07을 돌리면 트랙 A 부분에서 멈추므로, 그때는 07의 트랙 A 부분을 건너뛰도록 고쳐 쓴다).

`extras/`: 점수식 원안과 수정안을 비교할 때 쓴 탐색용 스크립트(`sim_score.py` 원안, `sim2.py` 후보 규칙 변경, `sim3.py` 분모 최소 3, `sim_missing.py`·`sim_noise.py` 직무별 역량·잡음 확인). 결과 재현용으로만 남겼다.

## 3. 파일 구성

| 파일 | 내용 |
|---|---|
| `paths.py` | 모든 경로 |
| `p1_engine.py`, `p1_filters.py`, `p1_rule175.py`, `p1_aliases_v1.py`, `aliases.py` | P1 매핑 참조 구현. `map_sentence(문장, 'A' 또는 'B')` → 역량 번호 |
| `engine/src/` | 팀원 엔진 `recommender.py`, `knowledge.py`, `licenses_kb.py`, `common.py` **원본 그대로**(11/16 Drive 버전, 수정 없음) |
| `07_sim_full.py` 안의 P3 부분 | `build_card()`: 문장마다 P1 사전 + careerlens.db 경험 규칙으로 역량을 붙이고, P3 3.1절 판정표로 L1~L3 등급을 정함. `user_profile()`: 같은 역량은 최고 등급 |
| `07_sim_full.py` 안의 트랙 B 부분 | 엔진 코드는 고치지 않고, `extract` 결과의 `evidence_strength`를 카드 등급(L3 1.0 · L2 0.75 · L1 0.5)으로 바꿔 넣음. 공고는 `is_near_duplicate`와 같은 회사·제목을 빼고 6건 |

## 4. 기대 결과 (로직 담당이 11/18 새 폴더에서 다시 돌려 확인)

- `run_p1_tests.py`: 정답 50/50, 검증 28/30 (불일치 VA09, VB09는 규칙서의 미해결 건)
- `02`: 트랙 A 사용 공고 4,398건(중복 1,787 · 비대상 275 제외)
- `04`: 공고 40,479건, 공고별 역량 120,186행
- `07`: 시뮬레이션 문서의 상위 공고·추천 직무와 같음. 김개발의 그룹 수만 1~2건 다름(시뮬레이션 뒤에 하드웨어 분류 규칙을 보완했기 때문)

## 5. 알아 둘 점

- **경험 카드 부분은 간이 구현이다.** 실제 서비스는 LLM이 슬롯을 뽑고 인터뷰로 채우지만, 시뮬레이션은 입력 문장에서 바로 카드를 만들었다. 행동·성과 판정도 정규식으로 단순하게 했다(`ACTION`, `RESULT`, `LEARN`).
- **경험 규칙 오류가 그대로 나온다.** careerlens.db·`knowledge.py`의 단어 하나짜리 경험 규칙 때문에 "부트캠프 → 행사 진행", "보고서 작성 시간을 줄였다 → 발표", "거래처 → 영업"이 잡힌다. 고치는 곳은 `knowledge.py`의 `EXPERIENCE_RULES`(EX024 767줄, EX027 773줄, EX036 791줄)다.
- **트랙 A 공고 역량은 규칙으로 붙인 값**이라 필수·우대 구분이 없고 잡음이 있다.
- **유사 기술 계수(0.9·0.6 등)는 시뮬레이션에 넣지 않았다.** 같은 역량 번호끼리만 일치로 봤다.
- 가상 인물과 결과 판정은 모두 로직 담당이 만든 것이며 사람 검수가 아니다.
