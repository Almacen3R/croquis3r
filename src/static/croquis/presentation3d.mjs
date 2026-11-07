// Visual settings only: never used to calculate quantities or prices.
import {ShapeUtils,Vector2} from './vendor/three/three.core.js';
export const DEFAULT_PRESENTATION={wall_color:'ivory',floor_finish:'tile',roof_type:'none',roof_color:'charcoal',roof_rise:.8,ridge_axis:'x'};
export function presentationSettings(document) {
  return {...DEFAULT_PRESENTATION,...document.presentation3d};
}

const EPS=1e-7;
export function insideRing(point,ring) {
  let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const a=ring[i],b=ring[j];
    if((a.y>point.z)!==(b.y>point.z)&&point.x<(b.x-a.x)*(point.z-a.y)/(b.y-a.y)+a.x)inside=!inside;
  }
  return inside;
}

// Clip floor polygons at the ridge so each roof face remains planar, even in L plans.
function clip(ring,axis,value,sign) {
  const result=[];
  for(let i=0;i<ring.length;i++) {
    const a=ring[i],b=ring[(i+1)%ring.length];
    const da=(a[axis]-value)*sign,db=(b[axis]-value)*sign;
    if(da>=-EPS)result.push(a);
    if((da>EPS&&db<-EPS)||(da<-EPS&&db>EPS)) {
      const t=(value-a[axis])/(b[axis]-a[axis]);
      result.push({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t});
    }
  }
  return result;
}

export function buildRoof(scene,settings) {
  const surfaces=[],closures=[];
  if(settings.roof_type==='none'||!scene.floors.length)return {surfaces,closures};
  const points=scene.floors.flat();
  const crossAxis=settings.ridge_axis==='x'?'y':'x';
  const low=Math.min(...points.map(p=>p[crossAxis])),high=Math.max(...points.map(p=>p[crossAxis]));
  const middle=(low+high)/2,half=(high-low)/2;
  const heights=scene.boxes.filter(b=>b.role==='wall').map(b=>b.position[1]+b.size[1]/2);
  const base=(heights.length?Math.max(...heights):2.5)+.04;
  const elevation=p=>base+(settings.roof_type==='gable'&&half>EPS?settings.roof_rise*Math.max(0,1-Math.abs(p[crossAxis]-middle)/half):0);
  const vertex=p=>[p.x,elevation(p),p.y];
  const perimeter=new Map(),key=p=>`${p.x.toFixed(6)},${p.y.toFixed(6)}`;
  for(const ring of scene.floors) {
    // Triangulate before clipping: a U-shaped ring can split into disconnected pieces.
    const triangles=ShapeUtils.triangulateShape(ring.map(p=>new Vector2(p.x,p.y)),[]).map(ids=>ids.map(i=>ring[i]));
    const parts=settings.roof_type==='gable'?triangles.flatMap(triangle=>[clip(triangle,crossAxis,middle,1),clip(triangle,crossAxis,middle,-1)]):[ring];
    for(const part of parts)if(part.length>=3)surfaces.push(part.map(vertex));
    for(let i=0;i<ring.length;i++) {
      const a=ring[i],b=ring[(i+1)%ring.length],id=[key(a),key(b)].sort().join('|');
      if(perimeter.has(id))perimeter.delete(id);else perimeter.set(id,[a,b]);
    }
  }
  // Fill gable ends on the external perimeter, never across internal room divisions.
  for(const [a,b] of perimeter.values()) {
    const cuts=[a];
    if((a[crossAxis]-middle)*(b[crossAxis]-middle)<-EPS) {
      const t=(middle-a[crossAxis])/(b[crossAxis]-a[crossAxis]);
      cuts.push({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t});
    }
    cuts.push(b);
    for(let i=1;i<cuts.length;i++) {
      const p=cuts[i-1],q=cuts[i];
      if(elevation(p)>base+EPS||elevation(q)>base+EPS)
        // End at the underside of the 8 cm roof slab, avoiding coplanar flicker.
        closures.push([[p.x,base-.04,p.y],[q.x,base-.04,q.y],
          [q.x,elevation(q)-.08,q.y],[p.x,elevation(p)-.08,p.y]]);
    }
  }
  return {surfaces,closures};
}

// Circle against oriented wall/frame/column and door rectangles at body height.
export function walkBlocked(scene,position,doorsOpen=false,radius=.18) {
  const obstacles=[...scene.boxes,...scene.openings.map(o=>({
    ...o,position:doorsOpen&&o.kind==='door'?o.openPosition:o.position,rotation:doorsOpen&&o.kind==='door'?o.openRotation:o.rotation,
  }))];
  return obstacles.some(box=>{
    if(box.position[1]-box.size[1]/2>1.75||box.position[1]+box.size[1]/2<.05)return false;
    const dx=position.x-box.position[0],dz=position.z-box.position[2];
    const c=Math.cos(box.rotation),s=Math.sin(box.rotation);
    const x=c*dx-s*dz,z=s*dx+c*dz;
    const nx=Math.max(0,Math.abs(x)-box.size[0]/2),nz=Math.max(0,Math.abs(z)-box.size[2]/2);
    return nx*nx+nz*nz<radius*radius;
  });
}

export function findWalkStart(scene) {
  for(const ring of [...scene.floors].sort((a,b)=>b.length-a.length)) {
    const minX=Math.min(...ring.map(p=>p.x)),maxX=Math.max(...ring.map(p=>p.x));
    const minZ=Math.min(...ring.map(p=>p.y)),maxZ=Math.max(...ring.map(p=>p.y));
    const center={x:(minX+maxX)/2,z:(minZ+maxZ)/2};
    const candidates=[center];
    for(let i=1;i<16;i++)for(let j=1;j<16;j++)candidates.push({x:minX+(maxX-minX)*i/16,z:minZ+(maxZ-minZ)*j/16});
    for(const point of candidates)if(insideRing(point,ring)&&!walkBlocked(scene,point))return point;
  }
  return null;
}

export function walkStep(scene,position,delta,doorsOpen=false) {
  const steps=Math.max(1,Math.ceil(Math.hypot(delta.x,delta.z)/.06));
  const point={...position},dx=delta.x/steps,dz=delta.z/steps;
  for(let i=0;i<steps;i++) {
    const next={x:point.x+dx,z:point.z+dz};
    if(!walkBlocked(scene,next,doorsOpen)){Object.assign(point,next);continue;}
    // Sliding avoids sticking to walls when walking diagonally.
    if(!walkBlocked(scene,{x:point.x+dx,z:point.z},doorsOpen))point.x+=dx;
    if(!walkBlocked(scene,{x:point.x,z:point.z+dz},doorsOpen))point.z+=dz;
  }
  return point;
}
