const modeSelect = document.getElementById("screen-mode");
const modeKey = "department-display-mode";
const screenModes = ["light", "high-contrast", "theme"];

function applyMode(mode) {
  document.documentElement.dataset.krdsMode = mode;
  modeSelect.value = mode;
}

try {
  const stored = localStorage.getItem(modeKey);
  if (screenModes.includes(stored)) applyMode(stored);
} catch {
  // Screen settings still work for the current page when storage is unavailable.
}

modeSelect.addEventListener("change", () => {
  applyMode(modeSelect.value);
  try { localStorage.setItem(modeKey, modeSelect.value); } catch {}
});

const menuButton = document.querySelector(".btn-navi");
const navigation = document.getElementById("primary-nav");
const compactMenu = matchMedia("(max-width: 767px)");

function setMenu(open) {
  navigation.hidden = !open;
  menuButton.setAttribute("aria-expanded", String(open));
}

function fitMenu() {
  menuButton.hidden = !compactMenu.matches;
  setMenu(!compactMenu.matches);
}

menuButton.addEventListener("click", () => setMenu(navigation.hidden));
document.getElementById("krds-header").addEventListener("keydown", event => {
  if (event.key === "Escape" && compactMenu.matches && !navigation.hidden) {
    setMenu(false);
    menuButton.focus();
  }
});
compactMenu.addEventListener("change", fitMenu);
fitMenu();
