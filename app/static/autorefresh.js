/* Live-monitoring auto-refresh — the board (/) and /fleet only.
 *
 * Soft, in-place refresh with NO full-page reload and NO duplicated render
 * logic: every interval it re-fetches the CURRENT page over HTTP and swaps only
 * the server-rendered `#live-content` region into the DOM. The server stays the
 * single source of rendered truth, so the refreshed content is always correct
 * and always matches a hard reload — we just avoid the flash and the scroll
 * jump. The fetch omits `?refresh=1`, so it rides the server's TTL cache (it
 * never hammers the GitHub API on the owner's behalf).
 *
 * Unobtrusive by contract: a visible "auto-refreshing every Ns · last updated
 * <time>" indicator with a pause/resume toggle (persisted in localStorage);
 * polling pauses while the tab is hidden and while a fetch is already in
 * flight; a transient network error keeps the prior content and retries next
 * tick. `prefers-reduced-motion` is honored in CSS (the pulse dot stops).
 */
(function () {
  "use strict";

  var root = document.querySelector("[data-autorefresh]");
  if (!root) return;

  var interval = parseInt(root.getAttribute("data-autorefresh"), 10);
  if (!interval || interval < 5) interval = 45;

  var target = document.getElementById("live-content");
  var statusEl = document.getElementById("ar-status");
  var toggleEl = document.getElementById("ar-toggle");
  var updatedEl = document.getElementById("ar-updated");
  var STORE_KEY = "autorefresh-paused";
  var timer = null;
  var inFlight = false;

  function isPaused() {
    try {
      return window.localStorage.getItem(STORE_KEY) === "1";
    } catch (e) {
      return false;
    }
  }

  function setPaused(v) {
    try {
      window.localStorage.setItem(STORE_KEY, v ? "1" : "0");
    } catch (e) {
      /* private mode / storage disabled — pause is session-only, fine */
    }
  }

  function stampNow() {
    if (!updatedEl) return;
    var d = new Date();
    updatedEl.textContent = d.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    updatedEl.setAttribute("datetime", d.toISOString());
  }

  function refresh() {
    if (inFlight || isPaused() || document.hidden || !target) return;
    inFlight = true;
    fetch(window.location.pathname + window.location.search, {
      headers: { "X-Requested-With": "autorefresh" },
      cache: "no-store",
      credentials: "same-origin",
    })
      .then(function (res) {
        if (!res.ok) throw new Error("http " + res.status);
        return res.text();
      })
      .then(function (text) {
        var doc = new DOMParser().parseFromString(text, "text/html");
        var fresh = doc.getElementById("live-content");
        if (fresh) {
          target.innerHTML = fresh.innerHTML;
          stampNow();
        }
      })
      .catch(function () {
        /* transient — keep the prior content and try again next tick */
      })
      .finally(function () {
        inFlight = false;
      });
  }

  function start() {
    if (!timer) timer = window.setInterval(refresh, interval * 1000);
  }

  function stop() {
    if (timer) {
      window.clearInterval(timer);
      timer = null;
    }
  }

  function render() {
    if (isPaused()) {
      if (statusEl) statusEl.textContent = "auto-refresh paused";
      if (toggleEl) {
        toggleEl.textContent = "resume";
        toggleEl.setAttribute("aria-pressed", "true");
      }
      if (root) root.classList.add("is-paused");
      stop();
    } else {
      if (statusEl)
        statusEl.textContent = "auto-refreshing every " + interval + "s";
      if (toggleEl) {
        toggleEl.textContent = "pause";
        toggleEl.setAttribute("aria-pressed", "false");
      }
      if (root) root.classList.remove("is-paused");
      start();
    }
  }

  if (toggleEl) {
    toggleEl.addEventListener("click", function () {
      setPaused(!isPaused());
      render();
    });
  }

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && !isPaused()) refresh();
  });

  stampNow();
  render();
})();
