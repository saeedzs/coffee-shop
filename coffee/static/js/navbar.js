/* Navbar helpers
   1. The row of category links shows a soft fade when more links are hidden off-screen,
      and starts scrolled so the current page is visible.
   2. On phones the bar slides away while reading down and comes back on scrolling up. */
(() => {
  const navbar = document.querySelector(".navbar");
  if (!navbar) return;                                   // the welcome page has no navbar
  const links = navbar.querySelector(".nav-links");
  const phone = window.matchMedia("(max-width: 800px)");

  // ---- 1. links row ----
  function updateFade() {
    links.classList.toggle("has-more", links.scrollLeft + links.clientWidth < links.scrollWidth - 2);
  }
  const active = links.querySelector(".active");
  if (active) {                                          // bring the current page's link into view
    const a = active.getBoundingClientRect();
    const c = links.getBoundingClientRect();
    links.scrollLeft += (a.left - c.left) - (c.width - a.width) / 2;
  }
  updateFade();
  links.addEventListener("scroll", updateFade, { passive: true });
  window.addEventListener("resize", updateFade);

  // ---- 2. hide while reading down (phones only) ----
  let lastY = window.scrollY;
  let waiting = false;
  const show = () => navbar.classList.remove("navbar-hidden");
  const hide = () => navbar.classList.add("navbar-hidden");

  function onScroll() {
    waiting = false;
    const y = window.scrollY;
    const delta = y - lastY;
    const typing = navbar.contains(document.activeElement) && document.activeElement.matches("input");

    if (!phone.matches || y < 80 || typing) show();      // desktop, top of page, or typing in search
    else if (delta > 8) hide();
    else if (delta < -8) show();

    if (Math.abs(delta) > 8 || y < 80) lastY = y;        // small slow scrolls add up until they count
  }

  window.addEventListener("scroll", () => {
    if (!waiting) { waiting = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  navbar.addEventListener("focusin", show);              // keyboard users tabbing into the bar
  phone.addEventListener("change", show);
})();
