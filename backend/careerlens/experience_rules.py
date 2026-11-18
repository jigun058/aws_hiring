"""경험 규칙 보정. 팀원이 한눈에 보도록 바꾼 규칙을 이 파일에만 모은다.

경험 규칙은 엔진 knowledge.EXPERIENCE_RULES와 careerlens.db experience_keyword_mapping(expert 규칙)
두 곳에 있는데 내용이 같다(tests/test_experience_rules.py가 확인). 그래서 보정한 목록 RULES 하나를
엔진(apply_to)과 경험 카드(card_rules) 양쪽에 쓴다. 원본 파일과 DB는 고치지 않는다.

근거: 시뮬레이션 결과 문서 '발견한 문제' 2·3번, P3 7.3절(EXB01~05). DESIGN.md ③.
정규식의 세부(어떤 활용형까지 잡을지)는 구현 담당 [기본값]이다.
"""
import csv
import re

from careerlens import paths  # noqa: F401  vendor 경로 설정
from careerlens.paths import DICT_CSV
import knowledge as K

# 기존 규칙에서 바꾼 것: 규칙 ID → 바꾼 필드
CHANGED = {
    # 2번: "부트캠프"가 "캠프"로 잡혀 행사 진행이 붙음 → 부트캠프 제외
    'EX024': dict(all_of=[r'행사|축제|이벤트|박람회|(?<!부트)(?<!부트 )캠프']),
    # 2번: "보고서 작성 시간을 줄였다"가 발표·PPT로 잡힘 → 작성·발표한 행동이 함께 있을 때만
    'EX027': dict(all_of=[r'보고서|발표|PPT|프레젠테이션',
                          r'작성(?:했|하였|해|하고)|발표(?:했|하였|해|하고)|썼|만들|맡']),
    # 3번: "거래처 전화 응대"만으로 영업(직접)이 붙음 → 거래처는 판매·제안 행동이 있을 때만
    'EX036': dict(all_of=[r'영업|거래처|판촉|세일즈',
                          r'영업|판촉|세일즈|판매|제안|수주|계약|발굴']),
}

# P3 7.3절 신규 규칙. 과대평가를 막으려고 모두 전이(transferable) 연결.
ADDED = [
    dict(id='EXB01', all_of=[r'부모|어머니|아버지|어르신|환자',   # P3 예시 "어머니 병원 동행"을 잡으려고 어머니·아버지 추가
                             r'돌보|돌봐|돌봤|돌봄|간병|병원 ?동행|식사 ?수발|투약'],
         activity='가족 돌봄', action='돌봄·간병', kw={'돌봄 서비스': 'transferable', '노인 돌봄 지식': 'transferable'},
         example='2년 동안 어머니 병원 동행과 투약을 챙겼다'),
    dict(id='EXB02', all_of=[r'아이|자녀', r'등하원|등원|하원|숙제|학습 ?지도|놀이'],
         activity='자녀 돌봄', action='학습 지도·놀이', kw={'아동 보육·지도': 'transferable'},
         example='아이 등하원과 숙제 지도를 했다'),
    dict(id='EXB03', all_of=[r'학부모회|자치회|반상회|바자회|동호회', r'총무|회계|임원|회장'],
         activity='지역 모임 운영', action='모임 운영·회계', kw={'조직 운영': 'transferable', '사무 행정': 'transferable'},
         example='학부모회에서 총무를 맡았다'),
    dict(id='EXB04', all_of=[r'회비|장부|가계부|회계', r'엑셀|Excel|스프레드시트'],   # P3: 엑셀을 썼다는 말이 있을 때만
         activity='회비·장부 정리', action='엑셀로 장부 정리', kw={'스프레드시트(엑셀)': 'transferable'},
         example='회비를 엑셀로 정리했다'),
    dict(id='EXB05', all_of=[r'반찬|도시락|급식|단체 ?식사', r'만들|준비|조리', r'봉사|행사|단체|\d+ ?인분'],
         activity='단체 조리', action='단체 식사 조리', kw={'조리': 'transferable'},
         example='복지관 봉사로 도시락 100인분을 만들었다'),
]

RULES = [dict(r, **CHANGED.get(r['id'], {})) for r in K.EXPERIENCE_RULES] + ADDED


def apply_to(matcher):
    """엔진(CareerMatcher)이 __init__에서 만든 규칙 목록을 보정본으로 바꾼다."""
    matcher.rules = [(r, [re.compile(p) for p in r['all_of']]) for r in RULES]


def card_rules():
    """경험 카드용: [(정규식 목록, kw_idx, 연결 방식)]. 시뮬레이션 07의 EXR과 같은 모양."""
    idx = {r['키워드']: int(r['kw_idx']) for r in csv.DictReader(open(DICT_CSV, encoding='utf-8-sig'))}
    return [([re.compile(p) for p in r['all_of']], idx[kw], mt) for r in RULES for kw, mt in r['kw'].items()]
