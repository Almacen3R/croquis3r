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
