"""⑥ 공고 역량 분석 — P2 명세 2절 규칙 처리(F2-1 ~ F2-4). AI 없음.
결과 형식은 P2 1절. 공고 DB 행이든 사용자가 붙여 넣은 글이든 같은 함수(analyze)를 쓴다.
"""
import re
import sqlite3

from careerlens import paths  # noqa: F401  vendor 경로 설정
from careerlens.cards import D
from careerlens.paths import CAREERLENS_DB
import p1_engine as E

# 칸 이름 → 결과의 source 이름. 순서가 중복 제거 우선순위다(필수·우대 칸이 먼저).
FIELDS = [('required_text', 'required_text'), ('preferred_text', 'preferred_text'),
          ('preference_field_raw', 'preference_field_raw'), ('license_field_raw', 'license_field_raw'),
          ('duty_text', 'duty_text'), ('title', 'title'), ('job_description_raw', 'job_description_raw'),
          ('computer_skills', 'computer_field')]

# ---------------- F2-1 구절 나누기 ----------------
# 나누는 자리 앞에 줄바꿈을 넣고 줄 단위로 자른다. 구분 기호(글머리표·번호)는 버린다.
_SPLITS = [
    (re.compile(r'\s{2,}'), '\n'),                                  # 원문 줄바꿈이 공백 여러 칸으로 들어와 있음
    (re.compile(r'(?<!\d)/|/(?!\d)'), '\n'),                         # 11/25 같은 날짜는 그대로
    (re.compile(r'(?:^|\s)·\s*'), '\n'),                             # 나열(청소·세탁)이 아닌 글머리 가운뎃점만
    (re.compile(r'[*★☆※○●■□▶▷◆◇•➤☞]'), '\n'),                      # 기호 글머리는 붙어 있어도("가능자★")
    (re.compile(r'(?:^|(?<=\s))-(?!\s*\d)'), '\n'),                  # '-'는 앞이 공백일 때만(09:00 - 18:00, A-B 제외)
    (re.compile(r'(?:^|(?<=\s))(?:\d{1,2}[.)](?!\d)|[①-⑳])'), '\n'),
    (re.compile(r'(?=[<\[【])'), '\n'),
]
_HEADER_PREF = re.compile(r'우대\s?(?:사항|조건|요건)?')
_HEADER_REQ = re.compile(r'자격\s?(?:요건|조건)|지원\s?자격|응시\s?자격|필수\s?(?:사항|조건|요건)')
_HEADER_RESET = re.compile(r'담당\s?업무|주요\s?업무|업무\s?내용|모집\s?(?:분야|부문|요강|인원)|근무\s?(?:조건|환경|시간|형태|지역|장소|요일)|고용\s?형태|'
                           r'복리\s?후생|급여|채용\s?절차|전형|접수|제출\s?서류|문의|연락처')


def _norm(s):
    return re.sub(r'[\s\W_]+', '', s)


def _header(text):
    """머리말이면 구간 신호('우대' / '필수' / None=초기화), 아니면 False. 짧은 구절의 앞부분만 본다."""
    head = text[:12]
    if len(_norm(text)) > 14:
        return False
    if _HEADER_PREF.search(head):
        return '우대'
    if _HEADER_REQ.search(head):
        return '필수'
    if _HEADER_RESET.search(head):
        return None
    return False


def split_field(text):
    t = text
    for pat, rep in _SPLITS:
        t = pat.sub(rep, t)
    return [c.strip(' \t,;:') for c in t.split('\n') if c.strip(' \t,;:')]


