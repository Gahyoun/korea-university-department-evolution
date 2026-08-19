"""Information-theoretic analysis of Korean academic department evolution.

The Alluvial DAG is the lineage backbone.  Faculty workbooks only supply the
time-varying size attribute.  No private source data are written by this module;
only aggregate tables and figures are exported.
"""
from __future__ import annotations

import json
import math
import os
import re
import unicodedata
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as font_manager
import numpy as np
import pandas as pd
import seaborn as sns
from kiwipiepy import Kiwi
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


EVENT_ORDER = ["continue", "close", "merge", "split", "complex"]
STRUCTURAL_EVENTS = {"close", "merge", "split", "complex"}
STATE_ORDER = ["small", "stable", "large", "absent"]
YEAR_MIN, YEAR_MAX = 2015, 2025

STOP = set(
    """학과 학부 전공 과정 계열 학 과 부 대학 학사 야간 주간 인문 사회 자연 과학 예술 체육
    공통 모집 단위 트랙 코스 심화 융합학 학년 신입 자유 자율 광역 분야 군 류 제 학위 학교 캠퍼스
    및 의 학과군 학부군 일반 특성화 연계 연합""".split()
)
KEEP_SHORT = {"AI", "IT", "SW", "ICT", "UX", "VR", "AR", "XR", "BIO", "K"}
MERGE_TOKENS = {
    ("인공", "지능"): "인공지능",
    ("빅", "데이터"): "빅데이터",
    ("반", "도체"): "반도체",
    ("사물", "인터넷"): "사물인터넷",
}


@dataclass
class AnalysisBundle:
    nodes: pd.DataFrame
    panel: pd.DataFrame
    typical: pd.DataFrame
    stable_ranges: pd.DataFrame
    temporal: pd.DataFrame
    info_table: pd.DataFrame
    predictive_table: pd.DataFrame
    multiclass_table: pd.DataFrame
    transition_matrix: pd.DataFrame
    modifier_table: pd.DataFrame
    bd_table: pd.DataFrame
    summary: dict


def _nfc(value) -> str:
    return unicodedata.normalize("NFC", str(value))


def school_key(value) -> str:
    """Preserve named campuses while removing administrative suffixes."""
    s = re.sub(r"\s+", "", _nfc(value).strip())
    s = re.sub(r"_(본교|분교|제?\d+캠퍼스)$", "", s)
    aliases = {
        "연세대학교(원주)": "연세대학교(미래)",
        "경상대학교": "경상국립대학교",
        "서울과학기술대학교(산업대)": "서울과학기술대학교",
        "한국전통문화대학교(일반)": "한국전통문화대학교",
        "강릉원주대학교": "국립강릉원주대학교",
        "부경대학교": "국립부경대학교",
        "공주대학교": "국립공주대학교",
        "군산대학교": "국립군산대학교",
        "금오공과대학교": "국립금오공과대학교",
        "목포대학교": "국립목포대학교",
        "목포해양대학교": "국립목포해양대학교",
        "순천대학교": "국립순천대학교",
        "창원대학교": "국립창원대학교",
        "한국교통대학교": "국립한국교통대학교",
        "한국해양대학교": "국립한국해양대학교",
        "한밭대학교": "국립한밭대학교",
    }
    return aliases.get(s, s)


def text_key(value) -> str:
    s = re.sub(r"\s+", "", _nfc(value))
    return re.sub(r"[ㆍ・‧⋅∙·･•]", "·", s)


