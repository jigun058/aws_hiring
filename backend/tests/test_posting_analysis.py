"""P2 공고 분석 규칙 처리 시험. 예시는 P2 명세 5절(1~5번, 6번은 AI라 제외)."""
import random
import re
import sqlite3

import pytest

from careerlens import posting_analysis as A
from careerlens.paths import CAREERLENS_DB


def run(text, **kw):
    return A.analyze(dict(job_description_raw=text, **kw))


def types(r):
    return [(c['text'], c['type']) for c in r['clauses']]


def test_example1_short_care_posting():
    r = run('4등급 남자어르신  점심식사차려드리기 말벗  시간: 11:00~14:00(월~금)  시급 : 13,000원',
            license_field_raw='요양보호사', occupation_id='OCC0410')
    assert {c['type'] for c in r['conditions']} == {'근무시간', '급여'}
    assert '돌봄 서비스' in {x['keyword'] for x in r['requirements']}
    assert r['licenses'] == [dict(license_id='LIC0278', name='요양보호사', type='필수', source='license_field_raw', legal_required=True)]


def test_example2_available_trap():
    r = run('- 급여: 1,548,000원 - 즉시 출근 가능자')
    assert [c['type'] for c in r['conditions']] == ['급여', '출근일']
    assert r['requirements'] == []


def test_example3_skill_available():
    r = run('5톤 운전가능자★ 동종업계 경력자')
    assert [(x['keyword'], x['type']) for x in r['requirements']] == [('차량 운전', '필수')]
    assert r['career']['quote'] == '동종업계 경력자'


def test_example4_preferred_beats_required_and_unmapped():
    r = run('미쯔비시, 포인트캠, 하이캠 가능자 우대')
    assert r['unmapped_requirements'] == [dict(quote='미쯔비시, 포인트캠, 하이캠 가능자 우대', type='우대')]


def test_example5_policy_preference():
    r = run('경증장애 복지카드소지자 우대')
    assert r['conditions'] == [dict(type='정책 우대', quote='경증장애 복지카드소지자 우대')]
    assert r['requirements'] == []


def test_attitude_and_physical_are_not_scored():
    r = run('책임감 있으신 분  야간 근무 가능자')
    assert r['requirements'] == []
    assert [x['keyword'] for x in r['display_only']] == ['책임감']
    assert [x['keyword'] for x in r['filters']] == ['교대·야간 근무 적응']


def test_same_competency_keeps_strongest_type():
    """필수 > 업무 > 우대 (P2 F2-3)"""
    r = run('지게차 운전 업무  지게차 운전 가능자 우대')
    assert [(x['keyword'], x['type']) for x in r['requirements'] if x['keyword'] == '지게차 운전'] == [('지게차 운전', '업무')]


def test_section_header_sets_type():
    r = run('<우대사항>  엑셀 능숙자  [자격요건]  운전면허 소지자')
    assert [t for _, t in types(r) if t] == ['우대', '필수']


def test_header_section_ends_at_next_header():
    r = run('자격요건  운전면허 소지자  근무형태  고용형태 : 기간제 근로계약  이메일(a@b.kr)')
    assert [t for _, t in types(r) if t] == ['필수', '업무', '업무']
    assert r['unmapped_requirements'] == []


def test_number_leftovers_are_dropped():
    assert [c['text'] for c in A.split_clauses(dict(duty_text='1 / 2 / 지게차 운전'))] == ['지게차 운전']


def test_confidence_levels():
    assert run('엑셀')['confidence'] == 'low'
    assert run('엑셀 문서 작성  재고 관리')['confidence'] == 'medium'


@pytest.fixture(scope='module')
def sample_rows():
    con = sqlite3.connect(f'file:{CAREERLENS_DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    ids = [r[0] for r in con.execute('select posting_id from job_postings where is_near_duplicate=0')]
    pick = random.Random(7).sample(ids, 300)
    q = ','.join('?' * len(pick))
    return [dict(r) for r in con.execute(f'select * from job_postings where posting_id in ({q})', pick)]


def test_split_loses_no_letters(sample_rows):
    """F2-1 검증 기준: 다시 이어 붙이면 내용 손실이 없음. 구분 기호·번호만 버리므로 글자(한글·영문)는 그대로여야 한다."""
    letters = lambda s: re.sub(r'[^가-힣A-Za-z]', '', s)
    for row in sample_rows:
        for col, _ in A.FIELDS:
            if row[col]:
                assert letters(''.join(A.split_field(row[col]))) == letters(row[col]), (row['posting_id'], col)


def test_quotes_are_in_source(sample_rows):
    """인용은 반드시 원문 조각이어야 한다(P2 1절)."""
    for row in sample_rows:
        whole = re.sub(r'\s+', ' ', ' '.join(str(row[c] or '') for c, _ in A.FIELDS))
        r = A.analyze(row)
        for x in r['requirements'] + r['display_only'] + r['filters'] + r['conditions'] + r['unmapped_requirements']:
            assert re.sub(r'\s+', ' ', x['quote']) in whole, (row['posting_id'], x['quote'])


def test_preference_field_values_are_policy_or_conditions():
    r = A.analyze(dict(job_description_raw='창고 정리', preference_field_raw='(준)고령자(50세이상) / 고용허가제 / 차량소지자'))
    assert [c['type'] for c in r['conditions']] == ['정책 우대', '정책 우대', '자차']
    assert r['unmapped_requirements'] == []
