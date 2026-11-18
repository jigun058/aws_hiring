"""Bedrock(Claude) 호출. LLM은 말만 다룬다: 경험 글 → 슬롯 인용, 질문 문장 다듬기, 답변 해석, 추천 이유 문장.
결과는 모두 코드가 검사하고(인용·금지 주제·숫자), 실패하면 None을 돌려 호출한 쪽이 규칙 대체를 쓴다.
"""
import json
import os
import re

MODEL = os.environ.get('CL_MODEL', 'global.anthropic.claude-sonnet-4-6')
REGION = os.environ.get('CL_REGION', 'ap-northeast-2')
_client = None

TYPES = ['job', 'internship', 'part_time', 'self_employed', 'project', 'education', 'community', 'family_care', 'certificate']
STYLE = ('사용자는 다시 일을 찾는 40~50대일 수 있다. 쉬운 말과 존댓말을 쓴다. '
         '경력 공백의 이유, 나이, 결혼·출산·육아, 건강, 가족 상황, 소득, 종교, 정치는 묻지도 말하지도 않는다.')


def client():
    global _client
    if _client is None:
        import boto3
        _client = boto3.Session(profile_name=os.environ.get('AWS_PROFILE')).client('bedrock-runtime', region_name=REGION)
    return _client


def converse(system, messages, max_tokens=1000, tools=None):
    """Bedrock Converse 한 번. 시험에서는 이 함수를 바꿔 끼운다."""
    kw = dict(modelId=MODEL, system=[{'text': system}], messages=messages,
              inferenceConfig={'temperature': 0, 'maxTokens': max_tokens})
    if tools:
        kw['toolConfig'] = {'tools': tools}
    return client().converse(**kw)


def _text(resp):
    return ''.join(c.get('text', '') for c in resp['output']['message']['content'])


def ask_json(system, user, max_tokens=1000):
    """JSON 하나를 돌려받는다. 형식 오류면 1회 재요청, 그래도 실패하면 None(P3 F3-1 예외 처리)."""
    msgs = [{'role': 'user', 'content': [{'text': user}]}]
    for _ in range(2):
        try:
            t = _text(converse(system + '\n반드시 JSON 하나만 출력한다. 설명이나 코드 블록 표시를 붙이지 않는다.', msgs, max_tokens))
            return json.loads(re.sub(r'^```(?:json)?|```$', '', t.strip()).strip())
        except json.JSONDecodeError:
            continue
        except Exception:   # 네트워크·권한·시간 초과: 규칙 대체로
            return None
    return None


def extract_experiences(text):
    """P3 F3-1 ②: 글 → 경험 단위로 나누고 슬롯별 {value, quote}. 인용 검사는 interview.fill이 한다."""
    system = ('너는 경험 정리 도우미다. 사용자가 쓴 글을 경험 단위로 나눈다. 경험 1개 = 같은 조직 + 같은 기간 + 같은 목적. '
              f'type은 {TYPES} 중 하나(직장=job, 아르바이트=part_time, 가게 운영=self_employed, 교육·수강=education, '
              '동호회·학부모회·봉사=community, 가족 돌봄=family_care, 자격증=certificate). '
              '슬롯: role(본인이 맡은 일), purpose(왜 했는지), actions(구체적으로 한 일, 여러 개), results(달라진 점·결과물, 여러 개), '
              'tools(쓴 프로그램·도구), period(기간), team_size(인원), challenges(어려웠던 점). '
              'quote는 사용자 글에서 그대로 복사한 조각이어야 한다. 글에 없는 내용은 만들지 말고 슬롯을 비운다. ' + STYLE)
    user = ('출력 형식: {"experiences":[{"activity":"짧은 활동명","type":"job","slots":[{"slot":"actions","value":"짧게 정리","quote":"원문 조각"}]}]}\n\n'
            f'사용자 글:\n{text}')
    r = ask_json(system, user, 1500)
    return r.get('experiences') if isinstance(r, dict) and isinstance(r.get('experiences'), list) else None


