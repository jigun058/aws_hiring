"""① 경험 수집 인터뷰와 ② 경험 카드의 코드 부분(P3 명세). LLM은 말만 다루고, 여기서 정한다:
슬롯 상태, 다음에 물을 슬롯(5.3), 종료(5.6), 모호함(5.2), 인용 검사(5.5), 근거 등급(3.1), 금지 질문 검사(5.4), 개인정보 가리기.

카드는 화면이 들고 있다가 요청마다 보내는 dict다(api.py). 같은 입력이면 항상 같은 결과가 나온다.
"""
import re

from careerlens.cards import D, LEARN, RANK, TEAM, SELF, build_card, tag_sentence

CORE = ['role', 'purpose', 'actions', 'results']
LIST_SLOTS = {'actions', 'results', 'tools'}
PAID = {'job', 'internship', 'part_time', 'self_employed'}
MAX_QUESTIONS = 8          # P3 5.6 [제안]
MAX_COMPETENCIES = 8       # P3 4.2

# P3 6.1 질문 은행: (기본 질문, 예시 선택지, 모를 때 쉬운 재질문)
BANK = {
    'role': ('이 일에서 직접 맡으신 일은 무엇이었나요?', ['계산·판매', '재고·물품 관리', '사무·서류 정리'], '여러 일 중에 가장 많이 하신 일 하나만 골라 주세요.'),
    'purpose': ('이 일을 왜 하게 되셨나요? 무엇을 해결하거나 만들려고 했는지 궁금해요.', ['맡은 업무라서', '모임·이웃을 돕기 위해', '불편한 점을 줄이려고'], '누구를 위한 일이었나요?'),
    'actions': ('그 일을 하면서 구체적으로 어떤 작업을 하셨나요? 무엇을, 어떻게 했는지 알려 주세요.', ['자료를 모아 정리', '손님·고객을 응대', '물건을 옮기고 정리'], '하루 동안 한 일을 순서대로 말씀해 주셔도 돼요.'),
    'results': ('그 결과 무엇이 달라졌나요? 숫자가 아니어도 괜찮아요.', ['실수가 줄었다', '맡은 일을 혼자 마감했다', '칭찬을 받았다'], '완성해서 남은 결과물이나 맡게 된 일이 있나요?'),
    'results_number': ('대략이라도 괜찮아요. 얼마나 달라졌는지 숫자로 말씀해 주실 수 있나요?', ['한 달에 몇 건', '몇 % 정도', '몇 명'], None),
    'tools': ('작업할 때 쓰신 프로그램이나 도구가 있나요?', ['엑셀', '계산대(POS)', '지게차'], None),
    'challenges': ('하면서 가장 어려웠던 점은 무엇이고, 어떻게 넘어가셨나요?', ['일이 몰렸다', '처음 해 보는 일이었다', '사람 사이 의견이 달랐다'], None),
    'period': ('언제부터 언제까지 하셨나요? 대략이라도 괜찮아요.', ['1년 미만', '1~3년', '3년 넘게'], None),
    'team_size': ('몇 명이 함께하셨나요?', ['혼자', '2~5명', '6명 이상'], None),
}

# P3 5.4 금지 주제. 질문 문장(LLM이 다듬은 것)에 나오면 기본 문장으로 되돌린다.
FORBIDDEN = re.compile(r'공백|쉬(?:셨|었|게 된)|그만두|퇴사 이유|나이|연세|몇 살|결혼|이혼|출산|임신|육아|자녀가 있|아이가 있|아이를 키우|'
                       r'건강|아프|병원에|질병|장애|가족 ?(?:상황|관계|사정)|남편|아내|배우자|소득|수입이|월급이 얼마|재산|종교|정치')

