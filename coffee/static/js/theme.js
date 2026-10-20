const root = document.documentElement;
const btn = document.getElementById("theme-toggle");

function apply(theme) {
  root.dataset.theme = theme;
  if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
}

apply(currentTheme());

if (btn) {
  btn.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    try {
      localStorage.setItem("themeOverride", JSON.stringify({ theme: next, at: Date.now() }));
    } catch (e) { /* storage blocked (private mode): the choice just won't be remembered */ }
    apply(next);
  });
}

// Re-check every minute so the switch happens live at the set hour
setInterval(() => {
  const t = currentTheme();
  if (t !== root.dataset.theme) apply(t);
}, 60000);
