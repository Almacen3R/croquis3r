import test from 'node:test';
import assert from 'node:assert/strict';
import {zoomView} from '../src/static/croquis/geometry.mjs';

test('zoom mantiene el punto bajo el cursor y la proporción del plano',()=>{
  const view=[-2,-1,16,12],anchor={x:3,y:4};
  const next=zoomView(view,.8,anchor);
  assert.equal(next[2],12.8);assert.ok(Math.abs(next[3]/next[2]-.75)<1e-12);
  assert.ok(Math.abs((anchor.x-view[0])/view[2]-(anchor.x-next[0])/next[2])<1e-12);
  assert.ok(Math.abs((anchor.y-view[1])/view[3]-(anchor.y-next[1])/next[3])<1e-12);
  const back=zoomView(next,1.25,anchor);
  back.forEach((value,i)=>assert.ok(Math.abs(value-view[i])<1e-12));
});

test('botones de zoom conservan el centro y limitan acercamiento y alejamiento',()=>{
  assert.deepEqual(zoomView([0,0,4,4],.5),[1,1,2,2]);
  assert.equal(zoomView([0,0,4,4],.00001)[2],1);
  assert.equal(zoomView([0,0,4,4],1000)[2],400);
});


const {unionBounds,centerViewOnBounds,fitViewToBounds}=await import('../src/static/croquis/viewport.mjs');
const centered=(view,bounds)=>{
 assert.ok(Math.abs(view[0]+view[2]/2-(bounds.x+bounds.width/2))<1e-10);
 assert.ok(Math.abs(view[1]+view[3]/2-(bounds.y+bounds.height/2))<1e-10);
};
test('rotation recenter preserves both view dimensions and effective SVG scale',()=>{
 const view=[-3,-4,18,12],bounds={x:0,y:-13,width:0,height:13};
 const next=centerViewOnBounds(view,bounds);centered(next,bounds);
 assert.deepEqual(next.slice(2),view.slice(2));
 for(const [w,h] of [[1400,500],[500,900]])assert.equal(Math.min(w/next[2],h/next[3]),Math.min(w/view[2],h/view[3]));
});
test('fit centers short and long walls in either orientation, including negative coordinates',()=>{
 for(const bounds of [{x:-9,y:-13,width:0,height:13},{x:-13,y:0,width:13,height:0},{x:2,y:3,width:.5,height:0},{x:2,y:3,width:0,height:.5}]){
  for(const viewport of [{width:1500,height:450},{width:450,height:900}]){
   const view=fitViewToBounds(bounds,viewport);centered(view,bounds);
   assert.ok(Math.abs(view[2]/view[3]-viewport.width/viewport.height)<1e-10);
   assert.ok(view[0]<=bounds.x&&view[1]<=bounds.y);
   assert.ok(view[0]+view[2]>=bounds.x+bounds.width&&view[1]+view[3]>=bounds.y+bounds.height);
  }
 }
});
test('visible content bounds include measurements and notes instead of origin or the grid',()=>{
 const bounds=unionBounds([{x:-13,y:0,width:13,height:0},{x:-14,y:-1,width:15,height:2},{x:3,y:2,width:4,height:1},null,{x:0,y:0,width:0,height:0}]);
 assert.deepEqual(bounds,{x:-14,y:-1,width:21,height:4});
 centered(fitViewToBounds(bounds,{width:1200,height:600}),bounds);
 assert.deepEqual(centerViewOnBounds([1,2,16,12],null),[1,2,16,12]);
 assert.deepEqual(fitViewToBounds(null),[-2,-2,16,12]);
});

test('four real drawing rotations stay centered without accumulating zoom changes',async()=>{
 const {rotateDrawingLeft}=await import('../src/static/croquis/rotation.mjs');
 let drawing={version:1,objects:[{kind:'wall',id:'a',x1:2,y1:3,x2:8,y2:3},{kind:'wall',id:'b',x1:8,y1:3,x2:8,y2:12}]};
 let view=[-2,-4,24,12];
 for(let i=0;i<4;i++){
  drawing=rotateDrawingLeft(drawing);
  const bounds=unionBounds(drawing.objects.map(w=>({x:Math.min(w.x1,w.x2),y:Math.min(w.y1,w.y2),width:Math.abs(w.x2-w.x1),height:Math.abs(w.y2-w.y1)})));
  view=centerViewOnBounds(view,bounds);centered(view,bounds);
  assert.deepEqual(view.slice(2),[24,12]);
 }
});
