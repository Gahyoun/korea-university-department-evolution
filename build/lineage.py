# -*- coding: utf-8 -*-
"""
학교별 학과 계보(flow) - 학부 단위 집계 + 통폐합 링크 + 학교통합 밴드.

노드 단위: "OO학부 XX전공"은 학부(OO학부)로 집계(members=전공들, msz=크기).
연도간 링크: cont / merge / split / soft  (+ x=대계열이동 플래그)
학교통합: 흡수된 학교(경남과기->경상국립, 국립강릉원주->강원)는
  흡수주체 페이지에서 하단 밴드(band>=1)로 자체 타임라인을 그리고,
  통합연도에 흡수주체(band0) 학과로 cross-band merge 링크(끌어올림).
"""
import json, re, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def unit_key(dept):
    d = re.sub(r"\(.*?\)", "", dept).strip()
    m = re.search(r"^(.*?학부)(?:\s|$|[A-Za-z0-9])", d) or re.search(r"^(.*?학부)", d)
    if m and "학부대학" not in m.group(1):
        return m.group(1).strip()
    return d

def norm_name(s):
    # 학과/학부/전공/과 접미를 일관 정리(핵심어+'학' 유지): 간호학과=간호학전공=간호학부=간호학
    s = re.sub(r"\(.*?\)", "", s or "").replace(" ", "")
    for suf in ("전공", "과정"):
        if s.endswith(suf):
            s = s[:-2]; break
    if s.endswith("학과") or s.endswith("학부"):
        s = s[:-1]                       # 간호학과->간호학
    elif s.endswith("계열"):
        s = s[:-2]
    elif len(s) >= 3 and s.endswith(("과", "부")):
        s = s[:-1]
    return s

def bigrams(s): return set(s[i:i+2] for i in range(len(s)-1)) or ({s} if s else set())
def jac(a, b):
    A, B = bigrams(a), bigrams(b)
    return len(A & B) / len(A | B) if A and B else 0.0

def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)

def ev_status(events):
    out = set()
    for k in ("new", "merge", "split"):
        if k in events: out.add(k)
    return out

def link_pair(A, B):
    links = []; usedA, usedB = set(), set()
    byd = collections.defaultdict(list); byn = collections.defaultdict(list)
    for n in B:
        if n["dcode"]: byd[n["dcode"]].append(n)
        byn[n["norm"]].append(n)
    def take(a, b, k):
        links.append((a["id"], b["id"], k)); usedA.add(a["id"]); usedB.add(b["id"])
    for a in A:
        if a["dcode"] and a["dcode"] in byd:
            cs = [m for m in byd[a["dcode"]] if m["id"] not in usedB]
            if cs: take(a, cs[0], "cont")
    for a in A:
        if a["id"] in usedA: continue
        if a["norm"] and a["norm"] in byn:
            cs = [m for m in byn[a["norm"]] if m["id"] not in usedB]
            if cs: take(a, cs[0], "cont")
    # 2.5) 느슨 매칭: 'X' vs 'X학'(학 유무만 차이) -> 연속. 핵심어 1글자(수학/화학/의학..)는 보호.
    def base(nm): return nm[:-1] if (nm.endswith("학") and len(nm) >= 3) else nm
    byb = collections.defaultdict(list)
    for m in B:
        if m["id"] in usedB: continue
        bk = base(m["norm"])
        if len(bk) >= 2: byb[bk].append(m)
    for a in A:
        if a["id"] in usedA: continue
        bk = base(a["norm"])
        if len(bk) < 2: continue
        cs = [m for m in byb.get(bk, []) if m["id"] not in usedB]
        if cs: take(a, cs[0], "cont")
    rem = lambda L, used: [x for x in L if x["id"] not in used]
    subA = collections.defaultdict(list); subB = collections.defaultdict(list)
    for a in rem(A, usedA): subA[a["sub"]].append(a)
    for b in rem(B, usedB): subB[b["sub"]].append(b)
    for b in rem(B, usedB):
        if "merge" in b["stev"]:
            cand = sorted([a for a in subA.get(b["sub"], []) if a["id"] not in usedA],
                          key=lambda a: -jac(a["norm"], b["norm"]))[:6]
            for a in cand: links.append((a["id"], b["id"], "merge")); usedA.add(a["id"])
            if cand: usedB.add(b["id"])
    for a in rem(A, usedA):
        if "split" in a["stev"]:
            cand = sorted([b for b in subB.get(a["sub"], []) if b["id"] not in usedB],
                          key=lambda b: -jac(a["norm"], b["norm"]))[:6]
            for b in cand: links.append((a["id"], b["id"], "split")); usedB.add(b["id"])
            if cand: usedA.add(a["id"])
    for b in rem(B, usedB):
        if "학부" in b["dept"]:
            cand = [a for a in rem(A, usedA) if a["broad"] == b["broad"] and len(a["norm"]) >= 2
                    and "학부" not in a["dept"] and a["norm"] in b["norm"]]
            if cand:
                for a in cand: links.append((a["id"], b["id"], "merge")); usedA.add(a["id"])
                usedB.add(b["id"])
    for a in rem(A, usedA):
        if "학부" in a["dept"]:
            cand = [b for b in rem(B, usedB) if b["broad"] == a["broad"] and len(b["norm"]) >= 2
                    and "학부" not in b["dept"] and b["norm"] in a["norm"]]
            if cand:
                for b in cand: links.append((a["id"], b["id"], "split")); usedB.add(b["id"])
                usedA.add(a["id"])
    pairs = []
    for a in rem(A, usedA):
        for b in subB.get(a["sub"], []):
            if b["id"] in usedB: continue
            j = jac(a["norm"], b["norm"])
            if j >= 0.4: pairs.append((j, a, b))
    for j, a, b in sorted(pairs, reverse=True, key=lambda x: x[0]):
        if a["id"] in usedA or b["id"] in usedB: continue
        take(a, b, "soft")
    return links

