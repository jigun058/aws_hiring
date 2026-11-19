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
