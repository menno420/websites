/* Page-level wiring for the review site. Depends on ds.js (window.SBDS).
   ds.js only DEFINES the chrome helpers — nothing works until a page script
   calls SBDS.initChrome() (the botsite/dashboard static/app.js idiom). This
   hydrates the theme toggle, the mobile nav drawer + hamburger icon, and the
   "/" / Ctrl-K command palette bindings. The review service is network-free
   at runtime, so instead of the siblings' /palette.json fetch the palette is
   fed from the server-rendered primary nav (progressive enhancement: every
   page works fully without this file). */
(function () {
  "use strict";
  // The grouped navigation changes height as its rows wrap. Native fragment
  // navigation needs that actual height, including after a viewport resize.
  var nav = document.querySelector(".sb-nav");
  if (nav) {
    var syncNavOffset = function () {
      document.documentElement.style.setProperty(
        "--rv-nav-offset", Math.ceil(nav.getBoundingClientRect().height) + 16 + "px"
      );
    };
    syncNavOffset();
    if (window.ResizeObserver) new ResizeObserver(syncNavOffset).observe(nav);
  }
  if (!window.SBDS) return;
  SBDS.initChrome();

  var pages = [];
  document.querySelectorAll(".sb-nav-links .sb-nav-link").forEach(function (a) {
    pages.push({
      group: "Pages",
      label: (a.textContent || "").trim(),
      href: a.getAttribute("href"),
    });
  });
  SBDS.palette.register(pages);
})();
