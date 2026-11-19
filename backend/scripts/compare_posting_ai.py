"""BACKLOG B21: 공고 표본 300건으로 규칙 / Nova Lite / Claude Haiku 4.5 비교 (P2 6절, DESIGN ⑥ 검수 방법).
사용법: AWS_PROFILE=tae python scripts/compare_posting_ai.py [--limit 5]   (Bedrock 비용이 든다)
- 표본: 상위 10개 직무 210건 + 나머지 90건, seed 고정. 처음 뽑을 때 공고 ID를 docs/reports/공고분석-AI비교/sample_ids.json에 저장하고 이후 그대로 쓴다.
- 보통 실행: 공고 전체 칸으로 규칙 처리 → 모델마다 구절 종류·표현 → 팀원 검수표(review.csv)
- 칸 가린 실행: 필수·우대 칸이 따로 있는 공고는 그 칸을 빼고 본문만으로 규칙·모델을 돌려, 원래 칸과 자동 비교
- 모델 응답은 data/derived/b21/에 저장해 두고, 다시 돌리면 저장본을 쓴다(돈이 다시 들지 않음).
"""
import argparse
import csv
import json
import random
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from careerlens.paths import CAREERLENS_DB, DATA
from careerlens import posting_ai as P
from careerlens import posting_analysis as A
from careerlens.cards import D

# 가격: AWS 공개 가격표(ap-northeast-2, 100만 토큰당 입력·출력 USD, 11/19 확인)
MODELS = {'nova': ('Nova Lite', 'apac.amazon.nova-lite-v1:0', 0.071, 0.284),
          'haiku': ('Claude Haiku 4.5', 'global.anthropic.claude-haiku-4-5-20251001-v1:0', 1.0, 5.0)}
SEED = 20261119
REPORT = Path(__file__).resolve().parents[2] / 'docs' / 'reports' / '공고분석-AI비교'
CACHE = DATA / 'derived' / 'b21'
SAME = {'경력': '조건'}   # 규칙의 '경력'은 AI 종류에 없어 조건으로 맞춰 비교


def load():
    con = sqlite3.connect(f'file:{CAREERLENS_DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    rows = {r['posting_id']: dict(r) for r in con.execute('select * from job_postings where is_near_duplicate=0')}
    lics = defaultdict(list)
    for pid, lid, name, level in con.execute('select posting_id, license_id, license_name, requirement_level from posting_licenses'):
        lics[pid].append((lid, name, level))
    names = dict(con.execute('select occupation_id, occupation_name from occupations'))
    return rows, lics, names


def sample(rows):
    f = REPORT / 'sample_ids.json'
    if f.exists():
        return json.loads(f.read_text())
    top = {o for o, _ in Counter(r['occupation_id'] for r in rows.values()).most_common(10)}
    ids = sorted(rows)
    rng = random.Random(SEED)
    pick = rng.sample([i for i in ids if rows[i]['occupation_id'] in top], 210) + rng.sample([i for i in ids if rows[i]['occupation_id'] not in top], 90)
    REPORT.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(sorted(pick), indent=0))
    return sorted(pick)


def blind(row):
    """필수·우대 칸 표시를 지운 공고: 제목과 본문만."""
    return {k: row[k] for k in ('posting_id', 'occupation_id', 'career', 'title', 'job_description_raw')}


def truth(text, row):
    """원래 필수·우대 칸으로 정한 정답 종류. 전처리가 본문 대부분(60% 이상)을 한 칸에 넣은 공고는 칸이 나뉜 게 아니라서 그 칸은 안 씀."""
    n, body = A._norm(text), len(A._norm(row['job_description_raw'] or ''))
    if len(n) < 4:
        return None
    field = {f: A._norm(row[f] or '') for f in ('required_text', 'preferred_text')}
    field = {f: v if len(v) < 0.6 * body else '' for f, v in field.items()}
    req, pref = n in field['required_text'], n in field['preferred_text']
    if req != pref:
        return '필수' if req else '우대'
    if not req and n in A._norm(row['duty_text'] or ''):
        return '업무'
    return None


