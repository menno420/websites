/* Page-level wiring for the bot site. Depends on ds.js (window.SBDS).
   - hydrates chrome (theme toggle, mobile drawer, command palette bindings)
   - loads the command-palette index from /palette.json
   - client-side filter/search for the Features and Commands pages (progressive
     enhancement: the full list is server-rendered; JS only hides non-matches). */
(function () {
  "use strict";
  if (!window.SBDS) return;
  SBDS.initChrome();

  // Command palette index (pages + features + games + commands).
  fetch("/palette.json")
    .then(function (r) { return r.ok ? r.json() : []; })
    .then(function (items) { SBDS.palette.register(items); })
    .catch(function () { /* palette simply stays empty on failure */ });

  // ── generic filter: pills toggle a category; a search box matches text ──
  function wireFilter(root) {
    var pills = root.querySelectorAll("[data-filter-pill]");
    var search = root.querySelector("[data-filter-search]");
    var items = root.querySelectorAll("[data-filter-item]");
    var countEl = root.querySelector("[data-filter-count]");
    var active = "all";

    function apply() {
      var q = (search && search.value || "").trim().toLowerCase();
      var shown = 0;
      items.forEach(function (el) {
        var catOk = active === "all" || el.getAttribute("data-cat") === active;
        var hay = (el.getAttribute("data-search") || "").toLowerCase();
        var qOk = !q || hay.indexOf(q) !== -1;
        var show = catOk && qOk;
        el.style.display = show ? "" : "none";
        if (show) shown++;
      });
      if (countEl) countEl.textContent = shown;
      var empty = root.querySelector("[data-filter-empty]");
      if (empty) empty.style.display = shown ? "none" : "";
    }

    pills.forEach(function (p) {
      p.addEventListener("click", function () {
        active = p.getAttribute("data-filter-pill");
        pills.forEach(function (o) { o.setAttribute("aria-pressed", String(o === p)); });
        apply();
      });
    });
    if (search) search.addEventListener("input", apply);
    apply();
  }

  document.querySelectorAll("[data-filter-root]").forEach(wireFilter);
})();
