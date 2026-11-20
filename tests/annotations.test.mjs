import test from 'node:test';
import assert from 'node:assert/strict';
import {moveAnnotation} from '../src/static/croquis/annotations.mjs';
import {packProject} from '../src/static/croquis/project-files.mjs';
import {buildHouseScene} from '../src/static/croquis/scene3d.mjs';
test('moving text and arrows keeps the original and moving an endpoint fixes the other',()=>{
  const a={id:'a',kind:'arrow',x1:1,y1:2,x2:3,y2:4,text:'Revisar'};
  assert.deepEqual(moveAnnotation(a,2,-1),{...a,x1:3,y1:1,x2:5,y2:3});
  assert.deepEqual(moveAnnotation(a,2,-1,2),{...a,x2:5,y2:3});
  assert.equal(a.x2,3);assert.equal(moveAnnotation(a,-2,-2,2),null);
  assert.equal(moveAnnotation(a,100,0),null);
  assert.deepEqual(moveAnnotation({kind:'text',x:0,y:1,text:'Nota'},.2,.3),{kind:'text',x:.2,y:1.3,text:'Nota'});
});
test('portable projects retain annotations and the 3D scene ignores them',()=>{
  const doc={version:1,objects:[],annotations:[{id:'n',kind:'text',x:0,y:0,text:'No incluye pintura',font_size:.25,color:'red'}]};
  assert.deepEqual(JSON.parse(packProject('Prueba',doc,[])).document,doc);
  assert.equal(buildHouseScene(doc).boxes.length,0);
});


test('Enter inserts a newline; Ctrl/Command Enter applies, without interrupting IME',async()=>{
  const {annotationSubmitKey}=await import('../src/static/croquis/annotations.mjs');
  assert.equal(Boolean(annotationSubmitKey({key:'Enter'})),false);
  assert.equal(Boolean(annotationSubmitKey({key:'Enter',shiftKey:true})),false);
  assert.equal(annotationSubmitKey({key:'Enter',ctrlKey:true}),true);
  assert.equal(annotationSubmitKey({key:'Enter',metaKey:true}),true);
  assert.equal(annotationSubmitKey({key:'Enter',ctrlKey:true,isComposing:true}),false);
});
test('SVG text preserves blank lines and CRLF with explicit baselines for PNG/PDF',async()=>{
  const {drawAnnotations}=await import('../src/static/croquis/annotations.mjs');
  const nodes=[];
  const draw=(tag,attrs,parent,text)=>{const node={tag,attrs,text,getBBox:()=>({x:0,y:0,width:2,height:2})};nodes.push(node);return node;};
  drawAnnotations([{id:'n',kind:'text',x:2,y:3,font_size:.25,text:'Primera\r\n\r\nTercera\nCuarta'}],draw,{});
  const lines=nodes.filter(n=>n.tag==='tspan');
  assert.deepEqual(lines.map(n=>n.text),['Primera',' ','Tercera','Cuarta']);
  assert.deepEqual(lines.map(n=>n.attrs.x),[2,2,2,2]);
  assert.deepEqual(lines.map(n=>n.attrs.y),[3,3.325,3.65,3.975]);
});
