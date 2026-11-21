// Presentation-only geometry. Never added to the construction document or quantities.
const {buildRoof,insideRing}=await import(`./presentation3d.mjs${new URL(import.meta.url).search}`);
export function openingDetails(opening) {
  const [w,h,d]=opening.size,details=[];
  const add=(role,size,position)=>details.push({role,size,position,rotation:0});
  if(opening.kind==='window') {
    if(w>=.85)add('frame',[.028,h,.045],[0,0,0]);
    if(h>=.9)add('frame',[w,.022,.045],[0,-h*.08,0]);
    add('sill',[w+.09,.035,.20],[0,-h/2-.035,0]);
  } else {
    const handleSide=opening.handleSide||1;
    for(const side of [-1,1]) {
      for(const y of [-h*.23,h*.23])add('door',[w*.76,h*.34,.012],[0,y,side*(d/2+.006)]);
      add('metal',[.04,.15,.018],[handleSide*w*.33,-h*.035,side*(d/2+.016)]);
      add('metal',[Math.min(.13,w*.22),.024,.045],[handleSide*(w*.33-.035),-h*.035,side*(d/2+.048)]);
    }
  }
  return details;
}
export function worldOpeningDetails(opening) {
  const c=Math.cos(opening.rotation),s=Math.sin(opening.rotation);
  return openingDetails(opening).map(detail=>({...detail,rotation:opening.rotation,
    position:[opening.position[0]+c*detail.position[0]+s*detail.position[2],
      opening.position[1]+detail.position[1],opening.position[2]-s*detail.position[0]+c*detail.position[2]]}));
}
export function facadeCamera(scene,roof) {
  const points=[...scene.boxes.flatMap(b=>[-1,1].flatMap(x=>[-1,1].flatMap(y=>[-1,1].map(z=>[b.position[0]+Math.cos(b.rotation)*x*b.size[0]/2+Math.sin(b.rotation)*z*b.size[2]/2,b.position[1]+y*b.size[1]/2,b.position[2]-Math.sin(b.rotation)*x*b.size[0]/2+Math.cos(b.rotation)*z*b.size[2]/2])))),...roof.surfaces.flat()];
  const low=[0,1,2].map(i=>Math.min(...points.map(p=>p[i]))),high=[0,1,2].map(i=>Math.max(...points.map(p=>p[i])));
  const target=low.map((v,i)=>(v+high[i])/2),radius=Math.max(2,Math.hypot(...low.map((v,i)=>high[i]-v))/2);
  let normal=[1,1];
  for(const door of scene.openings.filter(o=>o.kind==='door').sort((a,b)=>b.size[0]-a.size[0])) {
    const nx=Math.sin(door.rotation),nz=Math.cos(door.rotation),[x,,z]=door.position;
    const inside=side=>scene.floors.some(ring=>insideRing({x:x+side*nx*.3,z:z+side*nz*.3},ring));
    const plus=inside(1),minus=inside(-1);
    if(plus===minus)continue;
    const side=plus?-1:1;normal=[nx*side,nz*side];break;
  }
  const direction=[normal[0]+normal[1]*.28,.36,normal[1]-normal[0]*.28];
  const norm=Math.hypot(...direction),distance=radius*2.85;
  return {position:target.map((v,i)=>v+direction[i]/norm*distance),target,fov:42};
}
export function buildRenderPresentation(scene,settings,view=null) {
  const roof=view?.hideRoof?{surfaces:[],closures:[]}:buildRoof(scene,settings);
  const openings=scene.openings.map(o=>view?.doorsOpen&&o.kind==='door'?{...o,position:[...o.openPosition],rotation:o.openRotation}:{...o});
  return {...scene,settings:{...settings},openings,roof,details:openings.flatMap(worldOpeningDetails),
    camera:view?{position:[...view.position],target:[...view.target],fov:view.fov}:facadeCamera(scene,roof)};
}
