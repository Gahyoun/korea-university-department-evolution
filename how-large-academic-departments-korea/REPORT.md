# 한국 대학 학과 규모와 조직사건의 Temporal Analysis

## 지도교수 보고용 요약

**상태:** 탐색적 분석 완료. 방법과 결과는 보고 가능하지만, 논문 원고의 확정적 인과 주장 단계는 아니다.

**연구 질문:** 연도 `t`의 학과 교수 수가 `t+1`의 유지·폐과·합병·분리·명칭변경 확률에 어느 정도의 예측정보를 제공하는가?

**이론적 배경:** Bachmann et al.의 size-dependent organizational ecology와 Becker–Döring local growth/shrinkage 관점을 한국 대학 학과 계보의 실제 조직사건으로 확장한다.

---

## 1. 먼저 정의해야 할 측정대상

분석 단위는 **학과–연도 source node**다. 설명변수는 `t`년에 관찰된 전임교원 수이며,
결과변수는 Alluvial 계보에서 확인되는 `t→t+1` 사건이다.

| 사건 | operational definition |
|---|---|
| continue | 하나의 source가 하나의 successor로 이어짐 |
| close | 다음 연도 successor가 없음 |
| merge | 둘 이상의 predecessor가 하나의 successor로 이어짐 |
| split | 하나의 source가 둘 이상의 successor로 이어짐 |
| complex | many-to-many 재편; 예측에서는 split과 통합 |
| rename | one-to-one continuity 안에서 표시 학과명이 달라짐 |
| birth | predecessor가 없는 새 node; incumbent fate와 위험집합이 달라 별도 집계 |

Alluvial의 node 크기 `msz`는 학과에 묶인 전공 수이지 교수 수가 아니다. 교수 수는 대학알리미
연도별 교원 자료를 학교–연도–학과 수준에서 별도로 결합했다.

---

## 2. 분석 표본과 자료 품질

- Alluvial node, 2015–2025: **93,703개**
- next-event 분석에 사용한 source node: **65,979 department-years**
- 완전한 member-level 교수 수 결합률: **82.52%**
- 구조사건 `close/merge/split/complex`: **2,894건, 4.386%**
- one-to-one continuation 중 명칭변경: **3,224건, 5.111%**
- split/complex: **95건**으로 희소함

부분적인 이름 일치로 얻은 교수 수는 주 분석에서 제외했다. 따라서 현재 결과는 정확성이 높은 결합
표본에 대한 추정이며, 미결합 17.48%가 무작위로 빠졌다고 가정하지 않는다.

---

## 3. 핵심 경험적 결과: 전체 사건빈도는 규모에 반비례한다

분야별 대표규모 `s_f*`로 정규화한 현재 규모를 `x=s/s_f*`라 두었다. 아래 수치는 `t`년 규모 구간별
`t+1` 사건률이다.

| 현재 정규화 규모 | 모든 구조사건 | 폐과 | 합병 | 분리/복합 | continuation 중 명칭변경 |
|---:|---:|---:|---:|---:|---:|
| `x<0.5` | **8.87%** | **7.84%** | 0.96% | 0.074% | **7.03%** |
| `0.5≤x<0.8` | 6.10% | 5.19% | 0.87% | 0.044% | 6.08% |
| `0.8≤x<1.2` | 3.90% | 3.19% | 0.61% | 0.098% | 5.31% |
| `1.2≤x<2` | 3.51% | 2.79% | 0.60% | 0.126% | 4.77% |
| `x>2` | **2.82%** | **2.03%** | 0.42% | **0.368%** | **3.60%** |

따라서 coarse-grained한 명제, 작은 학과에서 다음 해 변화사건이 더 자주 발생한다는 자료와
일치한다. 가장 작은 구간의 전체 구조사건률은 가장 큰 구간의 약 **3.15배**, 폐과율은 약 **3.86배**다.

그러나 이 결론을 모든 사건에 적용하면 틀린다. **분리/복합 사건은 규모와 정비례**한다. 큰 학과는
존속성은 높지만 내부 분화 또는 조직적 분할의 channel이 열린다. 이것이 단순한 “large=unchanging”
서술보다 중요한 결과다.

---

## 4. 분야·연도 보정 temporal hazard

