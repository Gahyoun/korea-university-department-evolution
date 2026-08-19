# -*- coding: utf-8 -*-
"""
교수(전임교원) 데이터 추출: master parquet -> data/faculty.json (경량 조인 테이블).

원본: '../how large academy/output/master_2015_2025.parquet'
  (논문 how-large-academic-departments-korea 의 처리 산출물; ft=전임교원 수)
출력: data/faculty.json = { "YYYY|sbase|deptkey": ft, ... }
  - sbase: 캠퍼스(_제N캠퍼스, (…)) 및 '국립' 접두 제거한 본교명
  - deptkey: 학과명 정규화(가운뎃점 통일·공백제거) + 마지막 토큰(단과대학 접두 제거) + 학부 접두 합산
  - ft: 캠퍼스/전공 합산

pandas/pyarrow 필요(이 스크립트 한정). 이후 lineage 는 stdlib 로 faculty.json 만 읽는다.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# 원본 parquet 위치(환경변수로 override 가능)
DEFAULT = os.path.normpath(os.path.join(ROOT, "..", "how large academy", "output", "master_2015_2025.parquet"))
SRC = os.environ.get("FACULTY_PARQUET", DEFAULT)

DOTS = re.compile(r"[·・ㆍ‧⋅∙･•]")
def nd(s): return DOTS.sub("·", re.sub(r"\s+", "", str(s)))
def sbase_of(s):
    s = re.sub(r"\(.*?\)|_제\d+캠퍼스|_[^_]*캠퍼스", "", str(s)).strip()
    return re.sub(r"^국립", "", s)
def dept_keys(raw):
    ks = set()
    for base in {str(raw), str(raw).split(" ")[-1]}:   # 원본 + 마지막 토큰(단과대학 접두 제거)
        k = nd(base)
        if k: ks.add(k)
    m = re.search(r"^(.*?학부)", str(raw))              # 학부 접두(전공 합산용)
    if m: ks.add(nd(m.group(1)))
    return ks

def main():
    if not os.path.exists(SRC):
        print(f"[skip] faculty parquet 없음: {SRC}", file=sys.stderr)
        # 빈 테이블이라도 남겨 lineage 가 graceful 하게 동작
        json.dump({}, open(os.path.join(ROOT, "data", "faculty.json"), "w"))
        return
    import pandas as pd
    df = pd.read_parquet(SRC)
    fac = {}
    for r in df.itertuples():
        if pd.isna(r.ft): continue
        y = int(r.year); s = sbase_of(r.sbase)
        keys = dept_keys(r.dept_raw) | dept_keys(r.dkey)
        for k in keys:
            key = f"{y}|{s}|{k}"
            fac[key] = fac.get(key, 0.0) + float(r.ft)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "faculty.json"), "w", encoding="utf-8") as f:
        json.dump(fac, f, ensure_ascii=False, separators=(",", ":"))
    yrs = sorted({int(k.split("|")[0]) for k in fac})
    print(f"faculty.json: {len(fac)} keys · years {yrs[0]}–{yrs[-1]}")

if __name__ == "__main__":
    main()
