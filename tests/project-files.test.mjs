import test from 'node:test';
import assert from 'node:assert/strict';
import {packProject,projectFilename,pdfFromPng} from '../src/static/croquis/project-files.mjs';

test('el archivo conserva el documento completo y solo incluye SKU utilizados',()=>{
  const doc={version:1,objects:[{id:'p',kind:'door',door_rotation:3,assignments:[{article_id:4,factor:'2'}]}],
    columns:[{id:'c',column_type:'C',x:1,y:2}],ticoblock:{max_span:'1.5'}};
  const packed=JSON.parse(packProject(' Mi casa ',doc,[{id:4,sku:'BLOQUE',name:'Privado'},{id:5,sku:'OTRO'}],new Date('2026-10-26T00:00:00Z')));
  assert.equal(packed.format,'croquis3r-project');assert.equal(packed.format_version,1);
  assert.equal(packed.name,'Mi casa');assert.deepEqual(packed.document,doc);
  assert.deepEqual(packed.articles,[{id:4,sku:'BLOQUE'}]);
  for(const field of ['owner','id','revision','prices'])assert.equal(field in packed,false);
});

test('un proyecto sin artículos puede respaldarse sin consultar al servidor',()=>{
  assert.deepEqual(JSON.parse(packProject('Casa',{version:1,objects:[]},[])).articles,[]);
  assert.throws(()=>packProject(' ',{objects:[]},[]),/nombre/);
  assert.throws(()=>packProject('Casa',{objects:[{assignments:[{article_id:99}]}]},[]),/artículo/);
});

test('nombres de descarga no incluyen rutas y conservan extensión reconocible',()=>{
  assert.equal(projectFilename('Casa de José / primer piso','.croquis3r.json'),'Casa-de-Jose-primer-piso.croquis3r.json');
  assert.equal(projectFilename('../../','.png'),'croquis3r.png');
});

test('no descarga archivos que superan el tamaño admitido al importar',()=>{
  assert.throws(()=>packProject('Casa',{version:1,objects:[{label:'x'.repeat(1048576)}]},[]),/1 MB/);
});

test('la descarga PDF envía solo la lámina con sesión y CSRF y recibe un archivo binario',async()=>{
  const image=new Blob(['PNG'],{type:'image/png'});
  const result=await pdfFromPng(image,'Casa','csrf-propio',async(url,options)=>{
    assert.equal(url,'/api/export-pdf/');assert.equal(options.method,'POST');
    assert.equal(options.credentials,'same-origin');assert.equal(options.headers['X-CSRFToken'],'csrf-propio');
    assert.equal(options.body.get('name'),'Casa');assert.equal(options.body.get('image').type,'image/png');
    return new Response('%PDF-test',{status:200,headers:{'Content-Type':'application/pdf'}});
  });
  assert.equal(await result.text(),'%PDF-test');
});

test('fallos de PDF no se descargan como si fueran archivos correctos',async()=>{
  const image=new Blob(['PNG']);
  await assert.rejects(pdfFromPng(image,'Casa','',async()=>new Response('login',{status:403})),/sesión/);
  await assert.rejects(pdfFromPng(image,'Casa','',async()=>new Response('<html>Login</html>',{status:200,headers:{'Content-Type':'text/html'}})),/no devolvió un PDF/);
  await assert.rejects(pdfFromPng(image,'Casa','',async()=>{throw new Error('offline');}),/sigue abierto/);
  await assert.rejects(pdfFromPng(image,'Casa','',async()=>new Response(JSON.stringify({error:'Imagen inválida'}),{status:400})),/Imagen inválida/);
});
