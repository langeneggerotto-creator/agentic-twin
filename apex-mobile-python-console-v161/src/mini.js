(function(){
  function isQuote(ch){ return ch === String.fromCharCode(34) || ch === String.fromCharCode(39); }
  function splitArgs(s){
    const args = [];
    let cur = "";
    let quote = null;
    for(let i=0;i<s.length;i++){
      const ch = s[i];
      const escaped = i > 0 && s.charCodeAt(i-1) === 92;
      if(isQuote(ch) && !escaped){
        quote = quote === ch ? null : (quote || ch);
        cur += ch;
        continue;
      }
      if(ch === "," && !quote){
        args.push(cur.trim());
        cur = "";
        continue;
      }
      cur += ch;
    }
    if(cur.trim()) args.push(cur.trim());
    return args;
  }

  function run(src){
    const vars = Object.create(null);
    const out = [];
    const errs = [];
    const lines = String(src || "").split(/\r?\n/);

    function val(expr){
      expr = expr.trim();
      let m = expr.match(/^[\"'](.*?)[\"']$/);
      if(m) return m[1];
      if(expr === "files()") return APEX_FILES.names().join(", ");
      m = expr.match(/^read\(([\"'])(.*?)\1\)$/);
      if(m) return APEX_FILES.read(m[2]);
      if(/^-?\d+(\.\d+)?$/.test(expr)) return Number(expr);
      if(Object.prototype.hasOwnProperty.call(vars, expr)) return vars[expr];
      m = expr.match(/^(.+?)\s*\+\s*(.+)$/); if(m) return val(m[1]) + val(m[2]);
      m = expr.match(/^(.+?)\s*-\s*(.+)$/); if(m) return val(m[1]) - val(m[2]);
      m = expr.match(/^(.+?)\s*\*\s*(.+)$/); if(m) return val(m[1]) * val(m[2]);
      m = expr.match(/^(.+?)\s*\/\s*(.+)$/); if(m) return val(m[1]) / val(m[2]);
      throw new Error("Unsupported expression: " + expr);
    }

    for(let i=0;i<lines.length;i++){
      const line = lines[i].trim();
      if(!line || line.startsWith("#")) continue;
      try{
        let m = line.match(/^([a-zA-Z_]\w*)\s*=\s*(.+)$/);
        if(m){ vars[m[1]] = val(m[2]); continue; }
        m = line.match(/^print\((.*)\)$/);
        if(m){ out.push(splitArgs(m[1]).map(x => String(val(x))).join(" ")); continue; }
        errs.push("Skipped line " + (i+1) + ": " + line);
      }catch(e){
        errs.push("Line " + (i+1) + ": " + (e.message || String(e)));
      }
    }
    return {
      engine: "mini",
      ok: out.length > 0 && errs.length === 0,
      text: out.join("\n") + (errs.length ? "\n\n[Mini limitations]\n" + errs.join("\n") : "")
    };
  }

  window.APEX_MINI = { run };
})();
