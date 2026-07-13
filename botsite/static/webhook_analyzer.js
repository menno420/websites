/* Webhook payload analyzer (ORDER 022 item 4 SCAN AND INITIATE — the last
 * venture WEBSITE-IDEA batch-2 marker, "webhook-payload analyzer") —
 * vanilla JS, no deps, ZERO network.
 *
 * The privacy property IS the feature: everything happens in this tab.
 * This file performs no network I/O of any kind and holds no state beyond
 * the page. All provider knowledge (detection markers, signature guidance,
 * id prefixes, field notes) is parsed from the page's
 * #webhook-analyzer-config JSON — single-sourced from
 * botsite/data/webhook_analyzer.json; this file never re-declares a
 * provider claim. Output is rendered via createElement + textContent only
 * (never markup injection), so pasted payload content can never become
 * markup.
 *
 * Honesty rules: provider detection is reported with its evidence and
 * never as a certainty; field classifications are inferred-only (epoch
 * ranges, id shapes) and labeled as inferences; anything else is
 * "unknown". Signature guidance renders with its source line, including
 * the downgraded not-verified-this-session pointer for Discord.
 */
(function () {
  "use strict";
  var cfgEl = document.getElementById("webhook-analyzer-config");
  if (!cfgEl) return;
  var cfg;
  try {
    cfg = JSON.parse(cfgEl.textContent || "{}");
  } catch (e) {
    return;
  }
  if (!cfg.providers || !cfg.providers.length) return;

  var input = document.getElementById("wa-input");
  var results = document.getElementById("wa-results");
  var analyzeBtn = document.getElementById("wa-analyze");
  var sampleBtn = document.getElementById("wa-sample");
  if (!input || !results || !analyzeBtn || !sampleBtn) return;

  var MAX_DEPTH = 6;
  var MAX_FIELDS = 500;

  /* ------------------------------------------------------------------ *
   * DOM helpers — textContent only.
   * ------------------------------------------------------------------ */
  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    if (attrs) {
      for (var k in attrs) {
        if (Object.prototype.hasOwnProperty.call(attrs, k)) {
          node.setAttribute(k, attrs[k]);
        }
      }
    }
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function card(title) {
    var c = el("article", { "class": "sb-card", "style": "margin:0 0 14px;padding:16px" });
    c.appendChild(el("h2", { "style": "margin:0 0 6px" }, title));
    return c;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  /* ------------------------------------------------------------------ *
   * Provider detection — marker predicates keyed provider.id + marker.id.
   * The markers' human wording lives in the config; this registry is only
   * the executable shape check for each. A config marker with no predicate
   * here is skipped (drift-tolerant, never a crash).
   * ------------------------------------------------------------------ */
  function isObj(v) {
    return v !== null && typeof v === "object" && !Array.isArray(v);
  }

  var PREDICATES = {
    "stripe/object-event": function (b) { return b.object === "event"; },
    "stripe/type-string": function (b) { return typeof b.type === "string" && b.type.length > 0; },
    "stripe/data-object": function (b) { return isObj(b.data) && b.data.object !== undefined; },
    "stripe/evt-id": function (b) { return typeof b.id === "string" && b.id.indexOf("evt_") === 0; },
    "stripe/livemode": function (b) { return typeof b.livemode === "boolean"; },
    "github/action-repo-sender": function (b) {
      return typeof b.action === "string" && isObj(b.repository) && isObj(b.sender);
    },
    "github/push-shape": function (b) {
      return typeof b.ref === "string" && Array.isArray(b.commits) && isObj(b.repository);
    },
    "github/ping-shape": function (b) {
      return typeof b.zen === "string" && b.hook_id !== undefined;
    },
    "discord/type-numeric": function (b) { return typeof b.type === "number"; },
    "discord/application-id": function (b) { return typeof b.application_id === "string"; },
    "discord/token": function (b) { return typeof b.token === "string"; },
    "discord/id": function (b) { return typeof b.id === "string"; }
  };

  function detect(body) {
    if (!isObj(body)) return null;
    var best = null;
    for (var i = 0; i < cfg.providers.length; i++) {
      var p = cfg.providers[i];
      var matched = [];
      var known = 0;
      for (var j = 0; j < p.markers.length; j++) {
        var m = p.markers[j];
        var pred = PREDICATES[p.id + "/" + m.id];
        if (!pred) continue; // config drift: unknown marker, skip honestly
        known++;
        if (pred(body)) matched.push(m);
      }
      if (!matched.length) continue;
      var matchedIds = {};
      for (var k = 0; k < matched.length; k++) matchedIds[matched[k].id] = true;
      // strong_markers nonempty: strong iff ALL of them matched.
      // strong_markers empty (GitHub — each marker is a complete event
      // shape): strong iff ANY marker matched.
      var strong;
      if (p.strong_markers && p.strong_markers.length) {
        strong = p.strong_markers.every(function (id) { return matchedIds[id]; });
      } else {
        strong = matched.length > 0;
      }
      var candidate = {
        provider: p,
        matched: matched,
        total: known,
        strong: strong
      };
      if (!best
          || (candidate.strong && !best.strong)
          || (candidate.strong === best.strong
              && candidate.matched.length > best.matched.length)) {
        best = candidate;
      }
    }
    if (best && !best.strong && best.matched.length < 2) return null;
    return best;
  }

  function detectionText(d) {
    var evidence = d.matched.map(function (m) { return m.label; }).join("; ");
    if (d.strong) {
      return "Looks like " + d.provider.name + " (matched: " + evidence + ")";
    }
    return "Possibly " + d.provider.name + " (matched " + d.matched.length
      + " of " + d.total + " markers: " + evidence + ")";
  }

  /* ------------------------------------------------------------------ *
   * Field walk — depth- and count-capped, inference-only classification.
   * ------------------------------------------------------------------ */
  var ISO_RE = /^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/;
  var UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  var SNOWFLAKE_RE = /^\d{17,}$/;
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  var URL_RE = /^https?:\/\/\S+$/;
  // 2001-01-01T00:00:00Z .. 9999999999s (~2286) — the plausible-epoch window.
  var EPOCH_MIN_S = 978307200;
  var EPOCH_MAX_S = 9999999999;

  function idPrefixLabel(s) {
    for (var i = 0; i < cfg.providers.length; i++) {
      var prefixes = cfg.providers[i].id_prefixes || {};
      for (var pref in prefixes) {
        if (Object.prototype.hasOwnProperty.call(prefixes, pref)
            && s.indexOf(pref) === 0) {
          return prefixes[pref] + " (prefix " + pref + ", inferred)";
        }
      }
    }
    return null;
  }

  function jsonType(v) {
    if (v === null) return "null";
    if (Array.isArray(v)) return "array";
    return typeof v;
  }

  function classify(v) {
    if (v === null) return "null";
    if (typeof v === "boolean") return "boolean (" + v + ")";
    if (typeof v === "number") {
      if (Number.isInteger(v) && v >= EPOCH_MIN_S && v <= EPOCH_MAX_S) {
        return "epoch timestamp (inferred): " + new Date(v * 1000).toISOString();
      }
      if (Number.isInteger(v) && v >= EPOCH_MIN_S * 1000 && v <= EPOCH_MAX_S * 1000) {
        return "epoch timestamp, milliseconds (inferred): " + new Date(v).toISOString();
      }
      return "unknown";
    }
    if (typeof v === "string") {
      if (ISO_RE.test(v)) return "ISO-8601 date/time";
      var prefixed = idPrefixLabel(v);
      if (prefixed) return prefixed;
      if (UUID_RE.test(v)) return "UUID";
      if (SNOWFLAKE_RE.test(v)) return "possible snowflake id (unverified)";
      if (EMAIL_RE.test(v)) return "email-shaped string";
      if (URL_RE.test(v)) return "URL";
      return "unknown";
    }
    if (Array.isArray(v)) return "array (" + v.length + " items)";
    if (isObj(v)) return "object (" + Object.keys(v).length + " keys)";
    return "unknown";
  }

  function walk(value, path, depth, rows, state) {
    if (state.truncated) return;
    if (rows.length >= MAX_FIELDS) { state.truncated = "field cap (" + MAX_FIELDS + " fields)"; return; }
    rows.push({ path: path || "(root)", type: jsonType(value), cls: classify(value) });
    if (!isObj(value) && !Array.isArray(value)) return;
    if (depth >= MAX_DEPTH) {
      state.truncated = "depth cap (" + MAX_DEPTH + " levels)";
      return;
    }
    if (Array.isArray(value)) {
      for (var i = 0; i < value.length; i++) {
        walk(value[i], (path || "") + "[" + i + "]", depth + 1, rows, state);
        if (state.truncated) return;
      }
      return;
    }
    var keys = Object.keys(value);
    for (var j = 0; j < keys.length; j++) {
      var key = keys[j];
      walk(value[key], path ? path + "." + key : key, depth + 1, rows, state);
      if (state.truncated) return;
    }
  }

  /* ------------------------------------------------------------------ *
   * Field notes — provider gotchas surfaced only when the pasted payload
   * really exhibits them. Conditions keyed provider.id + note.id.
   * ------------------------------------------------------------------ */
  var NOTE_CONDITIONS = {
    "stripe/customer-email-null": function (b) {
      return isObj(b.data) && isObj(b.data.object)
        && b.data.object.customer_email === null;
    },
    "stripe/success-url-placeholder": function (b) {
      return isObj(b.data) && isObj(b.data.object)
        && typeof b.data.object.success_url === "string"
        && b.data.object.success_url.indexOf("{") !== -1;
    }
  };

  /* ------------------------------------------------------------------ *
   * Rendering.
   * ------------------------------------------------------------------ */
  function sourceLine(container, line) {
    var p = el("p", { "class": "sb-muted", "style": "margin:0 0 8px;font-size:var(--sb-text-xs)" });
    p.appendChild(document.createTextNode("Source: " + line.source_label));
    if (line.source_url) {
      p.appendChild(document.createTextNode(" — "));
      var a = el("a", { href: line.source_url, target: "_blank", rel: "noopener" },
                 line.source_url);
      p.appendChild(a);
    }
    container.appendChild(p);
  }

  function renderParseError(err, text) {
    var c = card("Could not parse that as JSON");
    c.appendChild(el("p", { "style": "margin:0 0 6px" },
      "The analyzer only reads JSON, and this input is not valid JSON. The parser said:"));
    c.appendChild(el("p", { "class": "sb-mono", "style": "margin:0 0 6px;overflow-x:auto" },
      String(err && err.message ? err.message : err)));
    var m = /position (\d+)/.exec(String(err && err.message || ""));
    if (m) {
      var pos = parseInt(m[1], 10);
      var start = Math.max(0, pos - 30);
      c.appendChild(el("p", { "class": "sb-muted", "style": "margin:0;font-size:var(--sb-text-sm)" },
        "Around position " + pos + ": …" + text.slice(start, pos + 30) + "…"));
    }
    results.appendChild(c);
  }

  function renderDetection(d) {
    var c = card("Provider detection");
    if (d) {
      c.appendChild(el("p", { "style": "margin:0 0 6px" }, detectionText(d)));
      c.appendChild(el("p", { "class": "sb-muted", "style": "margin:0;font-size:var(--sb-text-sm)" },
        "Shape-based inference only — a matching shape is evidence, never proof of origin."));
    } else {
      c.appendChild(el("p", { "style": "margin:0" },
        "Unrecognized — generic analysis only. The body shape matched no known provider's markers."));
    }
    results.appendChild(c);
  }

  function renderFieldTable(rows, truncated) {
    var c = card("Field walk (" + rows.length + " fields)");
    if (truncated) {
      c.appendChild(el("p", { "class": "sb-muted", "style": "margin:0 0 8px;font-size:var(--sb-text-sm)" },
        "Truncated at the " + truncated + " — the table below is a partial walk."));
    }
    var wrap = el("div", { "style": "overflow-x:auto" });
    var table = el("table", { "style": "width:100%;font-size:var(--sb-text-sm);border-collapse:collapse" });
    var thead = el("thead", null);
    var hr = el("tr", null);
    ["Path", "JSON type", "Classification"].forEach(function (h) {
      hr.appendChild(el("th", { "style": "text-align:left;padding:4px 10px 4px 0" }, h));
    });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = el("tbody", null);
    rows.forEach(function (r) {
      var tr = el("tr", null);
      tr.appendChild(el("td", { "class": "sb-mono", "style": "padding:2px 10px 2px 0;vertical-align:top" }, r.path));
      tr.appendChild(el("td", { "style": "padding:2px 10px 2px 0;vertical-align:top" }, r.type));
      tr.appendChild(el("td", { "style": "padding:2px 0;vertical-align:top" }, r.cls));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    c.appendChild(wrap);
    results.appendChild(c);
  }

  function renderGuidance(d, body) {
    if (!d) {
      if (cfg.generic && cfg.generic.header_reminder) {
        var g = card("Signature verification");
        g.appendChild(el("p", { "style": "margin:0" }, cfg.generic.header_reminder));
        results.appendChild(g);
      }
      return;
    }
    var p = d.provider;
    var c = card("Signature verification — " + p.name);
    if (p.signature.header) {
      c.appendChild(el("p", { "style": "margin:0 0 8px" },
        "Signature header: " + p.signature.header + " (an HTTP header — it is NOT in this pasted body)."));
    }
    p.signature.lines.forEach(function (line) {
      c.appendChild(el("p", { "style": "margin:0 0 2px" }, line.text));
      sourceLine(c, line);
    });
    if (cfg.generic && cfg.generic.header_reminder) {
      c.appendChild(el("p", { "class": "sb-muted", "style": "margin:6px 0 0;font-size:var(--sb-text-sm)" },
        cfg.generic.header_reminder));
    }
    results.appendChild(c);

    var notes = (p.field_notes || []).filter(function (n) {
      var cond = NOTE_CONDITIONS[p.id + "/" + n.id];
      return cond ? cond(body) : false;
    });
    if (notes.length) {
      var nc = card("Field notes for this payload");
      notes.forEach(function (n) {
        nc.appendChild(el("p", { "style": "margin:0 0 2px" }, n.text));
        sourceLine(nc, n);
      });
      results.appendChild(nc);
    }
  }

  function analyze() {
    clear(results);
    var text = input.value;
    if (!text || !text.trim()) {
      var c = card("Nothing to analyze");
      c.appendChild(el("p", { "style": "margin:0" },
        "Paste a webhook JSON payload above, or load the sample."));
      results.appendChild(c);
      return;
    }
    var body;
    try {
      body = JSON.parse(text);
    } catch (err) {
      renderParseError(err, text);
      return;
    }
    var d = detect(body);
    renderDetection(d);
    var rows = [];
    var state = { truncated: null };
    walk(body, "", 0, rows, state);
    renderFieldTable(rows, state.truncated);
    renderGuidance(d, body);
  }

  /* SYNTHETIC sample — a Stripe checkout.session.completed skeleton with
   * obviously-fake TESTsample ids, built so the customer_email-null gotcha
   * and the classifications demo instantly. Not a real event. */
  var SAMPLE = {
    "_note": "SYNTHETIC sample payload — not a real Stripe event",
    "id": "evt_TESTsample00000000000001",
    "object": "event",
    "created": 1784332800,
    "livemode": false,
    "type": "checkout.session.completed",
    "data": {
      "object": {
        "id": "cs_TESTsample00000000000001",
        "object": "checkout.session",
        "created": 1784332740,
        "customer": "cus_TESTsample0001",
        "customer_email": null,
        "customer_details": { "email": "buyer@example.com" },
        "payment_intent": "pi_TESTsample0001",
        "amount_total": 2900,
        "currency": "usd",
        "livemode": false,
        "success_url": "https://example.com/thanks?session_id={CHECKOUT_SESSION_ID}"
      }
    }
  };

  analyzeBtn.addEventListener("click", analyze);
  sampleBtn.addEventListener("click", function () {
    input.value = JSON.stringify(SAMPLE, null, 2);
    analyze();
  });
})();
