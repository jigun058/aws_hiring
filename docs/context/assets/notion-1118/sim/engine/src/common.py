import io
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "raw" / "seoul_jobs_raw.csv"
OUT = ROOT / "out"
WORK = ROOT / "work"
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)

TODAY = pd.Timestamp("2026-11-12")
RAW_ENCODING = "cp949"


def load_raw():
    data = RAW_CSV.read_bytes()
    text = data.decode(RAW_ENCODING, errors="replace")
    n_bad = text.count("�")
    df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, na_values=[""])
    return df, n_bad


MIDDOT = re.compile(r"(?<=[가-힣A-Za-z0-9\)])[?？](?=[가-힣A-Za-z0-9\(])")


def fix_text(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s).replace("�", "")
    s = MIDDOT.sub("·", s)
    s = re.sub(r"[ \t　]+", " ", s).strip()
    return s or None


def save_json(obj, name):
    (WORK / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def load_json(name):
    return json.loads((WORK / name).read_text(encoding="utf-8"))


def norm_key(s):
    s = re.sub(r"\s+", "", s)
    s = s.replace("및", "·").replace(",", "·")
    return s
