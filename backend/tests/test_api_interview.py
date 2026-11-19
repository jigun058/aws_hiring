"""인터뷰·추천 이유 API. LLM은 가짜로 바꿔 끼운다(실제 Bedrock 호출 없음)."""
import json

import pytest
from fastapi.testclient import TestClient

from careerlens import llm


@pytest.fixture(scope='module')
def client():
    from careerlens.api import app
    return TestClient(app)


def fake(replies):
    """converse를 바꿔 끼운다. replies: 호출 순서대로 돌려줄 JSON(dict) 또는 예외."""
    it = iter(replies)

    def converse(system, messages, max_tokens=1000, tools=None):
        r = next(it)
        if isinstance(r, Exception):
            raise r
        return {'output': {'message': {'content': [{'text': json.dumps(r, ensure_ascii=False)}]}}}
    return converse


def test_llm_down_uses_rules(client, monkeypatch):
    monkeypatch.setattr(llm, 'converse', fake([RuntimeError('down')] * 10))
    r = client.post('/api/interview/start', json=dict(text='회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 장부를 정리했습니다.', type='job')).json()
    c = r['cards'][0]
    assert c['card']['made_by'] == 'rule'
    assert c['card']['slot_status']['actions'] == 'filled'
    assert c['question']['slot'] == 'role' and c['question']['question'] == '이 일에서 직접 맡으신 일은 무엇이었나요?'
    a = client.post('/api/interview/answer', json=dict(card=c['card'], answer='경리 담당으로 장부랑 급여 정리를 맡았어요')).json()
    assert a['filled'] == ['role'] and a['card']['slot_status']['role'] == 'filled'
    assert '스프레드시트(엑셀)' in {x['keyword'] for x in a['competencies']}
    rec = client.post('/api/recommend', json=dict(cards=[a['card_in']])).json()
    assert rec['jobs'][0]['name'] == '경리 사무원'


def test_llm_split_and_fabricated_quote_dropped(client, monkeypatch):
    text = '마트에서 3년 동안 계산이랑 재고 관리를 했어요. 학부모회에서 총무를 맡아 회비를 엑셀로 정리했어요.'
    monkeypatch.setattr(llm, 'converse', fake([
        {'experiences': [
            {'activity': '마트 근무', 'type': 'job', 'slots': [
                {'slot': 'actions', 'value': '계산과 재고 관리', 'quote': '계산이랑 재고 관리를 했어요'},
                {'slot': 'results', 'value': '매출 20% 증가', 'quote': '매출을 20% 올렸어요'}]},   # 원문에 없는 인용 → 버림
            {'activity': '학부모회 총무', 'type': 'community', 'slots': [
                {'slot': 'role', 'value': '총무', 'quote': '총무를 맡아'},
                {'slot': 'actions', 'value': '회비 엑셀 정리', 'quote': '회비를 엑셀로 정리했어요'}]}]},
        {'question': '마트에서 주로 맡으신 일은 무엇이었나요?', 'options': ['계산', '재고 관리']},
        {'question': '혹시 아이가 있으셔서 학부모회를 하셨나요?', 'options': ['네', '아니요']},   # 금지 주제 → 기본 문장
    ]))
    cards = client.post('/api/interview/start', json=dict(text=text)).json()['cards']
    assert [c['card']['type'] for c in cards] == ['job', 'community']
    assert {c['card']['made_by'] for c in cards} == {'ai'}
    assert cards[0]['card']['slots']['results'] == []
    assert cards[0]['question']['question'] == '마트에서 주로 맡으신 일은 무엇이었나요?'
    assert '아이' not in cards[1]['question']['question']


