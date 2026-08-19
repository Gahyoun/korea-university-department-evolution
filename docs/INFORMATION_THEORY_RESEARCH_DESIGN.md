# 한국 대학 학과 진화의 통계물리·정보이론 연구 설계

## 0. 결론

이 연구는 충분히 가능하며, 원 논문의 중요한 한계를 직접 보완한다. Bachmann et al.은 규모 0으로의 전이를 폐쇄·합병·분할·개명까지 포함하는 하나의 `closure`로 처리하고, Becker–Döring(BD) 모형도 한 명 단위의 증감만 표현한다. 현재 저장소는 이 사건들을 명시적으로 구분하는 계보를 이미 만들었으므로, 한국 자료는 단순 재현보다 **“국소적 규모 동역학과 불연속 조직 재편을 결합한 확장”**에 더 적합하다.

다만 `생성·소멸·유지·merge·split`을 그대로 하나의 5-class next-event 문제로 두면 관측 단위가 정의되지 않는다.

- 기존 학과를 시점 `t`의 표본으로 잡으면 다음 해 `생성`은 그 학과에서 발생할 수 없다.
- merge와 split은 한 노드의 상태가 아니라 각각 다대일·일대다 **관계적 hyperedge event**다.
- 따라서 한 개의 평면적 5-class 분류기보다 아래 세 개의 연결된 과제가 올바르다.

1. **Incumbent competing risks:** 기존 학과가 다음 해 `continue/close/merge/split/complex` 중 무엇을 겪는가?
2. **Birth process:** 대학×세부분야의 아직 비어 있는 cell에서 다음 해 학과가 생기는가? 몇 개 생기는가?
3. **Partner/offspring model:** merge/split이 일어난다는 조건 아래 어느 학과와 결합하거나 어떤 후속 학과로 갈라지는가?

정보이론의 중심 결과는 단순 MI 순위가 아니라, 시간 순서에 맞게 교차검증한

\[
I(X_j;Y_{t+1}\mid Z_t)
=\mathbb E\left[\log_2\frac{p(Y_{t+1}\mid X_{j,t},Z_t)}{p(Y_{t+1}\mid Z_t)}\right]
\]

이다. 즉, 규모·분야·학교·연령·이웃 정보를 추가했을 때 다음 사건의 예측 불확실성이 **평균 몇 bit 줄어드는지**를 보고한다.

---

## 1. 실제 자료·코드 점검 결과

점검 대상은 공개 저장소의 commit `d8bcfea`와 로컬의 `how_large_departments_KR_2015-2025.ipynb`, 두 원자료 폴더다. `/mnt/data`에는 요청된 파일이 없었지만 동일 노트북이 Google Drive의 `how large academy/output/how_large_departments_KR_2015-2025.ipynb`에 있었고, 두 데이터 폴더도 읽을 수 있었다.

### 1.1 현재 노트북

- 2015–2025 학과-연도 92,570행, 학과 식별자 `(sbase, dkey)` 16,341개를 만든다.
- 표준분류 결합률은 전체 89.3%이며 연도별 84.8–98.6%다.
- `ft<=0`인 행이 12,811개(13.8%)다.
- 양의 규모 학과-연도 79,759행의 중앙값은 6명이지만, 원 논문처럼 학과별 장기 중앙값을 먼저 계산하면 14,179개 학과의 대표규모 중앙값은 5명이다.
- 현재 분포 적합은 학과별 대표규모가 아니라 모든 학과-연도 행을 독립 표본처럼 사용한다. 이는 장기 존속 학과에 더 큰 가중치를 주고 원 논문의 `typical size` 정의와 다르다.
- 현재 `scipy.stats.fit`은 likelihood 적합이고 적합도 검정을 하지 않는다. 원 논문은 후보분포를 tail-weighted KS로 최적화하고 bootstrap goodness-of-fit을 통과한 분포만 채택한다.
- `q_{s+1}/q_s`는 연속 pdf를 정수점에서 평가한다. 정수 학과규모에는 CDF 구간질량으로 이산화하는 편이 낫고, 원 논문처럼 `s*`에서 비가 1이 되도록 정규화해야 한다.
- 현재 시뮬레이션은 `beta=1`로 둔 가역 birth–death chain이다. BD 직관을 보여주는 데는 쓸 수 있지만, 이를 전체 비선형 BD 계의 직접 재현이라고 부르면 안 된다.

