"""직무 추천 보정 시험. 엔진 입력(scripts/build_engine_inputs.py)이 있어야 한다.
숫자는 11/19 실행값. 엔진·DB·규칙을 바꾸면 숫자가 달라지므로, 바뀐 이유를 확인한 뒤 고친다."""
import warnings

import pytest

from careerlens.cards import D, build_card
from careerlens.recommend import Recommender

warnings.filterwarnings('ignore')

PARK = [('물류센터 근무', 'job', '물류센터에서 10년 동안 지게차로 상하차와 운반을 했습니다. 입고 검수와 재고 관리도 맡았습니다.'),
        ('자격증', 'certificate', '지게차운전기능사 자격증과 1종 보통 운전면허를 보유하고 있습니다.')]
CHOI = [('회사 경리 업무', 'job', '회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 급여와 회계 장부를 정리하고 세금계산서를 발행했습니다. 거래처 전화 응대도 담당했습니다.'),
        ('자격증', 'certificate', '컴퓨터활용능력 2급 자격증을 취득했습니다.')]


@pytest.fixture(scope='module')
def R():
    return Recommender()


def run(R, persona, **kw):
    return R.recommend_cards([build_card(*c) for c in persona], **kw)


def scores(r):
    return [(j['occupation_name'], j['score']) for j in r['jobs']]


def test_reproduces_simulation_doc(R):
    """경험 종류 보정(B2)을 끄면 로직팀 시뮬레이션 문서의 박물류 결과와 같다(경험 규칙 보정은 박물류에 영향 없음)."""
    r = run(R, PARK, use_card_context=False)
    assert scores(r) == [('지게차 운전원', 60.5), ('창고 관리원', 58.73), ('하역 및 적재 단순 종사원', 57.6)]
    assert [p['company'] for p in r['jobs'][0]['postings']] == [
        '주식회사 오로라유통에프엔비', '삼우컴퍼니 주식회사', '신우밸브 주식회사', '주식회사 쌍진기업', '케이더블유피', '(주) 유비라이트']


def test_card_context_counts_job_experience(R):
    r = run(R, PARK)
    assert r['context'] == '인턴·직무 경력'
    assert scores(r) == [('지게차 운전원', 64.99), ('창고 관리원', 62.59), ('하역 및 적재 단순 종사원', 61.51)]
    assert scores(run(R, CHOI)) == [('경리 사무원', 59.56), ('회계 사무원', 57.5), ('영업 기획·관리·지원 사무원', 45.7)]


def test_card_levels_replace_evidence(R):
    """8번: 성과가 있는 카드(L3)는 같은 문장의 L2 카드보다 근거 점수가 높다."""
    base = run(R, CHOI)['jobs'][0]['score_breakdown']['experience']
    cards = [build_card(*c) for c in CHOI]
    for v in cards[0]['comps'].values():
        v['level'] = 'L3'
    assert R.recommend_cards(cards)['jobs'][0]['score_breakdown']['experience'] > base


@pytest.mark.parametrize('persona', [PARK, CHOI], ids=['박물류', '최경리'])
def test_no_duplicate_postings(R, persona):
    for j in run(R, persona)['jobs']:
        ps = j['postings']
        assert len(ps) == 6
        assert not {p['posting_id'] for p in ps} & R.near
        assert len({(p['company'], p['title']) for p in ps}) == len(ps)


def test_unpaid_user_gets_career_postings_last(R):
    """7번: 시뮬레이션에서 회계 사무원 공고 6건 중 5건이 경력직이던 최경리 조건."""
    oid = R.occ.loc[R.occ.occupation_name == '회계 사무원', 'occupation_id'].iloc[0]
    kws = set(R.extract(' '.join(c[2] for c in CHOI))['keywords'])
    paid = R.pick_postings(oid, kws, paid=True)
    unpaid = R.pick_postings(oid, kws, paid=False)
    assert any(p['career'] == '경력' for p in paid[:3])
    flags = [p['career'] == '경력' for p in unpaid]
    assert flags == sorted(flags)


def test_dictionary_names_match_engine(R):
    """8번은 역량 이름으로 엔진 결과와 카드를 맞춘다. 사전 이름이 엔진에 다 있어야 한다.
    예외: P1 최종판에서 트랙 A용으로 더한 IT 역량 4개(178~181)는 엔진·DB에 없다(트랙 B 영향 없음)."""
    p1_only = {'AI·머신러닝', '모바일 앱 개발', '데이터 엔지니어링', '소프트웨어 테스트'}
    assert {name for _, name in D.values()} - p1_only <= set(R.kw_list)
