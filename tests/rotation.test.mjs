import test from 'node:test';
import assert from 'node:assert/strict';
import {rotateDrawingLeft} from '../src/static/croquis/rotation.mjs';
import {length,openingPoints,doorSwing,floorArea} from '../src/static/croquis/geometry.mjs';
const walls=[[0,0,4,0],[4,0,4,3],[4,3,0,3],[0,3,0,0]].map((v,i)=>({id:'w'+i,kind:'wall',x1:v[0],y1:v[1],x2:v[2],y2:v[3],height:2.5,thickness:.12}));
const document={version:1,objects:[...walls,{id:'d',kind:'door',wall_id:'w0',offset:1,width:2,height:2.1,sill:0,door_rotation:3}],columns:[{id:'c',kind:'column',x:.5,y:3}],annotations:[{id:'a',kind:'arrow',x1:1,y1:2,x2:2,y2:3,text:'Nota'}, {id:'t',kind:'text',x:0,y:1,text:'Dos\nrenglones'}],presentation3d:{roof_type:'gable',ridge_axis:'x'}};
test('left quarter turn places top at left, keeps grid, identifiers, sizes and independent annotations',()=>{
 const rotated=rotateDrawingLeft(document);
 assert.deepEqual([rotated.objects[0].x2,rotated.objects[0].y2],[0,-4]);
 assert.deepEqual(rotated.columns[0],{...document.columns[0],x:3,y:-.5});
 assert.deepEqual(rotated.annotations[0],{...document.annotations[0],x1:2,y1:-1,x2:3,y2:-2});
 assert.deepEqual(rotated.annotations[1],{...document.annotations[1],x:1,y:0});
 assert.equal(rotated.presentation3d.ridge_axis,'z');
 assert.deepEqual(rotated.objects.at(-1),document.objects.at(-1));
 assert.deepEqual(rotated.objects.slice(0,4).map(length),walls.map(length));
 assert.equal(floorArea(rotated.objects.slice(0,4)).area,floorArea(walls).area);
 assert.equal(document.objects[0].x2,4);
});
test('four turns restore exact coordinates and roof orientation; undo can keep original unchanged',()=>{
 let rotated=document;for(let i=0;i<4;i++)rotated=rotateDrawingLeft(rotated);
 assert.deepEqual(rotated,document);
 assert.deepEqual(rotateDrawingLeft({version:1,objects:[]}),{version:1,objects:[]});
});
test('door endpoints and swing rotate together with their owning wall',()=>{
 const rotated=rotateDrawingLeft(document),door=document.objects.at(-1);
 const before=openingPoints(door,walls[0]),after=openingPoints(door,rotated.objects[0]);
 assert.deepEqual(after,{x1:before.y1,y1:-before.x1,x2:before.y2,y2:-before.x2});
 const swing=doorSwing(door,walls[0]),next=doorSwing(door,rotated.objects[0]);
 for(const key of ['hinge','open','closed'])assert.deepEqual(next[key],{x:swing[key].y,y:-swing[key].x});
});
