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
            nodes.append([n["year"], n["dept"], n["sub"], n["broad"], n["msz"], code, mem, n.get("band", 0)])
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
        index.append({
            "school": school, "file": "alluvial/" + fn,
            "y0": d["years"][0], "y1": d["years"][-1],
            "n": len(d["nodes"]), "base": d["base2014"],
            "trib": [b["name"] for b in d["bands"]],
            "cur": d["n_active_by_year"].get(str(meta["years"][-1]), 0),
        })
    index.sort(key=lambda x: -x["cur"])
    with open(os.path.join(ADIR, "_index.json"), "w", encoding="utf-8") as f:
        json.dump({"years": meta["years"], "schools": index}, f, ensure_ascii=False)
    # write viewer html
    with open(os.path.join(HERE, "alluvial_template.html"), encoding="utf-8") as f:
        html = f.read()
    with open(os.path.join(OUT, "alluvial.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("schools:", len(index), "| sample top:", [s["school"] for s in index[:5]])

if __name__ == "__main__":
    main()
