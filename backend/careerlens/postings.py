"""④ 채용공고: 직무 안 공고 순서와 공고 카드(P2 3절). ⑥ 분석 결과(data/derived/posting_analysis.jsonl)를 쓴다.

순서 = 엔진 postings_for와 같은 식(겹침 + 0.3 신입·무관 + 0.2 최근 등록)인데, 겹침을 P2 종류 가중치로 센다:
필수 2 · 업무 1 · 우대 1 (× 엔진 변별력). 분석 신뢰도 low는 뒤로, 유급 근무 경험이 없으면 '경력' 공고도 뒤로(7번).
엔진의 postings_for는 종류를 모르기 때문에 같은 식을 여기서 다시 계산한다.
"""
import json
import re

from careerlens.paths import DATA
from careerlens.posting_analysis import _license_id
from common import TODAY   # 엔진 기준일 2026-11-12 (vendor/engine/src/common.py)
import p1_engine as E

ANALYSIS = DATA / 'derived' / 'posting_analysis.jsonl'
TYPE_W = {'필수': 2, '업무': 1, '우대': 1}


def load_analysis():
    # shortcut: 63MB를 통째로 메모리에 올린다(약 수백 MB). 서버 메모리가 모자라면 SQLite 표로 옮긴다
    with open(ANALYSIS, encoding='utf-8') as f:
        return {r['posting_id']: r for r in map(json.loads, f)}


def user_license_ids(cards):
    return {lid for c in cards for m in E.LIC_NAMES.finditer(c['text']) if (lid := _license_id(m.group(0)))}


def candidates(R, oid, filters=None):
    """직무의 열린 공고(정확·유사 중복 제외)에 화면 필터를 적용."""
    p = R.posts
    p = p[(p.occupation_id == oid) & ~p.is_exact_duplicate & p.is_open_as_of_run & ~p.posting_id.isin(R.near)]
    f = filters or {}
    if f.get('sido'):
        p = p[p.sido == f['sido']]
    if f.get('sigungu'):
        p = p[p.sigungu == f['sigungu']]
    if f.get('hours') in ('시간제', '전일제'):
        p = p[p.is_part_time.astype(bool) == (f['hours'] == '시간제')]
    if f.get('deadline_days') is not None:
        p = p[(p.deadline - TODAY).dt.days <= int(f['deadline_days'])]
    return p


def ranked(R, A, oid, user_kws, paid, filters=None):
    p = candidates(R, oid, filters)
    if p.empty:
        return []
    span = max(1, (p.reg_date.max() - p.reg_date.min()).days)
    rows = []
    for r in p.itertuples():
        a = A.get(r.posting_id)
        ov = sum(TYPE_W[q['type']] * R.disc.get(q['keyword'], 1.0) for q in (a['requirements'] if a else []) if q['keyword'] in user_kws)
        score = ov + 0.3 * (r.경력 in ('신입', '관계없음')) + 0.2 * (r.reg_date - p.reg_date.min()).days / span
        low = a is None or a['confidence'] == 'low'
        rows.append((low, (not paid) and r.경력 == '경력', -score, -r.deadline.value, r))
    rows.sort(key=lambda x: x[:4])
    seen, out = set(), []
    for *_, r in rows:
        key = (r.기업명, r.채용제목)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def card(r, a, user_kws, user_lics):
    """공고 카드 1장(시안 ④). r: R.posts 행(itertuples), a: 분석 결과."""
    a = a or dict(requirements=[], licenses=[], display_only=[], filters=[], conditions=[], unmapped_requirements=[], confidence='low')
    req = {t: [dict(keyword=q['keyword'], kw_idx=q['kw_idx'], has=q['keyword'] in user_kws, quote=q['quote'])
               for q in a['requirements'] if q['type'] == t] for t in ('필수', '우대', '업무')}
    lics = [dict(name=v['name'], type=v['type'], legal_required=v['legal_required'], has=v['license_id'] in user_lics)
            for v in a['licenses'] if v['type'] != '언급' or v['legal_required']]
    d_day = int((r.deadline - TODAY).days) if r.deadline == r.deadline else None   # NaT 확인
    return dict(posting_id=r.posting_id, company=r.기업명, title=r.채용제목, sido=r.sido, sigungu=r.sigungu,
                part_time=bool(r.is_part_time), employment_type=r.employment_type, career=r.경력, education=r.최소학력,
                wage=re.sub(r',\s*$', '', str(r.임금조건 or '')), work_hours=r.work_hours, deadline=str(r.deadline.date()) if d_day is not None else None,
                d_day=d_day, until_hired=bool(r.until_hired),
                required=req['필수'], preferred=req['우대'], tasks=req['업무'],
                attitude=[dict(keyword=x['keyword'], quote=x['quote']) for x in a['display_only']],
                physical=[dict(keyword=x['keyword'], quote=x['quote']) for x in a['filters']],
                conditions=a['conditions'], licenses=lics,
                needs_license=[l['name'] for l in lics if l['legal_required'] and not l['has']],
                unmapped=a['unmapped_requirements'], thin=a['confidence'] == 'low', confidence=a['confidence'])

