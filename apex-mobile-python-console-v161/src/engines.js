(function(){
  let pyodide = null;
  let pyLoading = null;
  function loadScript(src){
    return new Promise((resolve,reject)=>{
      const s=document.createElement("script");
      s.src=src; s.async=true;
      s.onload=resolve;
      s.onerror=()=>reject(new Error("Script failed: "+src));
      document.head.appendChild(s);
    });
  }
  async function loadPyodideEngine(log){
    if(pyodide) return {ok:true};
    if(pyLoading) return pyLoading;
    pyLoading = (async()=>{
      try{
        if(!window.loadPyodide){ await loadScript("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"); }
        pyodide = await loadPyodide({
          indexURL:"https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
        });
        if(log) log("Pyodide loaded");
        return {ok:true};
      }catch(e){ pyLoading=null; return {ok:false,error:e.message || String(e)}; }
    })();
    return pyLoading;
  }
  async function runPyodide(code){
    const loaded = await loadPyodideEngine();
    if(!loaded.ok) return {engine:"pyodide", ok:false, text:"PYODIDE LOAD ERROR: "+loaded.error};
    const out = [];
    pyodide.setStdout({batched:s=>out.push(String(s))});
    pyodide.setStderr({batched:s=>out.push("STDERR: "+String(s))});
    try{
      pyodide.globals.set("apex_files", APEX_FILES.snapshot());
      const result = await pyodide.runPythonAsync(code);
      let text = out.join("\n");
      if(result !== undefined && result !== null) text += (text ? "\n" : "") + String(result);
      return {engine:"pyodide", ok:true, text:text || "(no output)"};
    }catch(e){
      return {engine:"pyodide", ok:false, text:"PYODIDE ERROR:\n"+(e && e.stack ? e.stack : String(e))};
    }
  }
  window.APEX_ENGINES = {
    loadPyodide: loadPyodideEngine,
    async run(code, preferred){
      if(preferred === "pyodide") return runPyodide(code);
      return APEX_MINI.run(code);
    },
    status(){ return {pyodide: !!pyodide}; }
  };
})();
