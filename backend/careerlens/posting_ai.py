"""⑥ 공고 AI 보완 — P2 F2-5. LLM은 구절마다 종류와 요구 표현(원문 인용)만 낸다. 역량 번호는 코드가 P1 사전으로 붙이고,
원문에 없는 인용은 버린다. 규칙 결과와 종류가 다르면 규칙 종류를 남긴다.
"""
from careerlens import llm
from careerlens.cards import D
from careerlens.posting_analysis import _norm, confidence_of
import p1_engine as E

TYPES = ('필수', '우대', '업무', '조건', '정책우대', '기타')
SYSTEM = ('아래 구절은 한 채용공고를 나눈 것이다. 각 구절이 지원자에게 필수로 요구하는 것(필수) / 있으면 좋은 것(우대) / 하게 될 업무(업무) / '
          '근무 조건(조건) / 정책 우대(정책우대) / 기타 중 무엇인지 고르고, 그 구절이 요구하는 능력·지식·도구·자격 표현을 원문 그대로 인용하라. '
          '근무시간, 급여, 출근 가능일, 거주지, 자차, 서류, 학력, 나이, 경력 연수·신입 여부는 조건이다. 장애인·보훈·고령자 우대는 정책우대다. '
          '"우대사항", "자격요건" 같은 머리말은 기타로 두고, 뒤 구절의 종류를 정할 때 참고한다. '
          '원문에 없는 말을 만들지 마라. 확실하지 않으면 기타로 둬라. '
          '출력 형식: {"clauses": [{"clause_id": 3, "type": "필수", "phrases": [{"text": "5톤 운전", "quote": "5톤 운전가능자"}]}]}. '
          '모든 구절을 한 번씩 넣는다. phrases의 text는 요구 표현, quote는 그 표현이 든 원문 그대로의 부분이다.')


def classify(clauses, job_name, model=None, usage=None):
    """clauses: analyze() 결과의 clauses. → {'clauses': {clause_id: {type, phrases[{text, quote, kw}]}}, 'bad_quotes': 버린 인용 수}
    LLM 실패·형식 오류면 None(호출한 쪽은 규칙 결과만 쓴다)."""
    rule_kws = sorted({D[k][1] for c in clauses for k in (c.get('kw') or [])})
    lines = '\n'.join(f"[{c['clause_id']}] {c['text']}" for c in clauses)
    r = llm.ask_json(SYSTEM, f'직무: {job_name}\n규칙이 이미 찾은 역량: {", ".join(rule_kws) or "없음"}\n구절:\n{lines}',
                     max_tokens=3000, model=model, usage=usage)
    if not isinstance(r, dict) or not isinstance(r.get('clauses'), list):
        return None
    text = {c['clause_id']: c['text'] for c in clauses}
    out, bad = {}, 0
    for x in r['clauses']:
        cid = x.get('clause_id') if isinstance(x, dict) else None
        if cid not in text:
            continue
        phrases = []
        for ph in x.get('phrases') or []:
            q, t = (str(ph.get('quote') or ''), str(ph.get('text') or '')) if isinstance(ph, dict) else ('', '')
            if not _norm(q) or _norm(q) not in _norm(text[cid]):   # 원문에 없는 인용은 버린다
                bad += 1
                continue
            phrases.append(dict(text=t, quote=q, kw=sorted(E.map_ko(t)['kw'] or E.map_ko(q)['kw'])))
        out[cid] = dict(type=x.get('type') if x.get('type') in TYPES else '기타', phrases=phrases)
    return dict(clauses=out, bad_quotes=bad)


def supplement(result, ai):
    """규칙 결과(analyze)에 AI 역량을 더한 새 결과. 구절 종류는 규칙 것이 필수·업무·우대면 그대로, 아니면 AI 종류.
    점수용 역량(C4·C5 제외)만 더한다. 사전에 없는 필수·우대 표현은 unmapped_requirements로."""
    reqs = {r['kw_idx']: r for r in result['requirements']}
    unmapped = list(result['unmapped_requirements'])
    for c in result['clauses']:
        a = ai['clauses'].get(c['clause_id'])
        if not a:
            continue
        t = c['type'] if c['type'] in ('필수', '업무', '우대') else a['type'] if a['type'] in ('필수', '업무', '우대') else None
        if not t:
            continue
        for ph in a['phrases']:
            for k in ph['kw']:
                cat, name = D[k]
                if cat not in ('C4', 'C5') and k not in reqs:   # 태도(C4)·신체(C5)는 점수에 안 씀(analyze와 같음)
                    reqs[k] = dict(kw_idx=k, keyword=name, category=cat, quote=ph['quote'], type=t, source=c['source'],
                                   clause_id=c['clause_id'], method='ai', status='confirmed')
            if not ph['kw'] and t in ('필수', '우대') and all(u['quote'] != ph['quote'] for u in unmapped):
                unmapped.append(dict(quote=ph['quote'], type=t, method='ai'))
    rank = {'필수': 0, '업무': 1, '우대': 2}
    requirements = sorted(reqs.values(), key=lambda r: (rank[r['type']], r['clause_id']))
    return dict(result, requirements=requirements, unmapped_requirements=unmapped, ai_used=True,
                confidence=confidence_of(requirements, result['licenses']))
