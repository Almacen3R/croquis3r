export function projectFilename(name, extension) {
  return (name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-zA-Z0-9_-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,80) || 'croquis3r') + extension;
}

export function packProject(name, document, articles, now = new Date()) {
  if (!name.trim() || name.trim().length>160) throw new Error('Dale un nombre al proyecto antes de descargarlo.');
  const used = new Set(document.objects.flatMap(obj=>(obj.assignments||[]).map(a=>a.article_id)));
  const references = [...used].map(id=>{
    const article=articles.find(a=>a.id===id);
    if(!article)throw new Error('No se encontró un artículo asignado. Revisa el catálogo antes de descargar el proyecto.');
    return {id,sku:article.sku};
  });
  const result=JSON.stringify({format:'croquis3r-project',format_version:1,name:name.trim(),
    exported_at:now.toISOString(),units:'m',document,articles:references});
  if(new TextEncoder().encode(result).byteLength>1048576)throw new Error('El proyecto supera el límite de 1 MB para volver a subirlo. Divide el dibujo en proyectos más pequeños.');
  return result;
}

export function downloadBlob(blob, filename) {
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}

export async function pdfFromPng(png, name, csrfToken, fetcher=fetch) {
  const body=new FormData();body.append('name',name);body.append('image',png,'croquis.png');
  let response;
  try {
    response=await fetcher('/api/export-pdf/',{method:'POST',credentials:'same-origin',
      headers:{'X-CSRFToken':csrfToken},body});
  } catch {
    throw new Error('No se pudo conectar para preparar el PDF. Tu croquis sigue abierto; vuelve a intentar o elige PNG.');
  }
  if(!response.ok) {
    const details=await response.json().catch(()=>null);
    if(response.status===401||response.status===403)throw new Error('Inicia sesión en otra pestaña y vuelve a descargar el PDF aquí, sin cerrar tu dibujo.');
    throw new Error(details?.error || `No se pudo preparar el PDF (${response.status}). Puedes volver a intentar o elegir PNG.`);
  }
  if(!response.headers.get('Content-Type')?.startsWith('application/pdf'))throw new Error('El servidor no devolvió un PDF. Revisa tu sesión y vuelve a intentar.');
  return response.blob();
}

export function wrapObservations(text, maxWidth, measure=line=>Array.from(line).length) {
  if(typeof text!=='string'||text.length>1000||text.split(/\r\n?|\n/).length>20||/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(text))throw new Error('Observaciones admite hasta 1000 caracteres y 20 renglones de texto.');
  if(!text.trim())return [];
  const lines=[];
  for(const paragraph of text.trim().split(/\r\n?|\n/)) {
    let line='';
    for(const word of paragraph.trim().split(/\s+/).filter(Boolean)) {
      if(line&&measure(`${line} ${word}`)<=maxWidth){line+=` ${word}`;continue;}
      if(line){lines.push(line);line='';}
      for(const char of Array.from(word)) {
        if(line&&measure(line+char)>maxWidth){lines.push(line);line='';}
        line+=char;
      }
    }
    lines.push(line);
  }
  return lines;
}

export async function drawingPng(svg, title, observations='') {
  const ns='http://www.w3.org/2000/svg',copy=svg.cloneNode(true);
  copy.setAttribute('xmlns',ns);copy.setAttribute('font-family','Arial, sans-serif');
  copy.removeAttribute('class');copy.removeAttribute('style');
  // Every exported drawing has a clean background, regardless of the screen preference.
  copy.querySelector('#grid-background')?.remove();
  copy.querySelector('#grid')?.remove();
  copy.querySelector('#preview')?.remove();
  copy.querySelectorAll('[data-endpoint],[data-handle]').forEach(node=>node.remove());
  const boxes=['scene','modulation','measurements'].map(id=>svg.querySelector(`#${id}`)).filter(g=>g?.childNodes.length).map(g=>g.getBBox());
  if(!boxes.length)throw new Error('Dibuja un croquis antes de descargar la imagen.');
  const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y));
  const w=Math.max(...boxes.map(b=>b.x+b.width))-x,h=Math.max(...boxes.map(b=>b.y+b.height))-y;
  const width=Math.max(w+2,8),baseHeight=Math.max(h+2.4,5),left=x-1,top=y-1.6;
  const measuring=document.createElement('canvas').getContext('2d');
  if(!measuring)throw new Error('El navegador no permite generar la imagen.');
  measuring.font='18px Arial';
  const notes=wrapObservations(observations,width-.7,line=>measuring.measureText(line).width/100);
  const height=baseHeight+(notes.length?.5+notes.length*.26:0);
  copy.setAttribute('viewBox',`${left} ${top} ${width} ${height}`);
  const scale=2400/Math.max(width,height),pxW=Math.round(width*scale),pxH=Math.round(height*scale);
  copy.setAttribute('width',pxW);copy.setAttribute('height',pxH);
  const white=document.createElementNS(ns,'rect');
  for(const [key,value] of Object.entries({x:left,y:top,width,height,fill:'#ffffff'}))white.setAttribute(key,value);
  copy.insertBefore(white,copy.firstChild);
  const label=(text,yy,size)=>{
    const node=document.createElementNS(ns,'text');node.textContent=text;
    for(const [key,value] of Object.entries({x:left+.35,y:yy,'font-size':size,fill:'#213d36'}))node.setAttribute(key,value);
    copy.append(node);
  };
  // Limitar el título mantiene su caja dentro de la lámina sin cortar texto.
  label(title.slice(0,65),top+.5,Math.min(.3,(width-.7)/Math.max(title.slice(0,65).length*.65,1)));
  if(notes.length) {
    label('Observaciones',top+baseHeight-.2,.20);
    copy.lastChild.setAttribute('font-weight','700');
    notes.forEach((line,index)=>label(line,top+baseHeight+.1+index*.26,.18));
  }
  const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml;charset=utf-8'}));
  try {
    const image=new Image();
    await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=()=>reject(new Error('No se pudo generar la imagen del croquis.'));image.src=url;});
    const canvas=document.createElement('canvas');canvas.width=pxW;canvas.height=pxH;
    const ctx=canvas.getContext('2d');if(!ctx)throw new Error('El navegador no permite generar la imagen.');
    ctx.drawImage(image,0,0);
    return await new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('No se pudo descargar la imagen.')),'image/png'));
  } finally {URL.revokeObjectURL(url);}
}
