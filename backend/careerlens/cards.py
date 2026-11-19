"""경험 카드의 코드 부분: 문장 → 역량(P1 매핑 + 보정된 경험 규칙), 역량별 근거 등급(P3 3.1).
로직팀 시뮬레이션 07_sim_full.py의 tag_sentence·build_card·user_profile을 옮겼다.
"""
import csv
import re

from careerlens import paths  # noqa: F401  vendor 경로 설정
from careerlens.experience_rules import card_rules
from careerlens.paths import DICT_CSV
import p1_engine as E

_ROWS = list(csv.DictReader(open(DICT_CSV, encoding='utf-8-sig')))
D = {int(r['kw_idx']): (r['분류코드'], r['키워드']) for r in _ROWS}
DEF = {int(r['kw_idx']): r['정의'] for r in _ROWS}
EXR = card_rules()
RANK = {'L0': 0, 'L1': 1, 'L2': 2, 'L3': 3}

# shortcut: 행동·성과 판정이 정규식이다(시뮬레이션 그대로). P3 인터뷰(LLM 슬롯 추출)가 붙으면 슬롯 값으로 판정한다.
LEARN = re.compile(r'배웠|수강|수료|강의를 들|공부했|익혔')
ACTION = re.compile(r'했|맡|만들|개발|집계|정리|수집|검증|발행|담당|운반|운영|관리|응대|발표|제작|분석')
RESULT = re.compile(r'\d+\s*(?:명|건|%|시간|분|개)\D{0,12}(?:사용|줄|늘|증가|감소|단축|달성)|에서\s*\d+\S*으로|수상|A\+|배포|채택')
TEAM = re.compile(r'우리 팀|팀이|팀은')
SELF = re.compile(r'저는|제가|맡아')


def tag_sentence(s):
    """문장 하나 → ({kw_idx: 연결 방식}, P1이 돌려준 비역량 표시)."""
    out = {}
    o = E.map_ko(s)
    for k in o['kw']:
        out[k] = 'synonym'
    for k in E.map_en(s)['kw']:
        out.setdefault(k, 'synonym')
    for parts, k, mt in EXR:
        if all(p.search(s) for p in parts) and k not in out:
            out[k] = mt
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
            elif LEARN.search(s) or not ACTION.search(s):
                lv = 'L1'
            elif team_only:
                lv = 'L0'
            else:
                lv = 'L3' if has_result else 'L2'
            cur = comps.get(k)
            if cur is None or RANK[lv] > RANK[cur['level']]:
                comps[k] = dict(level=lv, match=mt, quote=s)
    comps = {k: v for k, v in comps.items() if v['level'] != 'L0'}
    return dict(title=title, type=typ, text=text, has_result=has_result, comps=comps, licenses=lic)


def best_levels(cards):
    """여러 카드에서 같은 역량은 가장 높은 등급. {역량 이름: 등급}"""
    best = {}
    for c in cards:
        for k, v in c['comps'].items():
            name = D[k][1]
            if name not in best or RANK[v['level']] > RANK[best[name]]:
                best[name] = v['level']
    return best


# P3 4.1 ② 후보: 규칙으로 못 잡은 문장과 비슷한 사전 역량 n개. [기본값] 새 임베딩 대신 엔진과 같은 글자 단위 TF-IDF(DESIGN 3절).
# 태도(C4)·신체(C5)는 점수에 안 쓰므로 후보에서 뺀다.
_cand = None


def candidates(sentence, n=5):
    global _cand
    if _cand is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        rows = [r for r in _ROWS if r['분류코드'] not in ('C4', 'C5')]
        docs = [' '.join([r['키워드'], r['정의'], r['국문_별칭'].replace('|', ' ')]) for r in rows]
        vec = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), sublinear_tf=True)
        _cand = ([int(r['kw_idx']) for r in rows], vec, vec.fit_transform(docs))
    ids, vec, m = _cand
    sim = (m @ vec.transform([sentence]).T).toarray().ravel()
    return [ids[i] for i in sim.argsort()[::-1][:n] if sim[i] > 0]
