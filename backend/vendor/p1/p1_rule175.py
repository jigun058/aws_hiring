import re
NEG = re.compile(r'reports? (?:directly )?to\b|reporting (?:directly )?to\b|reporting line|direct reports|reporting structure', re.I)
FIELD = re.compile(r'(?:incident|witness|activity|daily|shift|accident|inspection|patrol|security|maintenance|service) reports?', re.I)
TERM = r'(?:reports?|reporting|insights?|findings|(?:tableau|looker|power bi|business|analytics|kpi|bi|metrics) dashboards?)'
ACT = r'(?:find\w*|uncover\w*|hunt\w*|unlock\w*|glean\w*|us(?:e|ing)|turn\w*|bring\w*|maintain\w*|design\w*|prepar\w*|creat\w*|build\w*|produc\w*|generat\w*|writ\w*|deliver\w*|present\w*|communicat\w*|shar\w*|translat\w*|summari[sz]\w*|run\w*|pull\w*|develop\w*|provid\w*|track\w*|analy[sz]\w*|derive\w*|surfac\w*|turn\w*|draw\w*|extract\w*|report\w*)'
ACT_NEAR = re.compile(ACT + r'(?:\W+\w+){0,10}?\W+' + TERM + r'|' + TERM + r'(?:\W+\w+){0,3}?\W+(?:to|for) (?:stakeholders|leadership|management|clients|executives|the team)', re.I)
DATA = re.compile(r'data|analy|metric|kpi|trend|performance|results|sales|financial|dashboard|stakeholder|business|customer|campaign|experiment|sql|excel|tableau|management|audience|recommendation|decision|leadership', re.I)
KO = re.compile(r'(?:분석|데이터|결과|성과|통계|실적)[^.]{0,15}(?:보고서|리포트|보고|인사이트)|(?:보고서|리포트)[^.]{0,8}(?:작성|정리)[^.]{0,10}(?:분석|데이터|결과|성과)|인사이트 도출|결과 해석', re.I)
def classify(s):
    """returns 175 (data interpretation/reporting), 162 (field record), 157 (document writing), or None"""
    if NEG.search(s) and not ACT_NEAR.search(NEG.sub(' ', s)):
        return None
    if KO.search(s):
        return 175
    if FIELD.search(s) and ACT_NEAR.search(s):
        return 162
    if ACT_NEAR.search(s):
        if DATA.search(s):
            return 175
        if re.search(r'writ\w*|prepar\w*', s, re.I):
            return 157
    return None

# applicant-directed condition (final): the sentence must describe what the applicant does/needs
APPLICANT = re.compile(r"\byou(?:'ll| will|'d| would)?\b|\byour\b|\bhelp us\b|\bif you\b|responsibilit|duties|what you(?:'ll| will) do|qualifications|requirements|^\W*[\w ,&/]{0,40}(?:intern|analyst|scientist|associate|specialist|manager)s?\s*:|responsible for|the (?:ideal )?candidate|ability to|experience (?:in|with|building|creating)|skills? (?:in|with)|proficien|^\W*(?:[a-z]+ ){0,2}?(?:prepar|creat|build|produc|generat|writ|deliver|present|communicat|shar|translat|summari[sz]|run|pull|develop|provid|track|analy[sz]|use|conduct|monitor|design|maintain|own|lead|support|assist)\w*\b", re.I)
COMPANY_SUBJ = re.compile(r"^\W*(?:(?i:we\b|we're|our\b|the company|customers\b|this (?:allows|enables|helps)|it\b|they\b|basically\b|what's in it)|[A-Z][\w&.\-']+(?: [A-Z][\w&.\-']+){0,3} (?:is|offers|provides|builds|helps|enables|empowers)\b)")
def classify_final(s):
    if COMPANY_SUBJ.search(s) and not re.search(r"\byou(?:'ll| will)?\b", s, re.I):
        return None
    if not APPLICANT.search(s.strip()) and not KO.search(s):
        return None
    return classify(s)
