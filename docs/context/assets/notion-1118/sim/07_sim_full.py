"""P3(경험 카드) + P4(트랙 A 점수식) + 팀원 엔진(트랙 B) 통합 시뮬레이션. 분석용 스크립트."""
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import sys, re, json, csv, sqlite3, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
sys.path.insert(0, HERE)
import p1_engine as E

D = {int(r['kw_idx']): (r['분류코드'], r['키워드']) for r in csv.DictReader(open(DICT_CSV, encoding='utf-8-sig'))}
NAME2IDX = {v[1]: k for k, v in D.items()}
con = sqlite3.connect(CAREERLENS_URI, uri=True)
EXR = []
for r in con.execute("select expression_pattern, keyword_id, match_type from experience_keyword_mapping where match_type!='synonym'"):
    parts = [re.compile(p.strip()) for p in r[0].split(' AND ')]
    EXR.append((parts, int(r[1][2:]) - 1, r[2]))

# ---------------- 가상 인물 (카드 단위 경험) ----------------
PERSONAS = {
 'A1': dict(track='A', name='김개발 (컴퓨터공학 4학년, 프론트엔드 지망)', target='software_engineering', cards=[
   ('졸업 프로젝트(동아리 예약 웹)', 'project', '졸업 프로젝트로 4명이 동아리 예약 웹 서비스를 만들었습니다. 저는 프론트엔드를 맡아 React와 TypeScript로 예약 화면과 로그인 기능을 개발했습니다. 배포 후 동아리원 120명이 사용했습니다.'),
   ('부트캠프 수강', 'education', '부트캠프에서 Node.js와 SQL을 배웠습니다.'),
   ('카페 아르바이트', 'part_time', '카페에서 1년 동안 주문 접수와 고객 응대를 했습니다.')]),
 'A2': dict(track='A', name='이데이터 (통계학 4학년, 데이터 분석 지망)', target='data_ai', cards=[
   ('학회 매출 분석 프로젝트', 'project', '학회 프로젝트에서 제가 PostgreSQL로 3년치 매출 데이터를 월별로 집계했고 Tableau로 지점별 대시보드를 만들었습니다. 그 결과 주간 보고서 작성 시간을 2시간에서 30분으로 줄였습니다.'),
   ('공공데이터 분석 과제', 'project', '수업 과제로 Python으로 공공데이터를 수집하고 회귀분석으로 결과를 검증했습니다.'),
   ('설문 조사 발표', 'community', '동아리에서 엑셀로 설문 결과를 정리해 발표했습니다.')]),
 'B1': dict(track='B', name='박물류 (50대, 물류센터 경력 10년)', cards=[
   ('물류센터 근무', 'job', '물류센터에서 10년 동안 지게차로 상하차와 운반을 했습니다. 입고 검수와 재고 관리도 맡았습니다.'),
   ('자격증', 'certificate', '지게차운전기능사 자격증과 1종 보통 운전면허를 보유하고 있습니다.')]),
 'B2': dict(track='B', name='최경리 (40대, 경력단절 전 경리 5년)', cards=[
   ('회사 경리 업무', 'job', '회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 급여와 회계 장부를 정리하고 세금계산서를 발행했습니다. 거래처 전화 응대도 담당했습니다.'),
   ('자격증', 'certificate', '컴퓨터활용능력 2급 자격증을 취득했습니다.')]),
}

# ---------------- P3: 역량 태깅 + 근거 등급 ----------------
LEARN = re.compile(r'배웠|수강|수료|강의를 들|공부했|익혔')
ACTION = re.compile(r'했|맡|만들|개발|집계|정리|수집|검증|발행|담당|운반|운영|관리|응대|발표|제작|분석')
RESULT = re.compile(r'\d+\s*(?:명|건|%|시간|분|개)\D{0,12}(?:사용|줄|늘|증가|감소|단축|달성)|에서\s*\d+\S*으로|수상|A\+|배포|채택')
TEAM = re.compile(r'우리 팀|팀이|팀은')
SELF = re.compile(r'저는|제가|맡아')
COEF = {'L3': 1.0, 'L2': 0.75, 'L1': 0.5}
RANK = {'L0': 0, 'L1': 1, 'L2': 2, 'L3': 3}

