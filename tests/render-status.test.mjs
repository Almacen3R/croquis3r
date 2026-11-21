import test from 'node:test';
import assert from 'node:assert/strict';
import {renderDuration,renderJobStatus,requestRenderJson} from '../src/static/croquis/render-status.mjs';
test('healthy rendering reports elapsed time and distinguishes worker outage from a completed image',()=>{
 assert.equal(renderDuration(365),'6 min 5 s');
 assert.match(renderJobStatus({status:'running',elapsed_seconds:365},true),/6 min 5 s/);
 assert.match(renderJobStatus({status:'queued',elapsed_seconds:20},false),/En espera.*no responde/);
 assert.match(renderJobStatus({status:'running'},false),/sin respuesta/);
 assert.match(renderJobStatus({status:'running'},null),/sin confirmar/);
 assert.equal(renderJobStatus({status:'ready'},false),'Lista para descargar');
 assert.equal(renderJobStatus({status:'failed'},false),'No completada');
});
test('hung status requests time out and abort without claiming the rendering failed',async()=>{
 let signal;
 await assert.rejects(requestRenderJson('/api/renders/',{},(_,opts)=>{signal=opts.signal;return new Promise(()=>{});},10),/consulta.*tardó demasiado/);
 assert.equal(signal.aborted,true);
});
test('an unconfirmed submission warns to check history before creating duplicates',async()=>{
 await assert.rejects(requestRenderJson('/api/renders/',{method:'POST'},()=>new Promise(()=>{}),10),/historial antes de generar otra/);
});
test('successful and rejected requests keep their actual result',async()=>{
 const response={available:true,jobs:[]};
 assert.equal(await requestRenderJson('/api/renders/',{},async()=>response,100),response);
 await assert.rejects(requestRenderJson('/api/renders/',{},async()=>{throw new Error('Sesion vencida');},100),/Sesion vencida/);
});
