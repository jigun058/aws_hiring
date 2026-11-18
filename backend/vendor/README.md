# 로직팀 코드 원본 (수정 금지)

팀원이 고쳐서 다시 주면 그대로 갈아 끼울 수 있게 이 폴더의 파일은 손대지 않는다. 바꿔야 할 동작은 `careerlens/` 쪽에서 감싸서 처리한다.

| 폴더 | 원본 | 받은 날 |
| --- | --- | --- |
| `engine/src/` | 팀원 추천 엔진 `recommender.py`, `knowledge.py`, `licenses_kb.py`, `common.py` (Drive `서울시데이터/careerlens_db_outputs/src/`와 같음 확인) | 11/16 Drive, 11/18 시뮬레이션 묶음 |
| `p1/` | P1 역량 매핑 참조 구현 `p1_engine.py` 외 4개 (Notion 참조 구현 묶음과 시뮬레이션 묶음이 같음 확인) | 11/18 |

- 엔진 입력(`engine/out/*.csv`, `engine/work/*.pkl`)은 git에 넣지 않는다. `python scripts/build_engine_inputs.py`로 `data/careerlens.db`에서 만든다.
- 엔진의 `common.py`는 기준일을 `2026-11-12`로 고정해 두었다(마감 D-day 계산).
