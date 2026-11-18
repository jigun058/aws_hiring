import re
import sqlite3

import pytest

from careerlens import experience_rules as X
from careerlens.paths import CAREERLENS_DB
import knowledge as K


def kws(sentence):
    out = {}
    for r in X.RULES:
        if all(re.search(p, sentence) for p in r['all_of']):
            out.update(r['kw'])
    return out


def test_db_rules_equal_engine_rules():
    """보정본 하나를 두 곳에 쓰는 전제. 팀원이 한쪽만 고치면 여기서 깨진다."""
    db = {}
    con = sqlite3.connect(f'file:{CAREERLENS_DB}?mode=ro', uri=True)
    for rid, pat, kw, mt in con.execute("select rule_id, expression_pattern, keyword, match_type "
                                        "from experience_keyword_mapping where match_type != 'synonym'"):
        db.setdefault(rid, [pat, {}])[1][kw] = mt
    assert db == {r['id']: [' AND '.join(r['all_of']), r['kw']] for r in K.EXPERIENCE_RULES}


def _example_param(r):
    # EX034 원본 규칙은 '돌보'만 있어 예시의 '돌봤다'를 못 잡는다. 로직팀 판단 대기(TEAM.md T19)
    marks = [pytest.mark.xfail(strict=True, reason='원본 규칙 문제')] if r['id'] == 'EX034' else []
    return pytest.param(r, id=r['id'], marks=marks)


@pytest.mark.parametrize('rule', [_example_param(r) for r in X.RULES])
def test_rule_matches_own_example(rule):
    assert all(re.search(p, rule['example']) for p in rule['all_of'])


@pytest.mark.parametrize('sentence,absent', [
    ('부트캠프에서 Node.js와 SQL을 배웠습니다.', '행사 진행'),
    ('그 결과 주간 보고서 작성 시간을 2시간에서 30분으로 줄였습니다.', '발표'),
    ('거래처 전화 응대도 담당했습니다.', '영업'),
    ('부모님을 모시고 살았습니다.', '돌봄 서비스'),
    ('아이를 키웠습니다.', '아동 보육·지도'),
    ('학부모회 활동을 했습니다.', '조직 운영'),
    ('학부모회 회비를 정리했습니다.', '스프레드시트(엑셀)'),
    # '집에서 반찬을 만들었다'는 원본 EX028(반찬 → 조리 직접)이 잡는다. P3 7.3과 어긋남, TEAM.md T19
])
def test_fixed_false_positives(sentence, absent):
    assert absent not in kws(sentence)


@pytest.mark.parametrize('sentence,present', [
    ('여름 캠프를 기획해 운영했습니다.', '행사 진행'),
    ('분석 결과를 보고서로 작성해 발표했습니다.', '발표'),
    ('거래처에 신제품을 제안해 계약했습니다.', '영업'),
    ('아이 학교 학부모회에서 총무를 맡아 회비를 엑셀로 정리했습니다.', '조직 운영'),
    ('아이 학교 학부모회에서 총무를 맡아 회비를 엑셀로 정리했습니다.', '스프레드시트(엑셀)'),
])
def test_still_matches(sentence, present):
    assert present in kws(sentence)


def test_card_rules_cover_all_rules():
    assert len(X.card_rules()) == sum(len(r['kw']) for r in X.RULES)


def test_p3_example7_family_care():
    """P3 9절 예시 7 문장이 EXB01에 걸려야 한다(표의 표현만으로는 안 걸려서 넓힘)."""
    k = kws('시어머니가 편찮으셔서 2년 동안 병원 같이 다니고 약 챙겨 드렸어요.')
    assert k['돌봄 서비스'] == 'transferable' and k['노인 돌봄 지식'] == 'transferable'
