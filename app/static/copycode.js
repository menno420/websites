// copycode.js — copy-to-clipboard buttons on every code block (ORDER 005,
// /environments). Attaches one small "copy" button to each <pre> inside a
// card (both raw code files and fenced blocks inside rendered markdown), so
// the owner can lift a setup script or env-var schema in one click. Vanilla
// JS, no dependency; degrades silently where the Clipboard API is missing
// (non-secure context / old browser) by leaving the plain selectable text.
(function () {
  "use strict";
  if (!navigator.clipboard || !window.isSecureContext) return;

  document.querySelectorAll(".card pre").forEach(function (pre) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.textContent = "copy";
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(pre.textContent).then(
        function () {
          btn.textContent = "copied ✓";
          setTimeout(function () { btn.textContent = "copy"; }, 2000);
        },
        function () {
          btn.textContent = "copy failed";
          setTimeout(function () { btn.textContent = "copy"; }, 2000);
        }
      );
    });
    var wrap = document.createElement("div");
    wrap.className = "copywrap";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(btn);
    wrap.appendChild(pre);
  });
})();