def test_certificate_card_from_resume_keeps_only_its_quotes(client, monkeypatch):
    """이력서처럼 경험이 여럿인 글: 자격증 카드에 글 전체가 아니라 그 카드의 인용만 들어간다(11/19 실제 PDF에서 찾음)."""
    text = '물류센터 8년. 엑셀로 재고 현황표 작성. 고객 전화 응대.\n자격\n지게차운전기능사 (2014)'
    monkeypatch.setattr(llm, 'converse', fake([
        {'experiences': [
            {'activity': '물류센터 근무', 'type': 'job', 'slots': [{'slot': 'actions', 'value': '재고표', 'quote': '엑셀로 재고 현황표 작성'}]},
            {'activity': '지게차운전기능사 취득', 'type': 'certificate', 'slots': [{'slot': 'role', 'value': '취득', 'quote': '지게차운전기능사 (2014)'}]}]},
    ] + [RuntimeError('down')] * 5))
    cert = client.post('/api/interview/start', json=dict(text=text)).json()['cards'][1]
    assert [a['value'] for a in cert['card']['slots']['actions']] == ['지게차운전기능사 (2014)']
    assert '스프레드시트(엑셀)' not in {k['keyword'] for k in cert['competencies']}


def test_explain_drops_invented_numbers(client, monkeypatch):
    job = dict(name='경리 사무원', score=59.56, gaps=['회계 프로그램'], cautions=[],
               evidence=[dict(keyword='회계·경리 처리', level='L2', card='회사 경리', quote='회사에서 5년 동안 경리 업무를 했습니다.')])
    monkeypatch.setattr(llm, 'converse', fake([{'reason': '합격 확률이 90%예요.'}]))
    r = client.post('/api/explain', json=dict(job=job)).json()
    assert r['by'] == 'rule' and '회계·경리 처리' in r['reason']
    monkeypatch.setattr(llm, 'converse', fake([{'reason': '5년 동안 경리 업무를 하신 경험이 회계·경리 처리와 이어져요.'}]))
    assert client.post('/api/explain', json=dict(job=job)).json()['by'] == 'ai'


def test_chat_calls_tool_and_answers(client, monkeypatch):
    calls = []

    def converse(system, messages, max_tokens=1000, tools=None):
        calls.append(messages[-1])
        if len(calls) == 1:
            return {'stopReason': 'tool_use', 'output': {'message': {'role': 'assistant', 'content': [
                {'toolUse': {'toolUseId': 't1', 'name': 'recommend_jobs', 'input': {}}}]}}}
        return {'stopReason': 'end_turn', 'output': {'message': {'role': 'assistant', 'content': [{'text': '경리 사무원이 가장 잘 맞아요.'}]}}}
    monkeypatch.setattr(llm, 'converse', converse)
    card = dict(title='회사 경리', type='job', text='회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 장부를 정리했습니다.')
    r = client.post('/api/chat', json=dict(messages=[dict(role='user', text='어떤 직무가 맞아요?')], cards=[card])).json()
    assert r == dict(reply='경리 사무원이 가장 잘 맞아요.', tools=['recommend_jobs'])
    tool_result = calls[1]['content'][0]['toolResult']['content'][0]['json']
    assert tool_result['jobs'][0]['name'] == '경리 사무원'


def test_chat_knows_screen_and_hides_ids(client, monkeypatch):
    systems = []

    def converse(system, messages, max_tokens=1000, tools=None):
        systems.append(system)
        return {'stopReason': 'end_turn', 'output': {'message': {'role': 'assistant', 'content': [{'text': '경리 사무원(OCC0001)은 잘 맞아요.'}]}}}
    monkeypatch.setattr(llm, 'converse', converse)
    card = dict(title='회사 경리', type='job', text='회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 장부를 정리했습니다.')
    job = client.post('/api/recommend', json=dict(cards=[card])).json()['jobs'][0]
    post = client.post('/api/postings', json=dict(cards=[card], occupation_id=job['occupation_id'])).json()['postings'][0]
    r = client.post('/api/chat', json=dict(messages=[dict(role='user', text='이 공고에서 부족한 게 뭐예요?')], cards=[card],
                                           occupation_id=job['occupation_id'], posting_id=post['posting_id'])).json()
    assert r['reply'] == '경리 사무원은 잘 맞아요.'
    assert f"보고 있는 직무: {job['name']}" in systems[0] and post['company'] in systems[0]