def phrase_question(q, card):
    """P3 F3-3: 기본 질문을 카드에 맞게 바꿔 말하기만. 금지 주제 검사는 interview.safe_question."""
    filled = {s: v['value'] for s, v in card['slots'].items() if isinstance(v, dict) and v.get('value')}
    system = ('너는 경험 인터뷰 질문을 다듬는다. 기본 질문이 묻는 것(슬롯)은 바꾸지 않고, 사용자의 활동에 맞게 2문장 이내로 바꿔 말한다. '
              '사용자가 말하지 않은 사실을 단정하지 않는다("~하셨군요" 금지, "~같은 일을 하셨나요?"는 가능). '
              '이미 답한 내용을 다시 묻지 않는다. 예시 선택지는 그 경험에서 흔한 답 2~3개. ' + STYLE)
    user = (f'활동: {card["activity"]} ({card["type"]})\n이미 들은 내용: {json.dumps(filled, ensure_ascii=False)}\n'
            f'기본 질문: {q["question"]}\n기본 선택지: {q["options"]}\n'
            '출력 형식: {"question":"...","options":["...","..."]}')
    r = ask_json(system, user, 300)
    if isinstance(r, dict) and isinstance(r.get('question'), str) and isinstance(r.get('options'), list):
        return dict(question=r['question'].strip(), options=[str(o) for o in r['options'][:3]])
    return None


def interpret_answer(slot, question, answer):
    """P3 F3-4: 답변 → {kind, slots[{slot, value, quote, is_estimate}]}. 인용 검사는 interview.apply_answer가 한다."""
    system = ('너는 인터뷰 답변을 정리한다. kind: content(내용 있음) / unknown(모름·기억 안 남) / skip(건너뛰기) / stop(그만) / other(다른 경험 이야기). '
              '한 답변에 여러 슬롯이 있으면 함께 채운다(role, purpose, actions, results, tools, period, team_size, challenges). '
              'quote는 답변에서 그대로 복사한 조각이다. 답변에 없는 내용은 만들지 않는다. "한 30% 정도"처럼 대략이면 is_estimate=true. ' + STYLE)
    user = (f'질문한 슬롯: {slot}\n질문: {question}\n답변: {answer}\n'
            '출력 형식: {"kind":"content","slots":[{"slot":"results","value":"짧게 정리","quote":"원문 조각","is_estimate":false}]}')
    r = ask_json(system, user, 600)
    if isinstance(r, dict) and r.get('kind') in ('content', 'unknown', 'skip', 'stop', 'other'):
        return dict(kind=r['kind'], slots=[x for x in r.get('slots') or [] if isinstance(x, dict)])
    return None


def explain_job(job, evidence):
    """추천 이유 2~3문장(DESIGN 5절). 엔진 결과와 카드 인용만 넘기고, 넘기지 않은 숫자가 나오면 버린다."""
    facts = dict(직무=job['name'], 점수=job['score'], 근거역량=[e['keyword'] for e in evidence if e.get('card')],
                 경험인용=[e['quote'] for e in evidence if e.get('quote')][:4], 부족역량=job.get('gaps', [])[:3],
                 주의=job.get('cautions', []))
    system = ('너는 직무 추천 이유를 설명한다. 주어진 사실만 써서 2~3문장으로 쓴다. 근거가 된 사용자 경험을 하나 이상 언급한다. '
              '"지원해 볼 만합니다"처럼 단정하지 않는다. 점수를 합격 가능성처럼 말하지 않는다. 주어진 것 말고 다른 역량이나 숫자를 쓰지 않는다. ' + STYLE)
    r = ask_json(system, f'사실: {json.dumps(facts, ensure_ascii=False)}\n출력 형식: {{"reason":"..."}}', 400)
    reason = r.get('reason') if isinstance(r, dict) else None
    if not isinstance(reason, str):
        return None
    allowed = set(re.findall(r'\d+(?:\.\d+)?', json.dumps(facts, ensure_ascii=False)))
    if set(re.findall(r'\d+(?:\.\d+)?', reason)) - allowed:   # 넘기지 않은 숫자 → 버림
        return None
    return reason.strip()