def norm_name(value) -> str:
    s = re.sub(r"\(.*?\)", "", text_key(value))
    for suffix in ("전공", "과정"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    if s.endswith(("학과", "학부")):
        s = s[:-1]
    elif s.endswith("계열"):
        s = s[:-2]
    elif len(s) >= 3 and s.endswith(("과", "부")):
        s = s[:-1]
    return s


_kiwi = Kiwi()
_keyword_cache: dict[str, tuple[str, ...]] = {}


def keywords(name: str) -> tuple[str, ...]:
    if name in _keyword_cache:
        return _keyword_cache[name]
    raw = []
    for token in _kiwi.tokenize(str(name)):
        if token.tag not in ("NNG", "NNP", "SL"):
            continue
        word = token.form.strip()
        upper = word.upper()
        if upper in KEEP_SHORT:
            raw.append(upper)
            continue
        word = re.sub(r"공학(과|부)$", "공학", word)
        word = re.sub(r"(학과|학부|전공)$", "", word)
        if len(word) >= 3:
            word = re.sub(r"과$", "", word)
        if len(word) < 2 or word in STOP:
            continue
        raw.append(word)
    merged, idx = [], 0
    while idx < len(raw):
        pair = tuple(raw[idx : idx + 2])
        if len(pair) == 2 and pair in MERGE_TOKENS:
            merged.append(MERGE_TOKENS[pair])
            idx += 2
        else:
            merged.append(raw[idx])
            idx += 1
    result = tuple(dict.fromkeys(merged))
    _keyword_cache[name] = result
    return result


def shannon(values: Iterable, weights: Iterable[float] | None = None) -> float:
    s = pd.Series(list(values))
    if s.empty:
        return np.nan
    if weights is None:
        counts = s.value_counts().to_numpy(float)
    else:
        w = pd.Series(list(weights), index=s.index)
        counts = w.groupby(s).sum().to_numpy(float)
    probs = counts[counts > 0] / counts.sum()
    return float(-(probs * np.log2(probs)).sum())


def conditional_entropy(df: pd.DataFrame, target: str, given: list[str], weight: str | None = None) -> float:
    if not given:
        return shannon(df[target], df[weight] if weight else None)
    total = df[weight].sum() if weight else len(df)
    answer = 0.0
    group_arg = given[0] if len(given) == 1 else given
    for _, group in df.groupby(group_arg, dropna=False):
        mass = group[weight].sum() if weight else len(group)
        answer += mass / total * shannon(group[target], group[weight] if weight else None)
    return float(answer)


def conditional_mutual_information(
    df: pd.DataFrame, x: str, y: str, z: list[str], weight: str | None = None
) -> float:
    return conditional_entropy(df, y, z, weight) - conditional_entropy(df, y, z + [x], weight)


def _find_faculty_file(directory: Path, year: int) -> Path:
    keys = [_nfc(f"{year}년"), "6-가-1", "전임교원 현황_학과별자료"]
    for path in directory.glob("*.xlsx"):
        name = _nfc(path.name)
        if "(1)" not in name and all(key in name for key in keys):
            return path
    raise FileNotFoundError(f"No faculty workbook for {year} in {directory}")


def _first_index(row, predicate):
    for idx, value in enumerate(row):
        if predicate(str(value).strip()):
            return idx
    return None


def load_faculty_panel(directory: str | Path, years=range(YEAR_MIN, YEAR_MAX + 1)) -> pd.DataFrame:
    directory = Path(directory)
    frames = []
    for year in years:
        raw = pd.read_excel(_find_faculty_file(directory, year), header=None)
        header_row = next(i for i in range(8) if any("학과" in str(v) for v in raw.iloc[i]))
        header = list(raw.iloc[header_row])
        c_type = _first_index(header, lambda v: v == "학교종류")
        c_school = _first_index(header, lambda v: v == "학교")
        c_dept = _first_index(header, lambda v: "학과" in v)
        c_undergrad = _first_index(header, lambda v: v == "학부")
        data = raw.iloc[header_row + 4 :].reset_index(drop=True)
        frame = pd.DataFrame(
            {
                "stype": data[c_type],
                "school_raw": data[c_school],
                "dept_raw": data[c_dept],
                "faculty_size": pd.to_numeric(data[c_undergrad], errors="coerce").fillna(0)
                + pd.to_numeric(data[c_undergrad + 1], errors="coerce").fillna(0),
            }
        )
        frame[["stype", "school_raw"]] = frame[["stype", "school_raw"]].ffill()
        frame = frame[(frame["stype"] == "대학교") & frame["dept_raw"].notna()].copy()
        frame["year"] = year
        frame["node_school"] = frame["school_raw"].map(school_key)
        frame["dept_key"] = frame["dept_raw"].map(text_key)
        frame["dept_norm"] = frame["dept_raw"].map(norm_name)
        frames.append(
            frame.groupby(["year", "node_school", "dept_key", "dept_norm"], as_index=False).agg(
                faculty_size=("faculty_size", "sum"),
                dept_raw=("dept_raw", "first"),
                school_raw=("school_raw", "first"),
            )
        )
    return pd.concat(frames, ignore_index=True)


def load_alluvial(repo_root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    repo_root = Path(repo_root)
    node_rows, edge_rows = [], []
    for path in sorted((repo_root / "alluvial").glob("*.json")):
        if path.name == "_index.json":
            continue
        obj = json.loads(path.read_text(encoding="utf-8"))
        fingerprint = path.stem
        for idx, node in enumerate(obj["nodes"]):
            year, dept, sub, broad, msz, evcode, members = node[:7]
            band = node[7] if len(node) > 7 else 0
            node_school = obj["school"] if band == 0 else obj["bands"][band - 1]["name"]
            uid = f"{fingerprint}:{idx}"
            node_rows.append(
                {
                    "uid": uid,
                    "file": path.name,
                    "node_id": idx,
                    "year": int(year),
                    "school": obj["school"],
                    "node_school": school_key(node_school),
                    "dept": dept,
                    "dept_key": text_key(dept),
                    "dept_norm": norm_name(dept),
                    "sub": sub or "미상",
                    "broad": broad or "기타",
                    "member_count": int(msz),
                    "members": members,
                    "event_code": int(evcode),
                    "band": int(band),
                }
            )
        for edge_idx, edge in enumerate(obj["links"]):
            source, target, kind = edge[:3]
            edge_rows.append(
                {
                    "edge_uid": f"{fingerprint}:e{edge_idx}",
                    "source": f"{fingerprint}:{source}",
                    "target": f"{fingerprint}:{target}",
                    "kind": {0: "continue", 1: "merge", 2: "split", 3: "soft"}.get(kind, "other"),
                    "cross_field": int(edge[3]) if len(edge) > 3 else 0,
                    "cross_band": int(edge[4]) if len(edge) > 4 else 0,
                }
            )
    return pd.DataFrame(node_rows), pd.DataFrame(edge_rows)


class UnionFind:
    def __init__(self, items):
        self.parent = {item: item for item in items}

    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left, right):
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[b] = a


def add_lineage_structure(nodes: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    nodes = nodes.copy()
    year_of = nodes.set_index("uid")["year"].to_dict()
    one_year = edges[edges.apply(lambda r: year_of[r.target] == year_of[r.source] + 1, axis=1)].copy()
    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    for edge in one_year.itertuples():
        outgoing[edge.source].append(edge)
        incoming[edge.target].append(edge)

    uf = UnionFind(nodes["uid"])
    for edge in one_year.itertuples():
        if edge.kind in {"continue", "soft"} and len(outgoing[edge.source]) == 1 and len(incoming[edge.target]) == 1:
            uf.union(edge.source, edge.target)
    nodes["segment_id"] = nodes["uid"].map(uf.find)
    nodes["segment_start"] = nodes.groupby("segment_id")["year"].transform("min")
    nodes["observed_age"] = nodes["year"] - nodes["segment_start"]

    dept_of = nodes.set_index("uid")["dept"].to_dict()
    records = []
    for row in nodes.itertuples():
        ins, outs = incoming[row.uid], outgoing[row.uid]
        target_names = [dept_of[e.target] for e in outs]
        source_names = [dept_of[e.source] for e in ins]
        is_split = len(outs) >= 2 or any(e.kind == "split" for e in outs)
        is_merge = any(len(incoming[e.target]) >= 2 or e.kind == "merge" for e in outs)
        if row.year >= YEAR_MAX:
            event_next = "censored"
        elif is_split and is_merge:
            event_next = "complex"
        elif is_split:
            event_next = "split"
        elif is_merge:
            event_next = "merge"
        elif outs:
            event_next = "continue"
        elif row.event_code & 8:
            event_next = "close"
        else:
            event_next = "censored"

        rename_next = False
        added_next: tuple[str, ...] = ()
        name_distance_next = np.nan
        if len(outs) == 1:
            target_name = target_names[0]
            rename_next = text_key(row.dept) != text_key(target_name)
            source_tokens, target_tokens = set(keywords(row.dept)), set(keywords(target_name))
            added_next = tuple(sorted(target_tokens - source_tokens))
            name_distance_next = 1 - SequenceMatcher(None, text_key(row.dept), text_key(target_name)).ratio()

        prev_rename = False
        added_prev: tuple[str, ...] = ()
        if len(ins) == 1 and len(outgoing[ins[0].source]) == 1:
            source_name = source_names[0]
            prev_rename = text_key(source_name) != text_key(row.dept)
            added_prev = tuple(sorted(set(keywords(row.dept)) - set(keywords(source_name))))

        records.append(
            {
                "uid": row.uid,
                "event_next": event_next,
                "successor_count": len(outs),
                "predecessor_count": len(ins),
                "rename_next": rename_next,
                "name_distance_next": name_distance_next,
                "added_modifiers_next": added_next,
                "added_modifier_count_next": len(added_next),
                "prev_rename": prev_rename,
                "added_modifiers_prev": added_prev,
                "added_modifier_count_prev": len(added_prev),
                "successors": tuple(e.target for e in outs),
                "predecessors": tuple(e.source for e in ins),
            }
        )
    return nodes.merge(pd.DataFrame(records), on="uid", how="left")


def attach_faculty_size(nodes: pd.DataFrame, faculty: pd.DataFrame) -> pd.DataFrame:
    nodes = nodes.copy()
    exact = faculty.set_index(["year", "node_school", "dept_key"])["faculty_size"].to_dict()
    normalized_groups = faculty.groupby(["year", "node_school", "dept_norm"])["faculty_size"].agg(list).to_dict()
    sizes, methods, scores = [], [], []
    for row in nodes.itertuples():
        names = list(row.members) if row.members else [row.dept]
        values, used_methods = [], []
        for name in names:
            value = exact.get((row.year, row.node_school, text_key(name)))
            if value is not None:
                values.append(float(value)); used_methods.append("exact")
                continue
            candidates = normalized_groups.get((row.year, row.node_school, norm_name(name)), [])
            if len(candidates) == 1:
                values.append(float(candidates[0])); used_methods.append("normalized_unique")
        if values:
            sizes.append(float(sum(values)))
            methods.append("exact" if all(m == "exact" for m in used_methods) else "normalized_unique")
            scores.append(len(values) / len(names))
        else:
            sizes.append(np.nan); methods.append("unmatched"); scores.append(0.0)
    nodes["faculty_size"] = sizes
    nodes["size_match_method"] = methods
    nodes["size_match_score"] = scores
    return nodes


def add_name_features(nodes: pd.DataFrame) -> pd.DataFrame:
    nodes = nodes.copy()
    all_tokens = {name: keywords(name) for name in nodes["dept"].unique()}
    nodes["name_tokens"] = nodes["dept"].map(all_tokens)
    nodes["name_token_count"] = nodes["name_tokens"].map(len)
    theme_entropy = []
    for row in nodes.itertuples():
        member_names = list(row.members) if row.members else [row.dept]
        member_tokens = [token for name in member_names for token in keywords(name)]
        theme_entropy.append(shannon(member_tokens) if member_tokens else 0.0)
    nodes["theme_entropy_proxy"] = theme_entropy

    token_counts, total_docs = Counter(), 0
    novelty = pd.Series(index=nodes.index, dtype=float)
    for year in sorted(nodes["year"].unique()):
        mask = nodes["year"] == year
        vocab = max(len(token_counts), 1)
        denom = total_docs + vocab
        for idx, toks in nodes.loc[mask, "name_tokens"].items():
            novelty.loc[idx] = (
                float(np.mean([-math.log2((token_counts[tok] + 1) / max(denom, 1)) for tok in toks]))
                if toks else 0.0
            )
        for toks in nodes.loc[mask, "name_tokens"]:
            token_counts.update(set(toks)); total_docs += 1
    nodes["name_novelty"] = novelty
    return nodes


def add_context_features(nodes: pd.DataFrame) -> pd.DataFrame:
    nodes = nodes.copy()
    annual = nodes[(nodes["year"].between(YEAR_MIN - 1, YEAR_MAX))].groupby(
        ["node_school", "year"], as_index=False
    ).agg(school_n_dept=("uid", "count"), school_total_ft=("faculty_size", "sum"))
    annual = annual.sort_values(["node_school", "year"])
    annual["school_delta_n"] = annual.groupby("node_school")["school_n_dept"].diff()
    annual["school_direction"] = pd.cut(
        annual["school_delta_n"], [-np.inf, -0.5, 0.5, np.inf], labels=["contract", "stable", "expand"]
    ).astype(object).fillna("unknown")
    nodes = nodes.merge(annual, on=["node_school", "year"], how="left")
    nodes["neighbor_count"] = (
        nodes.groupby(["node_school", "year", "broad"])["uid"].transform("count") - 1
    ).clip(lower=0)
    field_entropy = (
        nodes.groupby(["node_school", "year"])["broad"]
        .apply(shannon)
        .rename("school_field_entropy")
        .reset_index()
    )
    return nodes.merge(field_entropy, on=["node_school", "year"], how="left")


def add_size_lags(nodes: pd.DataFrame) -> pd.DataFrame:
    nodes = nodes.copy()
    size_of = nodes.set_index("uid")["faculty_size"].to_dict()
    lag = []
    for row in nodes.itertuples():
        if len(row.predecessors) == 1:
            lag.append(size_of.get(row.predecessors[0], np.nan))
        else:
            lag.append(np.nan)
    nodes["faculty_size_lag1"] = lag
    nodes["size_delta"] = nodes["faculty_size"] - nodes["faculty_size_lag1"]
    nodes["log_size"] = np.log1p(nodes["faculty_size"])
    return nodes


def stable_size_ranges(nodes: pd.DataFrame, edges: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    observed = nodes[(nodes["year"].between(YEAR_MIN, YEAR_MAX)) & (nodes["faculty_size"] > 0)].copy()
    typical = observed.groupby("segment_id", as_index=False).agg(
        typical_size=("faculty_size", "median"),
        broad=("broad", lambda s: s.mode().iat[0]),
        years_observed=("year", "nunique"),
    )
    rows = []
    for broad, group in typical.groupby("broad"):
        x = group["typical_size"].to_numpy(float)
        logx = np.log(x)
        median = float(np.exp(np.median(logx)))
        gsd = float(np.exp(logx.std()))
        counts = pd.Series(x.astype(int)).value_counts()
        rows.append(
            {
                "broad": broad,
                "n_segments": len(group),
                "median": median,
                "s_minus": median / gsd,
                "s_plus": median * gsd,
                "s_star": float(counts.idxmax()),
            }
        )
    ranges = pd.DataFrame(rows)
    nodes = nodes.merge(ranges[["broad", "s_minus", "s_plus", "s_star"]], on="broad", how="left")
    nodes["size_regime"] = np.select(
        [nodes["faculty_size"] < nodes["s_minus"], nodes["faculty_size"] < nodes["s_plus"]],
        ["small", "stable"],
        default="large",
    )
    nodes.loc[nodes["faculty_size"].isna() | (nodes["faculty_size"] <= 0), "size_regime"] = "unknown"
    nodes["normalized_size"] = nodes["faculty_size"] / nodes["s_star"].replace(0, np.nan)
    return nodes, typical.merge(ranges, on="broad", how="left")


def build_panel(repo_root: str | Path, faculty_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nodes, edges = load_alluvial(repo_root)
    nodes = add_lineage_structure(nodes, edges)
    faculty = load_faculty_panel(faculty_dir)
    nodes = attach_faculty_size(nodes, faculty)
    nodes = add_name_features(nodes)
    nodes = add_context_features(nodes)
    nodes = add_size_lags(nodes)
    nodes, typical = stable_size_ranges(nodes, edges)
    panel = nodes[
        nodes["year"].between(YEAR_MIN, YEAR_MAX - 1)
        & nodes["event_next"].isin(EVENT_ORDER)
        & (nodes["faculty_size"] > 0)
        & (nodes["size_match_score"] == 1)
    ].copy()
    panel["restructure_next"] = panel["event_next"].isin(STRUCTURAL_EVENTS).astype(int)
    panel["year_str"] = panel["year"].astype(str)
    return nodes, panel, typical


def temporal_summary(nodes: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    event = (
        panel.groupby(["year", "event_next"]).size().unstack(fill_value=0).reindex(columns=EVENT_ORDER, fill_value=0)
    )
    event_rates = event.div(event.sum(axis=1), axis=0)
    event_rates["rename"] = panel[panel["event_next"] == "continue"].groupby("year")["rename_next"].mean()
    births = nodes[nodes["year"].between(YEAR_MIN, YEAR_MAX) & ((nodes["event_code"] & 1) > 0)].groupby("year").size()
    event_rates["birth_count"] = births
    return event_rates.reset_index()


def permutation_cmi(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: list[str],
    strata: list[str],
    n_perm: int = 200,
    seed: int = 20260819,
) -> dict:
    work = df[[x, y] + list(dict.fromkeys(z + strata))].dropna().copy()
    observed = conditional_mutual_information(work, x, y, z)
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_perm):
        shuffled = work[y].copy()
        for _, index in work.groupby(strata, dropna=False).groups.items():
            vals = shuffled.loc[index].to_numpy(copy=True)
            rng.shuffle(vals)
            shuffled.loc[index] = vals
        permuted = work.copy(); permuted[y] = shuffled
        null.append(conditional_mutual_information(permuted, x, y, z))
    null = np.asarray(null)
    return {
        "measure": x,
        "bits": observed,
        "null_mean": float(null.mean()),
        "bias_corrected_bits": float(observed - null.mean()),
        "z_score": float((observed - null.mean()) / max(null.std(ddof=1), 1e-12)),
        "p_perm": float((1 + np.sum(null >= observed)) / (len(null) + 1)),
    }


def information_summary(panel: pd.DataFrame, n_perm: int = 200) -> pd.DataFrame:
    info_panel = panel.copy()
    info_panel["event_binary"] = np.where(info_panel["restructure_next"] == 1, "restructure", "continue")
    info_panel["size_regime3"] = info_panel["size_regime"]
    rows = [
        {
            "measure": "H(event)",
            "bits": shannon(info_panel["event_next"]),
            "null_mean": np.nan,
            "bias_corrected_bits": np.nan,
            "z_score": np.nan,
            "p_perm": np.nan,
        },
        permutation_cmi(
            info_panel, "size_regime3", "event_next", ["broad", "year_str"], ["broad", "year_str"], n_perm
        ),
        permutation_cmi(
            info_panel,
            "prev_rename",
            "event_binary",
            ["size_regime3", "broad", "year_str"],
            ["size_regime3", "broad", "year_str"],
            n_perm,
        ),
        permutation_cmi(
            info_panel,
            "school_direction",
            "event_binary",
            ["size_regime3", "broad", "year_str", "prev_rename"],
            ["size_regime3", "broad", "year_str", "prev_rename"],
            n_perm,
        ),
    ]
    labels = {
        "size_regime3": "I(size regime; event | field, year)",
        "prev_rename": "I(previous rename; restructure | size, field, year)",
        "school_direction": "TE-like I(school change; restructure | focal state)",
    }
    out = pd.DataFrame(rows)
    out["measure"] = out["measure"].replace(labels)
    return out


def _make_model(numeric: list[str], categorical: list[str], multiclass: bool = False) -> Pipeline:
    transformer = ColumnTransformer(
        [
            ("num", Pipeline([("scale", StandardScaler())]), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), categorical),
        ],
        remainder="drop",
    )
    model = LogisticRegression(
        max_iter=800,
        C=0.7,
        solver="lbfgs",
    )
    return Pipeline([("features", transformer), ("model", model)])


def _aligned_probabilities(model: Pipeline, frame: pd.DataFrame, classes: list[str]) -> np.ndarray:
    raw = model.predict_proba(frame)
    trained = list(model.named_steps["model"].classes_)
    aligned = np.full((len(frame), len(classes)), 1e-12)
    for idx, label in enumerate(trained):
        aligned[:, classes.index(str(label))] = raw[:, idx]
    aligned /= aligned.sum(axis=1, keepdims=True)
    return aligned


def rolling_predictions(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    work = panel.copy()
    fill_zero = [
        "size_delta",
        "school_delta_n",
        "school_field_entropy",
        "neighbor_count",
        "name_novelty",
        "name_token_count",
        "theme_entropy_proxy",
        "added_modifier_count_prev",
    ]
    for col in fill_zero:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)
    work["prev_rename"] = work["prev_rename"].astype(int)
    blocks = {
        "M0 field+time": (["year"], ["broad"]),
        "M1 + size": (["year", "log_size"], ["broad"]),
        "M2 + context": (
            [
                "year", "log_size", "size_delta", "observed_age", "school_delta_n",
                "school_field_entropy", "neighbor_count",
            ],
            ["broad"],
        ),
        "M3 + name history": (
            [
                "year", "log_size", "size_delta", "observed_age", "school_delta_n",
                "school_field_entropy", "neighbor_count", "prev_rename",
                "added_modifier_count_prev", "name_novelty", "name_token_count", "theme_entropy_proxy",
            ],
            ["broad"],
        ),
    }
    binary_rows, prediction_rows = [], []
    for test_year in range(2019, YEAR_MAX):
        train = work[work["year"] < test_year]
        test = work[work["year"] == test_year]
        if test.empty:
            continue
        for model_name, (numeric, categorical) in blocks.items():
            model = _make_model(numeric, categorical)
            model.fit(train, train["restructure_next"])
            prob = model.predict_proba(test)[:, list(model.named_steps["model"].classes_).index(1)]
            for idx, p in zip(test.index, prob):
                prediction_rows.append(
                    {
                        "index": idx, "year": test_year, "school": test.loc[idx, "node_school"],
                        "y": int(test.loc[idx, "restructure_next"]), "model": model_name, "p": float(p),
                    }
                )
            binary_rows.append(
                {
                    "year": test_year,
                    "model": model_name,
                    "n": len(test),
                    "log_loss_bits": log_loss(test["restructure_next"], prob, labels=[0, 1]) / np.log(2),
                    "brier": brier_score_loss(test["restructure_next"], prob),
                    "roc_auc": roc_auc_score(test["restructure_next"], prob),
                    "pr_auc": average_precision_score(test["restructure_next"], prob),
                }
            )
    predictions = pd.DataFrame(prediction_rows)
    performance = pd.DataFrame(binary_rows)
    aggregate = performance.groupby("model", as_index=False).apply(
        lambda g: pd.Series(
            {
                "n_test": int(g["n"].sum()),
                "log_loss_bits": np.average(g["log_loss_bits"], weights=g["n"]),
                "brier": np.average(g["brier"], weights=g["n"]),
                "roc_auc": np.average(g["roc_auc"], weights=g["n"]),
                "pr_auc": np.average(g["pr_auc"], weights=g["n"]),
            }
        ),
        include_groups=False,
    ).reset_index(drop=True)

    pivot = predictions.pivot_table(index=["index", "year", "school", "y"], columns="model", values="p").reset_index()
    ordered_models = list(blocks)
    info_rows = []
    for before, after, label in zip(
        ordered_models[:-1], ordered_models[1:], ["size", "context", "name history"]
    ):
        y = pivot["y"].to_numpy(int)
        pb = np.where(y == 1, pivot[before], 1 - pivot[before]).clip(1e-12, 1)
        pf = np.where(y == 1, pivot[after], 1 - pivot[after]).clip(1e-12, 1)
        pointwise = np.log2(pf / pb)
        rng = np.random.default_rng(20260819)
        schools = pivot["school"].unique()
        boot = []
        for _ in range(500):
            sampled = rng.choice(schools, len(schools), replace=True)
            idx = np.concatenate([np.flatnonzero(pivot["school"].to_numpy() == school) for school in sampled])
            boot.append(pointwise[idx].mean())
        info_rows.append(
            {
                "feature_block": label,
                "incremental_bits_per_event": pointwise.mean(),
                "ci_low": np.quantile(boot, 0.025),
                "ci_high": np.quantile(boot, 0.975),
            }
        )
    return aggregate, pd.DataFrame(info_rows), predictions


def multiclass_rolling(panel: pd.DataFrame) -> pd.DataFrame:
    work = panel.copy()
    # Eight many-to-many cases are too sparse to estimate as an independent class.
    # Retain them in the descriptive taxonomy, but pool them with split for prediction.
    work["event_model"] = work["event_next"].replace({"complex": "split"})
    for col in [
        "size_delta", "school_delta_n", "school_field_entropy", "neighbor_count", "name_novelty",
        "name_token_count", "theme_entropy_proxy", "added_modifier_count_prev",
    ]:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)
    work["prev_rename"] = work["prev_rename"].astype(int)
    specs = {
        "size-only": (["year", "log_size"], ["broad"]),
        "full": (
            [
                "year", "log_size", "size_delta", "observed_age", "school_delta_n",
                "school_field_entropy", "neighbor_count", "prev_rename",
                "added_modifier_count_prev", "name_novelty", "name_token_count", "theme_entropy_proxy",
            ],
            ["broad"],
        ),
    }
    # sklearn's multiclass log-loss interprets probability columns in sorted
    # label order, so keep this list alphabetic throughout fitting/evaluation.
    classes = sorted(["continue", "close", "merge", "split"])
    rows = []
    for test_year in range(2019, YEAR_MAX):
        train, test = work[work["year"] < test_year], work[work["year"] == test_year]
        counts = train["event_model"].value_counts().reindex(classes, fill_value=0).to_numpy(float) + 0.5
        prior = counts / counts.sum()
        prior_prob = np.repeat(prior[None, :], len(test), axis=0)
        prior_pred = np.array(classes)[prior_prob.argmax(axis=1)]
        rows.append(
            {
                "year": test_year,
                "model": "empirical-prior",
                "n": len(test),
                "log_loss_bits": log_loss(test["event_model"], prior_prob, labels=classes) / np.log(2),
                "macro_f1": f1_score(test["event_model"], prior_pred, labels=classes, average="macro", zero_division=0),
                "balanced_accuracy": balanced_accuracy_score(test["event_model"], prior_pred),
            }
        )
        for name, (num, cat) in specs.items():
            model = _make_model(num, cat, multiclass=True)
            model.fit(train, train["event_model"])
            prob = _aligned_probabilities(model, test, classes)
            # Rare-event probability regularization. This prevents a handful of
            # merge/split observations from receiving effectively zero probability.
            prob = 0.90 * prob + 0.10 * prior_prob
            pred = np.array(classes)[prob.argmax(axis=1)]
            rows.append(
                {
                    "year": test_year,
                    "model": name,
                    "n": len(test),
                    "log_loss_bits": log_loss(test["event_model"], prob, labels=classes) / np.log(2),
                    "macro_f1": f1_score(test["event_model"], pred, labels=classes, average="macro", zero_division=0),
                    "balanced_accuracy": balanced_accuracy_score(test["event_model"], pred),
                }
            )
    result = pd.DataFrame(rows)
    return result.groupby("model", as_index=False).apply(
        lambda g: pd.Series(
            {
                "n_test": int(g["n"].sum()),
                "log_loss_bits": np.average(g["log_loss_bits"], weights=g["n"]),
                "macro_f1": np.average(g["macro_f1"], weights=g["n"]),
                "balanced_accuracy": np.average(g["balanced_accuracy"], weights=g["n"]),
            }
        ),
        include_groups=False,
    ).reset_index(drop=True)


def transition_matrix(nodes: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    state = nodes.set_index("uid")["size_regime"].to_dict()
    year = nodes.set_index("uid")["year"].to_dict()
    rows = []
    outdegree = edges.groupby("source").size().to_dict()
    for edge in edges.itertuples():
        if year[edge.target] != year[edge.source] + 1 or not (YEAR_MIN <= year[edge.source] < YEAR_MAX):
            continue
        source_state, target_state = state.get(edge.source), state.get(edge.target)
        if source_state in STATE_ORDER[:-1] and target_state in STATE_ORDER[:-1]:
            rows.append((source_state, target_state, 1 / outdegree.get(edge.source, 1)))
    panel_nodes = nodes[nodes["year"].between(YEAR_MIN, YEAR_MAX - 1)]
    for row in panel_nodes.itertuples():
        if row.event_next == "close" and row.size_regime in STATE_ORDER[:-1]:
            rows.append((row.size_regime, "absent", 1.0))
    frame = pd.DataFrame(rows, columns=["source", "target", "weight"])
    matrix = frame.pivot_table(index="source", columns="target", values="weight", aggfunc="sum", fill_value=0)
    matrix = matrix.reindex(index=STATE_ORDER[:-1], columns=STATE_ORDER, fill_value=0)
    return matrix.div(matrix.sum(axis=1), axis=0)


def modifier_summary(panel: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    rows = []
    for row in panel[panel["rename_next"]].itertuples():
        for token in row.added_modifiers_next:
            rows.append({"year": row.year + 1, "modifier": token, "broad": row.broad})
    additions = pd.DataFrame(rows)
    if additions.empty:
        return pd.DataFrame(columns=["year", "modifier", "count", "share"])
    top = additions["modifier"].value_counts().head(top_n).index
    result = additions[additions["modifier"].isin(top)].groupby(["year", "modifier"]).size().rename("count").reset_index()
    result["share"] = result["count"] / result.groupby("year")["count"].transform("sum")
    return result


def bd_diagnostics(nodes: pd.DataFrame, typical: pd.DataFrame) -> pd.DataFrame:
    sizes = typical["typical_size"].to_numpy(float)
    fits = []
    for name, dist in [("SLN", stats.lognorm), ("SLL", stats.fisk)]:
        params = dist.fit(sizes)
        log_likelihood = np.sum(dist.logpdf(sizes, *params))
        fits.append((2 * len(params) - 2 * log_likelihood, name, dist, params))
    _, fit_name, dist, params = min(fits, key=lambda item: item[0])
    max_size = int(min(np.quantile(sizes, 0.995), 100))
    s = np.arange(1, max_size + 1)
    q = dist.cdf(s + 0.5, *params) - dist.cdf(np.maximum(s - 0.5, 0), *params)
    q = np.clip(q, 1e-15, None); q /= q.sum()
    s_star = int(s[np.argmax(q)])
    ratio = q[1:] / q[:-1]
    anchor = ratio[max(min(s_star - 1, len(ratio) - 1), 0)]
    ratio = ratio / anchor
    result = pd.DataFrame({"s": s[:-1], "bd_ratio": ratio})
    result["fit"] = fit_name; result["s_star"] = s_star

    size_of = nodes.set_index("uid")["faculty_size"].to_dict()
    transition_rows = []
    for row in nodes[nodes["year"].between(YEAR_MIN, YEAR_MAX - 1)].itertuples():
        if row.event_next != "continue" or len(row.successors) != 1 or not (row.faculty_size > 0):
            continue
        target_size = size_of.get(row.successors[0], np.nan)
        if target_size > 0:
            transition_rows.append((int(round(row.faculty_size)), target_size - row.faculty_size))
    drift = pd.DataFrame(transition_rows, columns=["s", "delta"])
    drift = drift.groupby("s")["delta"].agg(["mean", "count"]).reset_index()
    result = result.merge(drift, on="s", how="left")
    return result


def create_figures(bundle: AnalysisBundle, output_dir: str | Path) -> None:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore", category=FutureWarning)
    sns.set_theme(style="whitegrid", context="talk")
    apple_gothic = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")
    if apple_gothic.exists():
        font_manager.fontManager.addfont(str(apple_gothic))
    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ("AppleGothic", "NanumGothic", "Malgun Gothic"):
        if candidate in available:
            matplotlib.rcParams["font.family"] = candidate
            break
    matplotlib.rcParams["axes.unicode_minus"] = False

    temporal = bundle.temporal
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2))
    for event, color in zip(["close", "merge", "split"], ["#E45756", "#9D79D6", "#F2A541"]):
        axes[0].plot(temporal["year"], temporal[event] * 100, marker="o", label=event, color=color)
    axes[0].plot(temporal["year"], temporal["rename"] * 100, marker="o", label="rename among continuations", color="#4C9F70")
    axes[0].set(title="Annual organizational-event rates", xlabel="source year", ylabel="rate (%)")
    axes[0].legend(fontsize=10)
    axes[1].bar(temporal["year"], temporal["birth_count"], color="#52D68A")
    axes[1].set(title="Observed department births", xlabel="target year", ylabel="new nodes")
    fig.tight_layout(); fig.savefig(output_dir / "fig01_temporal_events.png", dpi=180); plt.close(fig)

    hazard = bundle.panel.copy()
    hazard["xbin"] = pd.cut(
        hazard["normalized_size"], bins=[0, 0.5, 0.8, 1.2, 2, np.inf], labels=["<0.5", "0.5–0.8", "0.8–1.2", "1.2–2", ">2"]
    )
    prob = hazard.groupby(["xbin", "event_next"], observed=True).size().rename("n").reset_index()
    prob["p"] = prob["n"] / prob.groupby("xbin", observed=True)["n"].transform("sum")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.lineplot(data=prob[prob["event_next"] != "continue"], x="xbin", y="p", hue="event_next", marker="o", ax=ax)
    ax.set(title="Structural-event probability vs normalized size", xlabel=r"$s/s_f^*$", ylabel="probability")
    fig.tight_layout(); fig.savefig(output_dir / "fig02_event_hazard_size.png", dpi=180); plt.close(fig)

    info = bundle.predictive_table
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(info["feature_block"], info["incremental_bits_per_event"], color=["#4C78A8", "#F58518", "#54A24B"])
    ax.errorbar(
        info["feature_block"], info["incremental_bits_per_event"],
        yerr=[info["incremental_bits_per_event"] - info["ci_low"], info["ci_high"] - info["incremental_bits_per_event"]],
        fmt="none", color="black", capsize=5,
    )
    ax.axhline(0, color="black", lw=1)
    ax.set(title="Out-of-time predictive information gain", ylabel="incremental bits / event", xlabel="feature block")
    fig.tight_layout(); fig.savefig(output_dir / "fig03_predictive_information.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    sns.heatmap(bundle.transition_matrix, annot=True, fmt=".3f", cmap="Blues", vmin=0, vmax=1, ax=ax)
    ax.set(title="Size-state transition matrix", xlabel=r"state at $t+1$", ylabel=r"state at $t$")
    fig.tight_layout(); fig.savefig(output_dir / "fig04_transition_matrix.png", dpi=180); plt.close(fig)

    modifiers = bundle.modifier_table
    fig, ax = plt.subplots(figsize=(12, 6))
    if not modifiers.empty:
        pivot = modifiers.pivot(index="year", columns="modifier", values="count").fillna(0)
        pivot.plot(ax=ax, marker="o")
    ax.set(title="Added modifiers in department renames", xlabel="target year", ylabel="count")
    ax.legend(fontsize=9, ncol=2)
    fig.tight_layout(); fig.savefig(output_dir / "fig05_added_modifiers.png", dpi=180); plt.close(fig)

    bd = bundle.bd_table
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
    axes[0].plot(bd["s"], bd["bd_ratio"], color="#4C78A8")
    axes[0].axhline(1, ls="--", color="black")
    axes[0].axvline(bundle.summary["bd_s_star"], ls=":", color="#E45756")
    axes[0].set(xscale="log", title="Static-distribution BD rate ratio", xlabel="faculty size s", ylabel=r"normalized $a_s/b_{s+1}$")
    drift = bd[bd["count"].fillna(0) >= 20]
    axes[1].plot(drift["s"], drift["mean"], marker="o", color="#F58518")
    axes[1].axhline(0, ls="--", color="black")
    axes[1].set(xscale="log", title="Empirical drift among continuing departments", xlabel="faculty size s", ylabel=r"mean $\Delta s$")
    fig.tight_layout(); fig.savefig(output_dir / "fig06_bd_and_empirical_drift.png", dpi=180); plt.close(fig)


def export_tables(bundle: AnalysisBundle, output_dir: str | Path) -> None:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "table01_stable_ranges.csv": bundle.stable_ranges,
        "table02_temporal_events.csv": bundle.temporal,
        "table03_information_measures.csv": bundle.info_table,
        "table04_binary_prediction.csv": bundle.predictive_table,
        "table05_binary_model_performance.csv": bundle.summary["binary_performance"],
        "table06_multiclass_prediction.csv": bundle.multiclass_table,
        "table07_transition_matrix.csv": bundle.transition_matrix.reset_index(),
        "table08_added_modifiers.csv": bundle.modifier_table,
    }
    for filename, frame in tables.items():
        frame.to_csv(output_dir / filename, index=False, encoding="utf-8-sig")


def run_analysis(
    repo_root: str | Path,
    faculty_dir: str | Path,
    figure_dir: str | Path | None = None,
    table_dir: str | Path | None = None,
    n_perm: int = 200,
) -> AnalysisBundle:
    repo_root = Path(repo_root)
    nodes_raw, edges = load_alluvial(repo_root)
    nodes, panel, typical = build_panel(repo_root, faculty_dir)
    ranges = (
        typical[["broad", "n_segments", "median", "s_minus", "s_plus", "s_star"]]
        .drop_duplicates("broad")
        .sort_values("broad")
        .reset_index(drop=True)
    )
    temporal = temporal_summary(nodes, panel)
    info = information_summary(panel, n_perm=n_perm)
    binary_performance, predictive_info, predictions = rolling_predictions(panel)
    multiclass = multiclass_rolling(panel)
    matrix = transition_matrix(nodes, edges)
    modifiers = modifier_summary(panel)
    bd = bd_diagnostics(nodes, typical)
    summary = {
        "n_alluvial_nodes_2015_2025": int(nodes[nodes["year"].between(YEAR_MIN, YEAR_MAX)].shape[0]),
        "n_analysis_rows": int(len(panel)),
        "size_match_rate_all_nodes": float(
            nodes[nodes["year"].between(YEAR_MIN, YEAR_MAX)]["faculty_size"].notna().mean()
        ),
        "size_full_member_match_rate": float(
            (nodes[nodes["year"].between(YEAR_MIN, YEAR_MAX)]["size_match_score"] == 1).mean()
        ),
        "event_entropy_bits": float(shannon(panel["event_next"])),
        "restructure_rate": float(panel["restructure_next"].mean()),
        "rename_rate_among_continue": float(panel.loc[panel["event_next"] == "continue", "rename_next"].mean()),
        "markov_entropy_rate_bits": float(
            sum(
                (panel["size_regime"].value_counts(normalize=True).get(state, 0))
                * shannon(matrix.loc[state].index, matrix.loc[state].values)
                for state in matrix.index
            )
        ),
        "bd_fit": str(bd["fit"].iat[0]),
        "bd_s_star": int(bd["s_star"].iat[0]),
        "binary_performance": binary_performance,
    }
    bundle = AnalysisBundle(
        nodes=nodes,
        panel=panel,
        typical=typical,
        stable_ranges=ranges,
        temporal=temporal,
        info_table=info,
        predictive_table=predictive_info,
        multiclass_table=multiclass,
        transition_matrix=matrix,
        modifier_table=modifiers,
        bd_table=bd,
        summary=summary,
    )
    if figure_dir is not None:
        create_figures(bundle, figure_dir)
    if table_dir is not None:
        export_tables(bundle, table_dir)
    return bundle
