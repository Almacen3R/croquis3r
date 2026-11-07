const {requestJson,cookieValue}=await import(`./http.mjs${new URL(import.meta.url).search}`);
const {buildRoof}=await import(`./presentation3d.mjs${new URL(import.meta.url).search}`);

export function setupRenders({source,name,sceneData,getSettings,sketchId}) {
  const button=document.getElementById('viewer3d-render');
  const status=document.getElementById('viewer3d-render-status');
  const list=document.getElementById('viewer3d-render-list');
  const feedback=document.getElementById('viewer3d-render-feedback');feedback.hidden=true;
  const inform=text=>{feedback.textContent=text;feedback.hidden=!text;};
  let closed=false,busy=false,timer=null,controller=null,lastJobs='';
  const node=(tag,text)=>{const el=document.createElement(tag);el.textContent=text;return el;};
  const labels={queued:'En cola',running:'Generando imagen…',ready:'Lista para descargar',failed:'No completada'};
  const refresh=async()=>{
    if(closed)return;
    controller=new AbortController();
    try {
      const result=await requestJson(`/api/renders/${sketchId?`?sketch_id=${encodeURIComponent(sketchId)}`:''}`,{signal:controller.signal});
      if(closed)return;
      button.disabled=busy||!result.available;
      status.textContent=result.available?'Imágenes de presentación · el proceso continúa si cierras la vista.':'El servicio de imágenes no está disponible por ahora. Puedes seguir usando la vista 3D.';
      const signature=JSON.stringify(result.jobs);
      if(signature===lastJobs)return;
      lastJobs=signature;
      const cards=result.jobs.map(job=>{
        const card=node('article','');card.className='render3d-card';
        card.append(node('strong',job.title),node('span',labels[job.status]||job.status),
          node('small',`${new Date(job.created_at).toLocaleString('es-CR')} · ${job.sketch_revision?`revisión ${job.sketch_revision}`:'vista capturada'} · ${job.fingerprint}`));
        if(job.error)card.append(node('p',job.error));
        if(job.image_url) {
          const preview=document.createElement('img');preview.src=job.image_url;preview.alt=`Presentación de ${job.title}`;preview.loading='lazy';card.append(preview);
          const link=node('a','Descargar imagen PNG');link.href=`${job.image_url}?download=1`;card.append(link);
        }
        return card;
      });
      list.replaceChildren(...cards);
      if(!cards.length)list.append(node('p','Las imágenes que generes aparecerán aquí.'));
    } catch(error) {if(!closed){status.textContent=error.message;button.disabled=true;}}
    finally {if(!closed)timer=setTimeout(refresh,4000);}
  };
  button.onclick=async()=>{
    if(busy)return;busy=true;button.disabled=true;
    inform('Enviando solicitud…');
    const settings={...getSettings()};
    const documentSnapshot={...source,presentation3d:settings};
    const scene={...sceneData,settings,roof:buildRoof(sceneData,settings)};
    try {
      const csrfName=document.querySelector('meta[name="csrf-cookie-name"]').content;
      await requestJson('/api/renders/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':cookieValue(document.cookie,csrfName)},
        body:JSON.stringify({name,document:documentSnapshot,scene,sketch_id:sketchId||null})});
      if(!closed){document.getElementById('viewer3d-renders').open=true;inform('Solicitud recibida. La imagen aparecerá aquí cuando termine.');}
    } catch(error){if(!closed)inform(error.message);}
    finally {busy=false;if(!closed){button.disabled=false;}}
  };
  refresh();
  return ()=>{closed=true;clearTimeout(timer);controller?.abort();button.onclick=null;};
}
