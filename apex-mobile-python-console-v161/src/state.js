(function(){
  const KEY = "apex_v161_notebook";
  window.APEX_STATE = {
    storageOK(){
      try{
        const key = "apex_v161_storage_test";
        localStorage.setItem(key,"ok");
        const ok = localStorage.getItem(key)==="ok";
        localStorage.removeItem(key);
        return ok;
      }catch(e){ return false; }
    },
    saveNotebook(notebook){
      try{
        const safe = {
          cells: notebook.cells,
          active: notebook.active,
          nextId: notebook.nextId,
          history: (notebook.history || []).slice(0,20),
          savedAt: new Date().toISOString()
        };
        localStorage.setItem(KEY, JSON.stringify(safe));
        return {ok:true};
      }catch(e){
        return {ok:false,error:e.message || String(e)};
      }
    },
    loadNotebook(){
      try{
        const raw = localStorage.getItem(KEY);
        return raw ? {ok:true,data:JSON.parse(raw)} : {ok:false,error:"No saved notebook"};
      }catch(e){ return {ok:false,error:e.message || String(e)}; }
    },
    clear(){
      try{ localStorage.removeItem(KEY); return {ok:true}; }
      catch(e){ return {ok:false,error:e.message || String(e)}; }
    }
  };
})();
