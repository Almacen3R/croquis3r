export const length = wall => Math.hypot(wall.x2 - wall.x1, wall.y2 - wall.y1);
export const clone = value => JSON.parse(JSON.stringify(value));
export function uid(crypto = globalThis.crypto) {
  if (typeof crypto?.randomUUID === 'function') return crypto.randomUUID();
  // randomUUID exige un contexto seguro; getRandomValues también funciona en HTTP LAN.
  if (typeof crypto?.getRandomValues !== 'function') {
    throw new Error('Este navegador no permite generar identificadores. Usa un navegador actualizado.');
  }
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}
export const GRID_STEP = 0.5; // Metros por cuadro, módulo mínimo de las recetas recibidas.

export function resizeEndpoint(wall, endpoint, point, walls, enabled = true, minimumLength = .1) {
  const p = snapPoint(point, walls, enabled, wall.id);
  const result = {...wall, [`x${endpoint}`]: p.x, [`y${endpoint}`]: p.y};
  if (length(result) + 1e-9 < minimumLength || Math.abs(p.x) > 100 || Math.abs(p.y) > 100) return null;
  return result;
}

export function snapPoint(point, walls, enabled = true, excludedId = null) {
  if (!enabled) return {x: +point.x.toFixed(3), y: +point.y.toFixed(3)};
  let best = null, distance = 0.18;
  for (const wall of walls.filter(w => w.id !== excludedId)) {
    for (const n of [1, 2]) {
      const p = {x: wall[`x${n}`], y: wall[`y${n}`]};
      const d = Math.hypot(point.x - p.x, point.y - p.y);
      if (d < distance) { best = p; distance = d; }
    }
  }
  return best || {x: Math.round(point.x / GRID_STEP) * GRID_STEP, y: Math.round(point.y / GRID_STEP) * GRID_STEP};
}