### 1.2 가장 큰 자료 문제: 캠퍼스 붕괴

현재 `sbase()`는 괄호와 `_제N캠퍼스/_분교`를 제거한다. 같은 연도에 서로 다른 원학교가 하나의 `sbase`로 합쳐지는 `(year, sbase)` cell이 262개였다. 예를 들어 고려대–고려대(세종), 연세대–연세대(미래), 한양대–한양대(ERICA), 건국대–건국대(글로컬)가 합쳐질 수 있다.

이는 규모를 합산하고 사건을 잘못 연결할 수 있으므로, 공개 저장소의 캐노니컬 학교·캠퍼스 식별 규칙을 size master에도 그대로 써야 한다. `school_raw`에서 괄호를 지우는 현재 방식은 폐기한다.

### 1.3 현재 계보 저장소의 사건 희소도

저장소의 배포 JSON을 2015–2024의 source-node 관점에서 다시 읽으면 다음 해 사건은 대략 다음과 같다.

| source 학과의 다음 전이 | 수 |
|---|---:|
| maintain/rename | 79,315 |
| close | 4,018 |
| merge로 흡수 | 628 |
| split | 144 |
| split+merge 복합 | 8 |
| gap-continuation | 563 |
| censor/기타 | 219 |

2015–2025의 `new` bit는 5,239개다. merge와 split은 각각 약 0.7%, 0.2% 수준이므로 accuracy는 무의미하고, rare-event calibration과 PR-AUC가 필수다.

또한 현재 노트북의 동일명칭 기준 연간 소멸률은 10.3%였지만, 계보를 적용한 close 비율은 약 4.7%였다. 정확한 최종값은 예측용 one-year resolver를 새로 만든 뒤 다시 계산해야 하지만, 명칭 변경을 폐과로 처리하는 편향이 크다는 것은 이미 분명하다.

### 1.4 현재 계보의 인식론적 지위

좋은 점은 `학과상태`를 관측값, 연도 간 연결을 추정값으로 문서화했다는 것이다. 그러나 예측 연구에는 다음을 분리해야 한다.

- **Retrospective lineage:** 최대 4–5년 뒤 재등장을 이용한 gap bridge/dead rescue를 허용한 역사 시각화용 계보.
- **Online one-year labels:** `t`와 `t+1`에 이용 가능한 코드·상태·명칭만으로 만든 예측 평가용 라벨.

후자를 만들지 않으면 5년 뒤 정보를 이용해 `t+1`의 폐과 여부를 재정의하므로, 예측 horizon이 흐려지고 미래정보 누출이 생긴다.

---

## 2. Event taxonomy와 temporal transition

### 2.0 Alluvial-first 원칙

연속성은 교수 수 notebook의 `(학교명, 학과명)` pivot에서 새로 추론하지 않는다. 공개 저장소의 Alluvial DAG를 **계보 backbone**으로 사용하고, 전임교원 자료는 그 노드에 속성으로 결합한다.

```text
Alluvial node/edge DAG                Faculty size table
(학교·연도·학과·members·event)       (학교·캠퍼스·연도·학과·ft)
              │                              │
              └──── canonical crosswalk ─────┘
                              │
                              ▼
             node-year panel with faculty_size
```

결합 규칙은 다음 순서다.

