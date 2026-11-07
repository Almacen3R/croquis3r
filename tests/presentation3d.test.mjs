import test from 'node:test';
import assert from 'node:assert/strict';
import {presentationSettings,buildRoof,walkBlocked,walkStep,findWalkStart,insideRing} from '../src/static/croquis/presentation3d.mjs';
import {buildHouseScene} from '../src/static/croquis/scene3d.mjs';
const wall={id:'w',kind:'wall',x1:0,y1:0,x2:4,y2:0,height:2.5,thickness:.12};
const wallsFrom=points=>points.map(([x1,y1],i)=>({...wall,id:String(i),x1,y1,x2:points[(i+1)%points.length][0],y2:points[(i+1)%points.length][1]}));
const rectangle=wallsFrom([[0,0],[4,0],[4,4],[0,4]]);
const house=objects=>buildHouseScene({objects});
const settings=presentationSettings({});
const projectedArea=faces=>faces.reduce((sum,ring)=>sum+Math.abs(ring.reduce((a,p,i)=>{const q=ring[(i+1)%ring.length];return a+p[0]*q[2]-q[0]*p[2];},0))/2,0);
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);

test('old documents get defaults without being modified',()=>{
  const doc={objects:rectangle};assert.equal(presentationSettings(doc).roof_type,'none');assert.equal(doc.presentation3d,undefined);
});
test('flat and pitched roofs retain L and U footprints without covering courtyards',()=>{
  for(const points of [[[0,0],[4,0],[4,2],[2,2],[2,4],[0,4]],[[0,0],[4,0],[4,4],[3,4],[3,1],[1,1],[1,4],[0,4]]]) {
    const scene=house(wallsFrom(points));
    for(const type of ['flat','gable'])for(const axis of ['x','z']){
      const roof=buildRoof(scene,{...settings,roof_type:type,ridge_axis:axis});
      close(projectedArea(roof.surfaces),scene.area);
      assert.ok(roof.surfaces.every(face=>face.every(p=>Number.isFinite(p[1])&&p[1]>=2.54-1e-7)));
    }
  }
});
test('roof has the selected ridge direction, rise and no closure over an interior division',()=>{
  const scene=house([...rectangle,{...wall,id:'inner',x1:2,y1:0,x2:2,y2:4}]);
  const roof=buildRoof(scene,{...settings,roof_type:'gable',roof_rise:1,ridge_axis:'x'});
  close(Math.max(...roof.surfaces.flat().map(p=>p[1])),3.54);
  assert.ok(roof.surfaces.flat().filter(p=>p[1]>3.5).every(p=>Math.abs(p[2]-2)<1e-7));
  assert.ok(roof.closures.every(face=>!face.every(p=>Math.abs(p[0]-2)<1e-7)));
});
test('roof is omitted when footprint is open, or when disabled',()=>{
  assert.equal(buildRoof(house([wall]),{...settings,roof_type:'gable'}).surfaces.length,0);
  assert.equal(buildRoof(house(rectangle),settings).surfaces.length,0);
});
test('walking cannot tunnel through a solid wall, including reversed/diagonal walls',()=>{
  const scene=house([wall]);
  assert.ok(walkStep(scene,{x:2,z:1},{x:0,z:-3}).z>.23);
  for(const w of [{...wall,x1:4,x2:0},{...wall,x2:4,y2:4}]){
    const data=house([w]);assert.equal(walkBlocked(data,{x:(w.x1+w.x2)/2,z:(w.y1+w.y2)/2}),true);
  }
});
test('windows block passage, doors allow passage only when open and wide enough',()=>{
  const opening={id:'o',kind:'door',wall_id:'w',offset:1,width:1,height:2.1,sill:0};
  const scene=house([wall,opening]);
  assert.equal(walkBlocked(scene,{x:1.5,z:0}),true);
  assert.equal(walkBlocked(scene,{x:1.5,z:0},true),false);
  assert.ok(walkStep(scene,{x:1.5,z:1},{x:0,z:-2},true).z<-.9);
  assert.ok(walkStep(scene,{x:1.5,z:1},{x:0,z:-2},false).z>.18);
  assert.equal(walkBlocked(house([wall,{...opening,kind:'window',sill:1,height:1.2}]),{x:1.5,z:0},true),true);
  assert.equal(walkBlocked(house([wall,{...opening,kind:'window',sill:0,height:2.1}]),{x:1.5,z:0},true),true);
});
test('walking start is inside a clear region and independent columns block movement',()=>{
  const scene=house([...rectangle,{...wall,id:'inner',x1:2,x2:2,y1:0,y2:4}]);
  const start=findWalkStart(scene);assert.ok(start);assert.ok(scene.floors.some(ring=>insideRing(start,ring)));assert.equal(walkBlocked(scene,start),false);
  const columns=buildHouseScene({objects:[],columns:[{id:'col',x:2,y:3,column_type:'C'}]});
  assert.equal(walkBlocked(columns,{x:2,z:3}),true);assert.equal(findWalkStart(columns),null);
});
