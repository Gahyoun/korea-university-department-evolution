"""Build the executable information-theory notebook from maintained cells."""
from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "department_evolution_information_theory.ipynb"


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text):
    return nbf.v4.new_code_cell(text.strip())


cells = [
    md(r"""
# 한국 대학 학과 진화: 통계물리–정보이론 temporal analysis

이 노트북은 Bachmann et al.의 size-dependent organizational ecology와 Becker–Döring 관점을
한국 대학 학과 Alluvial 계보에 확장한다.

핵심 질문은 다음과 같다.

> 현재 학과 규모, 대학 환경, 최근 개명과 명칭 수식어가 다음 해의 유지·폐지·통합·분리에 관해 각각 몇 bit의 정보를 제공하는가?

분석의 세 층은 다음과 같다.

1. **Local size dynamics:** `s → s±Δs`, stable range, Becker–Döring drift.
2. **Organizational events:** continue, close, merge, split, complex; birth는 별도 집계.
3. **Predictive information:** entropy, CMI, entropy rate, lagged/TE-like information, out-of-time information gain.

연속성은 `alluvial/*.json`의 DAG를 기준으로 하며, 교원 자료는 노드의 `faculty_size` 속성으로만 결합한다.
Alluvial의 `msz`(묶인 전공 수)와 전임교원 수를 혼동하지 않는다.

Sources: [Bachmann et al. (2026)](https://arxiv.org/abs/2607.22189),
[Shannon (1948)](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf),
[Schreiber (2000)](https://doi.org/10.1103/PhysRevLett.85.461).
"""),
    md(r"""
## 0. 실행 조건과 재현성

원자료 Excel은 공개 저장소에 넣지 않는다. 실행 전에 환경변수 `FACULTY_DATA_DIR`를
「6-가-1 전체 교원 대비 전임교원 현황」 파일 폴더로 지정한다.

```bash
export FACULTY_DATA_DIR="/path/to/대학알리미 데이터"
```

환경변수가 없으면 macOS Google Drive의 일반적인 위치를 자동 탐색한다.
산출물은 `analysis/figures`와 `analysis/tables`에 저장된다.
"""),
    code(r"""
import os, sys
from pathlib import Path
import pandas as pd
from IPython.display import Image, Markdown, display

REPO_ROOT = Path.cwd()
if not (REPO_ROOT / "alluvial").exists():
    REPO_ROOT = REPO_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

faculty_env = os.environ.get("FACULTY_DATA_DIR")
if faculty_env:
    FACULTY_DIR = Path(faculty_env)
else:
    candidates = list(Path.home().glob(
        "Library/CloudStorage/GoogleDrive-*/내 드라이브/how large academy/대학알리미 데이터"
    ))
    if not candidates:
        raise FileNotFoundError("Set FACULTY_DATA_DIR to the faculty workbook directory.")
    FACULTY_DIR = candidates[0]

FIG_DIR = REPO_ROOT / "analysis" / "figures"
TABLE_DIR = REPO_ROOT / "analysis" / "tables"
print("repository ready:", REPO_ROOT.exists())
print("faculty files found:", len(list(FACULTY_DIR.glob("*.xlsx"))))
"""),
    md(r"""
## 1. Alluvial-first panel 생성

예측 관측단위는 연도 `t`의 source node다. 한 node가 여러 후속 node를 가지면 split,
후속 node가 여러 predecessor를 가지면 merge다. `complex`는 many-to-many 재편이다.

교원 수 결합은 다음 순서를 따른다.

1. 이름 있는 캠퍼스를 보존한 학교 ID
2. 학교–연도–학과 exact match
3. 학부 노드의 `members` 교원 수 합산
4. 유일한 정규화명 match

불확실한 부분 match는 본 분석 표본에서 제외한다.
"""),
    code(r"""
from analysis.info_theory_pipeline import run_analysis

bundle = run_analysis(
    REPO_ROOT,
    FACULTY_DIR,
    figure_dir=FIG_DIR,
    table_dir=TABLE_DIR,
    n_perm=200,
)
pd.Series({k: v for k, v in bundle.summary.items() if not isinstance(v, pd.DataFrame)}, name="value")
"""),
    code(r"""
audit = pd.DataFrame({
    "quantity": [
        "Alluvial nodes, 2015–2025",
        "nodes with any faculty-size match",
        "nodes with complete member match",
        "analysis source-node rows",
        "restructure rate",
        "rename rate among continuations",
    ],
    "value": [
        bundle.summary["n_alluvial_nodes_2015_2025"],
        bundle.summary["size_match_rate_all_nodes"],
        bundle.summary["size_full_member_match_rate"],
        bundle.summary["n_analysis_rows"],
        bundle.summary["restructure_rate"],
        bundle.summary["rename_rate_among_continue"],
    ],
})
audit
"""),
    md(r"""
## 2. Temporal event decomposition

원 논문의 `closure: s>0 → 0`에는 실제 폐지, merge, split, rename이 섞일 수 있다.
여기서는 Alluvial degree를 이용해 이를 분해한다.

Birth는 기존 학과의 fate와 위험집합이 다르므로 count로 별도 표시한다. 본격적인 birth 예측에는
`(university, subfield, year)` absent-cell risk table이 필요하다.
"""),
    code(r"""
display(bundle.temporal.round(5))
display(Image(filename=str(FIG_DIR / "fig01_temporal_events.png")))
"""),
    md(r"""
## 3. 규모 의존 조직생태학

분야별 대표규모 분포에서 empirical mode `s*_f`와 한 geometric standard deviation 범위를 구한다.
아래 그래프는 `s/s*_f`에 따른 구조사건 확률을 보여준다.

규모가 사건에 주는 정보는

\[
I(S_t;E_{t+1}\mid F,T)
=H(E_{t+1}\mid F,T)-H(E_{t+1}\mid S_t,F,T)
\]

로 측정한다. 이는 size effect의 인과효과가 아니라 분야·연도를 조건화한 **잔여 예측정보**다.
"""),
    code(r"""
display(bundle.stable_ranges.round(3))
display(Image(filename=str(FIG_DIR / "fig02_event_hazard_size.png")))
"""),
    md(r"""
## 4. Entropy, CMI와 TE-like lagged information

- `H(event)`: 아무 feature가 없을 때 next event의 불확실성.
- `I(size regime; event | field, year)`: 원 논문의 size dependence를 bit로 요약.
- `I(previous rename; restructure | size, field, year)`: 직전 개명이 다음 구조재편에 주는 추가정보.
- `I(school change; restructure | focal state)`: 대학 전체 수축/팽창의 lagged directed predictive information.

마지막 값은 한 시차 CMI이므로 `TE-like`라고 부른다. 11개 연도로 continuous transfer entropy를
과도하게 추정하지 않는다. 모든 값은 구조를 보존한 block permutation null과 비교한다.
"""),
    code(r"""
bundle.info_table.round(6)
"""),
    md(r"""
## 5. Out-of-time predictive information gain

Rolling-origin validation에서 다음 모형을 순차 비교한다.

- M0: field + time
- M1: M0 + current size
- M2: M1 + size history, age, university/neighbor context
- M3: M2 + previous rename, added modifiers, name novelty, thematic-entropy proxy

두 모형의 확률 예측 차이는

\[
\widehat I(X;Y\mid Z)
=\frac{1}{N}\sum_i\log_2
\frac{\hat p_{full}(y_i\mid x_i,z_i)}{\hat p_{base}(y_i\mid z_i)}
\]

로 계산한다. Error bar는 university-cluster bootstrap 95% interval이다.
희소한 merge/split multiclass 확률은 training-fold empirical prior와 10% shrinkage하여
극단적인 zero-probability 예측을 막고, empirical-prior baseline과 직접 비교한다.
"""),
    code(r"""
display(bundle.summary["binary_performance"].round(6))
display(bundle.predictive_table.round(6))
display(bundle.multiclass_table.round(6))
display(Image(filename=str(FIG_DIR / "fig03_predictive_information.png")))
"""),
    md(r"""
## 6. 이름변경과 수식어 추가의 temporal signal

개명은 continuity를 끊지 않지만 정보는 버리지 않는다.

- `rename_next`: 동일 계보에서 표시명이 바뀌었는가?
- `added_modifiers_next`: 후속 명칭에 새로 나타난 명사 토큰
- `previous rename`: `t-1 → t` 개명 여부; `t+1` 예측에만 사용
- `name novelty`: 해당 연도까지의 과거 명칭 빈도에 대한 surprisal
- `theme entropy proxy`: 학부 `members` 명칭의 keyword entropy

`t → t+1`에 추가된 수식어를 같은 전이의 사건 예측 feature로 쓰면 leakage다. 따라서 동시 변화는
temporal outcome으로 기술하고, 예측에서는 직전 전이까지만 사용한다.
"""),
    code(r"""
display(bundle.modifier_table.sort_values(["year", "count"], ascending=[True, False]).head(40))
display(Image(filename=str(FIG_DIR / "fig05_added_modifiers.png")))
"""),
    md(r"""
## 7. Markov state와 entropy rate

규모 상태를 `small/stable/large`로 나누고 closure를 `absent` 전이로 둔다.

\[
T_{ab}=P(S_{t+1}=b\mid S_t=a),\qquad
h_1=H(S_{t+1}\mid S_t).
\]

split은 각 successor에 `1/outdegree` weight를 주어 source mass를 보존한다. 이 행렬은 조직 사건의
관계구조 전체를 대체하지 않으며, event-conditioned tensor의 1차 요약이다.
"""),
    code(r"""
display(bundle.transition_matrix.round(4))
print("First-order Markov entropy-rate approximation:", round(bundle.summary["markov_entropy_rate_bits"], 4), "bits/year")
display(Image(filename=str(FIG_DIR / "fig04_transition_matrix.png")))
"""),
    md(r"""
## 8. Becker–Döring local dynamics와 실제 구조사건

원 논문의 local process는

\[
D_s+F\rightleftharpoons D_{s+1}
\]

이다. 한국 계보에서는 이를 실제 조직반응과 분리한다.

\[
D_s\to\varnothing,\quad
D_s+D_r\to D_u,\quad
D_s\to D_r+D_u.
\]

왼쪽은 대표규모 분포에서 얻은 정규화된 `q_{s+1}/q_s`, 오른쪽은 실제 continue-only 평균 drift다.
정적 분포에서 도출한 방향과 동적 drift가 같은지는 model check이지, detailed balance의 증명은 아니다.
"""),
    code(r"""
print("selected static fit:", bundle.summary["bd_fit"], "| fitted mode:", bundle.summary["bd_s_star"])
display(bundle.bd_table.head(20).round(4))
display(Image(filename=str(FIG_DIR / "fig06_bd_and_empirical_drift.png")))
"""),
    md(r"""
## 9. 자동 Results 해석

다음 셀은 실행된 수치만 사용해 report할 수 있는 결과와 아직 주장할 수 없는 부분을 분리한다.
"""),
    code(r"""
info = bundle.info_table.set_index("measure")
pred = bundle.predictive_table.set_index("feature_block")
size_cmi = info.loc["I(size regime; event | field, year)", "bias_corrected_bits"]
rename_cmi = info.loc["I(previous rename; restructure | size, field, year)", "bias_corrected_bits"]
te_like = info.loc["TE-like I(school change; restructure | focal state)", "bias_corrected_bits"]

report = f'''
### Empirical results

- 분석표본은 **{bundle.summary['n_analysis_rows']:,} department-year source nodes**이고,
  완전한 member-level 교원수 결합률은 **{bundle.summary['size_full_member_match_rate']:.1%}**다.
- next-event entropy는 **{bundle.summary['event_entropy_bits']:.4f} bits**다. 낮은 값의 주원인은
  continue class의 압도적 빈도이며, 이것만으로 사건이 잘 예측된다는 뜻은 아니다.
- field와 year를 조건화한 size-regime의 bias-corrected CMI는
  **{size_cmi:.5f} bits/event**다. 한국 자료에서도 size-dependent organizational ecology와
  일치하는 잔여 예측정보가 존재한다.
- 직전 개명은 현재 규모·분야·연도를 알고도 다음 구조재편에
  **{rename_cmi:.5f} bits/event**의 정보를 더한다. 개명/수식어 변화는 단순 노이즈로 버리면 안 된다.
- 대학 전체 학과수 변화의 TE-like 잔여정보는 **{te_like:.5f} bits/event**다. 이는 institution-level
  restructuring field와 일치하지만 인과효과는 아니다.
- out-of-time model에서 size block은 **{pred.loc['size','incremental_bits_per_event']:.5f} bits/event**,
  name-history block은 **{pred.loc['name history','incremental_bits_per_event']:.5f} bits/event**를 추가했다.

### Report-worthy claim

> Department size retains out-of-time information about organizational fate after conditioning on field and time. Recent renaming and modifier changes provide additional predictive information, indicating that Korean department evolution is information-structured beyond size alone.

### What the data do not establish

- CMI와 TE-like 값은 causal effects가 아니다.
- merge/split은 매우 희소하므로 subtype 분류 성능은 별도로 제한을 명시해야 한다.
- `theme_entropy_proxy`는 명칭/member keyword 다양성이지 curriculum 또는 faculty composition의 직접 측정이 아니다.
- Alluvial matching heuristic과 미결합 교원수 노드에 대한 sensitivity analysis가 필요하다.
'''
display(Markdown(report))
"""),
    md(r"""
## 10. 논문용 Figure/Table 대응

| 논문 주장 | 산출물 |
|---|---|
| event decomposition over time | `fig01_temporal_events.png`, `table02_temporal_events.csv` |
| size-dependent organizational ecology | `fig02_event_hazard_size.png`, `table01_stable_ranges.csv` |
| information-theoretic quantification | `fig03_predictive_information.png`, `table03_information_measures.csv` |
| multistate/entropy-rate dynamics | `fig04_transition_matrix.png`, `table07_transition_matrix.csv` |
| rename/modifier temporal adaptation | `fig05_added_modifiers.png`, `table08_added_modifiers.csv` |
| BD local drift vs organizational jumps | `fig06_bd_and_empirical_drift.png` |

최종 원고에서는 `universality` 대신 `cross-field regularity`, `causal effect` 대신
`conditional predictive information`이라는 표현을 사용한다.
"""),
]


notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
)
nbf.write(notebook, OUT)
print(OUT)