1. Alluvial의 학교명과 `band`를 이용해 본교/흡수학교/캠퍼스를 보존한 `school_id`를 만든다.
2. 같은 학교·연도의 정확한 학과명 또는 2022+ 학교별학과코드로 먼저 결합한다.
3. Alluvial 노드가 학부 단위로 집계되어 `members`가 있으면, 해당 member들의 전임교원 수를 합산해 node의 `faculty_size`로 둔다.
4. 남은 항목만 같은 분야 안에서 정규화명·명칭 유사도로 결합하고 `match_method`, `match_score`, `ambiguous`를 기록한다.
5. `msz`는 **Alluvial 노드에 묶인 전공/학과 수**이고 `faculty_size`가 아니다. 분석에서 두 열을 절대로 바꾸어 쓰지 않는다.
6. Alluvial의 node index는 파일 내부 배열 위치라 재빌드 시 영속 ID가 아니다. `school_id + band + year + node_index + data_fingerprint`로 실행별 UID를 만들고, 결과 재현에는 manifest fingerprint를 저장한다.

split/merge가 있으므로 전체 connected component에 단일한 “학과 ID”를 부여하는 것도 피한다. 기본 관측단위는 **source node-year**이고, 후속·선행 노드 목록을 가진 DAG로 보존한다. 연속 유지 구간에만 별도의 `continuation_segment_id`를 부여하면 size history feature를 안전하게 계산할 수 있다.

### 2.1 기본 객체

- `department-year node`: `v=(canonical_school_id, canonical_department_lineage_id, year)`
- `size`: `s_v=학부 전임교원 수`
- `field`: 가능한 한 `broad/mid/sub`의 시점별 분류
- `directed lineage edge`: `v_t -> v_{t+1}`
- `event hyperedge`: 여러 source 또는 여러 target을 가질 수 있는 구조변경

### 2.2 사건의 결정적 정의

예측 시점 `t`의 기존 학과에 대해:

- `continue`: 다음 해 후속 학과가 정확히 하나이고, 그 target의 같은 해 predecessor도 하나. 개명·soft match는 별도 modifier로 둔다.
- `close`: `t+1`에 후속이 없고 공식 폐지 상태 또는 보수적 one-year resolver의 폐지 조건을 만족한다.
- `merge`: source가 들어가는 `t+1` target의 predecessor가 둘 이상이다.
- `split`: source가 연결되는 `t+1` target이 둘 이상이다.
- `complex`: 같은 전이에 merge와 split 조건이 동시에 나타나는 many-to-many 재편이다. 8건처럼 희소하므로 억지로 우선순위를 주지 않는다.
- `rename`, `cross_field`, `school_merger`, `gap`은 mutually exclusive class가 아니라 modifier다.

신설은 별도 risk set에서:

- `birth`: `(school, standardized_subfield)`가 `t`에 absent이고 `t+1`에 present가 되거나, 기존 cell 안에서 공식 `신설` 학과가 추가된다.
- 후보공간은 관측된 전국 표준 소계열의 유한 집합으로 고정한다. “아무 이름이나 생길 수 있다”는 무한 후보공간을 만들지 않는다.

### 2.3 상태와 사건을 분리한 transition tensor

규모 상태를

\[
S_t\in\{A,\mathcal R_-,\mathcal R_*,\mathcal R_+\}
\]

로 둔다. `A`는 absent, 나머지는 학문분야별 training-period stable range로 정한 small/stable/large다. 그 다음

\[
T^{(e)}_{ab}=P(S_{t+1}=b,E_{t+1}=e\mid S_t=a)
\]

를 추정한다. `A→present`는 birth, `present→A`는 close, present 사이의 다대일/일대다는 merge/split layer다. 이 tensor가 단순 5×5 행렬보다 관계 구조를 보존한다.

---

## 3. 정보이론 지표: 어떤 질문에 무엇을 쓰는가

