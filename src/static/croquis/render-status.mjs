const {requestJson}=await import(`./http.mjs${new URL(import.meta.url).search}`);
export function renderDuration(seconds=0) {
  const total=Math.max(0,Math.floor(seconds));return `${Math.floor(total/60)} min ${total%60} s`;
}
export function renderJobStatus(job,available) {
  if(job.status==='ready')return 'Lista para descargar';
  if(job.status==='failed')return 'No completada';
  if(available===null)return 'Estado sin confirmar: se volverá a consultar.';
  if(!available)return job.status==='queued'?'En espera: el servicio de imágenes no responde.':'Servicio sin respuesta: no se puede confirmar el avance.';
  return job.status==='queued'?`En cola · espera ${renderDuration(job.elapsed_seconds)}`:`Generando imagen · ${renderDuration(job.elapsed_seconds)}. Puede tardar varios minutos.`;
}
export async function requestRenderJson(path,options={},requester=requestJson,timeoutMs=15000) {
  const controller=new AbortController(),parent=options.signal;
  const abort=()=>controller.abort();if(parent?.aborted)abort();else parent?.addEventListener('abort',abort,{once:true});
  let timer;
  const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>{
    reject(new Error(options.method==='POST'?'No se pudo confirmar la solicitud a tiempo. Revisa el historial antes de generar otra imagen.':'La consulta del render tardó demasiado. Se volverá a intentar automáticamente.'));
    controller.abort();
  },timeoutMs);});
  try {return await Promise.race([requester(path,{...options,signal:controller.signal}),deadline]);}
  finally {clearTimeout(timer);parent?.removeEventListener('abort',abort);}
}
