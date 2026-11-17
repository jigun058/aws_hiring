"""careerlens_kaggle.db 만들기: 트랙 A(Kaggle) 공고를 careerlens.db와 같은 표 구조로 정리. 분석용 스크립트."""
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import re, csv, json, sqlite3, os, math
import numpy as np, pandas as pd

SRC = TRACKA_CLEAN
DICT = DICT_CSV
OUT = KAGGLE_DB
TEAM = sqlite3.connect(CAREERLENS_URI, uri=True)

df = pd.read_csv(SRC, low_memory=False)
df = df[df['트랙A사용'] == 1].reset_index(drop=True)
dic = list(csv.DictReader(open(DICT, encoding='utf-8-sig')))
CAT = {int(r['kw_idx']): r['분류코드'] for r in dic}

# ---------- 세부 직무 ----------
ROLE_RULES = {
 'software_engineering': [
  ('풀스택 개발자', 'Full Stack Engineer', r"full.?stack"),
  ('프론트엔드 개발자', 'Frontend Engineer', r"front.?end|\breact\b(?! native)|\bui engineer|web developer|javascript engineer|\bvue\b|angular"),
  ('모바일 앱 개발자', 'Mobile Engineer', r"\bios\b|android|mobile|react native|flutter|swift"),
  ('백엔드 개발자', 'Backend Engineer', r"back.?end|\bapi\b|server|golang|\bgo engineer|java engineer|python developer|django|rails|node"),
  ('데브옵스·인프라 엔지니어', 'DevOps / Infrastructure Engineer', r"devops|\bsre\b|site reliability|infrastructure|platform engineer|cloud engineer|systems engineer|kubernetes|distributed systems"),
  ('보안 엔지니어', 'Security Engineer', r"security"),
  ('QA·테스트 엔지니어', 'QA / Test Engineer', r"\bqa\b|quality assurance|\btest|sdet"),
  ('임베디드·펌웨어 개발자', 'Embedded / Firmware Engineer', r"embedded|firmware|robotics|autonomy|motion planning"),
  ('소프트웨어 엔지니어(일반)', 'Software Engineer (general)', r".*"),
 ],
 'data_ai': [
  ('데이터 분석가', 'Data Analyst', r"data analy|analytics|business intelligence|\bbi\b|insights analyst"),
  ('데이터 엔지니어', 'Data Engineer', r"data engineer|data platform|etl|pipeline"),
  ('데이터 사이언티스트', 'Data Scientist', r"data scien"),
  ('머신러닝·AI 엔지니어', 'ML / AI Engineer', r"machine learning|\bml\b|\bai\b|deep learning|nlp|computer vision|mlops|llm"),
  ('리서치 사이언티스트', 'Research Scientist', r"research"),
  ('데이터·AI(일반)', 'Data / AI (general)', r".*"),
 ],
 'hardware_engineering': [
  ('기계 엔지니어', 'Mechanical Engineer', r"mechanical|mechatronic|structur|propulsion|aerodynamic|aerospace|thermal|gnc"),
  ('전기·전자 엔지니어', 'Electrical Engineer', r"electrical|\brf\b|hardware|avionics|electronics"),
  ('제조·공정 엔지니어', 'Manufacturing / Process Engineer', r"manufactur|process|quality engineer|industrial"),
  ('하드웨어 엔지니어(일반)', 'Hardware Engineer (general)', r".*"),
 ],
 'sales': [
  ('영업 개발(SDR·BDR)', 'Sales Development (SDR/BDR)', r"\bsdr\b|\bbdr\b|sales development|business development"),
  ('기술 영업', 'Sales / Solutions Engineer', r"sales engineer|solutions engineer|pre.?sales"),
  ('영업 담당(AE·AM)', 'Account Executive / Manager', r"account executive|account manager|\bae\b"),
  ('영업(일반)', 'Sales (general)', r".*"),
 ],
 'design': [('프로덕트·UX 디자이너', 'Product / UX Designer', r"product design|\bux\b|user experience|interaction"),
            ('디자이너(일반)', 'Designer (general)', r".*")],
 'marketing': [('마케터', 'Marketing', r".*")],
 'product': [('프로덕트 매니저', 'Product Manager', r".*")],
 'people_hr': [('채용·인사', 'Recruiting / HR', r".*")],
 'support': [('고객 지원', 'Customer Support', r".*")],
 'operations': [('운영·사무', 'Operations / Admin', r".*")],
 'finance_legal': [('재무·법무', 'Finance / Legal', r".*")],
 'healthcare': [('간호', 'Nursing', r"\bnurse\b|\brn\b|\blpn\b|nurse practitioner"),
                ('의료·보건(일반)', 'Healthcare (general)', r".*")],
 'unclassified': [('미분류', 'Unclassified', r".*")],
}
FAM_KO = {'software_engineering': '소프트웨어 개발', 'data_ai': '데이터·AI', 'hardware_engineering': '하드웨어 엔지니어링', 'sales': '영업',
          'design': '디자인', 'marketing': '마케팅', 'product': '프로덕트', 'people_hr': '인사·채용', 'support': '고객 지원',
          'operations': '운영', 'finance_legal': '재무·법무', 'healthcare': '의료·보건', 'unclassified': '미분류'}