아래 odds ratio는 분야와 source year를 보정한 binomial GLM에서 얻었다. 설명변수 한 단위는
`log(s/s_f*)`의 1 standard deviation이며, 표준오차는 대학 단위로 cluster했다.

| 다음 해 사건 | N events | Spearman ρ | adjusted OR | cluster-robust 95% CI | 해석 |
|---|---:|---:|---:|---:|---|
| 모든 구조사건 | 2,894 | -0.0758 | **0.696** | [0.650, 0.746] | 규모 증가 시 전체 사건 odds 감소 |
| 폐과 | 2,375 | -0.0792 | **0.660** | [0.617, 0.707] | 가장 분명한 반비례 |
| 합병 | 424 | -0.0205 | **0.778** | [0.677, 0.894] | 약하지만 음의 관계 |
| 분리/복합 | 95 | +0.0228 | **1.674** | [1.387, 2.021] | 규모 증가 시 분리 odds 증가 |
| continuation 중 명칭변경 | 3,224 | -0.0477 | **0.826** | [0.774, 0.882] | 작은 학과에서 개명이 더 빈번 |

`p`값은 표본 수의 영향을 강하게 받으므로 효과의 크기와 신뢰구간을 우선한다. 특히 분리/복합은
사건 수가 95건뿐이므로 방향은 흥미롭지만 계보 라벨의 수작업 검증 전에는 정밀한 수치로 과해석하지 않는다.

### 연도 방향의 반복성

- 모든 구조사건: **10개 연도 모두 음의 ρ**
- 폐과: **10개 연도 모두 음의 ρ**
- 합병: **10개 연도 모두 음의 ρ**, 다수 연도는 희소사건으로 개별 유의성이 낮음
- 명칭변경: **10개 중 9개 연도에서 음의 ρ**
- 분리/복합: **10개 중 9개 연도에서 양의 ρ**

즉 pooled sample의 결과가 특정 한 해의 충격만으로 만들어졌다고 보기는 어렵다. 다만 연도별 계수의
절대값은 작으며, temporal consistency와 large-N statistical significance를 실질적 예측력과 혼동하지 않는다.

---

## 5. 정보이론적 정량화

단순 상관관계는 사건 종류의 불균형과 분야·연도 차이를 충분히 처리하지 못한다. 따라서 규모가 다음
사건의 불확실성을 실제로 얼마나 줄이는지 bit 단위로 추가 측정했다.

### Conditional mutual information

\[
I(S_t;E_{t+1}\mid F,T)
=H(E_{t+1}\mid F,T)-H(E_{t+1}\mid S_t,F,T).
\]

- size regime–event bias-corrected CMI: **0.00461 bits/event**
- field–year 구조를 보존한 permutation test: **p=0.00498**

값은 작다. 그러나 next-event entropy 자체가 **0.2949 bits**로 낮고 continue가 압도적인 희귀사건
문제라는 점을 고려해야 한다. 결론은 “규모가 사건을 결정한다”가 아니라 **분야와 연도를 알고도 규모가
작지만 검출 가능한 잔여 예측정보를 제공한다**는 것이다.

### Out-of-time predictive information

2019–2024 각 연도를 test fold로 두는 rolling-origin validation에서 field+time baseline에 규모를
추가했을 때:

- incremental predictive information: **0.00420 bits/event**
- university-cluster bootstrap 95% interval: **[0.00232, 0.00669]**
- ROC-AUC: **0.548 → 0.612**
- PR-AUC: **0.0506 → 0.0675**

따라서 규모 정보는 in-sample association을 넘어 미래 연도 확률예측에도 도움을 주었다. 다만 절대적
성능은 낮으며, 개별 학과의 사건을 확정적으로 맞히는 도구로 해석할 수 없다.

### 명칭변경의 추가정보

- 직전 명칭변경과 다음 구조개편의 bias-corrected CMI: **0.00130 bits/event**, `p=0.00498`
- 과거 명칭·수식어 이력의 out-of-time 추가정보: **0.00267 bits/event**

동일한 `t→t+1` 전이에서 관찰된 rename을 그 사건 예측에 사용하지 않았다. 예측에는 `t-1→t`까지의
이력만 사용해 leakage를 막았다. 명칭변경은 continuity를 끊는 사건이 아니라 조직 적응의 선행 신호로
보는 것이 현재 자료에 더 적합하다.

