# -*- coding: utf-8 -*-
"""
데이터 계약(스키마) 검증기. 산출된 out/ JSON의 무결성을 확인한다.
원본 데이터 없이 배포물만으로 동작 -> CI에서 회귀 방지 게이트로 사용.

검증:
  - manifest.json 필수 필드
  - alluvial/_index.json + 각 학교 파일: 노드/링크 스키마, 링크 s/t 범위(id==index), band 참조
  - namesplit/_index.json + 표본 파일
사용: python build/validate.py [--full]   (--full: 전체 학교 파일 검사, 기본: 표본 20개)
"""
import json, os, sys, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 배포 저장소(루트에 alluvial/) 와 개발 트리(out/alluvial/) 둘 다 지원
OUT = ROOT if os.path.isdir(os.path.join(ROOT, "alluvial")) else os.path.join(ROOT, "out")
errors = []
def err(msg): errors.append(msg)

def jload(p):
    with open(os.path.join(OUT, p), encoding="utf-8") as f: return json.load(f)

def check_alluvial(file, obj):
    N = len(obj["nodes"])
    for k in ("school", "years", "nodes", "links", "bands"):
        if k not in obj: err(f"{file}: missing '{k}'"); return
    for i, n in enumerate(obj["nodes"]):
        if len(n) != 10: err(f"{file}: node[{i}] arity {len(n)} != 10"); break
    nb = len(obj["bands"])
    for i, n in enumerate(obj["nodes"]):
        if not (0 <= n[7] <= nb): err(f"{file}: node[{i}] band {n[7]} out of [0,{nb}]"); break
    for j, l in enumerate(obj["links"]):
        if len(l) != 5: err(f"{file}: link[{j}] arity {len(l)} != 5"); break
        if not (0 <= l[0] < N and 0 <= l[1] < N):
            err(f"{file}: link[{j}] s/t {l[0]},{l[1]} out of [0,{N})"); break

def main():
    full = "--full" in sys.argv
    # manifest
    if not os.path.exists(os.path.join(OUT, "manifest.json")):
        err("manifest.json missing")
    else:
        m = jload("manifest.json")
        for k in ("schema_version", "data_version", "built_at", "stats"):
            if k not in m: err(f"manifest: missing '{k}'")
    # alluvial
    aidx = jload("alluvial/_index.json")
    schools = aidx["schools"]
    pick = schools if full else random.sample(schools, min(20, len(schools)))
    for s in pick:
        check_alluvial(s["file"], jload(s["file"]))
    # namesplit
    nidx = jload("namesplit/_index.json")
    subs = nidx["subs"]
    for s in (subs if full else random.sample(subs, min(10, len(subs)))):
        o = jload(s["file"])
        Nn = len(o["nodes"])
        for l in o["links"]:
            if not (0 <= l[0] < Nn and 0 <= l[1] < Nn):
                err(f"{s['file']}: link s/t out of range"); break

    if errors:
        print("VALIDATION FAILED:")
        for e in errors[:50]: print("  -", e)
        sys.exit(1)
    print(f"OK · schools {len(schools)} · subs {len(subs)} · checked "
          f"{'all' if full else 'sample'}")

if __name__ == "__main__":
    main()
