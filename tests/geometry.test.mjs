import test from 'node:test';
import assert from 'node:assert/strict';
import {uid, dimensionChains, dimensionLayout, snapPoint, openingPoints, duplicateObjects, resizeEndpoint, length, editOpening, placeOpening, transferOpening, doorSwing, columnPoint} from '../src/static/croquis/geometry.mjs';

const wall = {id:'a',kind:'wall',x1:0,y1:0,x2:4,y2:0,height:2.4,thickness:.15,assignments:[]};
test('cotas unen tramos contiguos incluso con dirección invertida, sin unir líneas separadas',()=>{
  const chains=dimensionChains([wall,{...wall,id:'b',x1:8,x2:4},{...wall,id:'c',x1:9,x2:10},{...wall,id:'d',y1:2,y2:2}]);
  assert.equal(chains.length,3);
  assert.deepEqual(chains[0],{horizontal:true,fixed:0,start:0,end:8});
});
test('ajuste prioriza extremos cercanos y respeta la cuadrícula o su desactivación',()=>{
  assert.deepEqual(snapPoint({x:4.12,y:.04},[wall]),{x:4,y:0});
  assert.deepEqual(snapPoint({x:1.13,y:1.26},[wall]),{x:1,y:1.5});
  assert.deepEqual(snapPoint({x:-.33,y:-1.26},[wall]),{x:-.5,y:-1.5});
  assert.deepEqual(snapPoint({x:1.13,y:1.26},[wall],false),{x:1.13,y:1.26});
});
test('aberturas siguen el sentido de una pared vertical invertida',()=>{
  const result=openingPoints({offset:1,width:.9},{...wall,x1:2,x2:2,y1:4,y2:0});
  assert.deepEqual(result,{x1:2,y1:3,x2:2,y2:2.1});
});
test('duplicar pared copia aberturas y asignaciones sin modificar el original',()=>{
  const opening={id:'door',kind:'door',wall_id:'a',offset:1,width:.9,assignments:[]};
  const objects=[wall,opening],copies=duplicateObjects(objects,wall);
  assert.equal(copies.length,2);assert.notEqual(copies[0].id,wall.id);
  assert.equal(copies[1].wall_id,copies[0].id);assert.equal(copies[0].y1,.5);
  copies[0].assignments.push({article_id:1});assert.equal(wall.assignments.length,0);
});

test('arrastrar cada extremo cambia largo y dirección conservando el otro extremo',()=>{
  const end = resizeEndpoint(wall,2,{x:3,y:4},[wall]);
  assert.equal(length(end),5);
  assert.deepEqual([end.x1,end.y1,end.x2,end.y2],[0,0,3,4]);
  const start = resizeEndpoint(wall,1,{x:1,y:4},[wall]);
  assert.deepEqual([start.x1,start.y1,start.x2,start.y2],[1,4,4,0]);
  assert.deepEqual([wall.x1,wall.y1,wall.x2,wall.y2],[0,0,4,0]);
});
test('extremos se ajustan a otra pared y rechazan largos que no admiten sus aberturas',()=>{
  const other = {...wall,id:'b',x1:3,y1:3.5,x2:5,y2:3.5};
  const end = resizeEndpoint(wall,2,{x:3.1,y:3.53},[wall,other]);
  assert.deepEqual([end.x2,end.y2],[3,3.5]);
  assert.equal(resizeEndpoint(wall,2,{x:0,y:0},[wall]),null);
  assert.equal(resizeEndpoint(wall,2,{x:1,y:0},[wall],true,1.9),null);
  assert.equal(resizeEndpoint(wall,2,{x:101,y:0},[wall]),null);
});
test('cotas diagonales fusionan tramos contiguos y distinguen paralelas',()=>{
  const diagonal = {...wall,x2:3,y2:4};
  const chains = dimensionChains([diagonal,{...wall,id:'b',x1:6,y1:8,x2:3,y2:4},{...diagonal,id:'c',y1:1,y2:5}]);
  assert.equal(chains.length,2);
  assert.ok(Math.abs(chains[0].end-chains[0].start-10)<1e-9);
});
test('aberturas siguen una pared rotada y duplicarla la desplaza perpendicularmente',()=>{
  const diagonal = {...wall,x2:3,y2:4};
  const p = openingPoints({offset:1,width:1},diagonal);
  assert.deepEqual(p,{x1:.6,y1:.8,x2:1.2,y2:1.6});
  const [copy] = duplicateObjects([diagonal],diagonal);
  assert.deepEqual([copy.x1,copy.y1,copy.x2,copy.y2],[-.4,.3,2.6,4.3]);
});

