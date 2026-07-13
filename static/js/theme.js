
(function(){
  const drawer = document.getElementById("menuDrawer");
  const openBtn = document.getElementById("openMenu");
  const closeBtn = document.getElementById("closeMenu");
  const backdrop = document.getElementById("drawerBackdrop");

  function open(){
    if(!drawer) return;
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden","false");
  }
  function close(){
    if(!drawer) return;
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden","true");
  }

  if(openBtn) openBtn.addEventListener("click", open);
  if(closeBtn) closeBtn.addEventListener("click", close);
  if(backdrop) backdrop.addEventListener("click", close);

  document.addEventListener("keydown", (e)=>{
    if(e.key === "Escape") close();
  });
})();
