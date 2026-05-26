(function(){
  const fileStore = Object.create(null);
  window.APEX_FILES = {
    async addFromFileList(inputFiles){
      const results = [];
      for(const file of inputFiles){
        try{
          const text = await file.text();
          fileStore[file.name] = text;
          results.push({name:file.name, chars:text.length, ok:true});
        }catch(e){ results.push({name:file.name, ok:false, error:e.message || String(e)}); }
      }
      return results;
    },
    names(){ return Object.keys(fileStore); },
    read(name){ return Object.prototype.hasOwnProperty.call(fileStore,name) ? fileStore[name] : ""; },
    snapshot(){ return Object.assign({}, fileStore); },
    clear(){ for(const k of Object.keys(fileStore)) delete fileStore[k]; },
    metadata(){ return Object.keys(fileStore).map(name => ({name, chars:fileStore[name].length})); }
  };
})();