test('cotas separan 1.5 + ventana 1 + 1.5 y ubican el total hacia afuera',()=>{
  const walls=[wall,{...wall,id:'r',x1:4,y1:0,x2:4,y2:4},{...wall,id:'b',x1:4,y1:4,x2:0,y2:4},{...wall,id:'l',x1:0,y1:4,x2:0,y2:0}];
  const layout=dimensionLayout(walls,[],[{wall_id:'r',offset:1.5,width:1}]);
  const right=layout.find(c=>c.a.x===4&&c.b.x===4);
  assert.deepEqual(right.parts.map(p=>p.length),[1.5,1,1.5]);
  assert.equal(right.length,4);assert.equal(right.nx,1);
  assert.equal(layout.find(c=>c.a.y===0&&c.b.y===0).ny,-1);
  assert.equal(layout.find(c=>c.a.y===4&&c.b.y===4).ny,1);
  assert.equal(layout.find(c=>c.a.x===0&&c.b.x===0).nx,-1);
});

test('cotas combinan tramos invertidos y eliminan límites repetidos de modulación',()=>{
  const pieces=[{...wall,x2:1.5},{...wall,id:'b',x1:2.5,x2:1.5},{...wall,id:'c',x1:4,x2:2.5}];
  const layout=dimensionLayout(pieces,[...pieces,pieces[0]]);
  assert.equal(layout.length,1);assert.equal(layout[0].length,4);
  assert.deepEqual(layout[0].parts.map(p=>p.length),[1.5,1,1.5]);
});

test('cotas diagonales conservan longitud euclídea y tramos de las recetas',()=>{
  const diagonal={...wall,x2:3,y2:4};
  const layout=dimensionLayout([diagonal],[],[{wall_id:'a',offset:1.5,width:1}]);
  assert.equal(layout[0].length,5);
  const parts=layout[0].parts.map(p=>p.length);
  assert.ok(Math.abs(parts[0]-1.5)<1e-9);assert.ok(Math.abs(parts[1]-1)<1e-9);assert.ok(Math.abs(parts[2]-2.5)<1e-9);
});


test('crear abertura ocupa el tramo de 2 m y limita paredes largas a 2 m',()=>{
  assert.deepEqual(placeOpening({...wall,x2:2},{x:0,y:0}),{offset:0,width:2});
  assert.deepEqual(placeOpening(wall,{x:2,y:0}),{offset:1,width:2});
  const sibling={id:'b',wall_id:'a',offset:1.5,width:1};
  assert.equal(placeOpening(wall,{x:2,y:0},[sibling]),null);
  assert.deepEqual(placeOpening(wall,{x:3,y:0},[sibling]),{offset:2.5,width:1.5});
});
test('mover abertura conserva ancho, ajusta a medios metros y no atraviesa vecinas',()=>{
  const o={id:'v',wall_id:'a',offset:1,width:1};
  assert.deepEqual(editOpening(o,wall,null,.6),{...o,offset:1.5});
  assert.deepEqual(editOpening(o,wall,null,.123,[],false),{...o,offset:1.123});
  const sibling={id:'b',wall_id:'a',offset:3,width:1};
  assert.deepEqual(editOpening(o,wall,null,10,[sibling]),{...o,offset:2});
  assert.deepEqual(editOpening(o,wall,null,-10),{...o,offset:0});
});
test('estirar extremos conserva el opuesto y respeta pared, vecinas y mínimo',()=>{
  const o={id:'v',wall_id:'a',offset:1,width:1};
  assert.deepEqual(editOpening(o,wall,1,-.5),{...o,offset:.5,width:1.5});
  assert.deepEqual(editOpening(o,wall,2,.5),{...o,width:1.5});
  assert.deepEqual(editOpening(o,wall,1,10),{...o,offset:1.5,width:.5});
  const sibling={id:'b',wall_id:'a',offset:2.5,width:1};
  assert.deepEqual(editOpening(o,wall,2,10,[sibling]),{...o,width:1.5});
  assert.deepEqual(editOpening(o,wall,1,-10),{...o,offset:0,width:2});
  assert.equal(o.width,1);
});


test('puerta pasa de horizontal a vertical conservando ancho y se mueve en Y',()=>{
  const o={id:'p',kind:'door',wall_id:'a',offset:1,width:1,height:2.1,sill:0};
  const vertical={...wall,id:'v',x1:4,x2:4,y1:0,y2:4};
  const moved=transferOpening(o,{x:4.05,y:2},[wall,vertical]);
  assert.deepEqual(moved,{...o,wall_id:'v',offset:1.5});
  assert.deepEqual(openingPoints(moved,vertical),{x1:4,y1:1.5,x2:4,y2:2.5});
  assert.equal(editOpening(moved,vertical,null,.5).offset,2);
  assert.equal(transferOpening(o,{x:4,y:2},[wall,{...vertical,height:2}]),null);
  assert.equal(transferOpening(o,{x:4,y:2},[wall,vertical],[{id:'b',wall_id:'v',offset:1,width:2}]),null);
  assert.equal(transferOpening(o,{x:8,y:2},[wall,vertical]),null);
});
test('puerta en pared vertical invertida se coloca al arrastrar sin cambiar orientación de apertura',()=>{
  const o={id:'p',kind:'door',wall_id:'a',offset:1,width:1,height:2.1,sill:0,door_rotation:3};
  const vertical={...wall,id:'v',x1:4,x2:4,y1:4,y2:0};
  assert.deepEqual(transferOpening(o,{x:4,y:1},[wall,vertical]),{...o,wall_id:'v',offset:2.5});
});
test('apertura tiene cuatro posiciones con bisagras y lados distintos, incluso en vertical',()=>{
  const o={offset:1,width:1};
  const positions=[0,1,2,3].map(door_rotation=>doorSwing({...o,door_rotation},wall));
  assert.deepEqual(positions.map(p=>p.hinge.x),[1,2,1,2]);
  assert.deepEqual(positions.map(p=>p.open.y),[1,-1,-1,1]);
  assert.equal(new Set(positions.map(p=>JSON.stringify(p))).size,4);
  assert.deepEqual(doorSwing(o,{...wall,x2:0,y2:4}).open,{x:-1,y:1});
});


