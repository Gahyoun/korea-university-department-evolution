# 인수인계 · 연간 데이터 업데이트 런북

이 프로젝트를 이어받아 **매년 신규 데이터를 수동으로 반영·배포**하기 위한 문서.
처리 규칙 전체는 [`METHODOLOGY.md`](METHODOLOGY.md), 데이터 계약은 [`SCHEMA.md`](SCHEMA.md).

- **Live**: https://gahyoun.github.io/korea-university-department-evolution/
- **배포 저장소**: `Gahyoun/korea-university-department-evolution` (public, GitHub Pages, main/root)
- **개발 트리(원본 포함)**: Google Drive `department anlaysis/` — `<연도>.xlsx`(2014~) + `build/` + `out/`
  (원본 xlsx는 용량상 저장소에 미포함. 개발 트리에만 둔다.)

## 구조 한 줄

```
원본 xlsx → [ETL: build/*.py] → out/ 정적 JSON → (repo 루트로 복사) → git push → Pages 자동 배포
```
런타임(뷰어)은 의존성 0. 처리(ETL)는 Python 결정론적 빌드.

---

## 매년 하는 일 (절차)

### 1. 새 연도 xlsx 확보
- [대학알리미](https://www.academyinfo.go.kr) → "학교별 학부(과) 리스트" 신규 연도 다운로드(보통 2~3월 공시).
- 기존과 동일한 **전처리 후** `20XX.xlsx` 파일명으로 저장.
- 개발 트리 루트(`department anlaysis/`)에 둔다. (기존 2014~ 파일과 같은 위치)

### 2. 빌드
개발 트리에서:
```bash
make deps      # 최초 1회 (numpy/openpyxl/kiwipiepy 고정 버전)
make all       # normalize → lineage → build_* → manifest → validate
```
> `make all` 은 마지막에 `validate.py` 로 산출물 계약을 검증한다. 실패 시 로그의 첫 에러부터 확인.

빌드 후 확인:
- `data/summary.json` — `n_records_active`, 연도별 학교/학과 수가 합리적인지.
- 콘솔 `manifest: <버전> | schools N` — 학교 수가 예년과 비슷한지(급변 시 필터·헤더 의심).

### 3. 저장소로 복사 (배포 레이아웃)
개발 트리는 `out/` 하위, 저장소는 **루트**에 서빙한다. 아래로 동기화:
```bash
SRC="<...>/department anlaysis"
DST=~/work/korea-university-department-evolution     # 저장소 클론 위치
rm -rf "$DST/alluvial" "$DST/namesplit"
cp "$SRC/out/"*.html "$SRC/out/manifest.json" "$DST/"
cp -R "$SRC/out/alluvial" "$SRC/out/namesplit" "$DST/"
cp "$SRC/build/"*.py "$SRC/build/"*_template.html "$DST/build/"   # 스크립트 변경 시
```

### 4. 커밋·배포
```bash
cd "$DST"
python build/validate.py --full        # 저장소 레이아웃에서도 재검증
git add -A
git commit -m "chore(data): 20XX 데이터 반영"
git push                               # push -> GitHub Pages 자동 재배포 (+ validate-data CI)
```
Pages 빌드 완료 후 라이브 확인. 옛 화면이 보이면 **강력 새로고침(⌘⇧R)** — 뷰어 fetch는 `no-cache`라 이후 자동 최신.

---

## 새 연도 반영 시 점검할 함정 (중요)

1. **헤더 변동**: 연도마다 헤더 행 위치·컬럼명이 다르다. `normalize.py` 의 `ALIASES` 에 새 표기가 있으면 추가. (예: 2026은 학교유형이 `학교구분`이 아니라 `학제` 컬럼.)
2. **계열 컬럼 부재**: 어떤 연도가 2026처럼 **대계열만** 수록하면, 중/소계열은 직전 연도 `(학교,학과명)`에서 상속하는 로직(`normalize.py` §2.5)이 그 연도에도 적용되는지 확인.
3. **가운뎃점**: 계열/학과명 `ㆍ(U+318D)` vs `・(U+30FB)` 변형 → `_DOTS` 정규화가 새 표기도 잡는지.
4. **신규 통합/명칭변경**: 그 해 새 국립대 통합·개명·분교 흡수가 생기면 `normalize.py` 의
   `MANUAL_RENAME`(동일학교 개명) / `MERGERS`(학교 통합, 하단 밴드) / `lineage.py` 의
   `CO_LOCATED`(같은 도시 통합=같은 소계열 흡수) 를 갱신.
5. **id 재색인 불변식**: 노드 제거 후 반드시 배열 index 재부여(`lineage.py`). 렌더가 깨지고
   드롭다운과 화면이 어긋나면 이 불변식 또는 브라우저 캐시를 의심.

---

## 파일 맵

| 파일 | 역할 |
|---|---|
| `build/normalize.py` | xlsx 로드·정규화·필터 → `data/records.json`, `schools.json`, `summary.json` |
| `build/lineage.py` | 학부 집계 + 계보 링크 추론 + 통합 밴드 → `data/lineage.json` |
| `build/build_alluvial.py` | 학교별 계보 → `out/alluvial/*.json` + `alluvial.html` |
| `build/build_namesplit.py` | 소계열 명칭 분화 → `out/namesplit/*.json` + `namesplit.html` |
| `build/build_keywords.py` | 키워드 temporal → `out/keywords.html` (데이터 임베드) |
| `build/make_manifest.py` | `out/manifest.json` (버전/빌드일/통계/지문) |
| `build/validate.py` | 데이터 계약 검증(CI 게이트, 루트/out 레이아웃 자동감지) |
| `Makefile` | 위 단계 원커맨드 (`make all`) |
| `.github/workflows/validate.yml` | 푸시 시 배포물 JSON 계약 검증 |

---

## 배포 = GitHub Pages

- main/root 를 Pages 소스로 사용. push 하면 `pages-build-deployment` 가 자동 재배포.
- `_index.json` 등 `_`접두 파일 때문에 **`.nojekyll` 필수**(이미 존재). 지우지 말 것.
- 리빌드가 자동으로 안 될 때: `gh api -X POST repos/Gahyoun/korea-university-department-evolution/pages/builds`.

문의/원저자: [@dotch_gahyoun](https://github.com/Gahyoun).