def test_chat_bedrock_down(client, monkeypatch):
    monkeypatch.setattr(llm, 'converse', fake([RuntimeError('down')]))
    r = client.post('/api/chat', json=dict(messages=[dict(role='user', text='안녕하세요')])).json()
    assert r['error'] and '다시 시도' in r['reply']


def test_agent_tool_accepts_occupation_name():
    from careerlens.api import _resolve_occ
    assert _resolve_occ('OCC0410') == 'OCC0410'
    assert _resolve_occ('요양보호사') == 'OCC0410'
    assert _resolve_occ('없는 직무') == '없는 직무'


def test_edit_card_field(client, monkeypatch):
    """② 화면에서 고친 칸: 원문이 되고 잠기며, 역량이 다시 계산된다. 질문은 그대로."""
    monkeypatch.setattr(llm, 'converse', fake([RuntimeError('down')] * 10))
    c = client.post('/api/interview/start', json=dict(text='회사에서 5년 동안 경리 업무를 했습니다.', type='job')).json()['cards'][0]
    q = c['card']['last_question']
    e = client.post('/api/interview/edit', json=dict(card=c['card'], field='actions', value='엑셀로 급여 장부를 정리했습니다.\n세금계산서를 발행했습니다.')).json()
    assert [x['value'] for x in e['card']['slots']['actions']] == ['엑셀로 급여 장부를 정리했습니다.', '세금계산서를 발행했습니다.']
    assert 'actions' in e['card']['locked'] and e['question'] == q
    assert '스프레드시트(엑셀)' in {x['keyword'] for x in e['competencies']}
    assert '엑셀로 급여 장부를 정리했습니다.' in e['card_in']['text']
    e = client.post('/api/interview/edit', json=dict(card=e['card'], field='type', value='part_time')).json()
    assert e['card_in']['type'] == 'part_time' and e['card_in']['paid'] is True
    assert client.post('/api/interview/edit', json=dict(card=e['card'], field='type', value='hobby')).status_code == 400
    e = client.post('/api/interview/edit', json=dict(card=e['card'], field='actions', value='')).json()
    assert e['card']['slot_status']['actions'] == 'missing' and 'actions' not in e['card']['locked']


def test_llm_endpoints_rate_limited(client, monkeypatch):
    from careerlens import api as X
    monkeypatch.setattr(X, 'PER_MIN', 2)
    monkeypatch.setattr(X, '_hits', X.defaultdict(X.deque))
    # 앞쪽 주소를 바꿔도 CloudFront가 붙인 맨 뒤 주소로 센다
    codes = [client.post('/api/chat', json={}, headers={'X-Forwarded-For': f'1.1.1.{i}, 9.9.9.9'}).status_code for i in range(3)]
    assert codes == [422, 422, 429]
    assert client.post('/api/chat', json={}, headers={'X-Forwarded-For': '8.8.8.8'}).status_code == 422   # 다른 사람은 그대로
    assert client.post('/api/recommend', json={}, headers={'X-Forwarded-For': '9.9.9.9'}).status_code == 422   # AI 안 쓰는 API는 안 셈


