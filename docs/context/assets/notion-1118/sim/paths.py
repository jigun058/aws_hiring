"""모든 스크립트가 쓰는 경로. 환경 변수로 바꿀 수 있다(기본값: 이 폴더의 data/, out/, engine/)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('CL_DATA', os.path.join(HERE, 'data'))
OUT = os.environ.get('CL_OUT', os.path.join(HERE, 'out'))
ENGINE_DIR = os.path.join(HERE, 'engine')
ENGINE_SRC = os.path.join(ENGINE_DIR, 'src')
CAREERLENS_DB = os.environ.get('CAREERLENS_DB', os.path.join(DATA, 'careerlens.db'))
CAREERLENS_URI = 'file:' + CAREERLENS_DB + '?mode=ro'
COURSES_JSON = os.environ.get('COURSES_JSON', os.path.join(DATA, 'courses.json'))
KAGGLE_CSV = os.environ.get('KAGGLE_CSV', os.path.join(DATA, 'postings_usa_candidates_no_senior_6343.csv'))
DICT_CSV = os.path.join(DATA, 'P1_competency_dictionary_final.csv')
POSTING_KW = os.path.join(OUT, 'posting_kw.json')
TRACKA_CLEAN = os.path.join(OUT, 'track_a_postings_보정본.csv')
TRACKA_SUMMARY = os.path.join(OUT, 'track_a_보정_요약.json')
KAGGLE_DB = os.path.join(OUT, 'careerlens_kaggle.db')
SIM_JSON = os.path.join(OUT, 'sim_full.json')
os.environ.setdefault('CAREERLENS_DB', CAREERLENS_DB)   # p1_engine.py가 읽음
os.environ.setdefault('COURSES_JSON', COURSES_JSON)
os.makedirs(OUT, exist_ok=True)
