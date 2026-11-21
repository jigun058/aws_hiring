"""직무 추천(트랙 B). 팀원 엔진을 상속해 바깥에서만 보정한다(엔진 파일은 그대로).

- 경험 규칙 보정: experience_rules.apply_to
- 시뮬레이션 8번: 엔진이 뽑은 역량 중 카드에 있는 것은 근거 강도를 카드 등급 계수로 바꾼다(07_sim_full.py 방식)
- BACKLOG B2: 엔진이 "회사에서 ~했다"를 '기타 경험'(0.6)으로 보는 문제 → 카드 유형으로 경험 맥락을 올린다
- 시뮬레이션 6번: 거의 같은 공고, 같은 회사·제목 공고를 하나만
- 시뮬레이션 7번: 유급 근무 경험이 없으면 '경력' 공고를 뒤로
- 시뮬레이션 5번(C4·C5 제외)은 보류(BACKLOG B1): 엔진 그대로
- 사용자가 카드에서 지운 역량(card['removed'], 역량 이름)은 엔진이 글에서 다시 찾아도 뺀다. 다른 카드에 남아 있으면 둔다
"""
import re
import threading

from careerlens import paths  # noqa: F401  vendor 경로 설정
from careerlens.cards import best_levels
from careerlens.experience_rules import apply_to
import knowledge as K
from recommender import CareerMatcher

COEF = {'L3': 1.0, 'L2': 0.75, 'L1': 0.5}
CTX_W = {name: w for name, _, w in K.EXPERIENCE_CONTEXTS}
# P3 경험 유형 → 엔진 경험 맥락 [기본값]. family_care·certificate는 엔진 기본값('기타 경험')
TYPE_CONTEXT = {'job': '인턴·직무 경력', 'internship': '인턴·직무 경력', 'self_employed': '인턴·직무 경력',
                'project': '프로젝트·공모전', 'part_time': '아르바이트',
                'community': '동아리·학회·대외활동', 'education': '수업·전공'}
PAID = {'job', 'internship', 'part_time', 'self_employed'}


def is_paid(cards):
    """유급 근무 경험이 있는가(시뮬레이션 7번). 카드의 paid 값이 없으면 유형으로 판단."""
    return any(c.get('paid', c['type'] in PAID) for c in cards)


class Recommender(CareerMatcher):
    def __init__(self):
        super().__init__()
        apply_to(self)
        # 시뮬레이션 4번: "지게차운전기능사·운전기사" 안의 "전기"가 전기·전자 지식으로 잡힘. 사용자 글에서만 막는다(TEAM T16, 공고 쪽은 그대로)
        self.lex = [(kw, re.compile(p.pattern.replace('전기', '(?<!운)전기'), p.flags) if kw == '전기·전자 지식' else p)
                    for kw, p in self.lex]
        self.near = set(self.posts.loc[self.posts.is_near_duplicate.astype(bool), 'posting_id'])
        self._lock = threading.Lock()   # extract 보정값을 인스턴스에 잠깐 싣기 때문에 한 번에 하나만
        self._override = None

    def extract(self, text):
        c = super().extract(text)
        if self._override:
            levels, ctx, removed = self._override
            for kw in removed:
                c['keywords'].pop(kw, None)
            for kw, f in c['keywords'].items():
                if kw in levels:
                    f['evidence_strength'] = COEF[levels[kw]]
            if ctx and CTX_W[ctx] > c['context_weight']:
                c['context'], c['context_weight'] = ctx, CTX_W[ctx]
        return c

    def recommend_cards(self, cards, n_jobs=3, n_posts=6, use_card_context=True):
        """cards: cards.build_card 결과 목록(type, text, comps). 선택 키 paid: 유급 근무 여부(없으면 유형으로 판단)."""
        levels = best_levels(cards)
        text = ' '.join(c['text'] for c in cards)
        ctxs = [TYPE_CONTEXT[c['type']] for c in cards if c['type'] in TYPE_CONTEXT] if use_card_context else []
        ctx = max(ctxs, key=CTX_W.get, default=None)
        removed = set().union(*(c.get('removed', ()) for c in cards)) - set(levels)
        with self._lock:
            self._override = (levels, ctx, removed)
            try:
                r = self.recommend(text)
                card = self.extract(text)
            finally:
                self._override = None
        paid = is_paid(cards)
        jobs = r['recommendations'][:n_jobs]
        for j in jobs:
            j['postings'] = self.pick_postings(j['occupation_id'], set(card['keywords']), paid, n_posts) if n_posts else []
        return dict(jobs=jobs, more=r['more_candidates'], engine_card=r['experience_card'],
                    context=card['context'], low_confidence=r['low_confidence'],
                    user_keywords=sorted(set(card['keywords']) | set(levels)))

    def pick_postings(self, oid, user_kws, paid, n=6):
        seen, keep = set(), []
        for p in self.postings_for(oid, user_kws, n=20):
            key = (p['company'], p['title'])
            if p['posting_id'] in self.near or key in seen:
                continue
            seen.add(key)
            keep.append(p)
        if not paid:
            keep.sort(key=lambda p: p['career'] == '경력')   # 안정 정렬: 나머지 순서는 그대로
        return keep[:n]
