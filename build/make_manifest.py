# -*- coding: utf-8 -*-
"""
빌드 매니페스트 생성: out/manifest.json
정적 데이터 API의 버전/메타데이터. 프론트가 읽어 버전·빌드일을 표기하고 캐시 무효화에 사용.
"""
import json, os, sys, platform, subprocess, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def load(p, default=None):
    fp = os.path.join(ROOT, p)
    if not os.path.exists(fp): return default
    with open(fp, encoding="utf-8") as f: return json.load(f)

def pkg(name):
    try:
        return __import__(name).__version__
    except Exception:
        return None

def dir_hash(rel):
    """폴더 내 파일 내용 해시(데이터 버전 지문). 파일명 정렬 후 크기+mtime 무관 내용 기반."""
    d = os.path.join(ROOT, rel); h = hashlib.sha256()
    for fn in sorted(os.listdir(d)):
        with open(os.path.join(d, fn), "rb") as f:
            h.update(fn.encode()); h.update(f.read())
    return h.hexdigest()[:12]

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    summary = load("data/summary.json", {})
    aidx = load("out/alluvial/_index.json", {})
    nidx = load("out/namesplit/_index.json", {})
    years = summary.get("years") or aidx.get("years") or []

    manifest = {
        "schema_version": "1.0",
        "data_version": now.strftime("%Y.%m.%d"),
        "built_at": now.replace(microsecond=0).isoformat(),
        "git_commit": os.environ.get("GIT_COMMIT"),
        "source": {
            "name": "대학알리미 학교별 학부(과) 리스트",
            "url": "https://www.academyinfo.go.kr",
            "coverage_years": [years[0], years[-1]] if years else None,
        },
        "generator": {
            "python": platform.python_version(),
            "numpy": pkg("numpy"), "openpyxl": pkg("openpyxl"), "kiwipiepy": pkg("kiwipiepy"),
        },
        "pipeline": ["normalize", "lineage", "build_alluvial", "build_namesplit", "build_keywords"],
        "stats": {
            "schools": len(aidx.get("schools", [])),
            "active_dept_records": summary.get("n_records_active"),
            "namesplit_subs": len(nidx.get("subs", [])),
            "years": years,
            "excluded": summary.get("excluded"),
        },
        "fingerprints": {
            "alluvial": dir_hash("out/alluvial"),
            "namesplit": dir_hash("out/namesplit"),
        },
    }
    with open(os.path.join(ROOT, "out", "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("manifest:", manifest["data_version"], "| schools", manifest["stats"]["schools"],
          "| fp", manifest["fingerprints"])

if __name__ == "__main__":
    main()
