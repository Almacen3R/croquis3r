import test from 'node:test';
import assert from 'node:assert/strict';
import {buildHouseScene} from '../src/static/croquis/scene3d.mjs';
import {presentationSettings,buildRoof,roofBoundaryEdges,insideRing} from '../src/static/croquis/presentation3d.mjs';
import {openingDetails,worldOpeningDetails,buildRenderPresentation} from '../src/static/croquis/visual-details3d.mjs';
const walls=[[0,0,4,0],[4,0,4,4],[4,4,0,4],[0,4,0,0]].map((v,i)=>({id:'w'+i,kind:'wall',x1:v[0],y1:v[1],x2:v[2],y2:v[3],height:2.5,thickness:.12}));
const document={version:1,objects:[...walls,{id:'door',kind:'door',wall_id:'w0',offset:1.5,width:1,height:2.1,sill:0},{id:'window',kind:'window',wall_id:'w1',offset:1,width:1.5,height:1.2,sill:1}]};
const area=faces=>faces.reduce((total,face)=>total+Math.abs(face.reduce((sum,p,i)=>{const q=face[(i+1)%face.length];return sum+p[0]*q[2]-q[0]*p[2];},0))/2,0);
test('decorative details remain separate and facade camera faces the entrance',()=>{
 const before=JSON.stringify(document),scene=buildHouseScene(document),snapshot=JSON.stringify(scene),settings={...presentationSettings({}),roof_type:'gable'};
 const result=buildRenderPresentation(scene,settings);
 assert.ok(result.details.some(d=>d.role==='metal'));assert.ok(result.details.some(d=>d.role==='sill'));
 assert.ok(result.camera.position[2]<0);assert.deepEqual(result.boxes,scene.boxes);
 assert.equal(JSON.stringify(scene),snapshot);assert.equal(JSON.stringify(document),before);
 for(const detail of result.details)assert.ok(detail.size.every(n=>n>0&&Number.isFinite(n)));
});
test('current interior camera respects hidden roof and doors, and details follow the open leaf',()=>{
 const scene=buildHouseScene(document),door=scene.openings.find(o=>o.kind==='door');
 const view={position:[2,1.6,2],target:[2,1.6,0],fov:70,doorsOpen:true,hideRoof:true};
 const result=buildRenderPresentation(scene,{...presentationSettings({}),roof_type:'gable'},view);
 assert.deepEqual(result.roof,{surfaces:[],closures:[]});
 assert.deepEqual(result.openings[0].position,door.openPosition);
 assert.equal(result.openings[0].rotation,door.openRotation);
 assert.deepEqual(result.camera,{position:view.position,target:view.target,fov:70});
 assert.deepEqual(result.details.slice(0,openingDetails(door).length),worldOpeningDetails({...door,position:door.openPosition,rotation:door.openRotation}));
 assert.notEqual(result.camera.position,view.position);
});
test('quarter turn of a vertical opening rotates details in the same world convention',()=>{
 const opening={kind:'window',size:[1.4,1.1,.025],position:[3,1.5,2],rotation:-Math.PI/2};
 const local=openingDetails(opening),world=worldOpeningDetails(opening);
 for(let i=0;i<local.length;i++){
  assert.ok(Math.abs(world[i].position[0]-(3-local[i].position[2]))<1e-8);
  assert.ok(Math.abs(world[i].position[2]-(2+local[i].position[0]))<1e-8);
 }
});
test('overhang expands only the exterior boundary, including split room junctions',()=>{
 const floors=[[{x:0,y:0},{x:4,y:0},{x:4,y:2},{x:0,y:2}], [{x:0,y:2},{x:2,y:2},{x:2,y:4},{x:0,y:4}], [{x:2,y:2},{x:4,y:2},{x:4,y:4},{x:2,y:4}]];
 for(const [a,b] of roofBoundaryEdges(floors))assert.ok(a.x===b.x&&(a.x===0||a.x===4)||a.y===b.y&&(a.y===0||a.y===4));
 const scene={...buildHouseScene(document),floors},settings={...presentationSettings({}),roof_type:'gable',roof_overhang:.25};
 const roof=buildRoof(scene,settings);assert.ok(Math.abs(area(roof.surfaces)-20.25)<1e-6);
 const noOverhang=buildRoof(scene,{...settings,roof_overhang:0});assert.ok(Math.abs(area(noOverhang.surfaces)-16)<1e-6);
 for(const face of roof.closures)assert.ok(face.every(p=>p[0]===0)||face.every(p=>p[0]===4)||face.every(p=>p[2]===0)||face.every(p=>p[2]===4));
});

test('overhang follows L and U plans without filling their large recesses',()=>{
 for(const [points,expected,empty] of [
  [[[0,0],[4,0],[4,2],[2,2],[2,4],[0,4]],16.25,{x:3,z:3}],
  [[[0,0],[6,0],[6,6],[4,6],[4,2],[2,2],[2,6],[0,6]],36.25,{x:3,z:5}]
 ]) {
  const ring=points.map(([x,y])=>({x,y}));
  for(const roof_type of ['flat','gable']){
   const roof=buildRoof({...buildHouseScene(document),floors:[ring]},{...presentationSettings({}),roof_type,roof_overhang:.25});
   assert.ok(Math.abs(area(roof.surfaces)-expected)<1e-6);
   assert.ok(!roof.surfaces.some(face=>insideRing(empty,face.map(p=>({x:p[0],y:p[2]})))));
  }
 }
});
test('handles remain opposite the hinge for all four door swings, including the open view',()=>{
 for(let rotation=0;rotation<4;rotation++){
  const drawing=JSON.parse(JSON.stringify(document));drawing.objects.find(o=>o.kind==='door').door_rotation=rotation;
  const scene=buildHouseScene(drawing),door=scene.openings.find(o=>o.kind==='door');
  const sign=rotation%2?-1:1;
  assert.ok(openingDetails(door).filter(d=>d.role==='metal').every(d=>Math.sign(d.position[0])===sign));
  const opened={...door,position:door.openPosition,rotation:door.openRotation};
  assert.ok(openingDetails(opened).filter(d=>d.role==='metal').every(d=>Math.sign(d.position[0])===sign));
 }
});
