"""P1 역량 매핑 참조 구현 자동 시험: 정답 50개 + 독립 검증 30개.
규칙서의 결과(정답 50/50, 검증 28/30)를 그대로 고정한다.
VA09·VB09는 규칙서의 미해결 건이라 실패가 정상(xfail strict): 로직팀이 고쳐서 통과하면 이 시험이 알려 준다."""
import csv
from pathlib import Path

import pytest

import careerlens.paths  # noqa: F401  vendor 경로·DB 환경 변수 설정
import p1_engine as E

FIX = Path(__file__).parent / 'fixtures'
KNOWN_FAIL = {'VA09', 'VB09'}


def parse(s):
    s = (s or '').strip()
    if not s or s.startswith('('):
        return set()
    return {int(x.split(':')[0]) for x in s.replace(' ', '').split(';') if x}


def rows(name, id_col, text_col, exp_col):
    out = []
    for r in csv.DictReader(open(FIX / name, encoding='utf-8-sig')):
        marks = [pytest.mark.xfail(strict=True, reason='규칙서 미해결 건')] if r[id_col] in KNOWN_FAIL else []
        out.append(pytest.param(r[text_col], r['트랙'], parse(r[exp_col]), id=r[id_col], marks=marks))
    return out


@pytest.mark.parametrize('text,track,expected', rows('P1_gold_mapping_50.csv', 'gold_id', '요구 문구', '기대 키워드(idx:이름)')
                         + rows('P1_validation_30.csv', 'val_id', '문장(원문)', '기대 키워드 idx(;구분)'))
def test_map_sentence(text, track, expected):
    assert set(E.map_sentence(text, track)['kw']) == expected