def test_cleared_fields_stay_cleared_and_change_recommendation(client, monkeypatch):
    monkeypatch.setattr(llm, 'converse', fake([RuntimeError('down')] * 10))
    start = lambda **k: client.post('/api/interview/start', json=k).json()['cards'][0]
    edit = lambda c, f, v: client.post('/api/interview/edit', json=dict(card=c['card'], field=f, value=v)).json()
    job = start(title='물류센터 근무', type='job', text='물류센터에서 10년 동안 지게차로 상하차와 운반을 했습니다. 입고 검수와 재고 관리도 맡았습니다.')
    cleared = edit(edit(job, 'actions', ''), 'role', '')
    assert cleared['card_in']['text'] == '' and cleared['competencies'] == []   # 처음 글로 되살아나지 않는다
    cert = start(title='자격증', type='certificate', text='지게차운전기능사 자격증과 1종 보통 운전면허를 보유하고 있습니다.')
    assert cert['card']['slots']['actions'] and '지게차 운전' in {k['keyword'] for k in cert['competencies']}   # 고칠 수 있게 칸에 보임
    no_fork = edit(cert, 'actions', '1종 보통 운전면허를 보유하고 있습니다.')
    assert '지게차 운전' not in {k['keyword'] for k in no_fork['competencies']}
    score = lambda cards: {j['name']: j['score'] for j in client.post('/api/recommend', json=dict(cards=cards)).json()['jobs']}
    assert score([job['card_in'], no_fork['card_in']]).get('지게차 운전원', 0) < score([job['card_in'], cert['card_in']])['지게차 운전원']


def test_chat_told_cards_and_how_to_fix_them(client, monkeypatch):
    seen = {}

    def converse(system, messages, max_tokens=1000, tools=None):
        seen['system'] = system
        return {'output': {'message': {'content': [{'text': '② 경험 카드에서 고쳐 주세요.'}]}}}
    monkeypatch.setattr(llm, 'converse', converse)
    card = dict(title='자격증', type='certificate', text='지게차운전기능사 자격증을 보유하고 있습니다.')
    client.post('/api/chat', json=dict(messages=[dict(role='user', text='사실 나 지게차 자격증 없어')], step='③ 직무 추천', cards=[card]))
    assert '지게차운전기능사 자격증을 보유' in seen['system'] and '이 카드 지우기' in seen['system']


def test_similar_cards_share_merge_key_and_merge_keeps_both(client, monkeypatch):
    """P3 1절: 이력서 PDF와 자격증 사진에서 같은 자격증 카드가 2장 생기면 같은 키 → 화면이 합치기를 제안. 합치면 두 원문이 다 남는다."""
    monkeypatch.setattr(llm, 'converse', fake([RuntimeError('down')] * 20))
    a = client.post('/api/interview/start', json=dict(text='지게차운전기능사 (2014)', type='certificate')).json()['cards'][0]
    b = client.post('/api/interview/start', json=dict(text='국가기술자격증 자격종목: 지게차운전기능사 취득일: 2014년 5월', type='certificate')).json()['cards'][0]
    c = client.post('/api/interview/start', json=dict(text='컴퓨터활용능력 2급 자격증', type='certificate')).json()['cards'][0]
    assert a['merge_keys'] == b['merge_keys'] == ['lic:지게차운전기능사'] and c['merge_keys'] != a['merge_keys']
    j1 = client.post('/api/interview/start', json=dict(text='물류센터에서 5년 일했어요', title='○○ 물류센터 재고 관리', type='job')).json()['cards'][0]
    j2 = client.post('/api/interview/start', json=dict(text='물류센터에서 지게차를 탔어요', title='물류센터 근무', type='job')).json()['cards'][0]
    assert j1['merge_keys'] == j2['merge_keys'] == ['w:물류센터']
    m = client.post('/api/interview/merge', json=dict(a=a['card'], b=b['card'])).json()
    assert m['card']['activity'] == a['card']['activity'] and len(m['card']['sources']) == 2
    assert {x['value'] for x in m['card']['slots']['actions']} >= {'지게차운전기능사 (2014)'} and len(m['card']['slots']['actions']) >= 2
    rec = client.post('/api/recommend', json=dict(cards=[m['card_in'], j1['card_in']])).json()
    assert rec['jobs']


