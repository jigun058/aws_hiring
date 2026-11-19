"""공고 AI 보완(P2 F2-5). LLM은 가짜로 바꿔 끼운다."""
import json

from careerlens import llm, posting_ai
from careerlens.posting_analysis import analyze


def reply(obj, usage=(100, 20)):
    return lambda system, messages, max_tokens=1000, tools=None, **k: {
        'output': {'message': {'content': [{'text': json.dumps(obj, ensure_ascii=False)}]}},
        'usage': {'inputTokens': usage[0], 'outputTokens': usage[1]}}


def test_ai_adds_competencies_keeps_rule_type_and_drops_invented_quotes(monkeypatch):
    r = analyze(dict(posting_id='X', title='물류 사원', job_description_raw='창고 물품 입출고  즉시 출근 가능자  컴퓨터 문서 작업 가능하신 분'))
    by_text = {c['text']: c for c in r['clauses']}
    ex, go = by_text['컴퓨터 문서 작업 가능하신 분'], by_text['즉시 출근 가능자']
    monkeypatch.setattr(llm, 'converse', reply({'clauses': [
        {'clause_id': ex['clause_id'], 'type': '우대', 'phrases': [{'text': '문서 작성', 'quote': '컴퓨터 문서 작업'}]},
        {'clause_id': go['clause_id'], 'type': '필수', 'phrases': [{'text': '지게차 운전', 'quote': '지게차 운전 가능자'}]},   # 원문에 없음
        {'clause_id': 99, 'type': '필수', 'phrases': []},   # 없는 구절
    ]}))
    usage = {}
    ai = posting_ai.classify(r['clauses'], '물류 사무원', usage=usage)
    assert ai['bad_quotes'] == 1 and 99 not in ai['clauses'] and usage == {'inputTokens': 100, 'outputTokens': 20, 'calls': 1}
    assert ai['clauses'][ex['clause_id']]['type'] == '우대'
    s = posting_ai.supplement(r, ai)
    added = [x for x in s['requirements'] if x['method'] == 'ai']
    assert [x['keyword'] for x in added] == ['문서작성(워드)'] and added[0]['type'] == ex['type']   # 종류는 규칙 것
    assert s['ai_used'] and '지게차 운전' not in {x['keyword'] for x in s['requirements']}


def test_ai_failure_returns_none(monkeypatch):
    monkeypatch.setattr(llm, 'converse', reply({'oops': 1}))
    r = analyze(dict(posting_id='X', job_description_raw='창고 물품 입출고'))
    assert posting_ai.classify(r['clauses'], '물류 사무원') is None
