// Prueba temporal de compatibilidad: sirve únicamente datos ficticios, sin base de datos.
// Usar una IP privada en vez de localhost para reproducir un origen HTTP no seguro.
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';

const host=process.argv[2]||'127.0.0.1';
const source=await readFile(new URL('../src/static/croquis/geometry.mjs',import.meta.url),'utf8');
const html=`<!doctype html><html lang="es"><meta charset="utf-8"><title>Croquis3R · Prueba HTTP de identificadores</title>
<style>body{font:17px system-ui;color:#213d36;background:#f4f6f1;max-width:900px;margin:55px auto;padding:25px}button{padding:14px;background:#2c6851;color:white;border:0;border-radius:6px;font:inherit}pre{white-space:pre-wrap;background:white;padding:22px;border:1px solid #dfe6dd;line-height:1.7}h1{font-size:28px}</style>
<h1>Croquis3R · Compatibilidad con HTTP de la LAN</h1><p>Prueba local con datos ficticios. No guarda ni modifica croquis.</p>
<pre id="environment"></pre><button id="run">Probar identificadores de objetos</button><pre id="result">Pendiente de ejecutar.</pre>
<script type="module">
${source}
document.querySelector('#environment').textContent='Origen: '+location.origin+'\\nContexto seguro: '+isSecureContext+'\\ncrypto.randomUUID: '+typeof globalThis.crypto?.randomUUID+'\\ncrypto.getRandomValues: '+typeof globalThis.crypto?.getRandomValues;
document.querySelector('#run').onclick=()=>{
  const lines=[];
  try{globalThis.crypto.randomUUID();lines.push('Llamada anterior: disponible en este origen.');}
  catch(error){lines.push('Error original reproducido: '+error.message);}
  try{
    const ids=Array.from({length:10000},()=>uid());
    if(new Set(ids).size!==ids.length)throw Error('Identificadores repetidos.');
    if(!ids.every(id=>/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id)))throw Error('Formato UUID incorrecto.');
    const wall={id:ids[0],kind:'wall',label:'Pared ficticia',x1:0,y1:0,x2:2,y2:0,assignments:[]};
    const opening={id:ids[1],kind:'door',wall_id:wall.id,offset:0,width:2,assignments:[]};
    const copies=duplicateObjects([wall,opening],wall);
    if(copies.length!==2||copies[1].wall_id!==copies[0].id||copies[0].id===wall.id)throw Error('Duplicación incorrecta.');
    lines.push('Corrección: OK · 10.000 UUID v4 válidos y distintos.','Duplicar pared con su puerta: OK.','Identificador de ejemplo: '+ids[0],'RESULTADO: APROBADO');
  }catch(error){lines.push('RESULTADO: FALLÓ · '+error.message);}
  document.querySelector('#result').textContent=lines.join('\\n');
};
</script></html>`;
createServer((request,response)=>{
  if(request.url!=='/'){response.writeHead(404);response.end();return;}
  response.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});
  response.end(html);
}).listen(18013,host,()=>console.log(`Prueba temporal: http://${host}:18013/`));
