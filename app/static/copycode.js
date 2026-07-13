// copycode.js — copy-to-clipboard buttons on every code block (ORDER 005,
// /environments; reused by the /projects/{package} dispatch screen). Attaches
// one small "copy" button to each <pre> inside a card (raw code files, full
// role-file prompt blocks, and fenced blocks inside rendered markdown), so
// the owner can lift a setup script or a coordinator prompt in one click.
// Vanilla JS, no dependency, no external asset. navigator.clipboard is the
// primary path; a hidden-textarea document.execCommand("copy") fallback
// covers non-secure contexts / older browsers; where neither exists the
// script degrades silently, leaving the plain selectable text.
(function () {
  "use strict";
  var hasAsync = !!(navigator.clipboard && window.isSecureContext);
  var hasExec = !!(
    document.queryCommandSupported && document.queryCommandSupported("copy")
  );
  if (!hasAsync && !hasExec) return;

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (e) {
      ok = false;
    }
    document.body.removeChild(ta);
    return ok;
  }

  // pre.nocopy = deliberately not copy-ready (a do-not-paste historical
  // file on /prompts) — no button; the text stays plain and selectable.
  document.querySelectorAll(".card pre:not(.nocopy)").forEach(function (pre) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.textContent = "copy";
    btn.addEventListener("click", function () {
      var done = function (ok) {
        btn.textContent = ok ? "copied ✓" : "copy failed";
        setTimeout(function () { btn.textContent = "copy"; }, 2000);
      };
      if (hasAsync) {
        navigator.clipboard.writeText(pre.textContent).then(
          function () { done(true); },
          function () { done(fallbackCopy(pre.textContent)); }
        );
      } else {
        done(fallbackCopy(pre.textContent));
      }
    });
    var wrap = document.createElement("div");
    wrap.className = "copywrap";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(btn);
    wrap.appendChild(pre);
  });
})();