def tag_sentence(s):
    out = {}
    o = E.map_ko(s)
    for k in o['kw']: out[k] = 'synonym'
    for k in E.map_en(s)['kw']: out.setdefault(k, 'synonym')
    for parts, k, mt in EXR:
        if all(p.search(s) for p in parts) and k not in out: out[k] = mt
    return out, o.get('non', [])

def build_card(title, typ, text):
    sents = [x.strip() for x in re.split(r'(?<=[.!?])\s+', text) if x.strip()]
    has_result = any(RESULT.search(s) for s in sents)
    team_only = bool(TEAM.search(text)) and not SELF.search(text)
    comps, lic = {}, []
    for s in sents:
        kws, non = tag_sentence(s)
        lic += [n for n in non if n.startswith('license')]
        for k, mt in kws.items():
            if typ == 'certificate':
                lv = 'L3'  # 자격 규칙으로 연결된 역량만 들어옴(P1 F0-2)
            elif LEARN.search(s): lv = 'L1'
            elif not ACTION.search(s): lv = 'L1'
            elif team_only: lv = 'L0'
            else: lv = 'L3' if has_result else 'L2'
            cur = comps.get(k)
            if cur is None or RANK[lv] > RANK[cur['level']]:
                comps[k] = dict(level=lv, match=mt, quote=s)
    comps = {k: v for k, v in comps.items() if v['level'] != 'L0'}
    return dict(title=title, type=typ, has_result=has_result, comps=comps, licenses=lic)

def user_profile(p):
    cards = [build_card(*c) for c in p['cards']]
    best = {}
    for c in cards:
        for k, v in c['comps'].items():
            if k not in best or RANK[v['level']] > RANK[best[k]['level']]:
                best[k] = dict(v, card=c['title'])
    return cards, best

# ---------------- 트랙 A: P4 ----------------
A = pd.read_csv(TRACKA_CLEAN, low_memory=False)
A = A[A['트랙A사용'] == 1].copy()
A['req'] = A['역량번호'].fillna('').astype(str).map(lambda s: [int(x) for x in s.split(';') if x.strip().isdigit()])
A['req'] = A['req'].map(lambda ks: [k for k in ks if D[k][0] not in ('C4', 'C5')])
ADJ = {'data_ai': ['software_engineering'], 'software_engineering': ['data_ai', 'hardware_engineering']}
CORE = {'C1', 'C2', 'C3', 'C7', 'C8'}

def career(r):
    y = r['CareerLens최소경력연수']
    if not pd.isna(y): return {1: 14, 2: 11, 3: 7}.get(int(y), 7), f'경력 {int(y)}년 명시'
    lv = r['CareerLens경력수준']
    return {'entry': (15, '신입'), 'mid': (5, 'mid 추정'), 'experienced': (5, 'mid 추정')}.get(lv, (9, '불명확'))

def score_track_a(best, target, fixed):
    ucore = {k for k in best if D[k][0] in CORE}
    rows = []
    for _, r in A.iterrows():
        req = r['req']
        fam = r['보정_직무분류']
        js = 15 if fam == target else (6 if fam in ADJ.get(target, []) else 0)
        if fixed:
            if len(req) <= 1 or not set(req) & ucore: continue
        else:
            if js == 0: continue
            if len(req) <= 1:
                rows.append(dict(group='확인 필요', tot=None)); continue
        vals = [COEF[best[k]['level']] if k in best else 0 for k in req]
        fit = sum(vals) / (max(len(vals), 3) if fixed else len(vals))
        cov = float(np.mean([v >= 0.5 for v in vals]))
        cs, cl = career(r)
        tot = 60 * fit + js + cs + 10
        g = '추천' if (tot >= 70 and cov >= 0.7 and r['공고신뢰도'] != 'low') else ('도전' if tot >= 55 and cov >= 0.5 else '미노출')
        rows.append(dict(group=g, tot=round(tot, 1), comp=round(60 * fit, 1), job=js, car=cs, car_label=cl, pref=10, cov=cov,
                         n=len(req), use=len(set(req) & set(best)), rel=r['공고신뢰도'], fam=fam,
                         title=str(r['채용공고제목']), role=str(r['보정_직무명']), company=str(r['기업명']), url=str(r['채용공고URL']),
                         matched=[D[k][1] + f"({best[k]['level']})" for k in req if k in best],
                         missing=[D[k][1] for k in req if k not in best]))
    t = pd.DataFrame(rows)
    return t

