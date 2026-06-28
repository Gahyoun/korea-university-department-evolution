# -*- coding: utf-8 -*-
"""
소계열별 '학과 명칭' alluvial.
전국 대학의 lineage 링크를 명칭 단위로 집계 -> 소계열별 명칭 계보 alluvial.
  노드 = (연도, 학과명),  크기 msz = 그 명칭을 가진 학교 수
  링크 = 명칭 전이(연도Y nameA -> 연도Y+1 nameB), weight = 전이 학교 수
         같은 명칭이면 연속(cont), 다르면 분화/개명(soft) + 노드에 merge/split 마킹.

out/namesplit/<slug>.json (학교 alluvial 과 동일 노드/링크 포맷) + _index.json
out/namesplit.html (뷰어)
"""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ND = os.path.join(ROOT, "out", "namesplit")

BADSUB = {"N.C.E.", "N.C.E", "기타", "인문사회", "공학", "자연과학", "예체능", "의학", "광역", ""}

def slug(s): return "".join(c if c.isalnum() else "_" for c in s)[:60]

def disp(name):
    """표시 명칭 정규화: 학과/학부/전공/과 접미 통일 (물리학과=물리학부=물리학전공=물리학)."""
    s = re.sub(r"\(.*?\)", "", name).strip()
    for suf in ("전공", "과정"):
        if s.endswith(suf): s = s[:-len(suf)]
    if s.endswith("학과") or s.endswith("학부"):
        s = s[:-1]                       # 물리학과->물리학, 물리학부->물리학
    elif s.endswith("과") and len(s) >= 3:
        s = s[:-1]                       # 교육과->교육
    elif s.endswith("부") and len(s) >= 3:
        s = s[:-1]
    return s.strip() or name