_PII = [(re.compile(r'\d{6}\s?-\s?[1-4]\d{6}'), '[주민번호]'), (re.compile(r'01[016-9][-\s.]?\d{3,4}[-\s.]?\d{4}'), '[전화번호]'),
        (re.compile(r'0\d{1,2}-\d{3,4}-\d{4}'), '[전화번호]'), (re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'), '[이메일]'),
        (re.compile(r'[가-힣]+(?:로|길)\s?\d+(?:-\d+)?(?:번길)?\s?\d*'), '[주소]')]

_VAGUE_ROLE = re.compile(r'(?:팀원|인턴|부원|막내|직원|사원|알바생?|아르바이트생?|회원|구성원|일반 ?직원)\s*(?:이었|였|으로|로)?\S*')
_VAGUE_RESULT = re.compile(r'배웠|보람|뿌듯|좋았|재밌|재미있|즐거|잘\s?됐|성장했|만족')
_CONCRETE_RESULT = re.compile(r'\d|줄였|줄었|늘었|늘렸|완성|마감|맡게|칭찬|수상|상을|합격|채택|만들었|발표')


def mask_pii(text):
    for pat, rep in _PII:
        text = pat.sub(rep, text)
    return text


def _norm(s):
    return re.sub(r'\s+', '', s or '')


def quote_ok(quote, source):
    """인용이 원문 조각인가(공백 차이만 허용). P3 5.5·F3-1 검증 기준."""
    return bool(quote) and _norm(quote) in _norm(source)


def is_vague(slot, value):
    v = (value or '').strip()
    if slot == 'role':
        return bool(_VAGUE_ROLE.fullmatch(v))
    if slot == 'actions':
        return len(re.sub(r'(?:그냥|일을?|업무를?|참여했|도왔|담당했|했|습니다|어요|어|다|요|[.\s])', '', v)) < 3
    if slot == 'results':
        return bool(_VAGUE_RESULT.search(v)) and not _CONCRETE_RESULT.search(v)
    return False   # 목적은 "시켜서"도 filled(P3 5.2)


def new_card(activity, typ, text='', source_id='chat_0'):
    """새 카드. text는 사용자가 처음 적은 글(또는 파일 텍스트) — 이후 인용 검사의 원문."""
    card = dict(activity=activity, type=typ, is_paid_work=typ in PAID, sources={source_id: mask_pii(text)},
                slots={s: ([] if s in LIST_SLOTS else None) for s in BANK if s != 'results_number'},
                slot_status={s: 'missing' for s in CORE + ['tools', 'challenges', 'period', 'team_size']},
                asked=[], unknown_streak=0, easy_pending=None, stopped=False, locked=[], status='draft')
    if typ in PAID:   # 유급 근무는 목적을 묻지 않는다(P3 예시 6)
        card['slots']['purpose'] = dict(value='유급 근무', quote='', source=None, by='system')
        card['slot_status']['purpose'] = 'filled'
    if typ == 'family_care':   # 왜 했는지·성과를 캐묻지 않는다(P3 7.2·예시 7, 금지 질문)
        card['slot_status']['purpose'] = card['slot_status']['results'] = 'not_asked'
    return card


def fill(card, slot, value, quote, source_id, by='ai_extracted', is_estimate=False):
    """슬롯 하나 채우기. 인용이 원문에 없거나 잠긴 슬롯이면 False(값을 버린다)."""
    if slot not in card['slots'] or slot in card['locked'] or not value:
        return False
    src = card['sources'].get(source_id, '')
    if not quote_ok(quote, src):
        return False
    item = dict(value=mask_pii(value), quote=quote, source=source_id, by=by, is_estimate=is_estimate)
    if slot in LIST_SLOTS:
        if any(_norm(x['quote']) == _norm(quote) for x in card['slots'][slot]):
            return True
        card['slots'][slot].append(item)
        vague = all(is_vague(slot, x['value']) for x in card['slots'][slot])
    else:
        card['slots'][slot] = item
        vague = is_vague(slot, value)
    if card['slot_status'].get(slot) != 'not_asked':
        card['slot_status'][slot] = 'vague' if vague else 'filled'
    return True


def _asked(card, slot, kind=None):
    return sum(1 for a in card['asked'] if a['slot'] == slot and (kind is None or a['kind'] == kind))


def next_question(card):
    """P3 5.3·5.6. → {'end': True, 'reason'} 또는 {'slot', 'kind', 'question', 'options'}(기본 문장)."""
    st = card['slot_status']
    if card['stopped']:
        return dict(end=True, reason='user_stop')
    if len(card['asked']) >= MAX_QUESTIONS:
        return dict(end=True, reason='max_questions')
    if card['unknown_streak'] >= 3:
        return dict(end=True, reason='unknown_streak')
    if card['easy_pending']:
        s = card['easy_pending']
        q, opts, easy = BANK[s]
        return dict(slot=s, kind='easy', question=easy or q, options=opts)
    for want in ('missing', 'vague'):   # ① 핵심 빈칸 → ② 핵심 모호 (같은 슬롯은 기본+쉬운 재질문 2번까지)
        for s in CORE:
            if st[s] == want and _asked(card, s) < 2:
                q, opts, _ = BANK[s]
                return dict(slot=s, kind='basic', question=q, options=opts)
    # ③ 자료·진술 불일치: 파일 업로드가 붙으면 넣는다. ④ 등급 올리기: 트랙 B는 희망 직무가 없어 건너뜀(P3 F3-2 선택 입력)
    res = card['slots']['results']
    if st['results'] == 'filled' and res and not any(re.search(r'\d', r['value']) for r in res) and not _asked(card, 'results', 'number'):
        q, opts, _ = BANK['results_number']   # ⑤ 정성 성과의 수치, 1회만
        return dict(slot='results', kind='number', question=q, options=opts)
    for s in ('period', 'team_size'):   # ⑥
        if st[s] == 'missing' and not _asked(card, s):
            q, opts, _ = BANK[s]
            return dict(slot=s, kind='basic', question=q, options=opts)
    if st['challenges'] == 'missing' and not _asked(card, 'challenges') and len(card['asked']) < 4:   # ⑦
        q, opts, _ = BANK['challenges']
        return dict(slot='challenges', kind='basic', question=q, options=opts)
    done = all(st[s] in ('filled', 'not_asked') for s in CORE)
    return dict(end=True, reason='complete' if done else 'no_more')


def record_question(card, q):
    card['asked'].append(dict(slot=q['slot'], kind=q['kind']))
    if q['kind'] == 'easy':
        card['easy_pending'] = None
    card['status'] = 'interviewing'


def apply_answer(card, slot, answer, interpretation, source_id):
    """P3 5.5. interpretation: {'kind': content|unknown|skip|stop|other, 'slots': [{slot, value, quote, is_estimate?}]}
    (LLM이 만든 것 또는 규칙 대체). 값마다 인용을 답변 원문으로 검사한다. → 실제로 채운 슬롯 목록"""
    card['sources'][source_id] = mask_pii(answer)
    kind = interpretation.get('kind', 'content')
    if kind == 'stop':
        card['stopped'] = True
        return []
    if kind == 'skip':
        card['slot_status'][slot] = 'skipped'
        card['unknown_streak'] += 1
        return []
    filled = []
    if kind == 'content':
        for x in interpretation.get('slots', []):
            if fill(card, x.get('slot'), x.get('value'), x.get('quote'), source_id, 'user_answer', bool(x.get('is_estimate'))):
                filled.append(x['slot'])
    if filled:
        card['unknown_streak'] = 0
        return filled
    # 모름, 무관한 답, 인용 검사 실패 → 같은 슬롯을 쉬운 형태로 1회. 그것도 모르면 unknown_by_user
    if _asked(card, slot, 'easy') or BANK.get(slot, (None, None, None))[2] is None:
        card['slot_status'][slot] = 'unknown_by_user'
        card['unknown_streak'] += 1
    else:
        card['easy_pending'] = slot
    return []


def safe_question(phrased, base):
    """LLM이 다듬은 질문이 금지 주제를 건드리거나 길면 기본 문장(P3 F3-3 예외 처리)."""
    if not phrased or FORBIDDEN.search(phrased) or len(re.findall(r'[.?!]', phrased)) > 2:
        return base
    return phrased


# ---------------- F3-5·F3-6 역량과 근거 등급 (슬롯 기반) ----------------
def _sentence(card, item):
    q = item['quote'] or item['value']
    src = card['sources'].get(item.get('source'), '')
    for s in re.split(r'(?<=[.!?])\s+|\n+', src):
        if q and _norm(q) in _norm(s):
            return s.strip()
    return q


_CAT_ORDER = {c: 0 for c in ('C1', 'C2', 'C3', 'C7', 'C8')} | {'C6': 1, 'C4': 2, 'C5': 2}


def competencies(card):
    """슬롯 인용에서 역량을 찾고 P3 3.1로 등급을 매긴다. → {kw_idx: {level, match, quote}} (cards.build_card와 같은 모양)"""
    if card['type'] == 'certificate':
        return build_card(card['activity'], 'certificate', ' '.join(card['sources'].values()))['comps']
    sl = card['slots']
    has_result = any(not is_vague('results', r['value']) for r in sl['results'])
    has_role = card['slot_status']['role'] == 'filled'
    # 인용이 짧게 잘려 주어가 빠지면("병원 같이 다니고…") 두 조건짜리 경험 규칙이 안 걸리므로, 인용이 든 원문 문장 전체로 찾는다
    sents = [(_sentence(card, x), 'action') for x in ([sl['role']] if sl['role'] else []) + sl['actions']]
    sents += [(_sentence(card, x), 'result') for x in sl['results']]
    sents += [(_sentence(card, x), 'tool') for x in sl['tools']]
    comps = {}
    for s, kind in sents:
        kws, _ = tag_sentence(s)
        for k, mt in kws.items():
            if kind == 'tool' or LEARN.search(s):
                lv = 'L1'   # 도구 이름만, 수강·학습만
            elif TEAM.search(s) and not SELF.search(s) and not has_role:
                lv = 'L0'   # 팀 성과인데 본인 역할 불명확
            else:
                lv = 'L3' if has_result else 'L2'
            if k not in comps or RANK[lv] > RANK[comps[k]['level']]:
                comps[k] = dict(level=lv, match=mt, quote=s)
    comps = {k: v for k, v in comps.items() if v['level'] != 'L0'}
    keep = sorted(comps, key=lambda k: (_CAT_ORDER.get(D[k][0], 3), -RANK[comps[k]['level']], k))[:MAX_COMPETENCIES]
    return {k: comps[k] for k in keep}


def card_text(card):
    """엔진(글 유사도·자체 추출)에 넘길 카드 글: 채운 슬롯의 인용."""
    sl = card['slots']
    parts = [x['quote'] for s in ('role', 'purpose') if sl[s] and sl[s]['quote'] for x in [sl[s]]]
    parts += [x['quote'] for s in ('actions', 'results', 'tools') for x in sl[s]]
    return ' '.join(parts) or ' '.join(card['sources'].values())


# ---------------- LLM이 실패했을 때의 규칙 대체 ----------------
from careerlens.cards import ACTION, RESULT  # noqa: E402

_UNKNOWN = re.compile(r'모르|몰라|기억(?:이)? ?(?:안|나지)|글쎄|생각이 안')
_SKIP = re.compile(r'건너|넘어가|패스|다음 ?질문|말하기 싫|말씀 ?드리기')
_STOP = re.compile(r'^(?:그만|끝|됐어요|이제 됐)')


def rule_extract(text):
    """경험 글 → 슬롯 후보(정규식). 시뮬레이션의 판정식과 같은 기준이다."""
    out = []
    for s in [x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+', text) if x.strip()]:
        if re.search(r'맡|담당', s):
            out.append(dict(slot='role', value=s, quote=s))
        if RESULT.search(s):
            out.append(dict(slot='results', value=s, quote=s))
        elif ACTION.search(s):
            out.append(dict(slot='actions', value=s, quote=s))
    return out


def rule_interpret(slot, answer):
    a = answer.strip()
    if _STOP.search(a):
        return dict(kind='stop')
    if _SKIP.search(a):
        return dict(kind='skip')
    if _UNKNOWN.search(a) and len(a) < 30:
        return dict(kind='unknown')
    return dict(kind='content', slots=[dict(slot=slot, value=a, quote=a)])
