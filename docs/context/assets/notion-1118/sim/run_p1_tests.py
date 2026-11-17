"""P1 역량 매핑 참조 구현 자동 시험: 정답 50개(P1_gold_mapping_50.csv) + 검증 30개(P1_validation_30.csv).
사용법: python run_p1_tests.py [--gold 경로] [--val 경로]
"""
import sys, os, csv, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paths import DATA   # careerlens.db·courses.json 위치를 환경 변수로 넘김
import p1_engine as E

def parse(s):
    s = (s or '').strip()
    if not s or s.startswith('('): return set()
    return {int(x.split(':')[0]) for x in s.replace(' ', '').split(';') if x}

def run(path, id_col, text_col, exp_col):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    ok, bad = 0, []
    for r in rows:
        got = set(E.map_sentence(r[text_col], r['트랙'])['kw'])
        exp = parse(r[exp_col])
        if got == exp: ok += 1
        else: bad.append((r[id_col], r['트랙'], sorted(exp), sorted(got)))
    return ok, len(rows), bad

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--gold', default=os.path.join(DATA, 'P1_gold_mapping_50.csv'))
    ap.add_argument('--val', default=os.path.join(DATA, 'P1_validation_30.csv'))
    a = ap.parse_args()
    for name, args in [('정답 50', (a.gold, 'gold_id', '요구 문구', '기대 키워드(idx:이름)')),
                       ('검증 30', (a.val, 'val_id', '문장(원문)', '기대 키워드 idx(;구분)'))]:
        ok, n, bad = run(*args)
        print(f'[{name}] {ok}/{n} 일치')
        for b in bad: print(f'   불일치 {b[0]} ({b[1]}) 기대 {b[2]} / 결과 {b[3]}')
