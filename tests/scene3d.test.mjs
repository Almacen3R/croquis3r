import test from 'node:test';
import assert from 'node:assert/strict';
import {buildHouseScene} from '../src/static/croquis/scene3d.mjs';

const wall={id:'w',kind:'wall',x1:0,y1:0,x2:4,y2:0,height:2.5,thickness:.12};
const door={id:'d',kind:'door',wall_id:'w',offset:1,width:1,height:2.1,sill:0};
const window={id:'v',kind:'window',wall_id:'w',offset:2.5,width:1,height:1.2,sill:1};
const scene=(objects,columns=[],ticoblock={})=>buildHouseScene({version:1,objects,columns,ticoblock});
const volume=boxes=>boxes.filter(b=>b.role==='wall').reduce((sum,b)=>sum+b.size.reduce((a,v)=>a*v,1),0);
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
const rectangle=[wall,{...wall,id:'b',x1:4,y1:0,x2:4,y2:4},{...wall,id:'c',x1:4,y1:4,x2:0,y2:4},{...wall,id:'e',x1:0,y1:4,x2:0,y2:0}];

test('solid wall uses meters and the same height and thickness without changing source',()=>{
  const document={version:1,objects:[wall]},before=JSON.stringify(document),result=buildHouseScene(document);
  assert.deepEqual(result.boxes[0].size,[4,2.5,.12]);
  assert.deepEqual(result.boxes[0].position,[2,1.25,0]);
  assert.equal(JSON.stringify(document),before);
});
test('door and window subtract full voids, retaining wall below window and lintels',()=>{
  const result=scene([wall,door,window]);
  close(volume(result.boxes),(4*2.5-1*2.1-1*1.2)*.12);
  for(const opening of [door,window])for(const box of result.boxes.filter(b=>b.role==='wall')) {
    const [x,y]=box.position,[width,height]=box.size;
    const intersects=x+width/2>opening.offset+1e-6&&x-width/2<opening.offset+opening.width-1e-6&&y+height/2>opening.sill+1e-6&&y-height/2<opening.sill+opening.height-1e-6;
    assert.equal(intersects,false);
  }
  assert.equal(result.openings.length,2);
  assert.ok(result.boxes.some(b=>b.role==='wall'&&b.position[0]===3&&b.position[1]===.5));
});
test('vertical reversed and diagonal walls place windows along their own direction',()=>{
  const vertical=scene([{...wall,x1:4,y1:4,x2:4,y2:0},window]);
  assert.deepEqual(vertical.openings[0].position,[4,1.6,1]);
  close(vertical.openings[0].rotation,Math.PI/2);
  const diagonal=scene([{...wall,x2:3,y2:4},window]);
  close(diagonal.openings[0].position[0],1.8);close(diagonal.openings[0].position[2],2.4);
  close(volume(diagonal.boxes),(5*2.5-1.2)*.12);
});
test('all four door swings agree with the sketch and retain the opening',()=>{
  const expected=[[1,1],[3,-1],[1,-1],[3,1]];
  for(let rotation=0;rotation<4;rotation++){
    const d={...door,width:2,door_rotation:rotation};
    const result=scene([wall,d]);
    assert.deepEqual([result.openings[0].openPosition[0],result.openings[0].openPosition[2]],expected[rotation]);
    close(volume(result.boxes),(10-4.2)*.12);
  }
});
test('overlapping openings remove their union instead of subtracting twice',()=>{
  const result=scene([wall,door,{...door,id:'d2',offset:1.5}]);
  close(volume(result.boxes),(10-1.5*2.1)*.12);
});
test('closed rooms get floors without a bounding rectangle over a concave plan',()=>{
  const points=[[0,0],[4,0],[4,2],[2,2],[2,4],[0,4]];
  const walls=points.map(([x1,y1],i)=>({...wall,id:String(i),x1,y1,x2:points[(i+1)%points.length][0],y2:points[(i+1)%points.length][1]}));
  const result=scene(walls);assert.equal(result.area,12);assert.equal(result.floors.length,1);assert.equal(result.floors[0].length,6);
  const divided=scene([...rectangle,{...wall,id:'divider',x1:2,x2:2,y1:0,y2:4}]);
  assert.equal(divided.area,16);assert.equal(divided.floors.length,2);
});
test('open walls do not invent a floor; independent columns are represented',()=>{
  const result=scene([wall],[{id:'c',x:9,y:7,column_type:'E'}]);
  assert.equal(result.floors.length,0);assert.ok(result.warnings.some(w=>w.includes('Cierra')));
  assert.deepEqual(result.boxes.find(b=>b.role==='column').position,[9,1.25,7]);
});
test('clipping warns about openings outside a wall; second level does not invent another floor',()=>{
  const result=scene([wall,{...window,offset:3.5,height:3}],[],{floor_level:2});
  close(volume(result.boxes),(10-.5*1.5)*.12);
  close(result.openings[0].size[0],.41);
  assert.ok(result.warnings.some(w=>w.includes('excede')));assert.ok(result.warnings.some(w=>w.includes('sola planta')));
});
