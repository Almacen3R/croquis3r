// Panel widths are browser preferences, never part of the saved drawing.
export function setupPanels(workspace) {
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
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();const [min,max]=limits(side);
      sizes[side]=event.key==='Home'?min:event.key==='End'?max:sizes[side]+(event.key==='ArrowRight'?20:-20)*(side==='left'?1:-1);
      apply();save();
    });
    handle.addEventListener('dblclick',()=>{sizes.left=236;sizes.right=304;apply();save();});
  }
  window.addEventListener('resize',apply);apply();
}
