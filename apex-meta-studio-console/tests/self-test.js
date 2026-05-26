(() => {
  const $ = (id) => document.getElementById(id);
  const out = $("out");
  const overall = $("overall");
  let lastReport = null;

  function pass(name, detail = "") { return { name, ok: true, detail }; }
  function fail(name, detail = "") { return { name, ok: false, detail }; }

  function miniRun(code) {
    const lines = String(code || "").split(/\r?\n/);
    const output = [];
    const funcs = {
      add: (a, b) => Number(a) + Number(b),
      reverse: (s) => String(s).split("").reverse().join("")
    };
    const safeEval = (expr) => {
      const trimmed = String(expr || "").trim();
      if (/^['"].*['"]$/.test(trimmed)) return trimmed.slice(1, -1);
      if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);
      const call = trimmed.match(/^([a-zA-Z_]\w*)\((.*)\)$/);
      if (call && funcs[call[1]]) {
        const args = splitArgs(call[2]).map(safeEval);
        return funcs[call[1]](...args);
      }
      const addParts = splitOutsideStrings(trimmed, "+");
      if (addParts.length > 1) return addParts.map(safeEval).reduce((a, b) => a + b, 0);
      return trimmed;
    };
    function splitArgs(s) { return splitOutsideStrings(s, ",").map(x => x.trim()).filter(Boolean); }
    function splitOutsideStrings(s, sep) {
      const res = []; let cur = ""; let q = null; let esc = false;
      for (const ch of String(s)) {
        if (esc) { cur += ch; esc = false; continue; }
        if (ch === "\\") { cur += ch; esc = true; continue; }
        if ((ch === "'" || ch === '"') && !q) { q = ch; cur += ch; continue; }
        if (ch === q) { q = null; cur += ch; continue; }
        if (ch === sep && !q) { res.push(cur); cur = ""; continue; }
        cur += ch;
      }
      res.push(cur); return res;
    }
    for (const raw of lines) {
      const line = raw.trim();
      if (!line || line.startsWith("#")) continue;
      const m = line.match(/^print\((.*)\)$/);
      if (m) output.push(String(safeEval(m[1])));
      else output.push(String(safeEval(line)));
    }
    return output.join("\n");
  }

  async function sha256(text) {
    if (!crypto || !crypto.subtle) throw new Error("crypto.subtle unavailable; use HTTPS/GitHub Pages/RawGithack, not file://");
    const bytes = new TextEncoder().encode(text);
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(hash)].map(b => b.toString(16).padStart(2, "0")).join("");
  }

  function storageOK() {
    const key = "apex_self_test_probe";
    try { localStorage.setItem(key, "ok"); return localStorage.getItem(key) === "ok"; }
    finally { try { localStorage.removeItem(key); } catch (_) {} }
  }

  async function runTests() {
    const tests = [];
    tests.push(pass("JavaScript boot", "self-test.js executed"));
    try { tests.push(storageOK() ? pass("localStorage probe cleanup", "probe write/read/remove succeeded") : fail("localStorage probe cleanup", "read mismatch")); }
    catch (e) { tests.push(fail("localStorage probe cleanup", e.message)); }
    tests.push(window.isSecureContext ? pass("Secure context", "required for clipboard/crypto") : fail("Secure context", "open through HTTPS host"));
    try {
      const h = await sha256("APEX");
      tests.push(h.length === 64 ? pass("SHA-256 hashing", h) : fail("SHA-256 hashing", "bad hash length"));
    } catch (e) { tests.push(fail("SHA-256 hashing", e.message)); }
    try {
      const result = miniRun('print("Hello World")\nprint("5+5")\nadd(5,7)\nreverse("APEX")');
      const expected = 'Hello World\n5+5\n12\nXEPA';
      tests.push(result === expected ? pass("Mini parser string safety", result) : fail("Mini parser string safety", `expected ${expected} got ${result}`));
    } catch (e) { tests.push(fail("Mini parser string safety", e.message)); }
    try {
      const manifest = { app: "APEX Meta Studio Console", version: "0.3-self-test", generated_at: new Date().toISOString(), source: location.href };
      const mh = await sha256(JSON.stringify(manifest));
      tests.push(pass("Manifest hash generation", mh));
    } catch (e) { tests.push(fail("Manifest hash generation", e.message)); }

    const ok = tests.every(t => t.ok);
    lastReport = { ok, time: new Date().toISOString(), url: location.href, userAgent: navigator.userAgent, tests };
    overall.textContent = ok ? "PASS" : "CHECK";
    overall.className = "pill " + (ok ? "good" : "bad");
    out.textContent = JSON.stringify(lastReport, null, 2);
  }

  async function copyReport() {
    if (!lastReport) await runTests();
    const text = JSON.stringify(lastReport, null, 2);
    try { await navigator.clipboard.writeText(text); }
    catch (_) {
      const t = document.createElement("textarea");
      t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove();
    }
  }

  function downloadReport() {
    if (!lastReport) return;
    const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "apex-console-self-test-report.json";
    document.body.appendChild(a); a.click();
    setTimeout(() => { a.remove(); URL.revokeObjectURL(url); }, 0);
  }

  $("runTests").addEventListener("click", runTests);
  $("copyReport").addEventListener("click", copyReport);
  $("downloadReport").addEventListener("click", downloadReport);
})();
