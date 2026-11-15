const numberFormat = new Intl.NumberFormat("ko-KR");
const resultMetrics = document.getElementById("result-metrics");
const detailsContent = document.getElementById("details-content");
const detailInstruction = detailsContent.textContent;
const activeSectionLinks = [...document.querySelectorAll(".krds-in-page-navigation-type a")];

function setActiveSection(id) {
  for (const link of activeSectionLinks) {
    if (link.hash === id) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  }
}

for (const link of activeSectionLinks) {
  link.addEventListener("click", () => setActiveSection(link.hash));
}

let sectionFrame = 0;
function trackAnalysisSection() {
  if (sectionFrame) return;
  sectionFrame = requestAnimationFrame(() => {
    sectionFrame = 0;
    const active = activeSectionLinks.filter(link =>
      document.getElementById(link.hash.slice(1)).getBoundingClientRect().top < 120
    ).at(-1) || activeSectionLinks[0];
    setActiveSection(active.hash);
  });
}
window.addEventListener("scroll", trackAnalysisSection, {passive: true});
trackAnalysisSection();

function updateAnalysisResult(title, context, metrics = []) {
  document.getElementById("result-title").textContent = title;
  document.getElementById("info").textContent = context;
  resultMetrics.replaceChildren(...metrics.map(([label, value]) => {
    const item = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    item.append(term, description);
    return item;
  }));
  resultMetrics.hidden = metrics.length === 0;
}

function resetPlotDetails() {
  const text = document.createElement("p");
  text.textContent = detailInstruction;
  detailsContent.replaceChildren(text);
  const selected = document.querySelector("#svg .is-selected");
  selected?.classList.remove("is-selected");
  selected?.setAttribute("aria-pressed", "false");
}

function plotSearchFeedback(term, count) {
  const message = document.getElementById("search-feedback");
  message.hidden = !term;
  message.textContent = !term ? "" : count
    ? `‘${term}’ 검색 결과 · 일치 노드 ${numberFormat.format(count)}개`
    : `‘${term}’와 일치하는 노드가 없습니다.`;
}

function plotSearchJump(input) {
  input.addEventListener("keydown", event => {
    if (event.key !== "Enter" || event.isComposing || !input.value.trim()) return;
    event.preventDefault();
    const match = document.querySelector("#svg [data-match]");
    if (!match) return;
    focusPlotTarget(match);
    match.dispatchEvent(new MouseEvent("click", {bubbles: true}));
  });
}

function focusPlotTarget(target) {
  const current = target.ownerSVGElement.querySelector("[data-plot-target][tabindex='0']");
  current?.setAttribute("tabindex", "-1");
  target.setAttribute("tabindex", "0");
  target.focus();
}

function configurePlotTarget(target, label, show) {
  target.dataset.plotTarget = "";
  target.setAttribute("role", "button");
  target.setAttribute("aria-label", label);
  target.setAttribute("aria-pressed", "false");
  target.setAttribute("tabindex", "-1");

  function inspect(event) {
    const bounds = target.getBoundingClientRect();
    const point = event.detail
      ? event
      : {clientX: bounds.right, clientY: bounds.top};
    show(point);

    const selected = target.ownerSVGElement.querySelector(".is-selected");
    selected?.classList.remove("is-selected");
    selected?.setAttribute("aria-pressed", "false");
    target.classList.add("is-selected");
    target.setAttribute("aria-pressed", "true");
    detailsContent.replaceChildren(...[...document.getElementById("tip").children].map(node => node.cloneNode(true)));
  }

  target.addEventListener("focus", () => {
    const current = target.ownerSVGElement.querySelector("[data-plot-target][tabindex='0']");
    if (current !== target) {
      current?.setAttribute("tabindex", "-1");
      target.setAttribute("tabindex", "0");
    }
  });
  target.addEventListener("click", inspect);
  target.addEventListener("keydown", event => {
    const steps = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1};
    const step = steps[event.key];
    if (step) {
      const nodes = [...target.ownerSVGElement.querySelectorAll("[data-plot-target]:not(.dim)")];
      const index = nodes.indexOf(target);
      if (index < 0) return;
      event.preventDefault();
      focusPlotTarget(nodes[Math.max(0, Math.min(nodes.length - 1, index + step))]);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      inspect(event);
      document.getElementById("chart-details").focus();
    }
  });
}

function enableFirstPlotTarget() {
  const nodes = document.querySelectorAll("#svg [data-plot-target]");
  for (const node of nodes) node.setAttribute("tabindex", "-1");
  const firstVisible = [...nodes].find(node => !node.classList.contains("dim"));
  firstVisible?.setAttribute("tabindex", "0");
}
