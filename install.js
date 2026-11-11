// "Get the app" for the Live Reggae Music website (website only; added to every page by tools/build_pages.py).
// - A permanent "Get the app" button at the top of the page.
//     Android / desktop Chrome & Edge: opens the browser's real install window.
//     iPhone (Safari, Chrome, Edge, Firefox on iOS 16.4+): Apple doesn't let a site add itself,
//     so it shows the two Share-menu steps instead.
// - A one-time tip at the bottom on phones, until dismissed (✕) or installed.
// Everything hides once the site is opened from the home-screen icon.
(function(){
  var KEY="rl-install-dismissed";
  function dismissed(){try{return localStorage.getItem(KEY)==="1"}catch(e){return false}}
  function remember(){try{localStorage.setItem(KEY,"1")}catch(e){}}
  var standalone=matchMedia("(display-mode: standalone)").matches||navigator.standalone===true;
  if(standalone)return;
  var ua=navigator.userAgent, ios=/iPhone|iPad|iPod/.test(ua)||(/Macintosh/.test(ua)&&navigator.maxTouchPoints>1),
      iosOther=/CriOS|FxiOS|EdgiOS/.test(ua), deferred=null;
  var SHARE='<svg width="14" height="16" viewBox="0 0 13 15" aria-hidden="true" style="vertical-align:-2px"><path d="M6.5 1v9M3 4l3.5-3L10 4M1.5 7v6.5h10V7" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';
  var css='<style>'+
    '.llapp{justify-self:start;display:inline-flex;align-items:center;gap:8px;font:600 14px/1 var(--body,system-ui,sans-serif);color:var(--ink,#F4F1E1);'+
      'background:var(--chip,#1A2C22);border:1.5px solid var(--accent,#FFC233);border-radius:999px;padding:8px 14px 8px 8px;cursor:pointer;'+
      '}'+
    '.llapp img{width:24px;height:24px;border-radius:6px}.llapp:focus-visible{outline:3px solid var(--bulb,#2FCB73);outline-offset:2px}'+
    '#llInstall{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:50;display:flex;gap:10px;align-items:center;'+
      'padding:12px 14px;border-radius:14px;background:var(--surface,#13201A);color:var(--ink,#F4F1E1);border:1.5px solid var(--accent,#FFC233);'+
      'box-shadow:0 6px 24px rgba(0,0,0,.45);font:14px/1.4 system-ui,sans-serif;max-width:560px;margin:0 auto}'+
    '#llInstall img{width:36px;height:36px;border-radius:8px;flex:none}#llInstall p{margin:0;flex:1}'+
    '#llInstall button,#llHow button{font:inherit;font-weight:700;border-radius:10px;padding:8px 12px;border:0;cursor:pointer}'+
    '#llInstall .go,#llHow .ok{background:var(--accent,#FFC233);color:#141006}#llInstall .x{background:transparent;color:var(--muted,#A8B5A2);padding:8px}'+
    '#llHow{position:fixed;inset:0;z-index:60;background:rgba(4,8,6,.72);display:flex;align-items:flex-end;justify-content:center;padding:16px}'+
    '#llHow .card{width:100%;max-width:440px;background:var(--surface,#13201A);color:var(--ink,#F4F1E1);border:1.5px solid var(--accent,#FFC233);'+
      'border-radius:18px;padding:20px;font:15px/1.5 system-ui,sans-serif;margin-bottom:env(safe-area-inset-bottom,0px)}'+
    '#llHow h2{margin:0 0 10px;font-size:18px;display:flex;gap:10px;align-items:center}#llHow h2 img{width:40px;height:40px;border-radius:10px}'+
    '#llHow ol{margin:0 0 16px;padding-left:22px}#llHow li{margin:6px 0}#llHow .ok{width:100%;padding:12px}'+
    '</style>';
  document.head.insertAdjacentHTML("beforeend",css);

  function iosSteps(){
    return '<ol><li>Tap '+(iosOther?'the <b>Share</b> '+SHARE+' button at the <b>top right</b> of the address bar':'the <b>Share</b> '+SHARE+' button at the <b>bottom</b> of Safari')+
      '.</li><li>Scroll down and tap <b>Add to Home Screen</b>.</li><li>Tap <b>Add</b>. Live Reggae Music appears on your home screen like an app.</li></ol>';
  }
  function howTo(){
    if(document.getElementById("llHow"))return;
    var body=ios?iosSteps():
      '<p style="margin:0 0 16px">Open your browser\'s menu (<b>⋮</b> or <b>⋯</b>) and choose <b>Install app</b> or <b>Add to Home screen</b>.</p>';
    var d=document.createElement("div");d.id="llHow";d.setAttribute("role","dialog");d.setAttribute("aria-modal","true");d.setAttribute("aria-label","Add Live Reggae Music to your home screen");
    d.innerHTML='<div class="card"><h2><img src="/icons/icon-192.png" alt="">Add Live Reggae Music to your home screen</h2>'+body+'<button type="button" class="ok">Got it</button></div>';
    document.body.appendChild(d);
    function close(){d.remove()}
    d.querySelector(".ok").onclick=close;d.onclick=function(e){if(e.target===d)close()};
    addEventListener("keydown",function k(e){if(e.key==="Escape"){close();removeEventListener("keydown",k)}});
    d.querySelector(".ok").focus();
  }
  function install(){
    if(deferred){deferred.prompt();deferred.userChoice.then(function(c){if(c.outcome==="accepted"){remember();hideAll()}});deferred=null}
    else howTo();
  }
  function hideAll(){var b=document.querySelector(".llapp");if(b)b.remove();var t=document.getElementById("llInstall");if(t)t.remove()}

  // Permanent button under the logo
  function addButton(){
    var logo=document.querySelector("header .logo");if(!logo||document.querySelector(".llapp"))return;
    var b=document.createElement("button");b.type="button";b.className="llapp";
    b.innerHTML='<img src="/icons/icon-192.png" alt="">Get the app';b.onclick=install;
    logo.insertAdjacentElement("afterend",b);
  }
  // Phones always get the button; computers only when the browser can really install (Chrome, Edge).
  var phone=ios||/Android|Mobi/.test(ua);
  function ready(fn){if(document.readyState==="loading")addEventListener("DOMContentLoaded",fn);else fn()}
  if(phone)ready(addButton);

  // One-time tip on phones
  function tip(html,canInstall){
    if(dismissed()||document.getElementById("llInstall")||innerWidth>=820)return;
    var bar=document.createElement("div");bar.id="llInstall";bar.setAttribute("role","note");
    bar.innerHTML='<img src="/icons/icon-192.png" alt=""><p>'+html+'</p>'+(canInstall?'<button class="go" type="button">Install</button>':'')+
      '<button class="x" type="button" aria-label="Dismiss">✕</button>';
    document.body.appendChild(bar);
    bar.querySelector(".x").onclick=function(){remember();bar.remove()};
    if(canInstall)bar.querySelector(".go").onclick=function(){bar.remove();install()};
  }
  addEventListener("beforeinstallprompt",function(e){e.preventDefault();deferred=e;ready(addButton);
    setTimeout(function(){tip("<b>Get the Live Reggae Music app</b> — one tap from your home screen.",true)},4000)});
  addEventListener("appinstalled",function(){remember();hideAll()});
  if(ios)setTimeout(function(){tip('<b>Add Live Reggae Music to your Home Screen:</b> tap '+(iosOther?'the ':'')+'Share '+SHARE+(iosOther?' button (top right)':'')+', then “Add to Home Screen”.',false)},4000);
})();