COMPILED = {f: [(ko, en, re.compile(p, re.I)) for ko, en, p in rules] for f, rules in ROLE_RULES.items()}

def first_chunk(r):
    parts = [p for p in re.split(r",|/|&|\+|\band\b|;|\(|\.\s", r) if p.strip()]
    return parts[0] if parts else r

def role_of(fam, role_text, title):
    rules = COMPILED.get(fam, COMPILED['unclassified'])
    for txt in (first_chunk(role_text), first_chunk(title), role_text, title):
        for ko, en, rx in rules[:-1]:
            if txt and rx.search(txt):
                return ko, en
    return rules[-1][0], rules[-1][1]

role_text = df['보정_직무명'].fillna('').astype(str)
title = df['채용공고제목'].fillna('').astype(str)
fam = df['보정_직무분류'].fillna('unclassified')
roles = [role_of(f, r, t) for f, r, t in zip(fam, role_text, title)]
df['role_ko'] = [r[0] for r in roles]
df['role_en'] = [r[1] for r in roles]

# 작은 직무(10건 미만)는 직무군 일반으로 합침
cnt = df.groupby(['보정_직무분류', 'role_ko']).size()
gen = {f: rules[-1] for f, rules in ROLE_RULES.items()}
for (f, rk), n in cnt.items():
    if n < 10 and rk != gen.get(f, gen['unclassified'])[0]:
        m = (df['보정_직무분류'] == f) & (df['role_ko'] == rk)
        df.loc[m, 'role_ko'] = gen[f][0]; df.loc[m, 'role_en'] = gen[f][1]

occ = (df.groupby(['보정_직무분류', 'role_ko', 'role_en']).size().reset_index(name='posting_count')
       .sort_values(['보정_직무분류', 'posting_count'], ascending=[True, False]).reset_index(drop=True))
fam_ids = {f: f'KFAM{i+1:02d}' for i, f in enumerate(sorted(occ['보정_직무분류'].unique()))}
occ['occupation_id'] = [f'KOCC{i+1:03d}' for i in range(len(occ))]
oid = {(r['보정_직무분류'], r['role_ko']): r['occupation_id'] for _, r in occ.iterrows()}
df['occupation_id'] = [oid[(f, r)] for f, r in zip(df['보정_직무분류'], df['role_ko'])]
df['posting_id'] = [f'K{i+1:06d}' for i in range(len(df))]

# ---------- keywords ----------
team_kw = pd.read_sql('select keyword_id, discriminative_weight, idf, idf_norm, is_common_competency, match_patterns from keywords', TEAM).set_index('keyword_id')
cat_avg = pd.read_sql('select category_code, avg(discriminative_weight) w from keywords group by category_code', TEAM).set_index('category_code')['w']
kw_rows = []
for r in dic:
    i = int(r['kw_idx']); kid = f'KW{i+1:04d}'
    t = team_kw.loc[kid] if kid in team_kw.index else None
    kw_rows.append(dict(keyword_id=kid, kw_idx=i, keyword=r['키워드'], category_code=r['분류코드'], keyword_category=r['분류명'],
                        definition=r['정의'], synonyms=r['국문_별칭'], en_aliases=r['영문_별칭'], match_patterns=(t['match_patterns'] if t is not None else None),
                        usage=r['용도'], is_common_competency=(int(t['is_common_competency']) if t is not None else 0),
                        discriminative_weight=(float(t['discriminative_weight']) if t is not None else round(float(cat_avg[r['분류코드']]), 4)),
                        weight_source=('careerlens.db' if t is not None else '같은 분류 평균(임시, U-01)')))
kw = pd.DataFrame(kw_rows)

# ---------- posting_keywords ----------
pk = []
for pid, ks in zip(df['posting_id'], df['역량번호'].fillna('').astype(str)):
    for k in [int(x) for x in ks.split(';') if x.strip().isdigit()]:
        pk.append(dict(posting_id=pid, keyword_id=f'KW{k+1:04d}', found_in='description', source='p1_rule',
                       requirement_type=None, status='confirmed'))
pk = pd.DataFrame(pk)

# ---------- occupation_keyword_profile ----------
pk_o = pk.merge(df[['posting_id', 'occupation_id']], on='posting_id')
n_occ = df.groupby('occupation_id').size()
overall = pk.groupby('keyword_id').posting_id.nunique() / len(df)
prof = pk_o.groupby(['occupation_id', 'keyword_id']).posting_id.nunique().reset_index(name='evidence_count')
prof['posting_share'] = prof.apply(lambda r: r.evidence_count / n_occ[r.occupation_id], axis=1)
prof['lift'] = prof.apply(lambda r: r.posting_share / max(overall[r.keyword_id], 1e-9), axis=1)
prof = prof[(prof.evidence_count >= 3) & (prof.posting_share >= 0.08)]
prof['importance'] = np.select([prof.posting_share >= 0.40, prof.posting_share >= 0.20], ['required', 'major'], 'supplementary')
prof['combined_score'] = prof.posting_share.round(4)
prof = prof.merge(kw[['keyword_id', 'keyword', 'category_code']], on='keyword_id')
prof['sources'] = 'posting_share(p1_rule)'
prof['use_in_score'] = (~prof.category_code.isin(['C4', 'C5'])).astype(int)

