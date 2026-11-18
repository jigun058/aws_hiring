"""P2 규칙 처리(F2-1~F2-4)를 유사 중복을 뺀 공고 전체(38,185건)에 돌려 파일로 저장한다. AI 없음.
결과: data/derived/posting_analysis.jsonl (공고 1건 = 1줄, P2 1절 형식) + 요약 출력
사용법: python scripts/analyze_postings.py   (16코어에서 약 3분)
"""
import json
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from careerlens.paths import CAREERLENS_DB, DATA
from careerlens import posting_analysis as A

OUT = DATA / 'derived' / 'posting_analysis.jsonl'


def work(args):
    row, lics = args
    return A.analyze(row, lics)


def main():
    con = sqlite3.connect(f'file:{CAREERLENS_DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute('select * from job_postings where is_near_duplicate=0 order by posting_id')]
    lics = defaultdict(list)
    for pid, lid, name, level in con.execute('select posting_id, license_id, license_name, requirement_level from posting_licenses'):
        lics[pid].append((lid, name, level))
    t = time.time()
    with Pool() as pool:
        results = pool.map(work, [(r, lics[r['posting_id']]) for r in rows], chunksize=200)
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        for r in results:   # 구절 목록(clauses)은 검수용이라 빼서 파일을 줄인다. 필요하면 analyze()로 다시 계산
            f.write(json.dumps({k: v for k, v in r.items() if k != 'clauses'}, ensure_ascii=False) + '\n')
    body = {r['posting_id']: len(r['job_description_raw'] or '') for r in rows}
    conf = Counter(r['confidence'] for r in results)
    low80 = sum(r['confidence'] == 'low' and body[r['posting_id']] >= 80 for r in results)
    rtypes = Counter(x['type'] for r in results for x in r['requirements'])
    print(f'공고 {len(results)}건, {time.time() - t:.0f}초 → {OUT}')
    print('신뢰도', dict(conf), f'| low 비율 {conf["low"] / len(results):.1%} | low + 본문 80자 이상(AI 대상) {low80}건')
    print('역량 종류', dict(rtypes), '| 필수 역량이 있는 공고', sum(any(x['type'] == '필수' for x in r['requirements']) for r in results),
          '| 우대 역량이 있는 공고', sum(any(x['type'] == '우대' for x in r['requirements']) for r in results))
    print('사전에 없는 요구가 있는 공고', sum(bool(r['unmapped_requirements']) for r in results),
          '| 법정 필수 자격이 붙은 공고', sum(any(v['legal_required'] for v in r['licenses']) for r in results))


if __name__ == '__main__':
    main()
