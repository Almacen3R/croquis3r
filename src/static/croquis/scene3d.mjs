// Renderer-independent scene in meters. Plan (x,y) becomes world (x,height,z=y).
// Shared geometric contract for the browser and a future Blender worker.
const {floorArea,doorSwing}=await import(`./geometry.mjs${new URL(import.meta.url).search}`);

const EPS = 1e-6;
const clamp = (v, low, high) => Math.max(low, Math.min(high, v));
const sorted = values => [...new Set(values)].sort((a,b) => a-b);

export function buildHouseScene(document) {
  const walls = document.objects.filter(o => o.kind === 'wall');
  const boxes = [], openings = [], warnings = [];
  const point = (w, distance, elevation) => {
    const length = Math.hypot(w.x2-w.x1,w.y2-w.y1);
    return [w.x1+(w.x2-w.x1)*distance/length, elevation, w.y1+(w.y2-w.y1)*distance/length];
  };
  const wallBox = (wall, from, to, bottom, top, role='wall', depth=wall.thickness) => {
    if(to-from<EPS || top-bottom<EPS)return;
    boxes.push({source:wall.id,role,size:[to-from,top-bottom,depth],
      position:point(wall,(from+to)/2,(bottom+top)/2),
      rotation:-Math.atan2(wall.y2-wall.y1,wall.x2-wall.x1)});
  };
  for(const wall of walls) {
    const length = Math.hypot(wall.x2-wall.x1,wall.y2-wall.y1);
    if(!Number.isFinite(length)||length<EPS||!(wall.height>0)||!(wall.thickness>0)) {
      warnings.push('Una pared sin dimensiones válidas no se pudo representar.');continue;
    }
    const cuts = document.objects.filter(o => ['door','window'].includes(o.kind)&&o.wall_id===wall.id).map(o=>{
      const start=clamp(o.offset,0,length),end=clamp(o.offset+o.width,0,length);
      const bottom=clamp(o.sill||0,0,wall.height),top=clamp((o.sill||0)+o.height,0,wall.height);
      if(Math.abs(start-o.offset)>EPS||Math.abs(end-o.offset-o.width)>EPS||Math.abs(top-(o.sill||0)-o.height)>EPS)
        warnings.push('Una abertura excede su pared: la vista muestra solo la parte que cabe.');
      return {...o,start,end,bottom,top};
    }).filter(o=>o.end-o.start>EPS&&o.top-o.bottom>EPS);
    const xs=sorted([0,length,...cuts.flatMap(o=>[o.start,o.end])]);
    for(let i=1;i<xs.length;i++) {
      const a=xs[i-1],b=xs[i],middle=(a+b)/2;
      const at=cuts.filter(o=>middle>o.start&&middle<o.end);
      const ys=sorted([0,wall.height,...at.flatMap(o=>[o.bottom,o.top])]);
      for(let j=1;j<ys.length;j++) {
        const bottom=ys[j-1],top=ys[j],center=(bottom+top)/2;
        if(!at.some(o=>center>o.bottom&&center<o.top))wallBox(wall,a,b,bottom,top);
      }
    }
    for(const o of cuts) {
      const width=o.end-o.start,height=o.top-o.bottom,frame=Math.min(.045,width/8,height/8);
      wallBox(wall,o.start,o.start+frame,o.bottom,o.top,'frame',wall.thickness+.025);
      wallBox(wall,o.end-frame,o.end,o.bottom,o.top,'frame',wall.thickness+.025);
      wallBox(wall,o.start,o.end,o.top-frame,o.top,'frame',wall.thickness+.025);
      if(o.kind==='window')wallBox(wall,o.start,o.end,o.bottom,o.bottom+frame,'frame',wall.thickness+.025);
      const center=point(wall,(o.start+o.end)/2,(o.bottom+o.top)/2);
      const clipped={...o,offset:o.start,width};
      const swing=o.kind==='door'?doorSwing(clipped,wall):null;
      openings.push({source:o.id,kind:o.kind,size:[width-2*frame,height-frame*(o.kind==='window'?2:1),o.kind==='window'?.025:.04],
        position:[center[0],center[1]-(o.kind==='door'?frame/2:0),center[2]],
        rotation:-Math.atan2(wall.y2-wall.y1,wall.x2-wall.x1),
        ...(swing?{openPosition:[(swing.hinge.x+swing.open.x)/2,center[1]-frame/2,(swing.hinge.y+swing.open.y)/2],
          openRotation:-Math.atan2(swing.open.y-swing.hinge.y,swing.open.x-swing.hinge.x)}:{})});
    }
  }
  for(const column of document.columns||[]) {
    const adjacent=walls.filter(w=>{
      const dx=w.x2-w.x1,dy=w.y2-w.y1,den=dx*dx+dy*dy;
      const t=den?clamp(((column.x-w.x1)*dx+(column.y-w.y1)*dy)/den,0,1):0;
      return Math.hypot(column.x-w.x1-t*dx,column.y-w.y1-t*dy)<.2;
    }).map(w=>w.height);
    const height=adjacent.length?Math.max(...adjacent):Math.max(2.5,...walls.map(w=>w.height));
    boxes.push({source:column.id,role:'column',size:[.21,height,.21],position:[column.x,height/2,column.y],rotation:0});
  }
  const floor=floorArea(walls,{includeRegions:true});
  if(!floor.regions.length)warnings.push('Cierra el contorno para mostrar el piso de la casa.');
  else if(floor.partial)warnings.push('El piso aparece únicamente en los recintos cerrados.');
  if(document.ticoblock?.floor_level===2)warnings.push('Se representa una sola planta; el nivel de cálculo no define otro piso en 3D.');
  return {version:1,units:'m',axes:'x horizontal, y up, z plan-y',boxes,openings,
    floors:floor.regions,area:floor.area,warnings:[...new Set(warnings)]};
}
