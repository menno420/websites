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
