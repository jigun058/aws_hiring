"""팀원 엔진(recommender.py)이 읽는 입력 파일을 careerlens.db에서 만든다.
엔진은 원래 팀원 전처리 결과(out/*.csv, work/*.pkl)를 읽는데, 같은 내용을 careerlens.db 표에서 다시 만든다.
결과: engine/out/*.csv, engine/work/s02_postings.pkl, engine/work/s02_posting_keywords.pkl
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
import sqlite3, pandas as pd

c = sqlite3.connect(CAREERLENS_URI, uri=True)
eo, ew = os.path.join(ENGINE_DIR, 'out'), os.path.join(ENGINE_DIR, 'work')
os.makedirs(eo, exist_ok=True); os.makedirs(ew, exist_ok=True)
for t in ['keywords', 'occupations', 'occupation_keyword_profile', 'keyword_relations', 'occupation_licenses', 'occupation_preferences', 'licenses']:
    d = pd.read_sql(f'select * from {t}', c)
    for col in ['is_common_competency', 'is_qualification', 'use_in_matching', 'is_policy_target', 'has_legal_license']:
        if col in d: d[col] = d[col].astype(bool)
    d.to_csv(os.path.join(eo, f'{t}.csv'), index=False)
p = pd.read_sql('select * from job_postings', c)
p['reg_date'] = pd.to_datetime(p.reg_date, errors='coerce'); p['deadline'] = pd.to_datetime(p.deadline, errors='coerce')
p['is_exact_duplicate'] = p.is_exact_duplicate.astype(bool); p['is_open_as_of_run'] = p.is_open_as_of_run.astype(bool)
p = p.rename(columns={'career': '경력', 'company': '기업명', 'title': '채용제목', 'region': '근무지역', 'min_education': '최소학력', 'wage_raw': '임금조건'})
p.to_pickle(os.path.join(ew, 's02_postings.pkl'))
k = pd.read_sql('select pk.posting_id, k.keyword from posting_keywords pk join keywords k using(keyword_id)', c)
k.to_pickle(os.path.join(ew, 's02_posting_keywords.pkl'))
print('공고', len(p), '| 공고별 역량', len(k), '| 저장 위치', ENGINE_DIR)
