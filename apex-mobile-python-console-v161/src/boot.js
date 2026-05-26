(function(){
  document.addEventListener("DOMContentLoaded", function(){
    if(!window.APEX_NOTEBOOK){
      document.body.innerHTML = '<pre style="color:white;background:#111;padding:20px">APEX boot failed: notebook module missing.</pre>';
      return;
    }
    APEX_NOTEBOOK.bind();
    APEX_NOTEBOOK.boot();
  });
})();
