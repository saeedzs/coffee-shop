/* Product detail pop-up.
   Tap a card to open it; swipe, arrow keys or the buttons move between items;
   Esc, the ✕, the dark area, or the phone's Back button close it.
   Every product has its own link (…/menu/tea/#p12), so an item can be shared. */
(() => {
  const dialog = document.getElementById("product-dialog");
  const cards = Array.from(document.querySelectorAll("[data-product]"));
  // Old browsers without <dialog>: the cards simply stay as they are.
  if (!dialog || !cards.length || typeof dialog.showModal !== "function") return;

  const $ = (selector) => dialog.querySelector(selector);
  const idOf = (i) => cards[i].dataset.product;
  let index = -1;
  let pushed = false;     // did we add a history entry, so Back can close the dialog?
  let fromPop = false;    // is the dialog being closed by the Back button?

  // Fill the dialog from the card on the page (copies, never raw HTML strings).
  function fill(card) {
    const media = $(".pd-media");
    media.classList.toggle("sold-out", card.classList.contains("sold-out"));
    const img = card.querySelector("img").cloneNode(true);
    img.loading = "eager";
    const marks = Array.from(card.querySelectorAll(".pbadge, .ribbon, .soldout-label"), (el) => el.cloneNode(true));
    media.replaceChildren(img, ...marks);

    $("#pd-name").textContent = card.querySelector(".card-open").textContent.trim();
    const category = card.querySelector(".tag");
    $(".pd-category").textContent = category ? category.textContent : "";
    $(".pd-ingredients").textContent = card.querySelector(".ingredients").textContent.trim();
    $(".pd-diet").replaceChildren(...Array.from(card.querySelectorAll(".diet .chip"), (c) => c.cloneNode(true)));
    $(".pd-prices").replaceChildren(card.querySelector(".prices").cloneNode(true));

    $(".pd-counter").textContent = `${index + 1} of ${cards.length}`;
    $(".pd-prev").disabled = index === 0;
    $(".pd-next").disabled = index === cards.length - 1;
    $(".pd-info").scrollTop = 0;
  }

  function show(i) {
    index = i;
    fill(cards[i]);
    if (!dialog.open) dialog.showModal();
  }

  function openByTap(i) {
    show(i);
    history.pushState({ pd: true }, "", "#p" + idOf(i));
    pushed = true;
  }

  function step(delta) {
    const next = index + delta;
    if (next < 0 || next >= cards.length) return;
    show(next);
    history.replaceState(history.state, "", "#p" + idOf(next));   // same history entry
  }

  function openFromHash() {
    const match = location.hash.match(/^#p(\d+)$/);
    if (!match) return false;
    const i = cards.findIndex((c) => c.dataset.product === match[1]);
    if (i < 0) return false;
    show(i);
    return true;
  }

  // --- wiring ---
  cards.forEach((card, i) => card.querySelector(".card-open").addEventListener("click", () => openByTap(i)));
  $(".pd-close").addEventListener("click", () => dialog.close());
  $(".pd-prev").addEventListener("click", () => step(-1));
  $(".pd-next").addEventListener("click", () => step(1));

  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });   // the dark area
  dialog.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });

  // Swipe left / right on touch screens
  let startX = null;
  dialog.addEventListener("touchstart", (e) => { startX = e.touches[0].clientX; }, { passive: true });
  dialog.addEventListener("touchend", (e) => {
    if (startX === null) return;
    const dx = e.changedTouches[0].clientX - startX;
    startX = null;
    if (Math.abs(dx) > 70) step(dx < 0 ? 1 : -1);
  }, { passive: true });

  // Closing: undo the history entry we added (or just clear the #p12 from the address)
  dialog.addEventListener("close", () => {
    if (fromPop) { fromPop = false; pushed = false; return; }
    if (pushed) { pushed = false; history.back(); }
    else if (/^#p\d+$/.test(location.hash)) history.replaceState(null, "", location.pathname + location.search);
  });

  // Back / Forward buttons
  window.addEventListener("popstate", () => {
    if (dialog.open && !(history.state && history.state.pd)) {
      fromPop = true;
      dialog.close();
    } else if (!dialog.open && openFromHash()) {
      pushed = !!(history.state && history.state.pd);
    }
  });

  // Page opened with a product link
  openFromHash();
})();
