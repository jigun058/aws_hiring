"""경로 모음. 로직팀 코드(vendor/)는 형제 모듈을 최상위 이름으로 import하고
import 시점에 환경 변수로 DB를 열기 때문에, 그보다 먼저 이 모듈을 import한다."""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('CL_DATA', BACKEND / 'data'))
CAREERLENS_DB = Path(os.environ.get('CAREERLENS_DB', DATA / 'careerlens.db'))
COURSES_JSON = Path(os.environ.get('COURSES_JSON', DATA / 'courses.json'))
DICT_CSV = DATA / 'P1_competency_dictionary_final.csv'
ENGINE_DIR = BACKEND / 'vendor' / 'engine'   # 엔진 common.py가 이 아래 out/, work/를 읽는다
ENGINE_SRC = ENGINE_DIR / 'src'
P1_SRC = BACKEND / 'vendor' / 'p1'

os.environ.setdefault('CAREERLENS_DB', str(CAREERLENS_DB))   # p1_engine.py가 읽음
os.environ.setdefault('COURSES_JSON', str(COURSES_JSON))
for p in (P1_SRC, ENGINE_SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