def split_clauses(row):
    """row: 칸 이름 → 글. → [{clause_id, text, source, section_hint, is_header}]"""
    out, seen = [], []
    for col, src in FIELDS:
        if not row.get(col):
            continue
        hint = None
        for text in split_field(str(row[col])):
            if len(re.findall(r'[가-힣A-Za-z]', text)) < 2:   # "1", "가" 같은 번호·글자 찌꺼기
                continue
            h = _header(text)
            if h is not False:
                hint = h
                if not re.search(r'[:：]\s*\S', text):   # "급여: 150만 원"처럼 내용이 붙어 있으면 내용으로도 판정
                    out.append(dict(clause_id=len(out), text=text, source=src, section_hint=hint, is_header=True))
                    continue
            n = _norm(text)
            # 같은 문장이 여러 칸에 있으면 앞(필수·우대) 칸 것만. 짧은 조각은 우연히 겹치기 쉬워 같을 때만 본다
            if not n or any(n == s or (len(n) >= 6 and n in s) for s in seen):
                continue
            seen.append(n)
            out.append(dict(clause_id=len(out), text=text, source=src, section_hint=hint, is_header=False))
    return out


# ---------------- F2-2 요구 종류 판정 ----------------
COND = re.compile(r'출근|근무 ?가능|요일|주\s?\d|시간|\d{1,2}:\d{2}|시급|월급|연봉|급여|수당|거주|인근|자차|차량\s?소지|출퇴근|보건증|이력서|서류|건강검진|결격|학력|나이|세 이하|연령|모집\s?인원')
POLICY = re.compile(r'장애인|보훈|취업보호|고령자|경력단절|기초수급|한부모|복지카드|고용허가제|고용촉진장려금')
CAREER = re.compile(r'경력자?|신입|경력 ?\d+ ?년')
CAREER_Q = re.compile(r'우대|이상|필수|무관')
PREF = re.compile(r'우대|선호|환영|가산점|있으면 좋|플러스')
REQ = re.compile(r'필수|반드시|요구|소지자|보유자|이수자|가능자|가능하신 분|있으신 분|만 지원|자격요건|지원자격')
MIN_YEARS = re.compile(r'경력\s?(\d{1,2})\s?년\s?이상')
# 조건 구절의 종류 이름(P2 1절 conditions). 위에서 먼저 맞는 것
COND_TYPES = [('급여', r'시급|월급|연봉|급여|수당'), ('출근일', r'출근'), ('자차', r'자차|차량\s?소지'), ('지역·거주', r'거주|인근|출퇴근'),
              ('서류', r'보건증|이력서|서류|건강검진|결격'), ('학력', r'학력'), ('나이', r'나이|세 이하|연령'), ('모집 인원', r'모집\s?인원'), ('근무시간', r'.')]


def clause_type(c, n_kw):
    t, src, hint = c['text'], c['source'], c['section_hint']
    if COND.search(t) and n_kw == 0:
        return '조건'
    if POLICY.search(t) and ('우대' in t or src == 'preference_field_raw'):   # 우대 조건 칸은 값만 들어 있음("고용허가제")
        return '정책우대'
    # P2 표는 '우대·이상·필수·무관'이 함께 있어야 하지만, P2 예시 3은 "동종업계 경력자"도 경력 조건으로 본다 → 예시를 따름
    if CAREER.search(t) and (CAREER_Q.search(t) or t.endswith('경력자') or re.fullmatch(r'신입|경력|경력무관', t)) and n_kw == 0:
        return '경력'
    if PREF.search(t) or src in ('preferred_text', 'preference_field_raw') or hint == '우대':
        return '우대'
    if REQ.search(t) or src in ('required_text', 'license_field_raw') or hint == '필수':
        return '필수'
    return '업무'


# ---------------- F2-3 역량·자격 연결, F2-4 신뢰도 ----------------
_RANK = {'필수': 0, '업무': 1, '우대': 2}
_LIC_LEVEL = {'필수(공고)': '필수', '우대(공고)': '우대', '언급': '언급'}
_con = sqlite3.connect(f'file:{CAREERLENS_DB}?mode=ro', uri=True, check_same_thread=False)
_LIC_ID = {re.sub(r'\s', '', n): i for i, n in _con.execute('select license_id, license_name from licenses where is_qualification=1')}
_LEGAL = {(o, l) for o, l in _con.execute("select occupation_id, license_id from occupation_licenses where requirement_type='필수(법정)'")}