def school_graph(yrmap, years, id0, band, gyodae=False):
    """단일 학교 타임라인 -> nodes(per_year), links(연도간). id는 id0부터.
    gyodae=True(교육대학)면 '초등X교육'≡'X교육' (초등 접두 제거)로 매칭."""
    nid = id0
    nodes = []; per_year = collections.defaultdict(list); deaths = collections.defaultdict(list)
    for y in years:
        agg = collections.OrderedDict()
        for r in yrmap.get(y, []):
            if not r["present"]:
                deaths[y].append({"dept": r["dept"], "broad": r["broad"]}); continue
            uk = unit_key(r["dept"])
            if uk not in agg:
                mkey = re.sub(r"^초등(?=.+교육)", "", uk) if gyodae else uk  # 교대: 초등 접두 제거
                agg[uk] = {"id": nid, "year": y, "dept": uk, "members": [], "band": band,
                           "sub_cnt": collections.Counter(), "mid_cnt": collections.Counter(),
                           "broad": r["broad"] or "기타", "dcode": r["dcode"],
                           "norm": norm_name(mkey), "stev": ev_status(r["event"])}
                nid += 1
            nd = agg[uk]
            nd["members"].append(r["dept"]); nd["stev"] |= ev_status(r["event"])
            if r["sub"]: nd["sub_cnt"][r["sub"]] += 1
            if r["mid"]: nd["mid_cnt"][r["mid"]] += 1
        for nd in agg.values():
            nd["members"] = sorted(set(nd["members"])); nd["msz"] = len(nd["members"])
            # 학부 집계 노드의 소/중계열 = 멤버 다수결(N.C.E/빈값 제외 우선)
            def pick(cnt):
                good = [(c, s) for s, c in cnt.items() if s not in ("N.C.E", "N.C.E.")]
                return (max(good)[1] if good else (max(cnt.items(), key=lambda kv: kv[1])[0] if cnt else ""))
            nd["sub"] = pick(nd["sub_cnt"]) or nd["broad"] or "기타"
            nd["mid"] = pick(nd["mid_cnt"]) or nd["broad"] or "기타"
            del nd["sub_cnt"]; del nd["mid_cnt"]
            nodes.append(nd); per_year[y].append(nd)
    links = []
    byid = {n["id"]: n for n in nodes}
    for a, b in zip(years, years[1:]):
        for s, t, k in link_pair(per_year[a], per_year[b]):
            links.append({"s": s, "t": t, "k": k, "x": 1 if byid[s]["broad"] != byid[t]["broad"] else 0})
    # gap-bridge: 같은 이름(norm)+소계열이 이전연도에 있었으면 신설 대신 연결(재등장)
    has_in = {l["t"] for l in links}; has_out = {l["s"] for l in links}
    by_ns = collections.defaultdict(list)
    for n in nodes: by_ns[(n["norm"], n["sub"])].append(n)
    for n in nodes:
        if n["year"] == years[0] or n["id"] in has_in:
            continue                                   # born(좌측 무링크)만 대상
        cands = [m for m in by_ns[(n["norm"], n["sub"])]
                 if m["year"] < n["year"] and m["id"] not in has_out and 0 < n["year"] - m["year"] <= 4]
        if cands:
            src = max(cands, key=lambda m: m["year"])
            links.append({"s": src["id"], "t": n["id"], "k": "cont",
                          "x": 1 if src["broad"] != n["broad"] else 0})
            has_in.add(n["id"]); has_out.add(src["id"])
    return nodes, per_year, deaths, links, nid