def main():
    L = json.load(open(os.path.join(ROOT, "data", "lineage.json"), encoding="utf-8"))
    YEARS = L["meta"]["years"]

    yi = {y: i for i, y in enumerate(YEARS)}
    # sub -> (year,name) -> set(schools)
    node_sch = collections.defaultdict(lambda: collections.defaultdict(set))
    # sub -> (yA,nA,yB,nB) -> set(schools)
    edge_sch = collections.defaultdict(lambda: collections.defaultdict(set))
    sub_broad = {}
    sub_mid_cnt = collections.defaultdict(collections.Counter)

    def clean_mid(m, broad):
        return broad if (not m or m in BADSUB) else m

    # pass1: 소계열별 disp 이름 수집 -> 'X'와 'X학' 공존 시 'X'를 'X학'으로 통일
    raw_names = collections.defaultdict(set)
    for school, d in L["schools"].items():
        for n in d["nodes"]:
            if n["sub"] in BADSUB: continue
            raw_names[n["sub"]].add(disp(n["dept"]))
    canon = {sub: {nm: (nm + "학" if (nm + "학") in S else nm) for nm in S}
             for sub, S in raw_names.items()}
    def cn(sub, name):
        dn = disp(name); return canon.get(sub, {}).get(dn, dn)

    for school, d in L["schools"].items():
        nodes = d["nodes"]   # dict nodes: year,dept,sub,mid,broad,msz,event,members,band
        for n in nodes:
            if n["sub"] in BADSUB: continue
            node_sch[n["sub"]][(n["year"], cn(n["sub"], n["dept"]))].add(school)
            sub_broad[n["sub"]] = n["broad"]
            sub_mid_cnt[n["sub"]][n.get("mid", n["broad"])] += 1
        for l in d["links"]:
            ns, nt = nodes[l["s"]], nodes[l["t"]]
            sub = ns["sub"]
            if sub in BADSUB: continue
            edge_sch[sub][(ns["year"], cn(sub, ns["dept"]), nt["year"], cn(sub, nt["dept"]))].add(school)

    os.makedirs(ND, exist_ok=True)
    index = []
    for sub, ns in node_sch.items():
        # kept names: ever>=2 schools OR in a name-change transition
        ever = collections.Counter()
        for (y, nm), sc in ns.items(): ever[nm] = max(ever[nm], len(sc))
        change_names = set()
        for (yA, nA, yB, nB) in edge_sch[sub]:
            if nA != nB: change_names.add(nA); change_names.add(nB)
        keep = {nm for nm in ever if ever[nm] >= 2 or nm in change_names}
        if len(keep) < 3: continue

        # node ids
        nid = {}; nodes = []
        years_present = sorted({y for (y, nm) in ns if nm in keep})
        if not years_present: continue
        y0, y1 = years_present[0], years_present[-1]
        for (y, nm), sc in sorted(ns.items()):
            if nm not in keep: continue
            nid[(y, nm)] = len(nodes)
            nodes.append({"y": y, "nm": nm, "msz": len(sc), "sch": sorted(sc)[:10]})
        # links
        links = []
        for (yA, nA, yB, nB), sc in edge_sch[sub].items():
            if nA not in keep or nB not in keep: continue
            a, b = nid.get((yA, nA)), nid.get((yB, nB))
            if a is None or b is None: continue
            links.append({"s": a, "t": b, "w": len(sc), "same": nA == nB})

        # events from degree (명칭 변화 기준)
        inn = collections.defaultdict(list); outn = collections.defaultdict(list)
        for l in links:
            outn[l["s"]].append(l); inn[l["t"]].append(l)
        out_nodes = []
        for i, nd in enumerate(nodes):
            contIn = any(l["same"] for l in inn[i]); contOut = any(l["same"] for l in outn[i])
            inDiff = any(not l["same"] for l in inn[i]); outDiff = any(not l["same"] for l in outn[i])
            code = 0
            if nd["y"] != y0 and not contIn: code |= 1     # new
            if outDiff: code |= 4                          # split (분화)
            if inDiff:  code |= 2                          # merge (개명/통합 유입)
            if nd["y"] != y1 and not contOut and not outDiff: code |= 8  # dead
            # 압축 노드: [year,dept,sub,broad,msz,evcode,members,band]
            out_nodes.append([nd["y"], nd["nm"], sub, sub_broad.get(sub, "기타"),
                              nd["msz"], code, nd["sch"], 0])
        out_links = [[l["s"], l["t"], (0 if l["same"] else 3), 0, 0, l["w"]] for l in links]

        obj = {"sub": sub, "broad": sub_broad.get(sub, "기타"),
               "years": years_present, "nodes": out_nodes, "links": out_links}
        fn = slug(sub) + ".json"
        with open(os.path.join(ND, fn), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        latest = {nm for (y, nm), sc in ns.items() if y == y1 and nm in keep}
        # 계열 학과 수 증감(연도별 총 학과=학교 합) — 전체 명칭 기준
        tot = [0] * len(YEARS)
        for (y, nm), sc in ns.items():
            tot[yi[y]] += len(sc)
        mid = clean_mid(sub_mid_cnt[sub].most_common(1)[0][0], sub_broad.get(sub, "기타"))
        index.append({"sub": sub, "mid": mid, "broad": sub_broad.get(sub, "기타"),
                      "file": "namesplit/" + fn, "names": len(keep), "cur": len(latest),
                      "splits": sum(1 for l in links if not l["same"]), "tot": tot})

    index.sort(key=lambda x: (x["broad"], x["mid"], x["sub"]))
    with open(os.path.join(ND, "_index.json"), "w", encoding="utf-8") as f:
        json.dump({"years": YEARS, "subs": index}, f, ensure_ascii=False)
    html = open(os.path.join(HERE, "namesplit_template.html"), encoding="utf-8").read()
    with open(os.path.join(ROOT, "out", "namesplit.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("subs:", len(index), "| top:", [s["sub"] for s in index[:6]])
    # 예시
    for k in index:
        if "물리" in k["sub"]:
            o = json.load(open(os.path.join(ND, slug(k["sub"]) + ".json"), encoding="utf-8"))
            ch = [(o["nodes"][l[0]][1], o["nodes"][l[1]][1], l[5]) for l in o["links"] if l[2] != 0]
            print(f"  [{k['sub']}] 분화 예:", [f"{a}→{b}({w})" for a, b, w in ch[:6]]); break

if __name__ == "__main__":
    main()