def run_model(key, mode, jobs):
    """jobs: [(posting_id, clauses, job_name)] → {posting_id: {ai, usage, sec}}. 저장본이 있으면 그것을 쓴다."""
    name, model_id, *_ = MODELS[key]
    f = CACHE / f'{key}_{mode}.jsonl'
    done = {}
    if f.exists():
        for line in f.read_text().splitlines():
            x = json.loads(line)
            done[x['posting_id']] = x
    todo = [j for j in jobs if j[0] not in done]

    def one(j):
        pid, clauses, job = j
        usage, t = {}, time.time()
        ai = P.classify(clauses, job, model=model_id, usage=usage)
        if ai:   # json 키는 문자열이 되므로 clause_id를 문자열로
            ai = dict(ai, clauses={str(k): v for k, v in ai['clauses'].items()})
        return dict(posting_id=pid, ai=ai, usage=usage, sec=round(time.time() - t, 2))
    if todo:
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f'{name} {mode}: {len(todo)}건 호출', flush=True)
        with ThreadPoolExecutor(4) as ex, open(f, 'a') as out:
            for x in ex.map(one, todo):
                done[x['posting_id']] = x
                out.write(json.dumps(x, ensure_ascii=False) + '\n')
                out.flush()
    for x in done.values():   # 다시 int 키로
        if x['ai']:
            x['ai'] = dict(x['ai'], clauses={int(k): v for k, v in x['ai']['clauses'].items()})
    return done


