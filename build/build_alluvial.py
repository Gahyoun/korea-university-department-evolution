# -*- coding: utf-8 -*-
"""
lineage.json -> out/alluvial/ (per-school compact JSON) + out/alluvial.html (viewer)
"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")
ADIR = os.path.join(OUT, "alluvial")

def slug(s):
    return "".join(c if c.isalnum() else "_" for c in s)

def main():
    with open(os.path.join(ROOT, "data", "lineage.json"), encoding="utf-8") as f:
        L = json.load(f)
    os.makedirs(ADIR, exist_ok=True)
    meta = L["meta"]
    index = []
    KIND = {"cont": 0, "merge": 1, "split": 2, "soft": 3}
    for school, d in L["schools"].items():
        # nodes -> [year, dept, sub, broad, msz, evcode, members]
        # evcode bits: new=1 merge=2 split=4 dead=8 cross=16
        nodes = []
        for n in d["nodes"]:
            ev = set(n["event"])
            code = ((1 if "new" in ev else 0) | (2 if "merge" in ev else 0) |
                    (4 if "split" in ev else 0) | (8 if "dead" in ev else 0) |
                    (16 if "cross" in ev else 0))
            mem = n["members"] if n["msz"] > 1 else []
            nodes.append([n["year"], n["dept"], n["sub"], n["broad"], n["msz"], code, mem,
                          n.get("band", 0), n.get("ft"), n.get("fte")])
            # [8]=전임교원 수(교수, null 가능) · [9]=ft 출처(0 관측 / 1 계보추정 / null 미상)
        # links -> [s, t, kind, cross, crossBand]
        links = [[l["s"], l["t"], KIND.get(l["k"], 3), l["x"], l.get("xb", 0)] for l in d["links"]]
        obj = {
            "school": school,
            "years": d["years"],
            "nodes": nodes,
            "links": links,
            "deaths": d["deaths"],
            "bands": d["bands"],
            "base2014": d["base2014"],
        }
        fn = slug(school) + ".json"
        with open(os.path.join(ADIR, fn), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        total = sum(d["n_active_by_year"].values())
        # 교수 총원: 최신 교수데이터 연도(2025) band0 합
        ftcur = round(sum(n["ft"] for n in d["nodes"]
                          if n.get("band", 0) == 0 and n["year"] == 2025 and n.get("ft")), 0)
        has_ft = any(n.get("ft") for n in d["nodes"])
        index.append({
            "school": school, "file": "alluvial/" + fn,
            "y0": d["years"][0], "y1": d["years"][-1],
            "n": len(d["nodes"]), "base": d["base2014"],
            "trib": [b["name"] for b in d["bands"]],
            "cur": d["n_active_by_year"].get(str(meta["years"][-1]), 0),
            "ftcur": ftcur, "hasft": has_ft,
        })
    index.sort(key=lambda x: x["school"])   # 가나다순
    with open(os.path.join(ADIR, "_index.json"), "w", encoding="utf-8") as f:
        json.dump({"years": meta["years"], "schools": index}, f, ensure_ascii=False)
    # write viewer html — 하나의 템플릿에서 크기 모드만 바꿔 두 페이지 생성(데이터 공유)
    with open(os.path.join(HERE, "alluvial_template.html"), encoding="utf-8") as f:
        tpl = f.read()
    def render(mode, title, sub):
        return (tpl.replace("__SIZE_MODE__", mode)
                   .replace("__PAGE_TITLE__", title).replace("__PAGE_SUB__", sub))
    with open(os.path.join(OUT, "alluvial.html"), "w", encoding="utf-8") as f:
        f.write(render("msz", "학과 계보 Alluvial",
                       "2014 기준 · 통합·분리·신설·폐지 · 노드 높이=전공/학과 수 · 대학알리미"))
    with open(os.path.join(OUT, "faculty.html"), "w", encoding="utf-8") as f:
        f.write(render("ft", "학과 계보 · 교수 수",
                       "노드 높이=전임교원(교수) 수 · 2015–2025 · 회색=교수수 미상 · 대학알리미/how-large-academic-departments"))
    n_ft = sum(1 for s in index if s.get("hasft"))
    print("schools:", len(index), "| 교수데이터 학교:", n_ft, "| pages: alluvial.html, faculty.html")

if __name__ == "__main__":
    main()
