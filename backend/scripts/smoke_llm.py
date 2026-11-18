"""실제 Bedrock으로 인터뷰·추천 이유·대화창을 한 번씩 돌려 본다(호출 약 6번, 1센트 안쪽).
사용법: AWS_PROFILE=tae ../.venv/bin/python scripts/smoke_llm.py
LLM이 실패해도 API는 규칙 대체로 답하므로, 출력의 by·error 값으로 실제 LLM이 답했는지 확인한다.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient

from careerlens import llm
from careerlens.api import app

c = TestClient(app)
show = lambda title, x: print(f'\n## {title}\n' + json.dumps(x, ensure_ascii=False, indent=1)[:1500])

t = time.time()
r = c.post('/api/interview/start', json=dict(text='15년 전에 마트에서 3년 동안 계산이랑 재고 관리를 했어요. 발주도 제가 넣었어요. '
                                                  '아이 학교 학부모회에서 총무를 맡아 회비를 엑셀로 정리했습니다.')).json()
show('경험 나누기 + 첫 질문', [dict(activity=x['card']['activity'], type=x['card']['type'], status=x['card']['slot_status'],
                               question=x['question'], competencies=[k['keyword'] for k in x['competencies']]) for x in r['cards']])
card = r['cards'][0]['card']
a = c.post('/api/interview/answer', json=dict(card=card, answer='매장 재고랑 발주를 맡았고, 월말 재고 차이를 거의 없앴어요.')).json()
show('답변 해석 + 다음 질문', dict(filled=a['filled'], status=a['card']['slot_status'], question=a['question'],
                              competencies=[(k['keyword'], k['level']) for k in a['competencies']]))
rec = c.post('/api/recommend', json=dict(cards=[a['card_in']] + [x['card_in'] for x in r['cards'][1:]])).json()
show('추천 TOP 3', [(j['name'], j['score']) for j in rec['jobs']])
show('추천 이유', c.post('/api/explain', json=dict(job=rec['jobs'][0])).json())
show('대화창', c.post('/api/chat', json=dict(messages=[dict(role='user', text='첫 번째 직무 공고 중에 서울에 있는 것만 알려 주세요.')],
                                             step='③ 직무 추천', cards=[a['card_in']], occupation_id=rec['jobs'][0]['occupation_id'])).json())
print(f'\n모델 {llm.MODEL}, {time.time() - t:.1f}초')
