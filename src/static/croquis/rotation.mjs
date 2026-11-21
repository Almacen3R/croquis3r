// Quarter-turn on the 0.50 m grid; openings keep their wall-relative dimensions.
export function rotateDrawingLeft(document) {
  const result=JSON.parse(JSON.stringify(document));
  const points=[];
  for(const o of [...result.objects,...(result.columns||[]),...(result.annotations||[])]) {
    for(const [x,y] of [['x','y'],['x1','y1'],['x2','y2']])if(Number.isFinite(o[x])&&Number.isFinite(o[y]))points.push({x:o[x],y:o[y]});
  }
  if(!points.length)return result;
  // The fixed origin preserves grid positions and makes four turns exact.
  const cx=0,cy=0;
  for(const o of [...result.objects,...(result.columns||[]),...(result.annotations||[])]) {
    for(const [x,y] of [['x','y'],['x1','y1'],['x2','y2']])if(Number.isFinite(o[x])&&Number.isFinite(o[y])) {
      const nextX=+(cx+o[y]-cy).toFixed(3),nextY=+(cy-o[x]+cx).toFixed(3);
      if(Math.abs(nextX)>100||Math.abs(nextY)>100)throw new Error('El giro saldría de los límites del croquis (±100 m).');
      o[x]=nextX;o[y]=nextY;
    }
  }
  if(result.presentation3d && (result.presentation3d.ridge_axis || result.presentation3d.roof_type==='gable')) {
    result.presentation3d.ridge_axis=result.presentation3d.ridge_axis==='z'?'x':'z';
  }
  return result;
}