| 지표 | 답하는 질문 | 권장 사용 | 주의 |
|---|---|---|---|
| `H(Y)` | 사건 자체가 얼마나 불확실한가? | 전체·분야·연도별 event entropy | class imbalance가 크면 작은 값이 자연스럽다. |
| `I(X;Y)` | 한 feature와 사건 사이에 총 정보가 있는가? | 단변량 탐색, permutation null과 함께 | confounding을 제거하지 못한다. |
| `I(X;Y|Z)` | 기존 정보 `Z` 뒤에도 `X`가 몇 bit를 더 주는가? | 논문의 핵심 feature-group 비교 | cross-fitted 확률로 계산한다. |
| entropy rate `h_mu` | 과거 사건을 알아도 남는 장기 불확실성은 얼마인가? | pooled event/state sequence의 Markov order 비교 | 개별 계보가 11년뿐이라 계층적 pooling이 필요하다. |
| transfer entropy `I(Y_{t+1};X_t^(k)|Y_t^(l),Z_t)` | 이웃 또는 학교 맥락의 과거가 focal event를 추가로 예측하는가? | neighbor shock → focal restructure | directed predictive dependence이지 인과효과가 아니다. |
| directed information | 양방향 feedback을 포함한 전체 시퀀스 정보흐름은? | 장기간·고빈도 자료가 생긴 후 보조분석 | 현재 11개 연도에는 파라미터가 과하다. |

권장 1차 결과는 `CMI`, 2차 결과는 neighbor-level `transfer entropy`다. Directed information은 본문에서 제외한다.

### 3.1 혼합형 feature에서의 CMI 추정

연속·범주·고차원 변수가 섞여 있으므로 무리한 다차원 binning보다 두 probabilistic model의 out-of-sample log-loss 차이를 쓴다.

\[
\widehat I(X;Y|Z)=\frac{1}{N\ln2}\sum_i
\left[\ln \hat p_{\rm full}(y_i|x_i,z_i)-
\ln \hat p_{\rm base}(y_i|z_i)\right].
\]

- 모든 확률은 rolling-origin test fold에서 계산한다.
- university cluster bootstrap으로 95% CI를 구한다.
- `year×field` 내 block permutation 또는 구조를 보존한 null ensemble과 비교한다.
- 유한표본에서는 추정치가 음수가 될 수 있으므로 0으로 잘라 보고하지 말고 CI와 함께 그대로 보인다.
- feature group 순서에 따른 conditional information 차이를 피하려면 여러 순서의 Shapley-CMI를 보조표에 둘 수 있다.

### 3.2 entropy rate와 Markov order

1차 Markov 근사에서는

\[
h_1=H(S_{t+1}|S_t),
\]

2차에서는 `h_2=H(S_{t+1}|S_t,S_{t-1})`다. `h_1-h_2`가 out-of-sample에서도 유의하면 1차 Markov 가정이 부족하다. 같은 검정은

\[
I(S_{t+1};S_{t-1}|S_t)
\]

로 표현할 수 있다.

---

## 4. Feature–event 정보량 설계

모든 동적 feature는 예측시점 `t` 또는 그 이전만 사용한다.

| 묶음 | feature 예시 | 현재 자료 상태 |
|---|---|---|
| Size | `log1p(ft_t)`, 분야별 percentile, `s_t/s*`, stable-range regime | 있음. campus ID 수정 필요 |
| Size history | `Δlog s`, 2–3년 slope, 변동성, zero/nonzero history, 신규전임교원 | 원자료에서 도출 가능 |
| Field | broad/mid/sub, field×year trend, 분류변경 | 있음. 결측 처리 필요 |
| Age | 최초 관측 이후 나이, left-censor flag, 마지막 개명 이후 기간 | lineage에서 도출 가능 |
| University | 총 학과수, 총 전임교원, 분야 포트폴리오 entropy, campus | 도출 가능 |
| Neighbor | 같은 학교·중/소계열 학과 수와 규모, HHI, 최근 신설/폐지 shock, name similarity | 도출 가능. 사건률은 1년 lag |
| Text/novelty | 학과명 토큰, AI·융합 등 keyword novelty, 전국 확산률 | 저장소 keyword ETL을 재사용 |
| Prestige | 시간별 학교 prestige/연구집중도 | 현재 notebook/master에는 없음 |
| Demand/resource | 학생수, 충원율, 예산·연구비, 지역 학령인구 | 현재 notebook/master에는 없음 |

