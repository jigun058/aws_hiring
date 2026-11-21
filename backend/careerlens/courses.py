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
OCC_CRS = defaultdict(set)   # 직무 → 맞는 과정: occCrs(직무별 최대 30개) + 과정별 연결 직무(과정별 최대 5개)
for o, lst in _d['occCrs'].items():
    OCC_CRS[o].update(cid for cid, _ in lst)
for c in _d['crs']:
    for o, _f, _k in c['occ']:
        OCC_CRS[o].add(c['id'])
OCC_CRS = dict(OCC_CRS)


def _view(c):
    s = next((s for s in sorted(c['sess'], key=lambda s: s[2]) if s[2] >= _today), None)
    if s is None:
        return None
    return dict(course_id=c['id'], name=c['t'], institution=c['inst'], type=c['type'], certificates=c['cert'],
                start=s[2], end=s[3], fee=s[4], region=s[5], url=s[6])


# P3 4.2 수료증: 사용자가 쓴 과정명 ↔ 고용24 과정명. 꾸밈말(괄호, '_육성', 자격·취득·과정 같은 말)을 떼고 비교한다.
# [기본값] 과정명 핵심이 4글자 이상이고 문장에 들어 있으면(짧은 활동명은 반대로 과정명 안에 들어 있어도) 맞는 것으로 본다.
# 여러 과정이 맞으면 핵심이 가장 긴(가장 구체적인) 과정, 같으면 번호가 앞선 과정.
_BRACKET = re.compile(r'[\(\[『「【<][^\)\]』」】>]*[\)\]』」】>]|_[^_]*$')
_FILLER = re.compile(r'자격증?|취득|과정|양성|필기|실기|수료|훈련|및')


def _core(t):
    return re.sub(r'[^가-힣A-Za-z0-9]', '', _FILLER.sub('', _BRACKET.sub(' ', t)))


_CORES = sorted(((_core(c['t']), cid) for cid, c in CRS.items()), key=lambda x: (-len(x[0]), x[1]))
_CORES = [(k, cid) for k, cid in _CORES if len(k) >= 4]


def match(text):
    """글 → 이름이 맞는 고용24 과정(dict) 또는 None."""
    t = _core(text)
    hit = next((cid for k, cid in _CORES if k in t), None)
    if hit is None and 4 <= len(t) <= 20:   # 활동명처럼 짧은 글: 과정명 안에 들어 있으면
        hit = next((cid for k, cid in reversed(_CORES) if t in k), None)
    return CRS[hit] if hit else None


def for_keyword(kw_idx, oid=None, n=3):
    fit = lambda cid: next((f for o, f, _ in CRS[cid]['occ'] if o == oid), 0)
    cands = BY_KW.get(kw_idx, [])
    # [기본값] 11/21: 과정이 연결된 직무면 그 직무에 맞는 과정만(보육교사 "안전 관리" → 소방설비 과정이 나오던 문제).
    # 연결된 과정이 없는 직무만 전처리 문서 방식(역량 연관도 순)
    if oid in OCC_CRS:
        cands = [x for x in cands if x[1] in OCC_CRS[oid]]
    out = []
    for rel, cid in sorted(cands, key=lambda x: (-x[0], -fit(x[1]), x[1])):
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