out = {'personas': {}}
for pid, p in PERSONAS.items():
    cards, best = user_profile(p)
    rec = dict(name=p['name'], track=p['track'],
               cards=[dict(title=c['title'], type=c['type'], has_result=c['has_result'],
                           comps=[(D[k][1], D[k][0], v['level'], v['match']) for k, v in sorted(c['comps'].items(), key=lambda x: -RANK[x[1]['level']])])
                      for c in cards],
               best={D[k][1]: v['level'] for k, v in best.items()})
    if p['track'] == 'A':
        asis = score_track_a(best, p['target'], fixed=False)
        fx = score_track_a(best, p['target'], fixed=True)
        fx = fx.sort_values(['tot', 'use', 'n'], ascending=False).drop_duplicates(['company', 'title'])
        a2 = asis.dropna(subset=['tot']).sort_values('tot', ascending=False)
        rec['asis'] = dict(counts=asis['group'].value_counts().to_dict(),
                           top=[dict(tot=x.tot, n=x.n, title=x.title[:50], role=x.role[:50]) for x in a2.head(6).itertuples()],
                           ties_at_top=int((a2['tot'] == a2['tot'].max()).sum()) if len(a2) else 0)
        rec['fixed'] = dict(counts=fx['group'].value_counts().to_dict(), n_candidates=len(fx),
                            top=[{k: (v if not isinstance(v, float) else round(v, 2)) for k, v in x._asdict().items() if k != 'Index'} for x in fx.head(6).itertuples()])
    out['personas'][pid] = rec

# ---------------- 트랙 B: 팀원 엔진 + P3 등급 ----------------
sys.path.insert(0, ENGINE_SRC)
import os; os.chdir(ENGINE_SRC)
from recommender import CareerMatcher
m = CareerMatcher()
near = set(pd.read_sql('select posting_id from job_postings where is_near_duplicate=1', con).posting_id)
orig_extract = m.extract
for pid, p in PERSONAS.items():
    if p['track'] != 'B': continue
    cards, best = user_profile(p)
    lv_by_name = {D[k][1]: v['level'] for k, v in best.items()}
    text = ' '.join(c[2] for c in p['cards'])
    def ext(t, lv=lv_by_name):
        c = orig_extract(t)
        for kw, f in c['keywords'].items():
            if kw in lv: f['evidence_strength'] = COEF[lv[kw]]
        return c
    m.extract = ext
    r = m.recommend(text)
    user_kws = set(m.extract(text)['keywords'])
    jobs = []
    for rec_ in r['recommendations'][:3]:
        ps = m.postings_for(rec_['occupation_id'], user_kws, n=20)
        seen, keep = set(), []
        for x in ps:
            key = (x['company'], x['title'])
            if x['posting_id'] in near or key in seen: continue
            seen.add(key); keep.append(x)
        jobs.append(dict(name=rec_['occupation_name'], score=rec_['score'], bd=rec_['score_breakdown'], open=rec_['market_open_postings'],
                         matched=rec_['matched_competencies'][:6], gaps=rec_['competency_gaps'][:4], cautions=rec_['cautions'],
                         postings=[dict(company=x['company'], title=x['title'], region=x['region'], career=x['career'], wage=x['wage'], d_day=x['d_day']) for x in keep[:6]],
                         n_dropped=len(ps[:6]) - len([x for x in ps[:6] if x['posting_id'] not in near])))
    out['personas'][pid]['engine'] = dict(jobs=jobs, engine_comps=r['experience_card']['competencies'], licenses=r['experience_card']['licenses'],
                                         more=[x['occupation_name'] for x in r['more_candidates']])
    m.extract = orig_extract

json.dump(out, open(SIM_JSON, 'w'), ensure_ascii=False, indent=1, default=str)
print('done')