`prestige`는 이름만 넣어서는 안 된다. 대학순위, faculty-hiring prestige, 연구비, 박사과정 여부 중 어느 개념인지 먼저 고정하고, `t` 시점에 이용 가능했던 연도별 값과 출처가 필요하다. 한 시점의 최신 순위를 과거 전체에 붙이면 누출과 개념오염이 생긴다.

### 4.1 권장 정보량 질문

1. `I(size_t; event_{t+1} | field, year)` — size-dependent organizational ecology의 직접 검정.
2. `I(size_history; event | size_t, field, year)` — 현재 크기보다 trajectory가 더 주는 정보.
3. `I(age; event | size, field, university)` — liability of newness/smallness 분리.
4. `I(prestige; event | size, field, university resources)` — prestige의 잔여정보. 인과효과로 표현하지 않는다.
5. `I(neighbor context; event | focal history, university, field, year)` — 학교 내부 포트폴리오 압력.
6. `TE(neighbor shocks→focal event)` — 이웃 변화의 lagged directed predictive information.

---

## 5. 예측모형과 baseline

### 5.1 incumbent competing-risk model

1차 모형은 계층적 multinomial discrete-time hazard다.

\[
P(E_{i,t+1}=e)=\operatorname{softmax}{
f_e(\log s_{it},\Delta s_{it},age_{it},neighbors_{it})
+u_{school,e}+v_{field,e}+\gamma_{year,e}
\}.
\]

- size는 spline으로 두어 비선형 위험을 표현한다.
- school/field partial pooling이 희소 merge/split을 안정화한다.
- 비교용 nonlinear model은 class-weighted gradient boosting을 쓴다.
- merge/split 표본이 너무 적으면 `any restructure`를 1차 endpoint로 두고, conditional subtype을 2차로 분류한다.

### 5.2 birth model

- 관측단위: `(school, subfield, year)` risk cell.
- endpoint: 다음 해 birth 여부 또는 birth count.
- logistic hazard와 hurdle negative-binomial/Poisson을 비교한다.
- 전국 field growth, 학교 portfolio gap, neighboring university adoption, prestige/resource를 설명변수로 둔다.

### 5.3 merge/split partner model

- merge: 같은 학교의 후보 학과 pair마다 pairwise score를 계산하고 실제 partner를 rank한다.
- split: source와 가능한 target-name/field 후보 사이의 ranking 문제로 둔다.
- 공통 feature: field distance, name similarity, size complementarity, 동일 college, 과거 공존.
- 평가지표: Recall@k, MRR, candidate-set log loss.

### 5.4 반드시 포함할 baseline

1. majority: 항상 maintain.
2. year별 또는 field×year별 empirical prior.
3. first-order Markov state/event model.
4. Bachmann size-only: `log size + field + year` hazard.
5. multinomial logistic full model.
6. nonlinear gradient boosting.

정확도 대신 per-class PR-AUC, macro-F1, balanced accuracy, multiclass log loss, Brier score, calibration curve를 보고한다. merge/split은 반드시 precision–recall curve를 별도로 제시한다.

---

## 6. Transition matrix, Markov, hidden state

### 6.1 본문용 행렬

다음 세 가지를 구분한다.

1. `P(E_{t+1}|size regime_t, field)` — 규모에 따른 next-event hazard.
2. `P(S_{t+1}|S_t)` — absent/small/stable/large의 Markov matrix.
3. `T^(e)_{ab}` — 각 규모상태 전이에 어떤 구조사건이 실렸는지 나타내는 event-conditioned tensor.

merge target은 predecessor 수에 비례해 여러 source가 한 target으로 들어가므로, 단순 노드 수와 faculty-mass-weighted matrix를 둘 다 제시한다. split도 각 target에 `1/outdegree` weight를 주는 node-conserving 버전과 교원수 기반 버전을 비교한다.

### 6.2 hidden-state 해석

HMM/HSMM은 탐색적으로만 쓴다. 가능한 latent state는 `growth pressure`, `inertial/stable`, `restructuring-prone`이지만, 이름은 emission/hazard 결과를 본 뒤 붙인다. 각 학과가 11년뿐이므로 개별 HMM은 불가능하고, field/school random effect를 둔 pooled model이 필요하다. BIC보다 held-out log loss와 state stability를 우선한다.

