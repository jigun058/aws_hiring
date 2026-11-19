"""단계별 API를 첫 화면부터 끝까지 한 번 관통한다(박물류·최경리). 엔진 입력과 공고 분석 결과 파일이 있어야 한다."""
import pytest
from fastapi.testclient import TestClient

PARK = [dict(title='물류센터 근무', type='job', text='물류센터에서 10년 동안 지게차로 상하차와 운반을 했습니다. 입고 검수와 재고 관리도 맡았습니다.'),
        dict(title='자격증', type='certificate', text='지게차운전기능사 자격증과 1종 보통 운전면허를 보유하고 있습니다.')]
CARE = [dict(title='어머니 돌봄', type='family_care', text='2년 동안 어머니 병원 동행과 투약을 챙겼습니다.')]


@pytest.fixture(scope='module')
def client():
    from careerlens.api import app
    return TestClient(app)


def test_meta(client):
    m = client.get('/api/meta').json()
    assert (m['occupations'], m['postings'], m['data_date']) == (810, 38185, '2026-11-12')
    assert m['sido'] == sorted(m['sigungu']) and '송파구' in m['sigungu']['서울']


def test_flow_park(client):
    draft = client.post('/api/cards/draft', json=dict(cards=PARK)).json()['cards']
    assert {'지게차 운전', '재고 관리'} <= {c['keyword'] for c in draft[0]['competencies']}

    rec = client.post('/api/recommend', json=dict(cards=draft)).json()
    job = rec['jobs'][0]
    assert (job['name'], job['score']) == ('지게차 운전원', 64.99)   # tests/test_recommend.py와 같은 숫자
    assert sum(p['max'] for p in job['parts'].values()) == 100
    assert any(e['card'] == '물류센터 근무' for e in job['evidence'])

    ps = client.post('/api/postings', json=dict(cards=draft, occupation_id=job['occupation_id'])).json()
    assert ps['total'] > 6 and len(ps['postings']) == 6
    first = ps['postings'][0]
    assert any(x['has'] for x in first['required'] + first['tasks'])
    assert [p['thin'] for p in ps['postings']] == sorted(p['thin'] for p in ps['postings'])   # 정보 부족 공고는 뒤로

    gy = client.post('/api/postings', json=dict(cards=draft, occupation_id=job['occupation_id'], filters=dict(sido='서울'))).json()
    assert all(p['sido'] == '서울' for p in gy['postings'])

    co = client.post('/api/courses', json=dict(cards=draft, occupation_id=job['occupation_id'], posting_id=first['posting_id'])).json()
    assert all(g['kind'] in ('license', 'competency') for g in co['gaps'])


def test_care_job_needs_license(client):
    """요양보호사 자격이 없는 사람에게 요양보호사 공고는 '자격 취득 후 지원'이고, ⑤에서 자격 과정이 나온다."""
    ps = client.post('/api/postings', json=dict(cards=CARE, occupation_id='OCC0410')).json()
    assert ps['postings'] and all('요양보호사' in p['needs_license'] for p in ps['postings'])
    co = client.post('/api/courses', json=dict(cards=CARE, occupation_id='OCC0410')).json()
    lic = [g for g in co['gaps'] if g['kind'] == 'license']
    assert lic and lic[0]['courses']


def test_unknown_occupation_is_404(client):
    assert client.post('/api/postings', json=dict(cards=PARK, occupation_id='NOPE')).status_code == 404


def test_analyze_posting(client):
    r = client.post('/api/analyze-posting', json=dict(text='- 급여: 1,548,000원 - 즉시 출근 가능자  5톤 운전가능자')).json()
    assert [(x['keyword'], x['type']) for x in r['requirements']] == [('차량 운전', '필수')]


def test_removed_competency_leaves_score(client):
    """화면에서 지운 역량은 엔진이 카드 글에서 다시 찾아도 점수·공고 비교에서 빠진다."""
    card = PARK[0]
    full = client.post('/api/recommend', json=dict(cards=[card])).json()
    assert '지게차 운전' in full['user_keywords']
    cut = client.post('/api/recommend', json=dict(cards=[dict(card, removed=[56])])).json()   # 56 = 지게차 운전
    assert '지게차 운전' not in cut['user_keywords']
    assert all(e['keyword'] != '지게차 운전' for j in cut['jobs'] for e in j['evidence'])
    assert [j['score'] for j in cut['jobs']] != [j['score'] for j in full['jobs']]
    both = client.post('/api/recommend', json=dict(cards=[dict(card, removed=[56]), PARK[1]])).json()   # 다른 카드엔 남아 있음
    assert both['user_keywords'] == client.post('/api/recommend', json=dict(cards=[card, PARK[1]])).json()['user_keywords']