---

## 6. 통계물리학적 해석

### 경험적으로 지지되는 부분

1. **Liability of smallness:** 작은 학과는 폐과·합병·개명 위험이 높다.
2. **Stable regime:** 분야별 대표규모 주변에서 상태 지속성이 가장 높다.
3. **Asymmetric dynamics:** 작은 쪽에서는 grow-or-close 압력이 강하고, 큰 쪽에서는 폐과보다 분리
   channel이 상대적으로 중요하다.
4. **Becker–Döring consistency check:** 대표규모 분포에서 복원한 local rate ratio의 전환점은
   `s*=4`이고, continue-only empirical drift도 소규모에서 양수였다. 정적 분포의 방향과 실제 drift가
   정성적으로 일치한다.

### 아직 지지되지 않는 부분

- detailed balance가 실제 한국 대학 조직에서 성립한다는 주장
- 교수 수가 폐과·합병을 인과적으로 유발한다는 주장
- 모든 분야에 동일한 보편적 임계크기가 존재한다는 주장
- 95건의 split/complex만으로 분리 메커니즘을 확정하는 주장

따라서 `universal law`가 아니라 **cross-field regularity**, `causal effect`가 아니라
**conditional predictive information / temporal association**으로 기술해야 한다.

---

## 7. 현재 단계에서 보고 가능한 결론

> 한국 대학 학과 계보에서 현재 교수 수는 다음 해 조직사건의 빈도와 체계적으로 연결되어 있다.
> 분야와 연도를 보정한 뒤에도 규모가 1 SD 증가하면 전체 구조사건 odds는 약 30%, 폐과 odds는 약
> 34% 감소했다. 이 음의 관계는 2015–2024의 모든 source year에서 반복됐다. 그러나 분리 사건은
> 반대 방향을 보여, 큰 학과일수록 split/complex odds가 증가했다. 따라서 학과 규모의 역할은 단순한
> 안정성 증가가 아니라, 소규모의 grow-or-close dynamics에서 대규모의 persistence-or-fragmentation
> dynamics로 조직사건의 channel을 전환하는 것으로 해석하는 것이 적절하다. 규모는 분야와 연도를
> 조건화한 뒤에도 작지만 유의한 정보량과 out-of-time 예측정보를 제공한다.

이 문장은 경험적 association에 한정되며 인과성과 정책적 적정 교수 수를 주장하지 않는다.

---

## 8. 나중에 또 확인하기

1. split/complex 95건과 merge 표본을 층화추출해 Alluvial lineage를 수작업 검증한다.
2. 교수 수 미결합 노드의 학교·분야·연도 편향을 inverse-probability weighting 또는 bound로 점검한다.
3. 의학계열의 극단적으로 큰 규모를 제외하거나 별도 분석한 sensitivity result를 제시한다.
4. 학교 고정효과, campus 처리, 교수 수 1–2년 lag, event window 2년의 robustness를 비교한다.
5. 대학 prestige·재정·입학정원·학령인구 노출은 자료가 확보된 뒤 competing explanation으로 추가한다.
6. rare-event multiclass model은 macro-F1이 개선되지 않았음을 본문에 명시한다.

---

## 9. 산출물

- 실행 완료 notebook: [`how_large_academic_departments_KR.ipynb`](how_large_academic_departments_KR.ipynb)
- size–event temporal association: [`figures/fig07_size_event_temporal_association.png`](figures/fig07_size_event_temporal_association.png)
- 전체 event timeline: [`figures/fig01_temporal_events.png`](figures/fig01_temporal_events.png)
- 규모별 event hazard: [`figures/fig02_event_hazard_size.png`](figures/fig02_event_hazard_size.png)
- 정보량: [`figures/fig03_predictive_information.png`](figures/fig03_predictive_information.png)
- 집계표: [`tables/`](tables)

## 참고

- Bachmann et al., [How large should academic departments be?](https://arxiv.org/abs/2607.22189) (2026).
- Shannon, [A Mathematical Theory of Communication](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf) (1948).
- Schreiber, [Measuring Information Transfer](https://doi.org/10.1103/PhysRevLett.85.461) (2000).