---

## 7. Becker–Döring과 불연속 조직사건의 연결

BD를 전체 모형으로 쓰지 말고 **존속 학과의 local size dynamics component**로 둔다.

\[
D_s + F \rightleftharpoons D_{s+1}
\]

에 다음 반응을 추가한다.

\[
\begin{aligned}
D_s &\to \varnothing &&\text{closure rate }c_s,\\
\varnothing &\to D_s &&\text{birth rate }\nu_s,\\
D_s+D_r &\to D_u &&\text{merge rate }\mu_{s,r\to u},\\
D_s &\to D_r+D_u &&\text{split rate }\sigma_{s\to r,u}.
\end{aligned}
\]

실제 연간 규모는 한 명 이상 점프하므로, continue 조건의 generalized kernel

\[
K^{cont}_{ss'}=P(s_{t+1}=s'\mid s_t=s,E=continue)
\]

도 함께 추정한다. 전체 전이는

\[
P(s'|s,Z)=p_{cont}(s,Z)K^{cont}_{ss'}+
\sum_{e\in\{close,merge,split\}}p_e(s,Z)K^{(e)}_{ss'}
\]

로 분해한다.

### 핵심 검정

1. training period의 학과별 대표규모 분포 `q_s`에서 BD ratio를 얻는다.
2. continue-only 자료에서 empirical drift `E[Δs|s,continue]`를 구한다.
3. `q_{s+1}/q_s`가 예측하는 방향과 empirical drift의 부호가 맞는지 검정한다.
4. 별도로 `c_s, μ_s, σ_s`를 크기함수로 추정한다.
5. 구조사건을 제외했을 때 detailed balance가 더 잘 성립하는지 probability current를 비교한다.

이렇게 해야 “BD가 merge/split을 설명한다”는 과장을 피하면서, **국소적 복원력과 구조적 점프가 어떻게 결합되는가**라는 새 기여가 생긴다.

---

## 8. 검증, robustness, leakage 방지

### 8.1 시간 분할

- rolling-origin 예: train 2015–2020 → test 2021, train through 2021 → test 2022, …, 최종 2024→2025.
- stable range, `s*`, normalization, target encoding, imputation, text vocabulary는 매 fold의 train에서만 적합한다.
- 동일 학과의 미래 행이 train에 들어가는 random row split은 금지한다.

### 8.2 entity-resolution 민감도

세 라벨을 병렬 보고한다.

1. strict: 공식 code/status와 exact match만.
2. conservative: one-year fuzzy match.
3. retrospective: 현재 gap/dead-rescue 계보.

threshold 0.3/0.4/0.5, 2022+ 학과코드 존재 구간, 캠퍼스 처리, 학교통합 처리별 결과를 비교한다. 사건별 층화표본을 사람이 이중 코딩해 precision/recall과 일치도를 보고한다.

### 8.3 null model

- MI/CMI: year×field의 사건 빈도를 보존하는 block permutation.
- neighbor TE: 각 학교의 context sequence를 circular shift하거나 같은 field·year의 다른 학교와 교환.
- transition: size marginal과 field composition을 보존한 configuration-style shuffle.
- mechanism: Gibrat size-independent null과 fitted size-dependent hazard를 out-of-sample likelihood로 비교.

### 8.4 기타 robustness

- 의학 포함/제외 및 별도 모형.
- 대학교만 vs 저장소 범위(대학교·교육대학·산업대학).
- zero-faculty 학과의 `absent`/`active but zero` 처리.
- 분류 결측을 삭제, missing category, probabilistic imputation으로 각각 분석.
- university-cluster bootstrap과 field-stratified bootstrap.
- class-weighting 전후 calibration, prior correction.
- 최신 prestige를 과거에 붙이지 않기, 동시연도 이웃 사건률을 feature로 쓰지 않기.

---

## 9. 논문 figure/table 제안

### Main figures

1. **Data and event ontology:** size table–lineage 결합 흐름과 continue/close/merge/split hyperedge 도식.
2. **Corrected Korean replication:** 학과별 대표규모 분포, 분야별 stable range, empirical growth/closure.
3. **Size-dependent structural hazards:** `P(close/merge/split|s,field)`과 confidence band.
4. **Information gain:** feature group별 cross-fitted CMI(bits/event) forest plot; class별 heatmap.
5. **Multistate dynamics:** `A/R-/R*/R+` Markov matrix와 event-conditioned flux.
6. **BD + structural events:** fitted BD ratio, continue-only empirical drift, structural-event hazard를 한 x축에 정렬.
7. **Prediction:** model별 PR-AUC, log loss, calibration; rare class PR curves.
8. **Neighbor information flow:** 유의한 lagged TE를 분야/학교 맥락별 network 또는 matrix로 표시.

### Main tables

1. 데이터 범위·결합률·캠퍼스/분류 결측·event counts.
2. event taxonomy, risk set, horizon, censoring 규칙.
3. baseline와 main model의 out-of-time 성능 및 CMI.
4. 주요 robustness 결과.

상세 matching threshold, HMM, 모든 분야별 행렬, manual audit confusion matrix는 SI로 보낸다.

---

## 10. 리뉴얼 notebook 설계

기존 27-cell notebook에 뒤쪽만 붙이는 것보다 다음 10개 모듈로 재구성하는 편이 안전하다.

1. `00_config_audit` — 경로, 버전, 파일 fingerprint, coverage.
2. `01_canonical_entities` — campus-preserving school ID와 department keys.
3. `02_size_panel` — 전임교원 size panel, zero/결측 규칙.
4. `03_online_lineage_events` — one-year nodes/edges/hyperedges와 label uncertainty.
5. `04_replication_corrected` — 학과별 median size, wKS fit, bootstrap GOF, stable range.
6. `05_feature_panel` — size history, age, university, neighbors, text.
7. `06_information_theory` — H/MI/CMI/TE와 structured nulls.
8. `07_multistate_bd` — transition tensor, empirical drift, extended BD.
9. `08_prediction` — rolling-origin baselines/main models/calibration.
10. `09_robustness_export` — 민감도, figure/table, machine-readable results.

### 10.1 계보 JSON에서 incumbent next-event를 만드는 셀 골격

```python
from pathlib import Path
from collections import defaultdict
import json, pandas as pd

def incumbent_events(alluvial_dir, y0=2015, y1=2024):
    rows = []
    for fp in Path(alluvial_dir).glob("*.json"):
        if fp.name == "_index.json":
            continue
        obj = json.loads(fp.read_text(encoding="utf-8"))
        nodes, links = obj["nodes"], obj["links"]
        ins, outs = defaultdict(list), defaultdict(list)
        for edge in links:
            s, t = edge[0], edge[1]
            outs[s].append(edge); ins[t].append(edge)

        for i, n in enumerate(nodes):
            year, dept, sub, broad, msz, evcode, members, band = n
            if not (y0 <= year <= y1):
                continue
            one_year = [e for e in outs[i] if nodes[e[1]][0] == year + 1]
            future_gap = [e for e in outs[i] if nodes[e[1]][0] > year + 1]

            is_split = len(one_year) >= 2 or any(e[2] == 2 for e in one_year)
            is_merge = any((nodes[e[1]][5] & 2) or e[2] == 1 for e in one_year)
            if is_split and is_merge: event = "complex"
            elif is_split:            event = "split"
            elif is_merge:            event = "merge"
            elif one_year:            event = "continue"
            elif future_gap:          event = "gap_censored"  # 예측 라벨로 쓰지 않음
            elif evcode & 8:          event = "close"
            else:                     event = "censored"

            rows.append(dict(
                school=obj["school"], node_id=i, year=year, dept=dept,
                sub=sub, broad=broad, band=band, event_next=event,
                split=is_split, merge=is_merge
            ))
    return pd.DataFrame(rows)
```

이 코드는 현재 배포 계보를 진단하는 출발점일 뿐이다. 최종 예측 라벨에는 future-gap을 사용하지 않는 별도 one-year resolver를 적용해야 한다.

### 10.2 out-of-time conditional information을 계산하는 셀 골격

```python
import numpy as np

def incremental_bits(y, p_base, p_full, classes):
    """같은 out-of-time test observations에서 full model이 추가한 bits/event."""
    class_to_col = {c: j for j, c in enumerate(classes)}
    jj = np.array([class_to_col[v] for v in y])
    eps = 1e-12
    pb = np.clip(p_base[np.arange(len(y)), jj], eps, 1)
    pf = np.clip(p_full[np.arange(len(y)), jj], eps, 1)
    pointwise = (np.log(pf) - np.log(pb)) / np.log(2)
    return pointwise.mean(), pointwise

# 각 rolling fold에서:
# base.fit(train[Z], y_train)
# full.fit(train[Z + X_group], y_train)
# p_base/p_full = calibrated predict_proba(test)
# fold의 pointwise bits를 저장한 뒤 university cluster bootstrap CI 계산
```

### 10.3 산출물의 권장 long table

최종 분석의 중심 테이블은 한 행이 `(department_id, year)`인 `panel_event_features.parquet`다.

필수 열:

```text
department_id, school_id, campus_id, year,
size_ft, size_lag1, size_slope3, size_regime_trainfit,
broad, mid, sub, observed_age, left_censored,
univ_total_ft, univ_n_dept, neighbor_n, neighbor_hhi,
neighbor_birth_rate_lag1, neighbor_close_rate_lag1,
event_next, event_uncertainty, label_source,
successor_ids, predecessor_ids, fold_id
```

birth risk table과 merge/split candidate-pair table은 별도로 둔다. 한 테이블에 억지로 합치지 않는다.

---

## 11. 최소 실행 순서

1. Alluvial node/edge를 canonical lineage backbone으로 적재한다.
2. campus-preserving canonical school ID를 만든다.
3. 교수 수 자료를 Alluvial node에 결합한다. `members`가 있는 학부 노드는 member 교수 수를 합산한다.
4. 2022+ 학과코드를 gold-standard 구간으로 삼아 crosswalk와 one-year resolver의 threshold를 검증한다.
5. size master와 lineage node의 결합률·오결합률을 보고한다.
6. corrected replication을 먼저 완성한다: typical size, wKS, GOF, stable range, empirical drift.
7. incumbent 4/5-class와 birth risk table을 분리 생성한다.
8. size-only baseline을 만들고 `I(size;event|field,year)`를 out-of-time으로 측정한다.
9. age/university/neighbor 묶음을 한 번에 하나씩 추가해 CMI를 측정한다.
10. rare event 성능이 확보된 뒤 partner ranking과 TE로 확장한다.

가장 작은 publishable claim은 다음과 같다.

> *After resolving department lineages and institutional campuses, department size carries significant out-of-time information about closure and restructuring risks beyond field and year. Local faculty-size drift is broadly consistent with size-dependent Becker–Döring dynamics, whereas mergers and splits constitute sparse, nonlocal organizational jumps whose risks depend additionally on institutional portfolio context.*

이 문장을 지지하지 못하면 prestige나 복잡한 HMM을 더하는 것이 아니라, 먼저 entity resolution과 event validity를 고쳐야 한다.

---

## 참고 자료

- Bachmann et al., [How large should academic departments be?](https://arxiv.org/abs/2607.22189), arXiv:2607.22189 (2026).
- Gahyoun, [korea-university-department-evolution](https://github.com/Gahyoun/korea-university-department-evolution).
- Shannon, [A Mathematical Theory of Communication](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf) (1948).
- Schreiber, [Measuring Information Transfer](https://doi.org/10.1103/PhysRevLett.85.461), *Physical Review Letters* 85, 461–464 (2000).
- Becker and Döring, [Kinetische Behandlung der Keimbildung in übersättigten Dämpfen](https://doi.org/10.1002/andp.19354160806) (1935).