def finalize_events(nodes, links, years_main):
    ins = collections.defaultdict(list); outs = collections.defaultdict(list)
    for l in links: outs[l["s"]].append(l); ins[l["t"]].append(l)
    for n in nodes:
        iv, ov = ins[n["id"]], outs[n["id"]]
        # 밴드별 첫/끝 연도 기준
        ev = set()
        if len(iv) >= 2 or any(l["k"] == "merge" for l in iv): ev.add("merge")
        if len(ov) >= 2 or any(l["k"] == "split" for l in ov): ev.add("split")
        if n.get("first") is not None and n["year"] != n["first"] and len(iv) == 0: ev.add("new")
        if n.get("last") is not None and n["year"] != n["last"] and len(ov) == 0: ev.add("dead")
        if any(l["x"] for l in iv + ov): ev.add("cross")
        n["event"] = sorted(ev)

def build():
    recs = load("records.json")
    mergers = load("schools.json")["mergers"]   # absorbed -> {into, year}
    absorbed_of = collections.defaultdict(list)
    for ab, info in mergers.items(): absorbed_of[info["into"]].append((ab, info["year"]))

    by_school = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in recs:
        by_school[r["school"]][r["year"]].append(r)
    YEARS = sorted({r["year"] for r in recs})

    out = {}
    merged_away = set(mergers.keys())   # 흡수되어 본교 밴드로만 표시 -> 독립목록 제외
    for school, yrmap in by_school.items():
        if school in merged_away:
            continue
        # active==0(빈 학교: 산업대 유령 등) 제외
        if not any(r["present"] for rs in yrmap.values() for r in rs):
            continue
        years = sorted(yrmap)
        nid = 0
        gyodae = school.endswith("교육대학교")
        nodes, per_year, deaths, links, nid = school_graph(yrmap, years, nid, 0, gyodae)
        for n in nodes: n["first"], n["last"] = years[0], years[-1]
        bands = []
        absorbed_origin_targets = set()
        ab_list = []   # (merge_year, 흡수밴드 norm 집합)

        for ab, my in absorbed_of.get(school, []):
            if ab not in by_school: continue
            ab_years = [y for y in sorted(by_school[ab]) if y <= my - 1]
            if not ab_years: continue
            bnodes, bpy, bdeaths, blinks, nid = school_graph(by_school[ab], ab_years, nid, len(bands) + 1,
                                                             ab.endswith("교육대학교"))
            for n in bnodes: n["first"], n["last"] = ab_years[0], ab_years[-1] + 1  # last+1 so 마지막해 dead 아님(통합)
            # cross-band merge: absorbed last year -> main merge-year(my) nodes
            last_ab = bpy[ab_years[-1]]
            main_my = per_year.get(my, [])
            byn = collections.defaultdict(list)
            for m in main_my: byn[m["norm"]].append(m)
            xlinks = []
            for a in last_ab:
                tgt = None
                if a["norm"] in byn and byn[a["norm"]]:
                    tgt = byn[a["norm"]][0]
                if tgt is None:
                    cand = [m for m in main_my if "학부" in m["dept"] and len(a["norm"]) >= 2 and a["norm"] in m["norm"]]
                    if cand: tgt = cand[0]
                if tgt is None:
                    # 같은 소계열 인접분야 합병 추론 (컴퓨터공학->컴퓨터과학부 등)
                    same = sorted([m for m in main_my if m["sub"] == a["sub"]],
                                  key=lambda m: -jac(a["norm"], m["norm"]))
                    if same and jac(a["norm"], same[0]["norm"]) >= 0.25:
                        tgt = same[0]
                if tgt is not None:
                    xlinks.append({"s": a["id"], "t": tgt["id"], "k": "merge", "x": 0, "xb": 1})
                    absorbed_origin_targets.add(tgt["id"])
            ab_list.append((my, {n["norm"] for n in bnodes}))
            nodes += bnodes; links += blinks + xlinks
            deaths_ab = {str(y): bdeaths[y] for y in bdeaths}
            bands.append({"idx": len(bands) + 1, "name": ab, "year": my,
                          "years": ab_years, "deaths": deaths_ab,
                          "n_active_by_year": {str(y): len(bpy[y]) for y in ab_years}})

        # band0 spurious 링크만 제거(고스트 ancestry 방지). cont(정상 연속)는 유지 -> 본교 자체 계보 보존.
        if absorbed_origin_targets:
            links = [l for l in links if not (l.get("xb") != 1 and l["k"] != "cont"
                                              and l["t"] in absorbed_origin_targets)]

        # 통합 legacy ghost 제거: 흡수밴드와 같은 이름인데 band0 등장이 [통합-1, 통합] 구간에만 있고
        # 통합연도까지만 존재(통합후 미존속)하는 band0 노드 = 흡수학교 학과의 잘못된 본교 중복.
        if ab_list:
            byid2 = {n["id"]: n for n in nodes}
            adj = collections.defaultdict(set)
            for l in links:
                if l.get("xb") or l["k"] != "cont": continue
                a, b = byid2.get(l["s"]), byid2.get(l["t"])
                if a and b and a["band"] == 0 and b["band"] == 0:
                    adj[l["s"]].add(l["t"]); adj[l["t"]].add(l["s"])
            ghost = set()
            for my, bnorms in ab_list:
                for n in nodes:
                    if n["band"] != 0 or n["id"] in ghost or n["norm"] not in bnorms:
                        continue
                    comp = {n["id"]}; st = [n["id"]]
                    while st:
                        x = st.pop()
                        for y in adj[x]:
                            if y not in comp: comp.add(y); st.append(y)
                    yrs = [byid2[c]["year"] for c in comp]
                    if min(yrs) >= my - 1 and max(yrs) <= my:
                        ghost |= comp
            if ghost:
                nodes = [n for n in nodes if n["id"] not in ghost]
                links = [l for l in links if l["s"] not in ghost and l["t"] not in ghost]

        # id 재색인: 산출 인코더/렌더러가 링크 s/t를 노드 배열 index로 참조하므로 id==index 보장 필수
        idmap = {n["id"]: i for i, n in enumerate(nodes)}
        for i, n in enumerate(nodes): n["id"] = i
        links = [dict(l, s=idmap[l["s"]], t=idmap[l["t"]])
                 for l in links if l["s"] in idmap and l["t"] in idmap]

        finalize_events(nodes, links, years)

        # cleanup working fields
        for n in nodes:
            for k in ("stev", "dcode", "norm", "first", "last"): n.pop(k, None)

        out[school] = {"years": years, "nodes": nodes, "links": links,
                       "deaths": {str(y): deaths[y] for y in deaths},
                       "bands": bands,
                       "n_active_by_year": {str(y): len(per_year[y]) for y in years},
                       "base2014": len(per_year[years[0]]) if years[0] == 2014 else 0}

    meta = {"years": YEARS, "schools": sorted(out)}   # 가나다순
    with open(os.path.join(ROOT, "data", "lineage.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "schools": out}, f, ensure_ascii=False)

    for s in ["경상국립대학교", "강원대학교"]:
        d = out[s]; km = collections.Counter(l["k"] for l in d["links"])
        xb = sum(1 for l in d["links"] if l.get("xb") == 1)
        print(f"{s}: nodes {len(d['nodes'])} bands {[(b['name'],b['year'],len(b['years'])) for b in d['bands']]} "
              f"links {dict(km)} cross-band {xb}")
    print("schools:", len(out))

if __name__ == "__main__":
    build()
