# 재현 빌드 파이프라인 (오프라인 ETL)
# 원본 <연도>.xlsx (2014-2026) 를 루트에 둔 뒤 `make` 실행.
# 산출: data/*.json (중간) + out/ (정적 데이터 API + 뷰어)
PY ?= python3

.PHONY: all data viz manifest validate serve clean deps

all: viz manifest validate   ## 전체 파이프라인

deps:            ## 의존성 설치 (빌드 전용; 런타임은 의존성 0)
	$(PY) -m pip install -r requirements.txt

data:            ## 1) 정규화·필터  2) 계보 추론
	$(PY) build/normalize.py
	$(PY) build/lineage.py

viz: data        ## 3) 뷰어 데이터 산출 (alluvial / namesplit / keywords)
	$(PY) build/build_alluvial.py
	$(PY) build/build_namesplit.py
	$(PY) build/build_keywords.py

manifest:        ## 4) 빌드 매니페스트 (버전/지문)
	$(PY) build/make_manifest.py

validate:        ## 5) 데이터 계약 검증 (CI 게이트)
	$(PY) build/validate.py

serve:           ## 로컬 미리보기 (파일 fetch용 정적 서버)
	cd out && $(PY) -m http.server 8800

clean:
	rm -rf data/*.json out/alluvial out/namesplit out/*.html out/manifest.json

help:            ## 타깃 목록
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'
