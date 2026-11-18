"""트랙 B 단계별 API. 실행: cd backend && ../.venv/bin/uvicorn careerlens.api:app --reload

로그인이 없어 서버는 사용자 상태를 들고 있지 않는다. 화면이 경험 카드를 들고 있다가 매 요청에 함께 보낸다.
(경험 카드 저장(DynamoDB)과 에이전트 대화는 다음 작업)
"""
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from careerlens import cards as C
from careerlens import courses, postings
from careerlens.posting_analysis import analyze
from careerlens.recommend import Recommender, is_paid
from common import TODAY
from recommender import WEIGHTS

app = FastAPI(title='CareerLens')
R = Recommender()
A = postings.load_analysis()
CardType = Literal['job', 'internship', 'part_time', 'self_employed', 'project', 'education', 'community', 'family_care', 'certificate']


class Competency(BaseModel):
    kw_idx: int
    level: Literal['L1', 'L2', 'L3']
    match: str = 'synonym'
    quote: str = ''


class CardIn(BaseModel):
    title: str
    type: CardType
    text: str = Field(min_length=1, max_length=5000)
    paid: Optional[bool] = None
    competencies: Optional[list[Competency]] = None   # 없으면 서버가 규칙으로 붙인다(초안)


class CardsReq(BaseModel):
    cards: list[CardIn] = Field(min_length=1, max_length=30)


class PostingFilters(BaseModel):
    sido: Optional[str] = None
    sigungu: Optional[str] = None
    hours: Optional[Literal['시간제', '전일제']] = None
    deadline_days: Optional[int] = Field(None, ge=0)


class PostingsReq(CardsReq):
    occupation_id: str
    filters: PostingFilters = PostingFilters()
    limit: int = Field(6, ge=1, le=50)


class CoursesReq(CardsReq):
    occupation_id: str
    posting_id: Optional[str] = None


class AnalyzeReq(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    occupation_id: Optional[str] = None


def _internal(cards):
    """API 카드 → cards.build_card 모양. 역량을 안 보냈으면 규칙으로 초안을 만든다."""
    out = []
    for c in cards:
        b = C.build_card(c.title, c.type, c.text)
        if c.competencies is not None:   # 사용자가 확인·수정한 역량이 우선
            b['comps'] = {x.kw_idx: dict(level=x.level, match=x.match, quote=x.quote) for x in c.competencies if x.kw_idx in C.D}
        if c.paid is not None:
            b['paid'] = c.paid
        out.append(b)
    return out


def _card_out(b):
    return dict(title=b['title'], type=b['type'], text=b['text'], has_result=b['has_result'], licenses=b['licenses'],
                competencies=[dict(kw_idx=k, keyword=C.D[k][1], category=C.D[k][0], **v)
                              for k, v in sorted(b['comps'].items(), key=lambda x: -C.RANK[x[1]['level']])])


def _occ(oid):
    if oid not in R.occ_idx:
        raise HTTPException(404, f'직무를 찾지 못했어요: {oid}')
    return oid


@app.get('/api/health')
def health():
    return dict(ok=True)


@app.get('/api/meta')
def meta():
    """화면 문구에 쓰는 실제 숫자와 데이터 기준일(BACKLOG B12·B13)."""
    return dict(occupations=len(R.occ_ids), postings=len(A), courses=courses.N_COURSES, data_date=str(TODAY.date()),
                sido=sorted(R.posts.sido.dropna().unique().tolist()))


@app.post('/api/cards/draft')
def cards_draft(req: CardsReq):
    """② 경험 카드 초안: 문장 → 역량·근거 등급(규칙). P3 LLM 인터뷰가 붙기 전의 출발점."""
    return dict(cards=[_card_out(b) for b in _internal(req.cards)])


@app.post('/api/recommend')
def recommend(req: CardsReq):
    """③ 직무 추천 TOP 3."""
    cards = _internal(req.cards)
    r = R.recommend_cards(cards, n_posts=0)
    by_name = {}
    for b in cards:
        for k, v in b['comps'].items():
            n = C.D[k][1]
            if n not in by_name or C.RANK[v['level']] > C.RANK[by_name[n]['level']]:
                by_name[n] = dict(level=v['level'], card=b['title'], quote=v['quote'])
    jobs = []
    for j in r['jobs']:
        bd = j['score_breakdown']
        jobs.append(dict(occupation_id=j['occupation_id'], name=j['occupation_name'], family=j['job_family'], score=j['score'],
                         parts={k: dict(value=bd[k], max=round(100 * w)) for k, w in WEIGHTS.items()},
                         evidence=[dict(keyword=n, **by_name[n]) if n in by_name else dict(keyword=n, level=None, card=None, quote=None)
                                   for n in j['matched_competencies']],
                         gaps=j['competency_gaps'], cautions=j['cautions'], missing_legal=j['missing_legal'],
                         open_postings=j['market_open_postings']))
    return dict(jobs=jobs, more=r['more'], low_confidence=r['low_confidence'], context=r['context'], user_keywords=r['user_keywords'])


@app.post('/api/postings')
def job_postings(req: PostingsReq):
    """④ 직무의 공고: P2 종류 가중치 순서 + 공고 카드."""
    oid = _occ(req.occupation_id)
    cards = _internal(req.cards)
    kws = set(R.recommend_cards(cards, n_posts=0)['user_keywords'])
    lics = postings.user_license_ids(cards)
    rows = postings.ranked(R, A, oid, kws, is_paid(cards), req.filters.model_dump())
    return dict(total=len(rows), postings=[postings.card(r, A.get(r.posting_id), kws, lics) for r in rows[:req.limit]])


@app.post('/api/courses')
def course_plan(req: CoursesReq):
    """⑤ 부족 역량별 교육과정. 공고를 골랐으면 그 공고 기준, 아니면 직무 기준."""
    oid = _occ(req.occupation_id)
    cards = _internal(req.cards)
    kws = set(R.recommend_cards(cards, n_posts=0)['user_keywords'])
    if req.posting_id:
        a = A.get(req.posting_id)
        if a is None:
            raise HTTPException(404, f'공고를 찾지 못했어요: {req.posting_id}')
        gaps = [(q['kw_idx'], q['type']) for q in a['requirements'] if q['keyword'] not in kws]
        lics = postings.user_license_ids(cards)
        missing = [v['name'] for v in a['licenses'] if v['legal_required'] and v['license_id'] not in lics]
    else:   # 엔진의 competency_gaps와 같은 기준: 직무 필수·주요 역량 중 없는 것, 배점 순
        idx = {n: k for k, (_, n) in C.D.items()}
        p = R.prof[(R.prof.occupation_id == oid) & R.prof.importance.isin(['required', 'major']) & ~R.prof.keyword.isin(kws)]
        p = p.assign(w=p.importance.map({'required': 1.0, 'major': 0.75}) * p.combined_score).sort_values('w', ascending=False)
        gaps = [(idx[n], None) for n in p.keyword if n in idx]
        lics = postings.user_license_ids(cards)
        legal = R.legal[R.legal.occupation_id == oid]
        missing = sorted(set(legal.loc[~legal.license_id.isin(lics), 'license_name']))[:1] if not legal.license_id.isin(lics).any() else []
    return dict(gaps=courses.plan(gaps, missing, oid))


@app.post('/api/analyze-posting')
def analyze_posting(req: AnalyzeReq):
    """⑥ 즉석 공고 분석(규칙). AI 보완(F2-5)은 다음 작업."""
    return analyze(dict(job_description_raw=req.text, occupation_id=req.occupation_id))
