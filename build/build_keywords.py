# -*- coding: utf-8 -*-
"""
소계열/대계열별 학과 명칭 키워드 temporal analysis.
records.json -> out/keywords.html (자체완결 데이터 임베드)

- 키워드 = 학과명에서 추출한 명사(kiwipiepy NNG/NNP/SL), 불용어 제거.
- 모드 'new'(신설 학과 키워드) / 'act'(활성 학과 전체).
- 대계열(전체+5) 스코프별 키워드 x 연도 카운트.
"""
import json, os, re, collections
from kiwipiepy import Kiwi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

STOP = set("""학과 학부 전공 과정 계열 학 과 부 대학 학사 야간 주간 인문 사회 자연 과학 예술 체육
공통 모집 단위 트랙 코스 심화 융합학 학년 신입 자유 자율 광역 분야 군 류 제 학위 학교 캠퍼스
및 의 학과군 학부군 일반 특성화 연계 연합""".split())
# 의미 보존(불용어에서 제외하고 싶은 핵심 키워드는 남김)
KEEP_SHORT = {"AI","IT","SW","ICT","UX","VR","AR","XR","BIO","K"}

kiwi = Kiwi()
_cache = {}
MERGE = {("인공","지능"):"인공지능", ("빅","데이터"):"빅데이터",
         ("반","도체"):"반도체", ("사물","인터넷"):"사물인터넷"}
def _clean(w):
    # 단위 접미(공학과/공학부/학과/학부/전공/과/부) 정리
    w = re.sub(r"공학과$","공학",w); w = re.sub(r"공학부$","공학",w)
    w = re.sub(r"학과$","",w);   w = re.sub(r"학부$","",w)
    w = re.sub(r"전공$","",w)
    if len(w) >= 3: w = re.sub(r"과$","",w)   # 교육과->교육 (2글자 핵심어는 보존)
    w = re.sub(r"^(과|부|학)$","",w)
    return w
def keywords(name):
    if name in _cache: return _cache[name]
    raw = []
    for t in kiwi.tokenize(name):
        if t.tag not in ("NNG","NNP","SL"): continue
        w = t.form.strip();
        if not w: continue
        up = w.upper()
        if up in KEEP_SHORT: raw.append(up); continue
        w = _clean(w)
        if len(w) < 2 or w in STOP: continue
        raw.append(w)
    # 인접 토큰 합성(인공지능 등)
    merged=[]; i=0
    while i < len(raw):
        if i+1 < len(raw) and (raw[i],raw[i+1]) in MERGE:
            merged.append(MERGE[(raw[i],raw[i+1])]); i+=2
        else: merged.append(raw[i]); i+=1
    seen=[]; [seen.append(w) for w in merged if w not in seen]
    _cache[name]=seen
    return seen

def main():
    recs = json.load(open(os.path.join(ROOT,"data","records.json"), encoding="utf-8"))
    years = sorted({r["year"] for r in recs})
    yi = {y:i for i,y in enumerate(years)}
    broads = ["ALL","인문사회","공학","자연과학","예체능","의학"]

    # counts[broad][mode][kw] = [per-year]
    def newgrid(): return [0]*len(years)
    counts = {b:{"new":collections.defaultdict(newgrid),"act":collections.defaultdict(newgrid)} for b in broads}
    examples = collections.defaultdict(collections.Counter)   # kw -> Counter(dept)
    kw_total = collections.Counter()

    for r in recs:
        if not r["present"]: continue
        b = r["broad"]; y = r["year"]; isnew = "new" in r["event"]
        kws = keywords(r["dept"])
        for kw in kws:
            kw_total[kw]+=1
            examples[kw][r["dept"]]+=1
            for scope in ("ALL", b if b in counts else None):
                if scope is None: continue
                counts[scope]["act"][kw][yi[y]] += 1
                if isnew:
                    counts[scope]["new"][kw][yi[y]] += 1

    # top keywords per (broad,mode) 제한
    TOPN = 70
    data = {}
    used_kw = set()
    for b in broads:
        data[b]={}
        for mode in ("new","act"):
            d = counts[b][mode]
            top = sorted(d.items(), key=lambda kv:-sum(kv[1]))[:TOPN]
            data[b][mode] = {kw:arr for kw,arr in top}
            used_kw.update(kw for kw,_ in top)

    ex = {kw:[d for d,_ in examples[kw].most_common(8)] for kw in used_kw}

    payload = {"years":years, "broads":broads, "data":data, "examples":ex}
    os.makedirs(os.path.join(ROOT,"out"), exist_ok=True)
    with open(os.path.join(HERE,"keywords_template.html"), encoding="utf-8") as f:
        html=f.read()
    html = html.replace("/*__DATA__*/","const PAYLOAD="+json.dumps(payload, ensure_ascii=False)+";")
    with open(os.path.join(ROOT,"out","keywords.html"),"w",encoding="utf-8") as f:
        f.write(html)
    print("keywords:",len(used_kw),"| top overall:",[k for k,_ in kw_total.most_common(15)])

if __name__=="__main__":
    main()
