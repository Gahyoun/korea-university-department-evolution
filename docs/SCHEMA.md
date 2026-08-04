# 데이터 계약 (SCHEMA)

정적 데이터 API(`out/`)의 JSON 구조. 뷰어(프론트)와 빌드(백엔드 ETL)의 계약이다.
버전은 `manifest.schema_version`. 크기 최소화를 위해 노드/링크는 **배열(위치 기반)** 로 인코딩한다.

## `manifest.json`
```jsonc
{
  "schema_version": "1.0",
  "data_version": "2026.08.04",          // 빌드일
  "built_at": "2026-08-04T05:00:00+00:00",
  "git_commit": "abc1234|null",
  "source": { "name": "대학알리미 …", "url": "…", "coverage_years": [2014, 2026] },
  "generator": { "python": "3.11.7", "numpy": "…", "openpyxl": "…", "kiwipiepy": "…" },
  "pipeline": ["normalize", "lineage", "build_alluvial", "build_namesplit", "build_keywords"],
  "stats": { "schools": 209, "active_dept_records": 120000, "namesplit_subs": 130,
             "years": [2014, …, 2026], "excluded": { "무전공": …, "교양": …, "모집단위": … } },
  "fingerprints": { "alluvial": "12hexchars", "namesplit": "12hexchars" }  // 내용 지문
}
```

## `alluvial/_index.json` — 학교 목록(가나다순)
```jsonc
{ "years": [2014, …, 2026],
  "schools": [ { "school": "가야대학교", "file": "alluvial/가야대학교.json",
                 "y0": 2014, "y1": 2026, "n": 350, "base": 14, "cur": 12,
                 "trib": ["경남과학기술대학교"] } ] }   // trib: 흡수된 학교(밴드)
```

## `alluvial/<학교>.json` — 학교별 계보
```jsonc
{ "school": "경상국립대학교",
  "years": [2014, …, 2026],
  "nodes": [ [year, dept, sub, broad, msz, evcode, members, band], … ],
  "links": [ [s, t, kind, cross, crossBand], … ],
  "deaths": { "2021": [ { "dept": "…", "broad": "…" } ] },
  "bands":  [ { "idx": 1, "name": "경남과학기술대학교", "year": 2022,
               "years": [2014, …, 2021], "deaths": {…}, "n_active_by_year": {…} } ],
  "base2014": 95 }
```
**node** = `[year:int, dept:str, sub:str, broad:str, msz:int, evcode:int, members:str[], band:int]`
- `evcode` 비트: `1`신설 `2`통합 `4`분리 `8`폐지 `16`대계열이동
- `band`: `0`=본교, `≥1`=흡수 학교(= `bands[band-1]`)
- `members`: 학부 소속 전공(≥2개일 때만), 그 외 `[]`

**link** = `[s:int, t:int, kind:int, cross:int, crossBand:int]`
- `s`,`t`: **노드 배열 인덱스**(= id, `id==index` 보장). 링크는 `nodes[s] → nodes[t]`
- `kind`: `0`연속 `1`통합 `2`분리 `3`재편/개명
- `cross`: 대계열 이동(1)
- `crossBand`: 학교통합 합류 링크(1)

## `namesplit/_index.json` — 소계열 계층
```jsonc
{ "years": [2014, …, 2026],
  "subs": [ { "sub": "물리학", "mid": "수학·물리·천문·지구", "broad": "자연과학",
              "file": "namesplit/물리학.json", "names": 72, "cur": 40, "splits": 3,
              "tot": [59, …, 46] } ] }   // tot: 연도별 학과 수
```

## `namesplit/<소계열>.json` — 명칭 분화 alluvial
```jsonc
{ "sub": "물리학", "broad": "자연과학", "years": [2014, …, 2026],
  "nodes": [ [year, name, sub, broad, msz, evcode, schools, band], … ],  // msz=학교 수, schools=예시학교 최대10
  "links": [ [s, t, kind, cross, crossBand, weight], … ] }               // weight=전이 학교 수
```

## 렌더러 계약(불변식)
- `link.s`, `link.t` 는 항상 `[0, len(nodes))` 범위 → 노드 제거 후 **id 재색인** 필수(`lineage.py`).
- `node.band ≤ len(bands)`.
- 뷰어는 per-school/per-sub 파일을 `{cache:"no-cache"}` 로 fetch(배포 후 stale 방지).
