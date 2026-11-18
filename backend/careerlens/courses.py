"""⑤ 교육과정 추천(교육과정 전처리 문서 그대로): 부족 역량 → 그 역량이 붙은 고용24 과정을 연관도 순으로.
연관도가 같으면 그 직무와의 적합도(courses.json의 occ)가 높은 과정을 먼저. 핵심 역량(C1·C2·C3·C7·C8)만.
"""
import json
import re
from collections import defaultdict

from careerlens.cards import D
from careerlens.paths import COURSES_JSON
from common import TODAY

CORE = {'C1', 'C2', 'C3', 'C7', 'C8'}
GAP_LABEL = {'필수': '필수 역량 부족', '우대': '우대 조건 부족', '업무': '처음 해 보는 업무', None: '직무에서 자주 요구'}

_d = json.load(open(COURSES_JSON, encoding='utf-8'))
_today = str(TODAY.date())
CRS = {c['id']: c for c in _d['crs']}
BY_KW = defaultdict(list)
for c in _d['crs']:
    for k, rel, _src in c['k']:
        BY_KW[k].append((rel, c['id']))
N_COURSES = len(CRS)


def _view(c):
    s = next((s for s in sorted(c['sess'], key=lambda s: s[2]) if s[2] >= _today), None)
    if s is None:
        return None
    return dict(course_id=c['id'], name=c['t'], institution=c['inst'], type=c['type'], certificates=c['cert'],
                start=s[2], end=s[3], fee=s[4], region=s[5], url=s[6])


def for_keyword(kw_idx, oid=None, n=3):
    fit = lambda cid: next((f for o, f, _ in CRS[cid]['occ'] if o == oid), 0)
    out = []
    for rel, cid in sorted(BY_KW.get(kw_idx, []), key=lambda x: (-x[0], -fit(x[1]), x[1])):
        v = _view(CRS[cid])
        if v:
            out.append(dict(v, relevance=rel))
        if len(out) == n:
            break
    return out


def for_license(name, n=3):
    key = re.sub(r'\s|\d급$', '', name)
    out = [v for c in CRS.values() if any(key in re.sub(r'\s', '', x) for x in c['cert']) and (v := _view(c))]
    return sorted(out, key=lambda v: v['start'])[:n]


def plan(gaps, missing_licenses=(), oid=None):
    """gaps: [(kw_idx, 공고 종류 '필수'/'우대'/'업무' 또는 None)]. 핵심 역량만 남기고 과정을 붙인다."""
    out = [dict(kind='license', name=name, label='법정 자격 필요', courses=for_license(name)) for name in missing_licenses]
    for k, t in gaps:
        if D[k][0] in CORE:
            out.append(dict(kind='competency', kw_idx=k, name=D[k][1], label=GAP_LABEL[t], courses=for_keyword(k, oid)))
    return out
