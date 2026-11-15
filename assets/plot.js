const plotTip = document.getElementById("tip");

function positionPlotTip(event) {
  const margin = 10;
  const box = plotTip.getBoundingClientRect();
  plotTip.style.left = Math.max(margin, Math.min(event.clientX + 14, innerWidth - box.width - margin)) + "px";
  plotTip.style.top = Math.max(margin, Math.min(event.clientY + 14, innerHeight - box.height - margin)) + "px";
}

const chartViewport = document.getElementById("wrap");
if (chartViewport) {
  const chart = document.getElementById("svg");
  let scale = 1;
  let drag;

  function updateZoom(next, x, y) {
    const width = Number(chart.getAttribute("width"));
    const height = Number(chart.getAttribute("height"));
    if (!width || !height) return;
    const ratio = next / scale;
    const left = (chartViewport.scrollLeft + x) * ratio - x;
    const top = (chartViewport.scrollTop + y) * ratio - y;
    scale = next;
    chart.style.width = `${width * scale}px`;
    chart.style.height = `${height * scale}px`;
    chartViewport.scrollTo(left, top);
  }

  chartViewport.addEventListener("chart-render", () => {
    updateZoom(scale, 0, 0);
    chartViewport.scrollTo(0, 0);
  });

  document.querySelectorAll("[data-chart-zoom]").forEach(button => {
    button.addEventListener("click", () => {
      const action = button.dataset.chartZoom;
      const next = action === "reset" ? 1 : action === "in" ? scale * 1.25 : scale / 1.25;
      updateZoom(Math.max(.4, Math.min(3, next)), chartViewport.clientWidth / 2, chartViewport.clientHeight / 2);
      if (action === "reset") chartViewport.scrollTo(0, 0);
    });
  });

  chartViewport.addEventListener("wheel", event => {
    if (!event.ctrlKey && !event.metaKey) return;
    event.preventDefault();
    const bounds = chartViewport.getBoundingClientRect();
    const next = scale * (event.deltaY < 0 ? 1.15 : 1 / 1.15);
    updateZoom(Math.max(.4, Math.min(3, next)), event.clientX - bounds.left, event.clientY - bounds.top);
  }, {passive: false});

  chart.addEventListener("pointerdown", event => {
    if (event.pointerType !== "mouse" || event.button !== 0 || event.target.closest("[data-id]")) return;
    drag = {x: event.clientX, y: event.clientY, left: chartViewport.scrollLeft, top: chartViewport.scrollTop};
    chartViewport.setPointerCapture(event.pointerId);
    chartViewport.classList.add("drag");
  });
  chartViewport.addEventListener("pointermove", event => {
    if (!drag) return;
    chartViewport.scrollTo(drag.left + drag.x - event.clientX, drag.top + drag.y - event.clientY);
  });
  chartViewport.addEventListener("lostpointercapture", () => {
    drag = null;
    chartViewport.classList.remove("drag");
  });
}

function dismissPlotTip() {
  if (plotTip.style.display !== "block") return;
  if (typeof hideTip === "function") hideTip();
  else plotTip.style.display = "none";
}

document.addEventListener("keydown", event => {
  if (event.key === "Escape") dismissPlotTip();
});
document.addEventListener("pointerdown", event => {
  if (!event.target.closest("[data-id], #grid circle")) dismissPlotTip();
});