test('columnas ajustan a propuestas, pared vertical y módulos en diagonal',()=>{
  assert.deepEqual(columnPoint({x:1.91,y:.05},[wall],[{x:2,y:0}]),{x:2,y:0});
  const vertical={...wall,x1:4,x2:4,y2:4};
  assert.deepEqual(columnPoint({x:4.1,y:1.43},[vertical]),{x:4,y:1.5});
  const diagonal={...wall,x2:3,y2:4};
  assert.deepEqual(columnPoint({x:.91,y:1.21},[diagonal]),{x:.9,y:1.2});
  assert.deepEqual(columnPoint({x:1.12,y:.1},[wall],[],false),{x:1.12,y:0});
});


test('puertas nuevas usan módulos baño 1.5, Estándar 2 y Amplia 3, nunca 1',()=>{
  assert.equal(placeOpening({...wall,x2:1.5},{x:.5,y:0},[],'door').width,1.5);
  assert.equal(placeOpening({...wall,x2:2},{x:1,y:0},[],'door').width,2);
  assert.equal(placeOpening({...wall,x2:3},{x:1,y:0},[],'door').width,3);
  assert.equal(placeOpening({...wall,x2:1},{x:.5,y:0},[],'door'),null);
  const o={id:'p',kind:'door',wall_id:'a',offset:1,width:2};
  assert.equal(editOpening(o,wall,2,1).width,3);
  assert.equal(editOpening(o,wall,2,-1).width,1.5);
  assert.equal(editOpening(o,wall,1,.5).width,1.5);
  assert.equal(editOpening(o,wall,null,.5).width,2);
});


test('identificadores funcionan sin randomUUID, como en HTTP LAN, con formato UUID v4',()=>{
  const onlyRandomValues={getRandomValues:array=>globalThis.crypto.getRandomValues(array)};
  const ids=Array.from({length:10000},()=>uid(onlyRandomValues));
  assert.equal(new Set(ids).size,ids.length);
  assert.ok(ids.every(id=>/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id)));
});
test('identificadores conservan versión y variante UUID incluso con bits extremos',()=>{
  assert.equal(uid({getRandomValues:array=>array.fill(255)}),'ffffffff-ffff-4fff-bfff-ffffffffffff');
  assert.equal(uid({getRandomValues:array=>array.fill(0)}),'00000000-0000-4000-8000-000000000000');
  assert.equal(uid({randomUUID:()=> 'native-id',getRandomValues:()=>{throw Error('No debería usarse');}}),'native-id');
  assert.throws(()=>uid({}),/navegador/);
});


test('crear puerta del tipo elegido nunca la reduce a otro tipo si no cabe',()=>{
  for(const width of [1.5,2,3]) {
    assert.equal(placeOpening(wall,{x:2,y:0},[],'door',width).width,width);
    assert.equal(placeOpening({...wall,x2:width-.5},{x:0,y:0},[],'door',width),null);
  }
  for(const width of [.5,1,2.5])assert.equal(placeOpening(wall,{x:2,y:0},[],'door',width),null);
  const occupied={id:'window',kind:'window',wall_id:wall.id,offset:1.5,width:2.5};
  assert.equal(placeOpening(wall,{x:.5,y:0},[occupied],'door',2),null);
  assert.equal(placeOpening(wall,{x:.5,y:0},[occupied],'door',1.5).width,1.5);
});

test('arrastrar ambos extremos mantiene módulos válidos aun sin ajuste de cuadrícula',()=>{
  const opening={id:'d',kind:'door',wall_id:wall.id,offset:.5,width:2};
  for(const endpoint of [1,2])for(const snap of [true,false])for(let i=-40;i<=40;i++) {
    const result=editOpening(opening,wall,endpoint,i/10,[opening],snap);
    if(result) {
      assert.ok([1.5,2,3].includes(result.width));
      assert.ok(result.offset>=0 && result.offset+result.width<=4);
    }
  }
});
