import fs from "node:fs";
import path from "node:path";

const ROOTS = ["apex-mobile-python-console-v161", "apex-rightschain-manifest-builder"];
const HOUSE_LINE_LIMIT = 400;
const TEXT_EXTENSIONS = new Set([".html", ".js", ".mjs", ".css"]);
const IGNORED_DIRS = new Set([".git", ".github", "node_modules", "vendor", "dist", "coverage", "playwright-report"]);

const RULES = [
  { id: "inline-html-event-handler", level: "error", extensions: new Set([".html"]), re: /\son[a-z]+\s*=/i, message: "Inline HTML event handlers are disallowed. Use addEventListener()." },
  { id: "executable-inline-script", level: "error", extensions: new Set([".html"]), re: /<script\b(?![^>]*\btype=["'](?:importmap|application\/json|application\/ld\+json)["'])[^>]*>[\s\S]*?<\/script>/i, message: "Executable inline script blocks are disallowed. Keep executable JavaScript in external files." },
  { id: "dynamic-script-injection", level: "warn", extensions: new Set([".js", ".mjs", ".html"]), re: /document\s*\.\s*createElement\s*\(\s*["']script["']\s*\)/, message: "Dynamic script injection found. It must stay reviewed and isolated." },
  { id: "dangerous-dynamic-code", level: "error", extensions: new Set([".js", ".mjs", ".html"]), re: /\b(eval|Function)\s*\(/, message: "Dynamic code execution is disallowed." },
  { id: "document-write", level: "error", extensions: new Set([".js", ".mjs", ".html"]), re: /document\s*\.\s*write\s*\(/, message: "document.write() is disallowed." },
  { id: "clipboard-api", level: "warn", extensions: new Set([".js", ".mjs"]), re: /navigator\s*\.\s*clipboard\s*\./, message: "Clipboard use requires secure-context guard and manual-copy fallback." },
  { id: "blob-url-download", level: "warn", extensions: new Set([".js", ".mjs"]), re: /URL\s*\.\s*createObjectURL\s*\(/, message: "Blob URL downloads must be user-triggered and revoked after click propagation." }
];

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (IGNORED_DIRS.has(entry.name) || entry.name.startsWith(".")) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (TEXT_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) out.push(full);
  }
  return out;
}

let failed = false;
let warnings = 0;
let scanned = 0;

for (const root of ROOTS) {
  for (const file of walk(root)) {
    scanned += 1;
    const ext = path.extname(file).toLowerCase();
    const text = fs.readFileSync(file, "utf8");
    const lineCount = text.split(/\r?\n/).length;

    if (lineCount > HOUSE_LINE_LIMIT) {
      console.error(`[error] ${file}: ${lineCount} lines exceeds ${HOUSE_LINE_LIMIT}-line reviewed-source limit.`);
      failed = true;
    }

    for (const rule of RULES) {
      if (!rule.extensions.has(ext) || !rule.re.test(text)) continue;
      const msg = `[${rule.level}] ${file}: ${rule.message}`;
      if (rule.level === "error") { console.error(msg); failed = true; }
      else { console.warn(msg); warnings += 1; }
    }
  }
}

console.log(`[content-scan] scanned=${scanned}; warnings=${warnings}; failed=${failed}`);
if (failed) process.exit(1);