# ---------- occupations ----------
occ['job_family_id'] = occ['보정_직무분류'].map(fam_ids)
occ['job_family_name'] = occ['보정_직무분류'].map(FAM_KO)
occ['job_family_code'] = occ['보정_직무분류']
occ['occupation_name'] = occ['role_ko']; occ['occupation_name_en'] = occ['role_en']
entry = df.assign(e=df['CareerLens경력수준'].eq('entry')).groupby('occupation_id').e.mean()
occ['entry_share'] = occ.occupation_id.map(entry).round(3)
occ['open_posting_count'] = occ['posting_count']
occ['market_size_log'] = np.log10(occ['posting_count'] + 1).round(3)
occ['n_profile_keywords'] = occ.occupation_id.map(prof[prof.use_in_score == 1].groupby('occupation_id').size()).fillna(0).astype(int)
occ['has_legal_license'] = 0
occ_out = occ[['occupation_id', 'occupation_name', 'occupation_name_en', 'job_family_id', 'job_family_name', 'job_family_code', 'posting_count',
               'open_posting_count', 'market_size_log', 'entry_share', 'n_profile_keywords', 'has_legal_license']]

# ---------- job_postings ----------
jp = pd.DataFrame(dict(
    posting_id=df.posting_id, source_key=df['CareerLens공고고유키'], source=df['수집출처'], occupation_id=df.occupation_id,
    original_occupation_label=df['CareerLens직무분류'], job_family_code=df['보정_직무분류'], role_text=df['보정_직무명'],
    company=df['기업명'], title=df['채용공고제목'], job_description_raw=df['채용공고상세내용'],
    required_text=None, preferred_text=None, region=df['근무지역'], remote_type=df['원격근무유형'],
    career=df['CareerLens경력수준'], min_years=df['CareerLens최소경력연수'], career_status=df['경력분류상태'],
    wage_raw=df['급여원문'], wage_min=df['최소급여'], wage_max=df['최대급여'], wage_currency=df['급여통화'], wage_period=df['급여지급주기'],
    reg_date=df['표준공고등록일'], url=df['채용공고URL'], apply_url=df['지원URL'],
    is_truncated=df['공고본문잘림의심여부'], is_multi_role=df['다중직무공고의심'], reliability=df['공고신뢰도'],
    n_score_keywords=df['점수용역량수'], skills=df['세부기술'], needs_status_check=1))
po = pd.DataFrame(dict(posting_id=df.posting_id, occupation_id=df.occupation_id, is_primary=1))

info = pd.DataFrame([dict(key=k, value=v) for k, v in {
    'name': 'careerlens_kaggle.db', 'built_at': '2026-11-17', 'track': 'A (Kaggle 미국 공고)',
    'source': 'track_a_postings_보정본.csv 중 트랙A사용=1', 'n_postings': len(df), 'n_occupations': len(occ),
    'keyword_dictionary': 'P1_competency_dictionary_final.csv (182개)',
    'posting_keywords_source': 'P1 규칙(p1_rule). requirement_type은 11/19 AI 추출 후 채움',
    'profile_rule': 'posting_share>=0.40 required / >=0.20 major / >=0.08 supplementary, evidence_count>=3',
    'needs_status_check': '트랙 A 공고는 모두 모집 여부 확인 필요(K-08)'}.items()])

if os.path.exists(OUT): os.remove(OUT)
con = sqlite3.connect(OUT)
for name, t in [('keywords', kw), ('occupations', occ_out), ('occupation_keyword_profile',
                prof[['occupation_id', 'keyword_id', 'keyword', 'category_code', 'importance', 'combined_score', 'posting_share', 'lift', 'evidence_count', 'use_in_score', 'sources']]),
                ('job_postings', jp), ('posting_occupations', po), ('posting_keywords', pk), ('build_info', info)]:
    t.to_sql(name, con, index=False)
con.execute('create index ix_pk_post on posting_keywords(posting_id)'); con.execute('create index ix_pk_kw on posting_keywords(keyword_id)')
con.execute('create index ix_jp_occ on job_postings(occupation_id)'); con.execute('create index ix_prof_occ on occupation_keyword_profile(occupation_id)')
con.commit(); con.close()
print('size MB', round(os.path.getsize(OUT) / 1e6, 1))
print(occ_out[['occupation_id', 'job_family_name', 'occupation_name', 'posting_count', 'entry_share', 'n_profile_keywords']].to_string(index=False))
