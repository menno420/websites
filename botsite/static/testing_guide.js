/* Guided-walkthrough side panel (ORDER 018 PR3) — vanilla JS, no deps.
 *
 * Two progressive enhancements over the plain-form step flow:
 *  1. chat with the AI guide (JSON POST, replies rendered via textContent —
 *     never innerHTML, so model/tester text can't become markup), and
 *  2. OPT-IN screen awareness: getDisplayMedia → periodic canvas frames →
 *     JPEG (quality/scale capped client-side) → multipart POST. Frames are
 *     analyzed server-side in memory and discarded — nothing is recorded.
 *     Capture pauses while this tab is hidden and stops on stop-sharing,
 *     the Stop button, or submitting the walkthrough.
 */
(function () {
  "use strict";
  var cfg = document.getElementById("guide-ai-config");
  if (!cfg || cfg.dataset.aiAvailable !== "1") return;

  var chatUrl = cfg.dataset.chatUrl;
  var frameUrl = cfg.dataset.frameUrl;
  var step = parseInt(cfg.dataset.step || "0", 10) || 0;
  var frameMax = parseInt(cfg.dataset.frameMax || "1500000", 10) || 1500000;

  var log = document.getElementById("guide-chat-log");
  var input = document.getElementById("guide-chat-input");
  var sendBtn = document.getElementById("guide-chat-send");

  function addMsg(who, text, muted) {
    if (!log) return;
    var p = document.createElement("p");
    p.style.marginTop = "6px";
    if (muted) p.className = "sb-hint";
    var b = document.createElement("strong");
    b.textContent = who + ": ";
    p.appendChild(b);
    p.appendChild(document.createTextNode(text)); // escaped by construction
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }

  function postJSON(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "same-origin",
    }).then(function (res) { return res.json(); });
  }

  function sendChat() {
    if (!input) return;
    var msg = (input.value || "").trim();
    if (!msg) return;
    input.value = "";
    addMsg("you", msg);
    postJSON(chatUrl, { message: msg, step: step })
      .then(function (data) {
        addMsg("guide", data.reply || "(no reply)", !data.ok);
      })
      .catch(function () {
        addMsg("guide", "Network hiccup — try again.", true);
      });
  }
  if (sendBtn) sendBtn.addEventListener("click", sendChat);
  if (input) {
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); sendChat(); }
    });
  }

  // ---- screen awareness (opt-in) -------------------------------------------
  var startBtn = document.getElementById("guide-share-start");
  var askBtn = document.getElementById("guide-share-ask");
  var stopBtn = document.getElementById("guide-share-stop");
  var status = document.getElementById("guide-share-status");
  if (!startBtn) return;

  var stream = null;
  var timer = null;
  var video = document.createElement("video");
  video.muted = true;
  var busy = false;
  var INTERVAL_MS = 15000;

  function setStatus(text) { if (status) status.textContent = text; }

  function encodeFrame(cb) {
    if (!stream || video.videoWidth === 0) return;
    var scale = Math.min(1, 1280 / video.videoWidth); // cap width → small payloads
    var canvas = document.createElement("canvas");
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(function (blob) {
      if (blob && blob.size > frameMax) {
        canvas.toBlob(function (smaller) { if (smaller && smaller.size <= frameMax) cb(smaller); }, "image/jpeg", 0.3);
      } else if (blob) {
        cb(blob);
      }
    }, "image/jpeg", 0.6);
  }

  function sendFrame(manual) {
    if (!stream || busy) return;
    if (document.hidden) return; // never capture while this tab is hidden
    busy = true;
    encodeFrame(function (blob) {
      var fd = new FormData();
      fd.append("frame", blob, "frame.jpg");
      fd.append("step", String(step));
      fetch(frameUrl, { method: "POST", body: fd, credentials: "same-origin" })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          busy = false;
          if (data.reply) addMsg("guide (screen)", data.reply, !data.ok);
          if (data.degraded) stopShare("The AI guide became unavailable — sharing stopped.");
        })
        .catch(function () { busy = false; });
    });
    if (manual) setStatus("Asked the guide about the current screen.");
  }

  function startTimer() {
    if (timer === null && stream) timer = window.setInterval(function () { sendFrame(false); }, INTERVAL_MS);
  }
  function haltTimer() {
    if (timer !== null) { window.clearInterval(timer); timer = null; }
  }

  function stopShare(msg) {
    haltTimer();
    if (stream) {
      stream.getTracks().forEach(function (t) { t.stop(); });
      stream = null;
    }
    video.srcObject = null;
    if (askBtn) askBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;
    startBtn.disabled = false;
    setStatus(msg || "Sharing stopped. Nothing is being captured.");
  }

  startBtn.addEventListener("click", function () {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
      setStatus("Your browser doesn't support screen sharing here — the steps and chat still work.");
      return;
    }
    navigator.mediaDevices.getDisplayMedia({ video: true, audio: false })
      .then(function (s) {
        stream = s;
        video.srcObject = s;
        video.play();
        startBtn.disabled = true;
        if (askBtn) askBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = false;
        setStatus("Sharing is ON — a frame goes to the AI guide about every 15 s while this tab is visible.");
        startTimer();
        s.getVideoTracks()[0].addEventListener("ended", function () { stopShare(); });
      })
      .catch(function () {
        setStatus("Screen sharing was cancelled — nothing was captured.");
      });
  });

  if (askBtn) askBtn.addEventListener("click", function () { sendFrame(true); });
  if (stopBtn) stopBtn.addEventListener("click", function () { stopShare(); });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      haltTimer(); // capture stops while the tab is hidden
    } else if (stream) {
      startTimer();
    }
  });

  // Finishing (or navigating) the walkthrough ends capture.
  var form = document.getElementById("guide-step-form");
  if (form) form.addEventListener("submit", function () { stopShare(); });
  window.addEventListener("pagehide", function () { stopShare(); });
})();
