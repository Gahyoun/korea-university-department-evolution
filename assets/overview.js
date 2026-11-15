async function showCoverage() {
  const response = await fetch("manifest.json", {cache: "no-cache"});
  if (!response.ok) return;

  const manifest = await response.json();
  const years = manifest.source?.coverage_years;
  if (years?.length === 2) {
    document.querySelector('[data-stat="years"]').textContent = years.join("–");
  }

  for (const key of ["schools", "active_dept_records", "namesplit_subs"]) {
    const value = manifest.stats?.[key];
    if (!Number.isFinite(value)) continue;
    const stat = document.querySelector(`[data-stat="${key}"]`);
    stat.firstChild.textContent = value.toLocaleString("ko-KR");
  }

  if (manifest.data_version && manifest.built_at) {
    document.getElementById("data-version").textContent =
      `데이터 버전 ${manifest.data_version} · 빌드 ${manifest.built_at.slice(0, 10)}`;
  }
}

showCoverage().catch(() => {});