def kw_names(ks):
    return ', '.join(D[k][1] for k in sorted(ks))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, help='표본 앞쪽 n건만(토큰 실측용)')
    a = ap.parse_args()
    rows, lics, names = load()
    ids = sample(rows)[:a.limit]
    rule = {i: A.analyze(rows[i], lics[i]) for i in ids}
    bl_ids = [i for i in ids if (rows[i]['required_text'] or rows[i]['preferred_text']) and rows[i]['job_description_raw']]
    rule_b = {i: A.analyze(blind(rows[i])) for i in bl_ids}
    job = {i: names.get(rows[i]['occupation_id'], '') for i in ids}
    res, res_b = {}, {}
    for key in MODELS:
        res[key] = run_model(key, 'full', [(i, rule[i]['clauses'], job[i]) for i in ids])
        res_b[key] = run_model(key, 'blind', [(i, rule_b[i]['clauses'], job[i]) for i in bl_ids])

    summary = dict(sample=len(ids), blind_sample=len(bl_ids), systems={})
    # ---- 칸 가린 실행: 원래 필수·우대 칸과 자동 비교 ----
    def types_of(sys_key, i):
        if sys_key == 'rule':
            return {c['clause_id']: SAME.get(c['type'], c['type']) for c in rule_b[i]['clauses'] if c['type']}
        ai = res_b[sys_key][i]['ai']
        return {k: v['type'] for k, v in ai['clauses'].items()} if ai else {}
    for s in ['rule', *MODELS]:
        pairs = []
        for i in bl_ids:
            got = types_of(s, i)
            for c in rule_b[i]['clauses']:
                t = truth(c['text'], rows[i]) if c['type'] else None
                if t:
                    pairs.append((t, got.get(c['clause_id'], '없음')))
        rp = [(t, g) for t, g in pairs if t in ('필수', '우대')]
        pred_req = [(t, g) for t, g in pairs if g == '필수']
        summary['systems'].setdefault(s, {}).update(
            labeled_clauses=len(pairs), req_pref_accuracy=round(sum(t == g for t, g in rp) / max(len(rp), 1), 3),
            req_precision=round(sum(t == '필수' for t, _ in pred_req) / max(len(pred_req), 1), 3),
            req_recall=round(sum(g == '필수' for t, g in pairs if t == '필수') / max(sum(t == '필수' for t, _ in pairs), 1), 3))
    # ---- 보통 실행: 실패·인용·비용·보완 효과 ----
    low = [i for i in ids if rule[i]['confidence'] == 'low' and len(rows[i]['job_description_raw'] or '') >= 80]
    summary['low_targets'] = len(low)
    summary['systems']['rule'].update(low_after=dict(Counter(rule[i]['confidence'] for i in low)))
    for key, (name, _, pin, pout) in MODELS.items():
        allx = list(res[key].values()) + list(res_b[key].values())
        tin = sum(x['usage'].get('inputTokens', 0) for x in allx)
        tout = sum(x['usage'].get('outputTokens', 0) for x in allx)
        ok = [i for i in ids if res[key][i]['ai']]
        after = {i: P.supplement(rule[i], res[key][i]['ai']) for i in low if res[key][i]['ai']}
        summary['systems'][key].update(
            name=name, failed=len(ids) - len(ok) + sum(not res_b[key][i]['ai'] for i in bl_ids), calls=len(allx),
            bad_quotes=sum(x['ai']['bad_quotes'] for x in allx if x['ai']),
            input_tokens=tin, output_tokens=tout, cost_usd=round(tin / 1e6 * pin + tout / 1e6 * pout, 4),
            cost_per_posting=round((tin / 1e6 * pin + tout / 1e6 * pout) / max(len(allx), 1), 5),
            sec_per_posting=round(sum(x['sec'] for x in allx) / max(len(allx), 1), 2),
            low_after=dict(Counter(r['confidence'] for r in after.values())),
            low_added_kw=round(sum(sum(x['method'] == 'ai' for x in r['requirements']) for r in after.values()) / max(len(after), 1), 2),
            type_agree_with_rule=round(sum(SAME.get(c['type'], c['type']) == res[key][i]['ai']['clauses'].get(c['clause_id'], {}).get('type')
                                           for i in ok for c in rule[i]['clauses'] if c['type'])
                                       / max(sum(1 for i in ok for c in rule[i]['clauses'] if c['type']), 1), 3))
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / f'summary{"_limit" if a.limit else ""}.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if a.limit:
        return
    # ---- 팀원 검수표: 결과가 다른 구절 전부 + 같은 구절 50개 ----
    head = ['공고ID', '직무', '구절번호', '구절', '규칙 종류', *[f'{MODELS[k][0]} 종류' for k in MODELS],
            '규칙 역량', *[f'{MODELS[k][0]} 역량' for k in MODELS], '결과가 다름', '정답 종류(필수/우대/업무/조건/정책우대/기타)', '역량 맞음(맞음/틀림)', '빠진 역량', '메모']
    diff, same = [], []
    for i in ids:
        for c in rule[i]['clauses']:
            if not c['type']:
                continue
            ts = [SAME.get(c['type'], c['type'])]
            ks = [set(k for k in c['kw'] if D[k][0] not in ('C4', 'C5'))]
            for key in MODELS:
                a_ = (res[key][i]['ai'] or {'clauses': {}})['clauses'].get(c['clause_id'])
                ts.append(a_['type'] if a_ else '없음')
                ks.append(set(k for ph in (a_ or {}).get('phrases', []) for k in ph['kw'] if D[k][0] not in ('C4', 'C5')) | ks[0])
            d = len(set(ts)) > 1 or len({frozenset(k) for k in ks}) > 1
            row = [i, job[i], c['clause_id'], c['text'], *ts, *[kw_names(k) for k in ks], '다름' if d else '같음', '', '', '', '']
            (diff if d else same).append(row)
    rng = random.Random(SEED)
    rng.shuffle(same)
    pick = sorted(rng.sample(range(len(diff)), min(150, len(diff))))   # 다른 구절이 많아 검수용은 150개만(전체는 review_all.csv)
    for name, rows_ in (('review.csv', [diff[k] for k in pick] + same[:50]), ('review_all.csv', diff)):
        with open(REPORT / name, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(head)
            w.writerows(rows_)
    print(f'검수표: 다른 구절 {len(diff)}개 중 {len(pick)}개 + 같은 구절 50개 → {REPORT / "review.csv"} (다른 구절 전체는 review_all.csv)')


if __name__ == '__main__':
    main()
