"""P3 인터뷰·카드 코드 부분 시험(LLM 없음). 예시 번호는 P3 9절."""
from careerlens import interview as I
from careerlens.cards import D


def names(comps):
    return {D[k][1]: (v['level'], v['match']) for k, v in comps.items()}


def answer(card, q, text, interp=None, n=[0]):
    n[0] += 1
    I.record_question(card, q)
    return I.apply_answer(card, q['slot'], text, interp or I.rule_interpret(q['slot'], text), f'chat_{n[0]}')


def test_paid_job_skips_purpose_and_asks_role_first():
    """예시 6: 유급 근무는 목적을 filled로 본다. 경력 공백은 묻지 않는다."""
    text = '15년 전에 마트에서 3년 동안 계산이랑 재고 관리 했어요. 발주도 제가 넣었어요.'
    c = I.new_card('마트 근무', 'job', text)
    for x in I.rule_extract(text):
        I.fill(c, x['slot'], x['value'], x['quote'], 'chat_0')
    assert c['slot_status']['purpose'] == 'filled' and c['slot_status']['actions'] == 'filled'
    q = I.next_question(c)
    assert q['slot'] == 'role' and not I.FORBIDDEN.search(q['question'])
    assert {'재고 관리', '주문·결제 처리'} <= set(names(I.competencies(c)))


def test_family_care_never_asks_purpose_or_results():
    """예시 7: 가족 돌봄은 목적·성과를 캐묻지 않는다. EXB01 → 돌봄 서비스·노인 돌봄 지식 L2 전이."""
    text = '시어머니가 편찮으셔서 2년 동안 병원 같이 다니고 약 챙겨 드렸어요.'
    c = I.new_card('시어머니 돌봄', 'family_care', text)
    I.fill(c, 'actions', '병원 동행과 약 챙기기', '병원 같이 다니고 약 챙겨 드렸어요', 'chat_0')
    asked = []
    while not (q := I.next_question(c)).get('end'):
        asked.append(q['slot'])
        answer(c, q, '건너뛸게요')
    assert 'purpose' not in asked and 'results' not in asked
    n = names(I.competencies(c))
    assert n['돌봄 서비스'] == ('L2', 'transferable') and n['노인 돌봄 지식'] == ('L2', 'transferable')


def test_quote_must_be_in_source():
    c = I.new_card('마트 근무', 'job', '마트에서 계산을 했어요.')
    assert not I.fill(c, 'results', '매출 20% 증가', '매출을 20% 늘렸어요', 'chat_0')   # 원문에 없는 수치
    assert c['slot_status']['results'] == 'missing'


def test_vague_slots():
    assert I.is_vague('role', '팀원') and not I.is_vague('role', '재고 관리 담당')
    assert I.is_vague('actions', '참여했어요') and not I.is_vague('actions', '엑셀로 회비를 정리했어요')
    assert I.is_vague('results', '많이 배웠고 보람 있었어요') and not I.is_vague('results', '재고 실수가 줄었어요')


def test_unknown_twice_then_moves_on():
    """예시 5 흐름: 모름 → 쉬운 재질문 1회 → 또 모름 → unknown_by_user, 다음 슬롯으로."""
    c = I.new_card('동아리', 'community', '동아리 총무를 맡았어요.')
    q = I.next_question(c)
    assert q['slot'] == 'role' and q['kind'] == 'basic'
    answer(c, q, '잘 모르겠어요')
    q2 = I.next_question(c)
    assert (q2['slot'], q2['kind']) == ('role', 'easy')
    answer(c, q2, '기억이 안 나요')
    assert c['slot_status']['role'] == 'unknown_by_user'
    assert I.next_question(c)['slot'] == 'purpose'


def test_ends_after_three_unknowns_or_eight_questions():
    c = I.new_card('동아리', 'community', '동아리 활동')
    for _ in range(3):
        q = I.next_question(c)
        answer(c, q, '건너뛸게요')
    assert I.next_question(c) == dict(end=True, reason='unknown_streak')
    c = I.new_card('동아리', 'community', '동아리 활동')
    c['asked'] = [dict(slot='tools', kind='basic')] * 8
    assert I.next_question(c)['reason'] == 'max_questions'


def test_result_upgrades_level():
    """예시 2: 행동 + 성과(제3자 평가) → L3."""
    c = I.new_card('학부모회', 'community', '학부모회에서 총무를 맡아 회비를 엑셀로 정리했습니다.')
    I.fill(c, 'actions', '회비를 엑셀로 정리', '회비를 엑셀로 정리했습니다', 'chat_0')
    assert names(I.competencies(c))['스프레드시트(엑셀)'][0] == 'L2'
    q = dict(slot='results', kind='basic')
    answer(c, q, '덕분에 회비 정산 실수가 없어져서 다음 해에도 총무를 맡았어요.')
    assert names(I.competencies(c))['스프레드시트(엑셀)'][0] == 'L3'