// Una cota continua para tramos colineales contiguos; los objetos siguen siendo editables.
export function dimensionChains(walls) {
  const groups = new Map();
  const diagonalGroups = new Map();
  for (const wall of walls) {
    if (wall.x1 !== wall.x2 && wall.y1 !== wall.y2) {
      const l = length(wall), sign = wall.x2 > wall.x1 ? 1 : -1;
      const ux = sign * (wall.x2-wall.x1)/l, uy = sign * (wall.y2-wall.y1)/l;
      const fixed = -uy*wall.x1+ux*wall.y1;
      const key = [ux,uy,fixed].map(v=>(Math.round(v*1e6)/1e6).toFixed(6)).join(':');
      const values = [ux*wall.x1+uy*wall.y1,ux*wall.x2+uy*wall.y2];
      if (!diagonalGroups.has(key)) diagonalGroups.set(key, []);
      diagonalGroups.get(key).push({diagonal:true,ux,uy,fixed,start:Math.min(...values),end:Math.max(...values)});
      continue;
    }
    const horizontal = wall.y1 === wall.y2;
    const fixed = horizontal ? wall.y1 : wall.x1;
    const values = horizontal ? [wall.x1, wall.x2] : [wall.y1, wall.y2];
    const key = `${horizontal}:${fixed}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({horizontal, fixed, start: Math.min(...values), end: Math.max(...values)});
  }
  const chains = [];
  for (const group of groups.values()) {
    group.sort((a, b) => a.start - b.start);
    for (const segment of group) {
      const previous = chains.at(-1);
      if (previous && previous.horizontal === segment.horizontal && previous.fixed === segment.fixed && segment.start <= previous.end + 0.001) {
        previous.end = Math.max(previous.end, segment.end);
      } else chains.push({...segment});
    }
  }
  for (const group of diagonalGroups.values()) {
    group.sort((a,b)=>a.start-b.start);
    const merged = [];
    for (const segment of group) {
      const previous = merged.at(-1);
      if (previous && segment.start <= previous.end + .001) previous.end = Math.max(previous.end, segment.end);
      else merged.push({...segment});
    }
    chains.push(...merged);
  }
  return chains;
}

export function openingPoints(opening, wall) {
  const l = length(wall), ux = (wall.x2 - wall.x1) / l, uy = (wall.y2 - wall.y1) / l;
  const x = wall.x1 + ux * opening.offset, y = wall.y1 + uy * opening.offset;
  return {x1: x, y1: y, x2: x + ux * opening.width, y2: y + uy * opening.width};
}

const rounded = value => +value.toFixed(3);
export function projectOnWall(point, wall) {
  return ((point.x-wall.x1)*(wall.x2-wall.x1)+(point.y-wall.y1)*(wall.y2-wall.y1))/length(wall);
}

export function columnPoint(point, walls, proposals=[], snap=true) {
  if(snap){
    const near=proposals.map(p=>({...p,d:Math.hypot(p.x-point.x,p.y-point.y)})).filter(p=>p.d<.25).sort((a,b)=>a.d-b.d)[0];
    if(near)return {x:near.x,y:near.y};
  }
  const candidates=walls.map(w=>{
    const l=length(w), at=Math.max(0,Math.min(l,projectOnWall(point,w)));
    return {w,l,at,x:w.x1+(w.x2-w.x1)*at/l,y:w.y1+(w.y2-w.y1)*at/l};
  }).map(c=>({...c,d:Math.hypot(c.x-point.x,c.y-point.y)})).filter(c=>c.d<.3).sort((a,b)=>a.d-b.d);
  if(candidates.length){
    const {w,l,at}=candidates[0],t=snap?Math.max(0,Math.min(l,Math.round(at/GRID_STEP)*GRID_STEP)):at;
    return {x:+(w.x1+(w.x2-w.x1)*t/l).toFixed(6),y:+(w.y1+(w.y2-w.y1)*t/l).toFixed(6)};
  }
  return snapPoint(point,walls,snap);
}

// Conserva el punto bajo el cursor y la proporción de la vista al ampliar.
export function zoomView(view, factor, anchor=null) {
  const [x,y,w,h]=view;
  const width=Math.max(1,Math.min(400,w*factor)),ratio=width/w;
  const at=anchor || {x:x+w/2,y:y+h/2};
  return [at.x-(at.x-x)*ratio,at.y-(at.y-y)*ratio,width,h*ratio];
}

export function doorSwing(opening, wall) {
  const p=openingPoints(opening,wall), rotation=opening.door_rotation || 0;
  const reverse=rotation%2===1, side=rotation<2?1:-1;
  const hinge=reverse?{x:p.x2,y:p.y2}:{x:p.x1,y:p.y1};
  const closed=reverse?{x:p.x1,y:p.y1}:{x:p.x2,y:p.y2};
  const dx=closed.x-hinge.x,dy=closed.y-hinge.y;
  const open={x:hinge.x-side*dy,y:hinge.y+side*dx};
  return {hinge,closed,open,sweep:side===1?0:1};
}

// Arrastrar el cuerpo conserva el ancho y permite pasar a otra pared cercana.
export function transferOpening(opening, point, walls, siblings=[], snap=true) {
  const candidates=walls.map(wall=>{
    const at=projectOnWall(point,wall), l=length(wall), t=Math.max(0,Math.min(l,at));
    const x=wall.x1+(wall.x2-wall.x1)*t/l,y=wall.y1+(wall.y2-wall.y1)*t/l;
    return {wall,at,distance:Math.hypot(point.x-x,point.y-y)};
  }).filter(c=>c.distance<=.35).sort((a,b)=>a.distance-b.distance);
  for(const {wall,at} of candidates){
    if(wall.id===opening.wall_id)return null;
    if(length(wall)<opening.width || wall.height<opening.sill+opening.height)continue;
    let offset=at-opening.width/2;
    if(snap)offset=Math.round(offset/GRID_STEP)*GRID_STEP;
    offset=rounded(Math.max(0,Math.min(length(wall)-opening.width,offset)));
    if(siblings.some(o=>o.id!==opening.id && o.wall_id===wall.id && offset<o.offset+o.width-1e-6 && offset+opening.width>o.offset+1e-6))continue;
    return {...opening,wall_id:wall.id,offset};
  }
  return null;
}

// El intervalo libre contiguo impide atravesar otra abertura durante el arrastre.
function openingBounds(opening, wall, siblings) {
  let low=0, high=length(wall);
  for (const other of siblings.filter(o=>o.wall_id===wall.id && o.id!==opening.id)) {
    if(other.offset+other.width<=opening.offset+1e-6) low=Math.max(low,other.offset+other.width);
    else if(other.offset>=opening.offset+opening.width-1e-6) high=Math.min(high,other.offset);
  }
  return {low,high};
}

export function editOpening(opening, wall, endpoint, distance, siblings=[], snap=true) {
  const {low,high}=openingBounds(opening,wall,siblings);
  const adjust=value=>snap?Math.round(value/GRID_STEP)*GRID_STEP:value;
  let start=opening.offset, end=start+opening.width;
  if(endpoint===1) start=Math.max(low,Math.min(end-.5,adjust(start+distance)));
  else if(endpoint===2) end=Math.min(high,Math.max(start+.5,adjust(end+distance)));
  else start=Math.max(low,Math.min(high-opening.width,adjust(start+distance)));
  const width=endpoint?end-start:opening.width;
  if(width<.5-1e-6 || start<low-1e-6 || start+width>high+1e-6) return null;
  if(opening.kind==='door' && endpoint){
    const available=endpoint===1?opening.offset+opening.width-low:high-opening.offset;
    const valid=[.5,1,1.5,2,3].filter(size=>size<=available+1e-6).sort((a,b)=>Math.abs(a-width)-Math.abs(b-width));
    if(!valid.length)return null;
    return {...opening,offset:rounded(endpoint===1?opening.offset+opening.width-valid[0]:opening.offset),width:valid[0]};
  }
  return {...opening,offset:rounded(start),width:rounded(width)};
}

export function placeOpening(wall, position, siblings=[], kind='window', requestedWidth=null) {
  const at=Math.max(0,Math.min(length(wall),projectOnWall(position,wall)));
  let low=0,high=length(wall);
  for(const other of siblings.filter(o=>o.wall_id===wall.id)) {
    if(at>other.offset+1e-6 && at<other.offset+other.width-1e-6) return null;
    if(other.offset+other.width<=at+1e-6)low=Math.max(low,other.offset+other.width);
    else if(other.offset>=at-1e-6)high=Math.min(high,other.offset);
  }
  const available=Math.floor((high-low+1e-6)/GRID_STEP)*GRID_STEP;
  const width=kind==='door'?(requestedWidth ?? (available>=2?2:available>=1.5?1.5:available>=1?1:available>=.5?.5:0)):Math.min(2,available);
  if(kind==='door' && (![.5,1,1.5,2,3].includes(width) || width>available+1e-6))return null;
  if(width<.5)return null;
  const offset=Math.max(low,Math.min(high-width,Math.round((at-width/2)/GRID_STEP)*GRID_STEP));
  return {offset:rounded(offset),width:rounded(width)};
}

// Dos niveles de cotas: partes cercanas a la pared y total hacia el exterior.
// Incluye límites dibujados, aberturas y la división propuesta por el servidor.
export function dimensionLayout(walls, segments = [], openings = []) {
  if (!walls.length) return [];
  const xs=walls.flatMap(w=>[w.x1,w.x2]), ys=walls.flatMap(w=>[w.y1,w.y2]);
  const center={x:(Math.min(...xs)+Math.max(...xs))/2,y:(Math.min(...ys)+Math.max(...ys))/2};
  const all=[...walls,...segments,...openings.flatMap(o=>{
    const wall=walls.find(w=>w.id===o.wall_id);return wall?[openingPoints(o,wall)]:[];
  })];
  return dimensionChains(walls).map(chain=>{
    const ux=chain.diagonal?chain.ux:chain.horizontal?1:0;
    const uy=chain.diagonal?chain.uy:chain.horizontal?0:1;
    const origin=chain.diagonal?{x:-uy*chain.fixed,y:ux*chain.fixed}:chain.horizontal?{x:0,y:chain.fixed}:{x:chain.fixed,y:0};
    const point=t=>({x:origin.x+ux*t,y:origin.y+uy*t});
    const middle=point((chain.start+chain.end)/2);
    let nx=uy,ny=-ux;
    if((middle.x-center.x)*nx+(middle.y-center.y)*ny < -1e-8){nx=-nx;ny=-ny;}
    const values=[chain.start,chain.end];
    for(const segment of all) for(const n of [1,2]) {
      const x=segment[`x${n}`],y=segment[`y${n}`];
      if(Math.abs(-uy*(x-origin.x)+ux*(y-origin.y))>1e-5)continue;
      const t=ux*(x-origin.x)+uy*(y-origin.y);
      if(t>chain.start+1e-5&&t<chain.end-1e-5)values.push(t);
    }
    values.sort((a,b)=>a-b);
    const unique=values.filter((v,i)=>i===0||v-values[i-1]>1e-5);
    const parts=unique.slice(0,-1).map((v,i)=>({a:point(v),b:point(unique[i+1]),length:unique[i+1]-v}));
    return {a:point(chain.start),b:point(chain.end),length:chain.end-chain.start,
      ux,uy,nx,ny,parts:parts.length>1?parts:[]};
  });
}

export function duplicateObjects(objects, object) {
  const copy = clone(object);
  copy.id = uid();
  copy.label = `${object.label || 'Objeto'} · copia`.slice(0, 100);
  if (copy.kind === 'wall') {
    const l = length(copy), dx = -(copy.y2-copy.y1)/l*.5, dy = (copy.x2-copy.x1)/l*.5;
    for (const n of [1, 2]) { copy[`x${n}`] = +(copy[`x${n}`]+dx).toFixed(3); copy[`y${n}`] = +(copy[`y${n}`]+dy).toFixed(3); }
    const children = objects.filter(o => o.wall_id === object.id).map(o => ({...clone(o), id: uid(), wall_id: copy.id}));
    return [copy, ...children];
  }
  copy.offset = +(copy.offset + copy.width + 0.1).toFixed(3);
  return [copy];
}

// El tipo se deriva del módulo para evitar metadatos contradictorios.
export function doorName(width) {
  return ({0.5:'Puerta de 0,50 m',1:'Puerta de 1 m',1.5:'Puerta de 1,50 m',2:'Puerta Estándar',3:'Puerta Amplia'})[width] || 'Puerta fuera de catálogo · corregir';
}


// Área de las caras cerradas del grafo de paredes, medida sobre sus líneas de referencia.
// Divide cruces/T antes de recorrer caras; las divisiones interiores no duplican superficie.
export function floorArea(walls) {
  const eps=1e-7, cross=(a,b)=>a.x*b.y-a.y*b.x;
  const edges=new Map(), nodes=new Map();
  const key=p=>`${+p.x.toFixed(6)},${+p.y.toFixed(6)}`;
  const point=(w,t)=>({x:w.x1+(w.x2-w.x1)*t,y:w.y1+(w.y2-w.y1)*t});
  const cuts=walls.map(()=>[0,1]);
  for(let i=0;i<walls.length;i++)for(let j=i+1;j<walls.length;j++) {
    const a=walls[i],b=walls[j],r={x:a.x2-a.x1,y:a.y2-a.y1},s={x:b.x2-b.x1,y:b.y2-b.y1};
    const q={x:b.x1-a.x1,y:b.y1-a.y1},d=cross(r,s);
    if(Math.abs(d)>eps) {
      const t=cross(q,s)/d,u=cross(q,r)/d;
      if(t>=-eps&&t<=1+eps&&u>=-eps&&u<=1+eps){cuts[i].push(Math.max(0,Math.min(1,t)));cuts[j].push(Math.max(0,Math.min(1,u)));}
    } else if(Math.abs(cross(q,r))<eps) {
      for(const [w,v,index] of [[a,b,i],[b,a,j]])for(const n of [1,2]) {
        const dx=w.x2-w.x1,dy=w.y2-w.y1,den=dx*dx+dy*dy;
        if(den<eps)continue;
        const t=((v[`x${n}`]-w.x1)*dx+(v[`y${n}`]-w.y1)*dy)/den;
        if(t>eps&&t<1-eps)cuts[index].push(t);
      }
    }
  }
  const connect=(a,b)=>{
    const ka=key(a),kb=key(b);if(ka===kb)return;
    for(const [k,p] of [[ka,a],[kb,b]])if(!nodes.has(k))nodes.set(k,{...p,adj:new Set()});
    nodes.get(ka).adj.add(kb);nodes.get(kb).adj.add(ka);
    edges.set([ka,kb].sort().join('|'),[ka,kb]);
  };
  walls.forEach((w,i)=>{const ts=[...new Set(cuts[i])].sort((a,b)=>a-b);for(let n=1;n<ts.length;n++)connect(point(w,ts[n-1]),point(w,ts[n]));});
  for(const node of nodes.values())node.adj=[...node.adj].sort((a,b)=>Math.atan2(nodes.get(a).y-node.y,nodes.get(a).x-node.x)-Math.atan2(nodes.get(b).y-node.y,nodes.get(b).x-node.x));
  const visited=new Set(),faces=[],used=new Set();
  for(const [a,b] of edges.values())for(const [start,end] of [[a,b],[b,a]]) {
    if(visited.has(`${start}|${end}`))continue;
    let u=start,v=end;const ring=[],ringEdges=[];
    do {
      visited.add(`${u}|${v}`);ring.push(nodes.get(u));ringEdges.push([u,v].sort().join('|'));
      const adjacent=nodes.get(v).adj,index=adjacent.indexOf(u),next=adjacent[(index+adjacent.length-1)%adjacent.length];
      u=v;v=next;
    } while((u!==start||v!==end)&&ring.length<=2*edges.size);
    const area=ring.reduce((sum,p,i)=>sum+cross(p,ring[(i+1)%ring.length]),0)/2;
    if(area>eps){faces.push({ring,area});for(const e of ringEdges)used.add(e);}
  }
  const inside=(p,ring)=>{
    let found=false;
    for(let i=0,j=ring.length-1;i<ring.length;j=i++) {
      const a=ring[i],b=ring[j];
      if((a.y>p.y)!==(b.y>p.y)&&p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x)found=!found;
    }
    return found;
  };
  // Un recinto cerrado aislado dentro de otro ya forma parte de su superficie.
  // Las caras de un mismo componente ya son disjuntas. Solo comparar
  // componentes separados evita trabajo cuadrático en croquis con muchos cuartos.
  let component=0;
  for(const node of nodes.values())if(node.component===undefined) {
    const pending=[node];node.component=component++;
    while(pending.length){const current=pending.pop();for(const k of current.adj){const next=nodes.get(k);if(next.component===undefined){next.component=node.component;pending.push(next);}}}
  }
  const groups=new Map();
  for(const face of faces){const id=face.ring[0].component;if(!groups.has(id))groups.set(id,[]);groups.get(id).push(face);}
  const area=faces.filter(face=>![...groups].some(([id,others])=>id!==face.ring[0].component&&others.some(outer=>outer.area>face.area+eps&&face.ring.every(p=>inside(p,outer.ring))))).reduce((sum,f)=>sum+f.area,0);
  return {area:area>eps?+area.toFixed(6):null,partial:used.size<edges.size};
}