def test_llm_closed_choice_only_from_candidates_and_not_scored(client, monkeypatch):
    """P3 4.1 ②: 규칙이 못 잡은 행동 문장만 후보 중에서 AI가 고른다. 후보 밖 번호는 버리고, 고른 것은 점수에 넣지 않는다."""
    from careerlens import cards as C
    s1, s2 = '손님들 머리를 자르고 염색을 해 드렸어요.', '화단에 꽃을 심었어요.'
    c1, c2 = C.candidates(s1), C.candidates(s2)
    outside = next(k for k in C.D if k not in c2)
    monkeypatch.setattr(llm, 'converse', fake([
        {'experiences': [{'activity': '미용실 근무', 'type': 'job', 'slots': [
            {'slot': 'actions', 'value': '머리 손질', 'quote': '손님들 머리를 자르고 염색을 해 드렸어요'},
            {'slot': 'actions', 'value': '꽃 심기', 'quote': '화단에 꽃을 심었어요'}]}]},
        RuntimeError('phrase down'),
        {'choices': [{'id': 0, 'kw': c1[0], 'reason': '손님을 맞아 요청대로 해 드림'}, {'id': 1, 'kw': outside, 'reason': '후보 밖'}]},
    ]))
    r = client.post('/api/interview/start', json=dict(text=s1 + ' ' + s2)).json()['cards'][0]
    ai = [k for k in r['competencies'] if k['match'] == 'llm_choice']
    assert [(k['kw_idx'], k['quote']) for k in ai] == [(c1[0], s1)] and ai[0]['reason']
    assert r['card']['llm_choices'][s2] == [None, None]
    from careerlens.api import CardIn, _internal
    assert c1[0] not in _internal([CardIn(**r['card_in'])])[0]['comps']   # 점수에 쓰는 카드 등급에 들어가지 않음


def test_chat_stream_sends_pieces_tools_and_hides_ids(client, monkeypatch):
    """B27: 답을 조각으로 흘려보낸다. 도구를 부르면 그 이름을 먼저 알리고, 조각 사이에 걸친 직무 번호도 지운다."""
    calls = []

    def stream(system, messages, max_tokens=1000, tools=None):
        calls.append(messages[-1])
        if len(calls) == 1:
            yield ('text', '찾아볼게요.')
            return {'role': 'assistant', 'content': [{'text': '찾아볼게요.'}, {'toolUse': {'toolUseId': 't1', 'name': 'recommend_jobs', 'input': {}}}]}, 'tool_use'
        for t in ['경리 사무원 (OC', 'C0123)이 가장 ', '잘 맞아요.']:
            yield ('text', t)
        return {'role': 'assistant', 'content': [{'text': '…'}]}, 'end_turn'
    monkeypatch.setattr(llm, 'converse_stream', stream)
    card = dict(title='회사 경리', type='job', text='회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 장부를 정리했습니다.')
    r = client.post('/api/chat/stream', json=dict(messages=[dict(role='user', text='어떤 직무가 맞아요?')], cards=[card]))
    evs = [json.loads(x) for x in r.text.splitlines()]
    assert {'tool': 'recommend_jobs'} in evs and evs[-1] == {'done': True}
    assert ''.join(e.get('t', '') for e in evs) == '찾아볼게요.\n\n경리 사무원이 가장 잘 맞아요.'
    assert calls[1]['content'][0]['toolResult']['content'][0]['json']['jobs'][0]['name'] == '경리 사무원'


def test_chat_stream_bedrock_down(client, monkeypatch):
    def down(*a, **k):
        raise RuntimeError('down')
        yield
    monkeypatch.setattr(llm, 'converse_stream', down)
    r = client.post('/api/chat/stream', json=dict(messages=[dict(role='user', text='안녕')]))
    assert [json.loads(x) for x in r.text.splitlines()] == [{'error': '지금은 답을 드리기 어려워요. 잠시 뒤 다시 시도해 주세요.'}]
