"""팀원 엔진(recommender.py)이 읽는 입력 파일을 careerlens.db에서 만든다.
로직팀 sim/04_build_engine_inputs.py와 같은 처리이고, 저장 위치만 vendor/engine/ 아래다.
결과: vendor/engine/out/*.csv, vendor/engine/work/s02_postings.pkl, s02_posting_keywords.pkl
기대: 공고 40,479건, 공고별 역량 120,186행
사용법: python backend/scripts/build_engine_inputs.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from careerlens.paths import CAREERLENS_DB, ENGINE_DIR

import pandas as pd

c = sqlite3.connect(f'file:{CAREERLENS_DB}?mode=ro', uri=True)
eo, ew = ENGINE_DIR / 'out', ENGINE_DIR / 'work'
eo.mkdir(exist_ok=True)
ew.mkdir(exist_ok=True)
for t in ['keywords', 'occupations', 'occupation_keyword_profile', 'keyword_relations', 'occupation_licenses', 'occupation_preferences', 'licenses']:
    d = pd.read_sql(f'select * from {t}', c)
    for col in ['is_common_competency', 'is_qualification', 'use_in_matching', 'is_policy_target', 'has_legal_license']:
        if col in d:
            d[col] = d[col].astype(bool)
    d.to_csv(eo / f'{t}.csv', index=False)
p = pd.read_sql('select * from job_postings', c)
p['reg_date'] = pd.to_datetime(p.reg_date, errors='coerce')
p['deadline'] = pd.to_datetime(p.deadline, errors='coerce')
p['is_exact_duplicate'] = p.is_exact_duplicate.astype(bool)
p['is_open_as_of_run'] = p.is_open_as_of_run.astype(bool)
p = p.rename(columns={'career': '경력', 'company': '기업명', 'title': '채용제목', 'region': '근무지역', 'min_education': '최소학력', 'wage_raw': '임금조건'})
p.to_pickle(ew / 's02_postings.pkl')
k = pd.read_sql('select pk.posting_id, k.keyword from posting_keywords pk join keywords k using(keyword_id)', c)
k.to_pickle(ew / 's02_posting_keywords.pkl')
print('공고', len(p), '| 공고별 역량', len(k), '| 저장 위치', ENGINE_DIR)
