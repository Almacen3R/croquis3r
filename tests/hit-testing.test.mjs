import test from 'node:test';
import assert from 'node:assert/strict';
import {structuralHit,wallAtPoint} from '../src/static/croquis/geometry.mjs';
const horizontal={id:'h',kind:'wall',x1:0,y1:0,x2:4,y2:0,thickness:.12};
const vertical={id:'v',kind:'wall',x1:4,y1:4,x2:4,y2:0,thickness:.12};
const column={id:'c',kind:'column',x:2,y:0};
test('column halo does not steal wall selection; visible column remains selectable',()=>{
  assert.equal(structuralHit({x:2.18,y:0},[horizontal],[column],'c').id,'h');
  assert.equal(structuralHit({x:2,y:0},[horizontal],[column],'c').id,'c');
  assert.equal(structuralHit({x:2.08,y:.08},[horizontal],[column],'c').id,'c');
});
test('door and window resolve wall under column, without depending on SVG target',()=>{
  for(const tool of ['door','window']) {
    assert.equal(structuralHit({x:2,y:0},[horizontal],[column],'c',tool).id,'h');
    assert.equal(structuralHit({x:2,y:.05},[horizontal],[column],null,tool).id,'h');
    assert.equal(structuralHit({x:2,y:1},[horizontal],[column],'c',tool),null);
  }
});
test('nearest reversed, diagonal and corner walls resolve from unsnapped cursor',()=>{
  const diagonal={...horizontal,id:'d',x2:4,y2:4};
  assert.equal(wallAtPoint({x:4.03,y:2},[horizontal,vertical]).id,'v');
  assert.equal(wallAtPoint({x:1,y:1.03},[diagonal]).id,'d');
  assert.equal(wallAtPoint({x:4,y:.2},[horizontal,vertical]).id,'v');
  assert.equal(wallAtPoint({x:4.3,y:0},[horizontal]),null);
  assert.equal(wallAtPoint({x:1,y:1},[{...horizontal,x2:0}]),null);
});
test('openings, handles and standalone columns retain normal selection',()=>{
  const door={id:'door',kind:'door',wall_id:'h'};
  const objects=[horizontal,door];
  assert.equal(structuralHit({x:2,y:0},objects,[column],'door').id,'door');
  assert.equal(structuralHit({x:0,y:0},objects,[column],'h').id,'h');
  assert.equal(structuralHit({x:2,y:2},[],[{...column,y:2}],'c').id,'c');
  assert.equal(structuralHit({x:2,y:0},objects,[],'door','door').id,'h');
  assert.equal(structuralHit({x:2,y:2},objects,[],null),null);
});
