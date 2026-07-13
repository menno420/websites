/* "Should I build it?" rubric scorer (ORDER 022 item 4, venture WEBSITE-IDEA
 * batch-2 intake) — vanilla JS, no deps, zero network.
 *
 * Everything here is presentation over the committed rubric data: the axes,
 * weights, verdict bands, and thresholds are parsed from the page's
 * #rubric-config JSON (single-sourced from botsite/data/rubric.json — this
 * file never re-declares a weight or threshold). The weighted total is
 * computed exactly the way venture-lab's intakes show it (sum of
 * weight·score, arithmetic displayed so a reviewer can recompute it), and
 * the verdict text is the rubric's own band wording. Output is rendered via
 * textContent only (never markup injection), and nothing is sent anywhere.
 */
(function () {
  "use strict";
  var cfgEl = document.getElementById("rubric-config");
  if (!cfgEl) return;
  var cfg;
  try {
    cfg = JSON.parse(cfgEl.textContent || "{}");
  } catch (e) {
    return;
  }
  if (!cfg.axes || !cfg.axes.length || !cfg.bands || !cfg.bands.length) return;

  var totalEl = document.getElementById("rubric-total");
  var verdictEl = document.getElementById("rubric-verdict");
  var arithEl = document.getElementById("rubric-arithmetic");
  var weakestEl = document.getElementById("rubric-weakest");

  function fmt(n) {
    // Trim float noise: 3.5500000000000003 -> "3.55".
    return (Math.round(n * 100) / 100).toFixed(2);
  }

  function bandFor(total) {
    // Bands are ordered by ascending max; the last band has max: null (open
    // top). A total lands in the first band whose max it stays under —
    // boundaries follow the rubric's own ranges ("below ~3.0" / "3.0–3.5" /
    // "above 3.5"), so an exact 3.0 reads as 3.0–3.5 and an exact 3.5 does too.
    for (var i = 0; i < cfg.bands.length; i++) {
      var b = cfg.bands[i];
      if (b.max === null || b.max === undefined) return b;
      if (i === 0 ? total < b.max : total <= b.max) return b;
    }
    return cfg.bands[cfg.bands.length - 1];
  }

  function readScores() {
    var scores = [];
    for (var i = 0; i < cfg.axes.length; i++) {
      var axis = cfg.axes[i];
      var input = document.getElementById("score-" + axis.id);
      if (!input) return null; // template/config drift: fail silent, page still informs
      var value = parseFloat(input.value);
      if (isNaN(value)) value = 0;
      scores.push({ axis: axis, value: value });
      var out = document.getElementById("out-" + axis.id);
      if (out) out.textContent = String(value);
    }
    return scores;
  }

  function recompute() {
    var scores = readScores();
    if (!scores) return;
    var total = 0;
    var products = [];
    var terms = [];
    for (var i = 0; i < scores.length; i++) {
      var w = scores[i].axis.weight;
      var v = scores[i].value;
      total += w * v;
      terms.push(w.toFixed(2) + "·" + v);
      products.push(fmt(w * v));
    }
    // The anti-gaming rules demand the arithmetic be shown so a reviewer can
    // recompute it — same shape as the kit's worked example.
    if (arithEl) {
      arithEl.textContent =
        terms.join(" + ") + " = " + products.join(" + ") + " = " + fmt(total);
    }
    if (totalEl) totalEl.textContent = fmt(total);
    var band = bandFor(total);
    if (verdictEl) {
      verdictEl.textContent =
        band.range + " — " + band.label + (band.caveat ? ", " + band.caveat : "");
    }
    // Rule 3: the two lowest scores are the honest ones.
    if (weakestEl) {
      var sorted = scores.slice().sort(function (a, b) { return a.value - b.value; });
      weakestEl.textContent =
        "Your two lowest scores — the honest ones (rule 3): " +
        sorted[0].axis.name + " (" + sorted[0].value + ") and " +
        sorted[1].axis.name + " (" + sorted[1].value + "). " +
        "Copy them into “Why this might fail” in plain words.";
    }
  }

  for (var i = 0; i < cfg.axes.length; i++) {
    var input = document.getElementById("score-" + cfg.axes[i].id);
    if (input) input.addEventListener("input", recompute);
  }
  recompute();
})();
