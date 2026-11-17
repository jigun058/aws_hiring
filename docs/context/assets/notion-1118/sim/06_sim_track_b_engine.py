import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import sys, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,ENGINE_SRC)
from recommender import CareerMatcher
m=CareerMatcher()
P={
'B1 경력단절(마트·학부모회)':"15년 전에 마트에서 3년 동안 계산이랑 재고 관리를 했어요. 발주도 제가 넣었어요. 아이 학교 학부모회에서 총무를 맡아 회비를 엑셀로 정리했습니다.",
'B2 중장년(물류 지게차)':"물류센터에서 10년 동안 지게차로 상하차와 운반을 했습니다. 입고 검수와 재고 관리도 맡았습니다. 지게차운전기능사 자격증과 1종 보통 운전면허를 보유하고 있습니다.",
'B3 경력단절(경리 사무)':"회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 급여와 회계 장부를 정리하고 세금계산서를 발행했습니다. 거래처 전화 응대도 담당했습니다. 컴퓨터활용능력 2급 자격증을 취득했습니다.",
}
for name,t in P.items():
    r=m.recommend(t)
    cv=r['experience_card']
    print('\n=====',name,'| 저신뢰' if r['low_confidence'] else '')
    print(' 역량:',cv['competencies'][:10],' 자격:',cv['licenses'])
    tot=0
    for rec in r['recommendations']:
        ps=m.postings_for(rec['occupation_id'],set(m.extract(t)['keywords']),n=6)
        tot+=len(ps)
        print(f" ▶ {rec['occupation_name']} ({rec['score']}) 열린공고 {rec['market_open_postings']} | 맞는역량 {rec['matched_competencies'][:4]} | 주의 {rec['cautions'][:1]}")
        for p in ps[:6]: print(f"     - {p['company'][:14]} | {p['title'][:34]} | {p['region'][:12]} | {p['career']} | 겹침 {p['matched_keywords']}")
    print(' 더 보기 후보:',[x['occupation_name'] for x in r['more_candidates']])