def _license_id(name):
    return _LIC_ID.get(re.sub(r'\s|\d급$|특급$', '', name)) or _LIC_ID.get(re.sub(r'\s', '', name))


def analyze(row, posting_licenses=()):
    """row: posting_id·occupation_id·career와 FIELDS의 칸. posting_licenses: [(license_id, license_name, requirement_level)]"""
    clauses = split_clauses(row)
    reqs, display, filters, conds, unmapped = {}, {}, {}, [], []
    lic = {}
    for lid, name, level in posting_licenses:
        t = _LIC_LEVEL.get(level, '언급')
        if lid not in lic or _RANK.get(t, 9) < _RANK.get(lic[lid]['type'], 9):
            lic[lid] = dict(license_id=lid, name=name, type=t, source='posting_licenses')
    career_quote = None
    for c in clauses:
        if c['is_header']:
            continue
        broken = '??' in c['text']   # 깨진 글자는 역량 대조에서만 뺀다
        m = {'kw': set(), 'non': []} if broken else E.map_ko(c['text'])
        kws = sorted(m['kw'])
        c['type'] = typ = clause_type(c, len(kws))
        c['kw'] = kws
        if typ in ('조건', '정책우대'):
            label = '정책 우대' if typ == '정책우대' else next(n for n, p in COND_TYPES if re.search(p, c['text']))
            conds.append(dict(type=label, quote=c['text']))
            continue
        if typ == '경력':
            career_quote = career_quote or c['text']
            continue
        found_lic = False
        for mm in E.LIC_NAMES.finditer(c['text']):
            lid = _license_id(mm.group(0))
            if lid:
                found_lic = True
                if lid not in lic:   # posting_licenses에 없는 자격만 신호 규칙으로
                    lic[lid] = dict(license_id=lid, name=mm.group(0), type=typ if typ != '업무' else '언급', source=c['source'])
        for k in kws:
            cat, name = D[k]
            item = dict(kw_idx=k, keyword=name, category=cat, quote=c['text'])
            if cat == 'C4':
                display.setdefault(k, item)
            elif cat == 'C5':
                filters.setdefault(k, item)
            else:
                cur = reqs.get(k)
                if cur is None or _RANK[typ] < _RANK[cur['type']]:   # 필수 > 업무 > 우대
                    reqs[k] = dict(item, type=typ, source=c['source'], clause_id=c['clause_id'], method='rule', status='confirmed')
        if typ in ('필수', '우대') and not kws and not found_lic:
            unmapped.append(dict(quote=c['text'], type=typ))
    oid = row.get('occupation_id')
    for v in lic.values():
        v['legal_required'] = (oid, v['license_id']) in _LEGAL
    body = ' '.join(str(row.get(k) or '') for k in ('job_description_raw', 'career_edu_text'))
    my = MIN_YEARS.search(body)
    requirements = sorted(reqs.values(), key=lambda r: (_RANK[r['type']], r['clause_id']))
    n = len(requirements)
    signal = any(r['type'] in ('필수', '우대') for r in requirements) or any(v['type'] in ('필수', '우대') for v in lic.values())
    confidence = 'high' if n >= 3 and signal else 'medium' if n >= 2 else 'low'
    return dict(posting_id=row.get('posting_id'), occupation_id=oid, requirements=requirements, licenses=list(lic.values()),
                display_only=list(display.values()), filters=list(filters.values()), conditions=conds,
                career=dict(field=row.get('career'), min_years=int(my.group(1)) if my else None, quote=career_quote),
                unmapped_requirements=unmapped, confidence=confidence, ai_used=False,
                clauses=[{k: c.get(k) for k in ('clause_id', 'text', 'source', 'section_hint', 'type', 'kw')} for c in clauses])
