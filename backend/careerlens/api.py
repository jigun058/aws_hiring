"""트랙 B 단계별 API. 실행: cd backend && ../.venv/bin/uvicorn careerlens.api:app --reload

로그인이 없어 서버는 사용자 상태를 들고 있지 않는다. 화면이 경험 카드를 들고 있다가 매 요청에 함께 보낸다.
(경험 카드 저장(DynamoDB)과 에이전트 대화는 다음 작업)
"""
import re
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from careerlens import cards as C
from careerlens import courses, interview as I, llm, postings
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


# ---------------- ① 경험 수집 인터뷰 (P3) ----------------
class InterviewStart(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    title: Optional[str] = None
    type: Optional[CardType] = None


class InterviewAnswer(BaseModel):
    card: dict
    answer: str = Field(min_length=1, max_length=2000)


def _comps_out(comps):
    return [dict(kw_idx=k, keyword=C.D[k][1], category=C.D[k][0], **v) for k, v in sorted(comps.items(), key=lambda x: -C.RANK[x[1]['level']])]


def _ask_next(card):
    """다음 질문(코드가 고름) → LLM이 다듬음(실패·금지 주제면 기본 문장) → 질문 기록."""
    q = I.next_question(card)
    if q.get('end'):
        card['status'] = 'generated'
        card['last_question'] = None
        return q
    p = llm.phrase_question(q, card)
    if p:
        q = dict(q, question=I.safe_question(p['question'], q['question']), options=p['options'] or q['options'])
    I.record_question(card, q)
    card['last_question'] = q
    return q


def _interview_out(card, q):
    comps = I.competencies(card)
    return dict(card=card, question=q, competencies=_comps_out(comps),
                card_in=dict(title=card['activity'], type=card['type'], text=I.card_text(card), paid=card['is_paid_work'],
                             competencies=[dict(kw_idx=k, level=v['level'], match=v['match'], quote=v['quote']) for k, v in comps.items()]))


@app.post('/api/interview/start')
def interview_start(req: InterviewStart):
    """경험 글 → 경험 카드 초안(여러 장일 수 있음)과 카드마다 첫 질문."""
    text = I.mask_pii(req.text)
    exps = llm.extract_experiences(text)
    if not exps:   # LLM 실패 → 글 전체를 카드 하나로, 슬롯은 규칙으로
        exps = [dict(activity=req.title or '내 경험', type=req.type or 'job', slots=I.rule_extract(text))]
    out = []
    for e in exps:
        typ = req.type if (req.type and len(exps) == 1) else (e.get('type') if e.get('type') in llm.TYPES else 'job')
        card = I.new_card(req.title if len(exps) == 1 and req.title else str(e.get('activity') or '내 경험')[:60], typ, text)
        for x in e.get('slots') or []:
            if isinstance(x, dict):
                I.fill(card, x.get('slot'), x.get('value'), x.get('quote'), 'chat_0', is_estimate=bool(x.get('is_estimate')))
        out.append(_interview_out(card, _ask_next(card)))
    return dict(cards=out)


@app.post('/api/interview/answer')
def interview_answer(req: InterviewAnswer):
    card = req.card
    try:
        q = card['last_question'] or {}
        slot = q['slot']
        source_id = f'chat_{len(card["sources"])}'
    except (KeyError, TypeError):
        raise HTTPException(400, '카드 형식이 올바르지 않거나 물어본 질문이 없어요')
    answer = I.mask_pii(req.answer)
    interp = llm.interpret_answer(slot, q.get('question', ''), answer) or I.rule_interpret(slot, answer)
    filled = I.apply_answer(card, slot, answer, interp, source_id)
    res = _interview_out(card, _ask_next(card))
    res.update(filled=filled, other_experience=interp.get('kind') == 'other')
    return res


class ExplainReq(BaseModel):
    job: dict


@app.post('/api/explain')
def explain(req: ExplainReq):
    """③ 추천 이유 문장. 점수는 바꾸지 않는다. LLM이 실패하거나 규칙에 걸리면 코드가 만든 문장."""
    j = req.job
    try:
        ev = [e for e in j['evidence'] if e.get('card')]
        reason = llm.explain_job(j, j['evidence'])
    except (KeyError, TypeError):
        raise HTTPException(400, '직무 정보 형식이 올바르지 않아요')
    if reason and not I.FORBIDDEN.search(reason):
        return dict(reason=reason, by='ai')
    names = ', '.join(e['keyword'] for e in ev[:2])
    base = f'{j["name"]}에서 자주 찾는 역량 가운데 {names} 경험이 있어 추천했어요.' if names else f'{j["name"]}의 업무와 경험이 겹쳐 추천했어요.'
    return dict(reason=base, by='rule')


# ---------------- 에이전트 대화창 (DESIGN 5절): LLM이 도구 4개를 골라 부른다 ----------------
class ChatMsg(BaseModel):
    role: Literal['user', 'assistant']
    text: str = Field(min_length=1, max_length=4000)


class ChatReq(BaseModel):
    messages: list[ChatMsg] = Field(min_length=1, max_length=40)
    step: Optional[str] = None                 # 화면의 지금 단계(예: '④ 채용공고')
    cards: list[CardIn] = Field(default_factory=list, max_length=30)
    occupation_id: Optional[str] = None
    posting_id: Optional[str] = None


_S = lambda props, req=(): {'json': {'type': 'object', 'properties': props, 'required': list(req)}}
TOOLS = [
    {'toolSpec': {'name': 'map_competencies', 'description': '문장 하나를 공통 역량 사전(182개)의 역량으로 바꾼다. 사용자가 새 경험을 말했을 때 어떤 역량인지 볼 때 쓴다.',
                  'inputSchema': _S({'text': {'type': 'string'}}, ['text'])}},
    {'toolSpec': {'name': 'recommend_jobs', 'description': '사용자의 경험 카드로 직무 TOP 3과 점수 구성, 근거 역량, 부족 역량을 계산한다.',
                  'inputSchema': _S({})}},
    {'toolSpec': {'name': 'search_postings', 'description': '한 직무의 채용공고를 찾는다. 필터: 시·도(서울/경기/인천), 시간제/전일제, 마감까지 남은 일수.',
                  'inputSchema': _S({'occupation_id': {'type': 'string', 'description': '직무 번호(OCC로 시작) 또는 직무 이름'}, 'sido': {'type': 'string'}, 'hours': {'type': 'string', 'enum': ['시간제', '전일제']},
                                     'deadline_days': {'type': 'integer'}}, ['occupation_id'])}},
    {'toolSpec': {'name': 'search_courses', 'description': '직무(또는 고른 공고)에서 부족한 역량을 채울 국비 교육과정을 찾는다.',
                  'inputSchema': _S({'occupation_id': {'type': 'string', 'description': '직무 번호(OCC로 시작) 또는 직무 이름'}, 'posting_id': {'type': 'string'}}, ['occupation_id'])}},
]
AGENT_SYSTEM = ('너는 CareerLens의 커리어 도우미다. 다시 일을 찾는 사람이 경험을 정리하고, 맞는 직무와 채용공고, 국비 교육과정을 찾도록 돕는다. '
                '직무·공고·과정·점수에 관한 사실은 반드시 도구를 불러 얻은 결과만 말한다. 결과가 0건이면 0건이라고 말하고, 없는 공고나 과정을 지어내지 않는다. '
                '점수는 합격 가능성이 아니라 경험과 직무가 겹치는 정도를 비교한 값이며, 네가 점수를 바꾸거나 새로 매기지 않는다. '
                '공고는 서울시 일자리포털에 2026년 11월 12일 기준으로 올라온 수도권(서울·경기·인천) 공고다. '
                '도구 결과의 d_day(마감까지 남은 날)는 2026년 11월 12일 기준이다. "마감까지 n일 남았다", "서두르라"고 말하지 않고, 필요하면 "11월 12일 기준 D-n"이라고 쓴다. '
                '답은 대화창에 들어가는 3~5문장의 평범한 글이다. 표, 굵은 글씨, 이모지를 쓰지 않는다. 공고를 소개할 때는 3건까지 회사·지역·급여만 한 줄씩. '
                '"부담 없이 지원하실 수 있어요", "~해 볼 만합니다"처럼 단정하거나 권하지 않는다. ' + llm.STYLE)


def _resolve_occ(x):
    """에이전트는 직무 번호 대신 이름을 넣기도 한다. 번호 → 그대로, 이름이 정확히 같거나 한 직무에만 들어 있으면 그 번호."""
    if x in R.occ_idx:
        return x
    names = R.occ.set_index('occupation_id').occupation_name
    hit = names[names == x]
    if hit.empty:
        hit = names[names.str.contains(re.escape(x))] if x else hit
    return hit.index[0] if len(hit) == 1 else x


def _tool(name, args, req):
    cards = req.cards
    if name == 'map_competencies':
        kws, _ = C.tag_sentence(str(args.get('text', ''))[:500])
        return dict(competencies=[dict(keyword=C.D[k][1], category=C.D[k][0], match=m) for k, m in kws.items()])
    if not cards:
        return dict(error='아직 저장한 경험 카드가 없어요. 경험을 먼저 입력해야 해요.')
    if name == 'recommend_jobs':
        r = recommend(CardsReq(cards=cards))
        return dict(jobs=[dict(occupation_id=j['occupation_id'], name=j['name'], score=j['score'], evidence=[e['keyword'] for e in j['evidence']][:6],
                               gaps=j['gaps'][:4], cautions=j['cautions'], open_postings=j['open_postings']) for j in r['jobs']])
    oid = _resolve_occ(str(args.get('occupation_id') or req.occupation_id or ''))
    if name == 'search_postings':
        f = PostingFilters(**{k: args[k] for k in ('sido', 'hours', 'deadline_days') if args.get(k) is not None})
        r = job_postings(PostingsReq(cards=cards, occupation_id=oid, filters=f, limit=5))
        return dict(total=r['total'], postings=[dict(company=p['company'], title=p['title'], region=f"{p['sido']} {p['sigungu']}", wage=p['wage'],
                                                     d_day=p['d_day'], career=p['career'], has_required=[x['keyword'] for x in p['required'] if x['has']],
                                                     missing_required=[x['keyword'] for x in p['required'] if not x['has']], needs_license=p['needs_license'],
                                                     info_thin=p['thin']) for p in r['postings']])
    if name == 'search_courses':
        r = course_plan(CoursesReq(cards=cards, occupation_id=oid, posting_id=args.get('posting_id') or req.posting_id))
        return dict(gaps=[dict(name=g['name'], label=g['label'], courses=[dict(name=c['name'], institution=c['institution'], start=c['start'],
                                                                            fee=c['fee'], region=c['region']) for c in g['courses']]) for g in r['gaps']])
    return dict(error=f'모르는 도구: {name}')


@app.post('/api/chat')
def chat(req: ChatReq):
    ctx = f'지금 화면: {req.step or "알 수 없음"}. 경험 카드 {len(req.cards)}장.' + (f' 보고 있는 직무: {req.occupation_id}.' if req.occupation_id else '')
    msgs = [{'role': m.role, 'content': [{'text': m.text}]} for m in req.messages]
    used = []
    try:
        for _ in range(5):   # 도구 호출은 최대 4번, 다섯 번째는 답
            resp = llm.converse(AGENT_SYSTEM + '\n' + ctx, msgs, 900, TOOLS)
            out = resp['output']['message']
            calls = [c['toolUse'] for c in out['content'] if 'toolUse' in c]
            if resp.get('stopReason') != 'tool_use' or not calls:
                return dict(reply=''.join(c.get('text', '') for c in out['content']).strip(), tools=used)
            msgs.append(out)
            results = []
            for c in calls:
                used.append(c['name'])
                try:
                    res = _tool(c['name'], c.get('input') or {}, req)
                except HTTPException as e:
                    res = dict(error=e.detail)
                results.append({'toolResult': {'toolUseId': c['toolUseId'], 'content': [{'json': res}]}})
            msgs.append({'role': 'user', 'content': results})
    except Exception:   # Bedrock 오류·시간 초과: 상태 안내(DESIGN 5절)
        return dict(reply='지금은 답을 드리기 어려워요. 잠시 뒤 다시 시도해 주세요.', tools=used, error=True)
    return dict(reply='질문이 길어져 답을 정리하지 못했어요. 조금 더 짧게 물어봐 주시겠어요?', tools=used, error=True)
