"""Render the common analysis layout and page-specific chart markup."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYOUT = HERE / "viewer_layout.html"
PAGES = {
    "alluvial": (
        "alluvial", "학과 계보",
        "대학별 학과의 신설·통합·분리·폐지 흐름을 2014–2026년 자료로 살펴봅니다.",
        "노드를 선택하면 해당 학과의 연도, 계열, 전공 수와 학과 상태를 확인할 수 있습니다.",
        (
            ("노드 높이", "학과·학부에 묶인 전공 수입니다. 대계열을 선택하면 차트에 학과명이 표시됩니다."),
            ("연도 간 연결", "리본은 학과코드·명칭·소계열을 바탕으로 추정한 연결입니다. 신설·통합·분리·폐지는 공시된 학과 상태입니다."),
            ("대학 간 통합", "흡수된 대학의 학과는 아래쪽에 따로 표시되고, 통합 연도에 본교로 연결됩니다."),
        ),
    ),
    "faculty": (
        "alluvial", "전임교원 계보",
        "2015–2025년 학과 계보에서 전임교원 규모가 어떻게 달라졌는지 살펴봅니다.",
        "노드를 선택하면 전임교원 수와 값의 출처를 확인할 수 있습니다.",
        (
            ("노드 높이", "전임교원 수입니다. 회색 노드는 교원 수가 미상인 학과입니다."),
            ("관측과 추정", "상세에서 공시 관측값, 계보 추정값, 미상 여부를 확인할 수 있습니다. 결과 요약의 교원 합계에는 관측값과 추정값이 포함됩니다."),
            ("연도 범위", "전임교원 자료가 있는 2015–2025년을 표시합니다."),
        ),
    ),
    "namesplit": (
        "namesplit", "학과명 분화",
        "2014–2026년 전국 대학에서 같은 소계열의 학과명이 어떻게 이어지고 갈라졌는지 살펴봅니다.",
        "노드를 선택하면 해당 연도에 같은 이름을 사용한 대학 수와 학교 예시를 확인할 수 있습니다.",
        (
            ("계열 선택", "대계열, 중계열, 소계열 순서로 범위를 좁힙니다."),
            ("노드와 연결", "노드 높이는 같은 이름을 쓰는 대학 수입니다. 대각선 리본은 이름이 바뀌거나 갈라진 연결을 표시합니다."),
            ("연도별 학과 수", "작은 막대 차트는 계열에 포함된 전체 학과 수를 보여줍니다. 학과명 흐름 차트는 표시 기준에 맞는 명칭을 사용합니다."),
        ),
    ),
    "keywords": (
        "keywords", "학과명 키워드 추이",
        "2014–2026년 학과명에 등장한 키워드의 빈도와 변화를 연도별로 비교합니다.",
        "차트의 원을 선택하면 해당 연도 빈도, 초기·최근 평균과 학과명 예시를 확인할 수 있습니다.",
        (
            ("원의 크기", "해당 연도에 키워드가 학과명에 등장한 횟수입니다. 원이 없는 해는 등장 횟수가 0건입니다."),
            ("급상승·급하락", "최근 3년 평균에서 초기 3년 평균을 뺀 값입니다. 순위에서 키워드를 선택하면 차트의 해당 행이 강조됩니다."),
            ("집계 대상", "신설 학과와 활성 학과를 전환해 학과명에 쓰이는 키워드가 어떻게 다른지 비교할 수 있습니다."),
        ),
    ),
}
NAV = {"alluvial": "DEPARTMENT", "faculty": "FACULTY", "namesplit": "NAMES", "keywords": "KEYWORDS"}


def render_viewer(page, payload=None):
    template, title, subtitle, detail, guide = PAGES[page]
    source = (HERE / f"{template}_template.html").read_text(encoding="utf-8")
    parts = dict(re.findall(r"<!-- (filters|chart|script) -->\n(.*?)\n<!-- /\1 -->", source, re.S))
    values = {
        "PAGE_TITLE": title, "PAGE_SUB": subtitle, "DETAIL_INSTRUCTION": detail,
        "GUIDE": "\n".join(f"          <div><dt>{label}</dt><dd>{text}</dd></div>" for label, text in guide),
        **{key.upper(): value for key, value in parts.items()},
        **{f"{key}_CURRENT": ' aria-current="page"' if name == page else "" for name, key in NAV.items()},
    }
    if template == "alluvial":
        mode = "ft" if page == "faculty" else "msz"
        values["SCRIPT"] = values["SCRIPT"].replace("__SIZE_MODE__", mode)
    if page == "keywords":
        values["SCRIPT"] = values["SCRIPT"].replace("/*__DATA__*/", payload)
    return re.sub(r"__([A-Z_]+)__", lambda match: values[match[1]], LAYOUT.read_text(encoding="utf-8"))
