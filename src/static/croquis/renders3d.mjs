const {cookieValue}=await import(`./http.mjs${new URL(import.meta.url).search}`);
const {buildRenderPresentation}=await import(`./visual-details3d.mjs${new URL(import.meta.url).search}`);

const {requestRenderJson,renderJobStatus}=await import(`./render-status.mjs${new URL(import.meta.url).search}`);

export function setupRenders({source,name,sceneData,getSettings,getView,sketchId}) {
  const button=document.getElementById('viewer3d-render');
  const status=document.getElementById('viewer3d-render-status');
  const list=document.getElementById('viewer3d-render-list');
  const feedback=document.getElementById('viewer3d-render-feedback');feedback.hidden=true;
  const inform=text=>{feedback.textContent=text;feedback.hidden=!text;};
  let closed=false,busy=false,available=false,timer=null,controller=null,lastJobs='';
  const node=(tag,text)=>{const el=document.createElement(tag);el.textContent=text;return el;};
  const updateStates=(jobs,health)=>{for(const job of jobs){const element=list.querySelector(`[data-job-id="${job.id}"] [data-render-state]`);if(element)element.textContent=renderJobStatus(job,health);}};
  const refresh=async()=>{
    if(closed)return;
    controller=new AbortController();
    try {
      const result=await requestRenderJson(`/api/renders/${sketchId?`?sketch_id=${encodeURIComponent(sketchId)}`:''}`,{signal:controller.signal});
      if(closed)return;
      available=result.available;button.disabled=busy||!available;
      status.textContent=available?`El render puede tardar varios minutos (límite ${Math.round((result.timeout_seconds||600)/60)} min). Continúa si cierras la vista.`:'El servicio de imágenes no responde. Las imágenes listas siguen disponibles; las que están en cola esperan al servicio.';
      updateStates(result.jobs,available);
      const signature=JSON.stringify({available,jobs:result.jobs.map(({elapsed_seconds,...job})=>job)});
      if(signature===lastJobs)return;
      lastJobs=signature;
      const cards=result.jobs.map(job=>{
        const card=node('article','');card.className='render3d-card';card.dataset.jobId=job.id;
        const state=node('span',renderJobStatus(job,available));state.dataset.renderState='';
        card.append(node('strong',job.title),state,
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
    } catch(error) {if(!closed){available=false;status.textContent=error.message;button.disabled=true;for(const state of list.querySelectorAll('[data-render-state]'))if(!state.textContent.includes('descargar')&&!state.textContent.includes('completada'))state.textContent='Estado sin confirmar. No necesitas volver a generar la imagen; se volverá a consultar.';}}
    finally {if(!closed)timer=setTimeout(refresh,4000);}
  };
  button.onclick=async()=>{
    if(busy||!available)return;busy=true;button.disabled=true;
    inform('Enviando solicitud…');
    try {
      const settings={...getSettings()};
      const documentSnapshot={...source,presentation3d:settings};
      const useCurrent=document.getElementById('viewer3d-render-view').value==='current';
      const scene=buildRenderPresentation(sceneData,settings,useCurrent?getView():null);
      const csrfName=document.querySelector('meta[name="csrf-cookie-name"]').content;
      await requestRenderJson('/api/renders/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':cookieValue(document.cookie,csrfName)},
        body:JSON.stringify({name,document:documentSnapshot,scene,sketch_id:sketchId||null})});
      if(!closed){document.getElementById('viewer3d-renders').open=true;inform('Solicitud recibida. Revisa aquí el tiempo y el estado; el proceso continúa si cierras la vista.');}
    } catch(error){if(!closed){available=false;inform(error.message);}}
    finally {busy=false;if(!closed){button.disabled=!available;}}
  };
  refresh();
  return ()=>{closed=true;clearTimeout(timer);controller?.abort();button.onclick=null;};
}
