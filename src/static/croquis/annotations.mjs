export const isAnnotation=obj=>['text','arrow'].includes(obj?.kind);
export function moveAnnotation(original,dx,dy,endpoint=null) {
  const result={...original};
  const keys=original.kind==='text'?['x','y']:endpoint?[`x${endpoint}`,`y${endpoint}`]:['x1','y1','x2','y2'];
  for(const key of keys){result[key]=+(original[key]+(key.startsWith('x')?dx:dy)).toFixed(3);if(Math.abs(result[key])>100)return null;}
  if(result.kind==='arrow'&&Math.hypot(result.x2-result.x1,result.y2-result.y1)<.1)return null;
  return result;
}
export function drawAnnotations(annotations,draw,parent,selected=null) {
  for(const a of annotations) {
    const color=({black:'#172e29',blue:'#174e99',red:'#a52323'})[a.color||'black'];
    const group=draw('g',{'data-object':a.id,'data-annotation':a.kind,cursor:'move'},parent);
    if(a.kind==='arrow') {
      const angle=Math.atan2(a.y2-a.y1,a.x2-a.x1),head=Math.min(.22,Math.hypot(a.x2-a.x1,a.y2-a.y1)*.35);
      draw('line',{x1:a.x1,y1:a.y1,x2:a.x2,y2:a.y2,stroke:color,'stroke-width':.04,'stroke-linecap':'round'},group);
      draw('path',{d:`M ${a.x2} ${a.y2} L ${a.x2-head*Math.cos(angle-.45)} ${a.y2-head*Math.sin(angle-.45)} L ${a.x2-head*Math.cos(angle+.45)} ${a.y2-head*Math.sin(angle+.45)} Z`,fill:color},group);
      draw('line',{x1:a.x1,y1:a.y1,x2:a.x2,y2:a.y2,stroke:'transparent','stroke-width':.25,'data-annotation-hit':''},group);
    }
    const x=a.kind==='text'?a.x:a.x1,y=a.kind==='text'?a.y:a.y1-.18,size=a.font_size||.25;
    if(a.text) {
      const text=draw('text',{x,y,fill:color,'font-family':'Arial, sans-serif','font-size':size,'font-weight':700,'paint-order':'stroke',stroke:'#fff','stroke-width':.045,'stroke-linejoin':'round'},group);
      a.text.replace(/\r\n?/g,'\n').split('\n').forEach((line,i)=>draw('tspan',{x,dy:i?size*1.3:0},text,line||' '));
      const bounds=text.getBBox();
      draw('rect',{x:bounds.x-.06,y:bounds.y-.04,width:Math.max(.2,bounds.width+.12),height:Math.max(size,bounds.height+.08),fill:'transparent','data-annotation-hit':''},group);
      if(a.id===selected)draw('rect',{x:bounds.x-.08,y:bounds.y-.06,width:Math.max(.2,bounds.width+.16),height:bounds.height+.12,fill:'none',stroke:color,'stroke-width':.018,'stroke-dasharray':'.08 .05','data-handle':'selection','pointer-events':'none'},group);
    }
    if(a.id===selected&&a.kind==='arrow')for(const n of [1,2])draw('circle',{cx:a[`x${n}`],cy:a[`y${n}`],r:.09,fill:'#fff',stroke:color,'stroke-width':.03,'data-object':a.id,'data-endpoint':n},group);
  }
}