def test_learning_only_stays_l1():
    c = I.new_card('정보화 교육', 'education', '구청에서 엑셀을 배웠어요.')
    I.fill(c, 'actions', '엑셀 배우기', '엑셀을 배웠어요', 'chat_0')
    assert names(I.competencies(c))['스프레드시트(엑셀)'][0] == 'L1'


def test_forbidden_question_falls_back():
    base = I.BANK['role'][0]
    assert I.safe_question('경력이 공백인 이유가 있으신가요?', base) == base
    assert I.safe_question('아이가 있으셔서 쉬셨나요?', base) == base
    assert I.safe_question('마트에서 주로 어떤 일을 맡으셨나요?', base) == '마트에서 주로 어떤 일을 맡으셨나요?'


def test_pii_masked():
    m = I.mask_pii('연락처 010-1234-5678, 메일 a.b@x.com, 주민번호 800101-2345678')
    assert '010' not in m and '@' not in m and '2345678' not in m


def test_same_input_same_question():
    """F3-2 검증 기준: 같은 입력 → 같은 결과."""
    a, b = I.new_card('카페', 'part_time', '카페 아르바이트'), I.new_card('카페', 'part_time', '카페 아르바이트')
    assert I.next_question(a) == I.next_question(b)


def test_team_size_not_asked():
    """11/20 로직팀 요청: 팀 규모는 역량·점수에 쓰이지 않아 묻지 않는다. 기간은 묻는다."""
    from careerlens import interview as I
    c = I.new_card('경리', 'job', '장부 정리 담당. 장부를 엑셀로 정리했다. 마감이 하루 빨라졌다. 업무라서 했다.')
    for slot, q in [('role', '장부 정리 담당'), ('actions', '장부를 엑셀로 정리했다'), ('results', '마감이 하루 빨라졌다'), ('purpose', '업무라서 했다')]:
        I.fill(c, slot, q, q, 'chat_0')
    asked = []
    while not (q := I.next_question(c)).get('end'):
        asked.append(q['slot'])
        I.record_question(c, q)
        I.apply_answer(c, q['slot'], '건너뛸게요', dict(kind='skip'), f'chat_{len(c["sources"])}')
    assert 'period' in asked and 'team_size' not in asked


def test_course_name_links_course_competencies_at_l1():
    """P3 4.2 수료증: 고용24 과정명과 맞으면 그 과정의 역량을 L1로(match='course'). 수료 이야기가 아니면 붙이지 않는다."""
    from careerlens import interview as I
    from careerlens.cards import D
    c = I.new_card('요양보호사 과정', 'education', '작년에 요양보호사 자격취득과정을 수료했어요.')
    I.fill(c, 'actions', '요양보호사 과정 수료', '요양보호사 자격취득과정을 수료했어요', 'chat_0')
    comps = {D[k][1]: v for k, v in I.competencies(c).items()}
    got = {k: v for k, v in comps.items() if v['match'] == 'course'}   # 문장에서 이미 찾은 역량은 그대로, 과정에서는 빠진 것만 더한다
    assert '가사·생활 지원' in got and comps['신체활동 지원']['match'] != 'course'
    assert all(v['level'] == 'L1' and '요양보호사' in v['course'] for v in got.values())
    j = I.new_card('요양원 근무', 'job', '요양원에서 5년 동안 어르신 식사를 도와 드렸어요.')
    I.fill(j, 'actions', '어르신 식사 도움', '요양원에서 5년 동안 어르신 식사를 도와 드렸어요', 'chat_0')
    assert not any(v['match'] == 'course' for v in I.competencies(j).values())


def test_certificate_card_course_completion_is_l1_not_l3():
    """AI가 수료 이야기를 자격증 카드로 분류해도, 과정 수료만이면 자격 규칙 역량은 L1(P3 3.1·4.2). 취득·보유면 L3."""
    from careerlens.cards import build_card
    done = build_card('요양보호사 자격취득과정 수료', 'certificate', '작년에 요양보호사 자격취득과정을 수료했어요.')['comps']
    held = build_card('요양보호사', 'certificate', '요양보호사 자격증을 취득했습니다.')['comps']
    assert done and {v['level'] for v in done.values()} == {'L1'}
    assert held and {v['level'] for v in held.values()} == {'L3'}
