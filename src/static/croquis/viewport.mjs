// Camera math only: drawing geometry and material quantities are unaffected.
export function unionBounds(rectangles) {
  const boxes=rectangles.filter(b=>b&&[b.x,b.y,b.width,b.height].every(Number.isFinite)&&b.width>=0&&b.height>=0&&(b.width>0||b.height>0));
  if(!boxes.length)return null;
  const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y));
  return {x,y,width:Math.max(...boxes.map(b=>b.x+b.width))-x,height:Math.max(...boxes.map(b=>b.y+b.height))-y};
}
export function centerViewOnBounds(view,bounds) {
  if(!bounds)return [...view];
  return [bounds.x+bounds.width/2-view[2]/2,bounds.y+bounds.height/2-view[3]/2,view[2],view[3]];
}
export function fitViewToBounds(bounds,viewport={width:4,height:3}) {
  if(!bounds)return [-2,-2,16,12];
  const ratio=viewport.width>0&&viewport.height>0?viewport.width/viewport.height:4/3;
  let width=Math.max(6,bounds.width+1.6),height=Math.max(5,bounds.height+1.6);
  if(width/height<ratio)width=height*ratio;else height=width/ratio;
  return centerViewOnBounds([0,0,width,height],bounds);
}
