# 한국 4년제 대학 학과의 변천사 · 2014–2026

대학알리미 "학교별 학부(과) 리스트"(2014–2026) 13개년을 정규화하여, 대학별 학과의
**신설·통합·분리·폐지**와 소·대계열별 **학과명 키워드 추세**를 인터랙티브하게 본다.

> "창의", "융합" 같은 첨단·세부분야 특성화 학과명이 늘어나는 흐름을 데이터로 추적한 프로젝트.

🔗 **Live**: https://gahyoun.github.io/korea-university-department-evolution/

## 산출물

| 페이지 | 내용 |
|---|---|
| [`index.html`](index.html) | 랜딩 — 프로젝트 개요·읽는 법 |
| [`alluvial.html`](alluvial.html) | **학과 계보 Alluvial** — 대학 선택(가나다) → 2014~2026 학과 흐름. 노드 크기=학부/학과에 묶인 전공 수. 학부 통폐합으로 굵어지고 분리로 가늘어진다. 대계열 필터 시 학과명 라벨 표시. 학교통합은 상·하 밴드. |
| [`namesplit.html`](namesplit.html) | **소계열 학과명 분화 Alluvial** — 대계열▸중계열▸소계열 계층 선택 → 전국 대학에서 학과 "이름"이 어떻게 이어지고 갈라지는지. 노드=명칭, 크기=학교 수. 상단에 계열 학과 수 증감 스트립. |
| [`keywords.html`](keywords.html) | **학과명 키워드 Temporal** — 신설/활성 학과명 키워드의 연도별 버블 + 급상승 랭킹(융합·AI·반도체·스마트…). |

## 아키텍처

읽기 전용 분석 데이터셋 → **서버·DB 없는 정적 데이터 API**가 정답인 구조.

```
원본 xlsx (2014–2026)                 [비공개, 로컬]
        │  오프라인 ETL (Python, 결정론적)
        ▼
build/normalize → lineage → build_*    [백엔드 = 빌드 파이프라인]
        │
        ▼
out/  alluvial/<학교>.json · namesplit/<소계열>.json · manifest.json   [버전드 정적 데이터]
        │  GitHub Pages CDN (gzip · 무한 캐시 · 운영비 0)
        ▼
alluvial.html · namesplit.html · keywords.html   [얇은 렌더링 클라이언트, 런타임 의존성 0]
```

- **효율적 데이터 이동**: 전 데이터를 한 번에 싣지 않고, 선택한 학교/소계열 JSON만 **지연 로드**(`fetch`, `no-cache`로 배포 후 stale 방지). 노드/링크는 배열(위치 기반)로 인코딩해 크기 최소화.
- **버저닝**: [`manifest.json`](manifest.json) — 데이터 버전·빌드일·툴 버전·통계·내용 지문. 프론트가 읽어 표기.
- **데이터 계약**: [`docs/SCHEMA.md`](docs/SCHEMA.md) — 뷰어↔빌드 JSON 스키마.
- **처리 기준(재현성)**: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — 필터·정규화·계보 추론·통합 처리의 전 규칙.
- **CI**: 푸시 시 [`build/validate.py`](build/validate.py)가 배포물 JSON 계약(링크 범위·밴드 참조 등)을 검증(`validate-data`).
- **연간 업데이트**: 데이터는 매년 수동 반영. 절차·점검 함정은 [`docs/HANDOFF.md`](docs/HANDOFF.md)(인수인계 런북) 참조.

## 재현 빌드

원본 `<연도>.xlsx`(2014–2026, [대학알리미](https://www.academyinfo.go.kr) 공개자료)를 루트에 두고:

```bash
make deps      # pip install -r requirements.txt (빌드 전용; 런타임은 의존성 0)
make all       # normalize → lineage → build_* → manifest → validate
make serve     # http://localhost:8800  (로컬 미리보기)
```

개별 단계·규칙은 [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md), 산출 스키마는 [`docs/SCHEMA.md`](docs/SCHEMA.md) 참조.

## 데이터 출처 / 면책

데이터: [대학알리미](https://www.academyinfo.go.kr) 학교별 학부(과) 리스트 2014–2026.
계열 분류·통합·연결은 정규화·추정을 포함하며 실제와 다를 수 있다.

데이터 처리·시각화 by [@dotch_gahyoun](https://github.com/Gahyoun).
