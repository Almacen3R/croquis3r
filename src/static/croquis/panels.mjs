// Panel widths are browser preferences, never part of the saved drawing.
export function setupPanels(workspace) {
  setupCanvasHeight(workspace);
  const key='croquis3r-panel-widths', sizes={left:236,right:304};
  try {const saved=JSON.parse(localStorage.getItem(key));for(const side of ['left','right'])if(Number.isFinite(saved?.[side]))sizes[side]=saved[side];} catch {}
  const limits=side=>[side==='left'?180:210, Math.max(side==='left'?180:210,Math.min(460,innerWidth-330-(side==='left'?sizes.right:sizes.left)))];
  const apply=()=>{
    for(const side of ['left','right']) {
      const [min,max]=limits(side);sizes[side]=Math.max(min,Math.min(max,sizes[side]));
      workspace.style.setProperty(`--${side}-width`,`${sizes[side]}px`);
      const handle=workspace.querySelector(`[data-resize="${side}"]`);
      handle.setAttribute('aria-valuemin',min);handle.setAttribute('aria-valuemax',max);handle.setAttribute('aria-valuenow',sizes[side]);
    }
  };
  const save=()=>{try{localStorage.setItem(key,JSON.stringify(sizes));}catch{}};
  for(const handle of workspace.querySelectorAll('[data-resize]')) {
    const side=handle.dataset.resize;let drag=null;
    handle.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;event.preventDefault();
      drag={x:event.clientX,width:sizes[side]};handle.setPointerCapture(event.pointerId);
      document.body.classList.add('resizing-panels');
    });
    handle.addEventListener('pointermove',event=>{
      if(!drag)return;sizes[side]=drag.width+(event.clientX-drag.x)*(side==='left'?1:-1);apply();
    });
    const end=()=>{if(!drag)return;drag=null;document.body.classList.remove('resizing-panels');save();};
    for(const event of ['pointerup','pointercancel','lostpointercapture'])handle.addEventListener(event,end);
    handle.addEventListener('keydown',event=>{
      if(event.ctrlKey||event.metaKey||event.altKey)return;
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();const [min,max]=limits(side);
      sizes[side]=event.key==='Home'?min:event.key==='End'?max:sizes[side]+(event.key==='ArrowRight'?20:-20)*(side==='left'?1:-1);
      apply();save();
    });
    handle.addEventListener('dblclick',()=>{sizes.left=236;sizes.right=304;apply();save();});
  }
  window.addEventListener('resize',apply);apply();
}

function setupCanvasHeight(workspace) {
  const area=workspace.querySelector('#drawing-area'), handle=workspace.querySelector('#canvas-height-resizer');
  const key='croquis3r-canvas-height', min=320, max=1600;
  let height=null, drag=null;
  try {const saved=Number(localStorage.getItem(key));if(Number.isFinite(saved)&&saved>=min)height=saved;}catch{}
  const apply=()=>{
    if(height!==null){height=Math.max(min,Math.min(max,height));area.style.height=`${height}px`;}
    else area.style.removeProperty('height');
    handle.setAttribute('aria-valuemin',min);handle.setAttribute('aria-valuemax',max);
    handle.setAttribute('aria-valuenow',Math.round(area.getBoundingClientRect().height));
  };
  const save=()=>{try {if(height===null)localStorage.removeItem(key);else localStorage.setItem(key,String(height));}catch{}};
  handle.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;event.preventDefault();
    drag={y:event.clientY,height:area.getBoundingClientRect().height};handle.setPointerCapture(event.pointerId);
    document.body.classList.add('resizing-canvas-height');
  });
  handle.addEventListener('pointermove',event=>{
    if(!drag)return;height=drag.height+event.clientY-drag.y;apply();
  });
  const end=()=>{if(!drag)return;drag=null;document.body.classList.remove('resizing-canvas-height');save();};
  for(const event of ['pointerup','pointercancel','lostpointercapture'])handle.addEventListener(event,end);
  handle.addEventListener('keydown',event=>{
    if(event.ctrlKey||event.metaKey||event.altKey)return;
    if(!['ArrowUp','ArrowDown','Home','End'].includes(event.key))return;
    event.preventDefault();height=event.key==='Home'?min:event.key==='End'?max:area.getBoundingClientRect().height+(event.key==='ArrowDown'?40:-40);apply();save();
  });
  handle.addEventListener('dblclick',()=>{height=null;apply();save();});
  window.addEventListener('resize',apply);apply();
}
