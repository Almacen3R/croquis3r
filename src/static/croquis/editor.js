const {length, clone, uid, snapPoint, dimensionLayout, openingPoints, duplicateObjects, resizeEndpoint, editOpening, placeOpening, transferOpening, doorSwing, columnPoint, doorName, floorArea, zoomView} = await import(`./geometry.mjs${new URL(import.meta.url).search}`);
const {requestJson, cookieValue} = await import(`./http.mjs${new URL(import.meta.url).search}`);

const {packProject, projectFilename, downloadBlob, drawingPng, pdfFromPng} = await import(`./project-files.mjs${new URL(import.meta.url).search}`);

const $ = id => document.getElementById(id);
const {setupPanels}=await import(`./panels.mjs${new URL(import.meta.url).search}`);
setupPanels(document.querySelector('.workspace'));
const svg = $('canvas');
const NS = 'http://www.w3.org/2000/svg';
const state = {document: {version: 1, objects: []}, selected: null, tool: 'select', start: null,
  articles: [], templates: [], id: null, revision: null, isTemplate: false, dirty: false,
  history: [], future: [], estimate: null, estimateTimer: null, estimateRequest: 0, view: [-2, -2, 16, 12]};
let drag = null;
let panDrag = null;
let settingsDirty = false;
let downloadInProgress = false;
const walls = () => state.document.objects.filter(o => o.kind === 'wall');
const allObjects = () => [...state.document.objects,...(state.document.columns||[])];
const selected = () => allObjects().find(o => o.id === state.selected);
const fmt = value => Number(value).toLocaleString('es-CR', {maximumFractionDigits: 2, minimumFractionDigits: 2});
const typeName = kind => ({wall: 'Pared', door: 'Puerta', window: 'Ventana', column:'Columna'}[kind]);
const objectName = obj => obj.kind==='door' ? ([2,3].includes(obj.width) ? `${doorName(obj.width)} · ${fmt(obj.width)} m` : doorName(obj.width)) : obj.label || typeName(obj.kind);
const basisName = basis => ({area: 'm² netos', length: 'm lineales', object: 'objeto'}[basis]);

function element(tag, attrs = {}, content = null) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (content !== null) node.textContent = content;
  return node;
}
function shape(tag, attrs, parent = $('scene'), text = null) {
  const node = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== null) node.textContent = text;
  parent.append(node);
  return node;
}
function message(text, error = false) {
  $('message').hidden = !text;
  $('message').textContent = text;
  $('message').classList.toggle('error', error);
}
async function api(path, options = {}) {
  const cookieName = document.querySelector('meta[name="csrf-cookie-name"]').content;
  const csrf = cookieValue(document.cookie, cookieName);
  return requestJson(path, {...options, headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf, ...options.headers}});
}
function action(fn) { return async event => { try { await fn(event); } catch (error) { message(error.message, true); } }; }
function snapshot() { return clone(state.document); }
function markDirty() {
  state.dirty = true;
  $('save-status').textContent = state.id ? 'Cambios sin guardar' : 'Sin guardar';
  queueEstimate();
}
function commit(before = snapshot()) {
  state.history.push(before);
  if (state.history.length > 60) state.history.shift();
  state.future = [];
  markDirty(); render();
}
function mutate(fn) { const before = snapshot(); fn(); commit(before); }
function setTool(tool) {
  state.tool = tool; state.start = null; $('preview').replaceChildren();
  document.querySelectorAll('[data-tool]').forEach(b => b.classList.toggle('active', b.dataset.tool === tool));
  svg.classList.toggle('drawing', tool !== 'select');
  $('tool-hint').textContent = ({select: 'Rueda para acercar o alejar; arrastra el fondo para mover la vista. Las bolitas cambian el largo.',
    wall: 'Haz clic en el inicio y luego en el final de la pared. Esc cancela el trazo.',
    column_C: 'Haz clic para colocar una columna C, en pared o independiente. Esc termina.',
    column_E: 'Haz clic para colocar una columna E, en pared o independiente. Esc termina.',
    pan: 'Arrastra el plano para mover la vista. Usa la rueda para acercar o alejar. Esc vuelve a Seleccionar.',
    door: 'Haz clic sobre una pared para colocar una puerta. Arrastra sus extremos para ajustar el largo en pasos de 0,50 m.', window: 'Haz clic en el tramo de pared que ocupará la ventana (hasta 2 m). Después puedes ajustar sus extremos.'})[tool];
  $('pan-view').setAttribute('aria-pressed',String(tool==='pan'));
  svg.classList.toggle('panning',tool==='pan');
  render();
}
function rawPoint(event) {
  return new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse());
}
function point(event, excludedId = null) {
  const p = rawPoint(event);
  return snapPoint(p, walls(), $('snap').checked, excludedId);
}
function wallDefaults() {
  const template = state.templates.find(t => String(t.id) === $('object-templates').value);
  return template ? clone(template.specification) : {kind:'wall',height:walls()[0]?.height||2.5,thickness:walls()[0]?.thickness||(state.document.ticoblock?.block_family==='10'?.10:.12),assignments:[]};
}
function addOpening(wall, kind, position) {
  let height = kind === 'door' ? 2.1 : 1.2;
  const placement = placeOpening(wall, position, state.document.objects,kind);
  if (!placement) throw new Error(kind==='door'?'No hay al menos 0,50 m libres para colocar la puerta en esta pared.':'No hay espacio libre para colocar la ventana.');
  const {offset,width} = placement;
  if (wall.height < (kind === 'door' ? height : height + 1)) throw new Error('La pared no tiene altura suficiente para esta abertura.');
  const opening = {id: uid(), kind, label: `${kind==='door'?doorName(width):typeName(kind)} ${state.document.objects.filter(o => o.kind === kind).length + 1}`,
    wall_id: wall.id, offset, width, height, sill: kind === 'door' ? 0 : 1,
    assignments: []};
  mutate(() => { state.document.objects.push(opening); state.selected = opening.id; });
  setTool('select');
  message(`${kind==='door'?doorName(width):typeName(kind)} de ${fmt(width)} m creada. Arrastra el cuerpo para moverla o las bolitas para cambiar el largo. El largo es el módulo de cálculo.`);
}
function render() {
  $('scene').replaceChildren(); $('measurements').replaceChildren();
  for (const wall of walls()) {
    const active = wall.id === state.selected;
    shape('line', {x1: wall.x1, y1: wall.y1, x2: wall.x2, y2: wall.y2,
      stroke: active ? '#4f8f6b' : '#3a5147', 'stroke-width': wall.thickness, 'stroke-linecap': 'square', 'data-object': wall.id});
    shape('line', {x1: wall.x1, y1: wall.y1, x2: wall.x2, y2: wall.y2, stroke: 'transparent', 'stroke-width': Math.max(.25, wall.thickness), 'data-object': wall.id});
  }
  for (const opening of state.document.objects.filter(o => ['door','window'].includes(o.kind))) {
    const wall = walls().find(w => w.id === opening.wall_id); if (!wall) continue;
    const p = openingPoints(opening, wall), active = opening.id === state.selected;
    const color = active ? '#c48b4a' : opening.kind === 'door' ? '#b18357' : '#669ca6';
    shape('line', {...p, stroke: '#fff', 'stroke-width': wall.thickness + .035});
    shape('line', {...p, stroke: color, 'stroke-width': opening.kind === 'window' ? .065 : .025, 'data-object': opening.id});
    if (opening.kind === 'door') {
      const {hinge,closed,open,sweep}=doorSwing(opening,wall);
      shape('path', {d: `M ${closed.x} ${closed.y} A ${opening.width} ${opening.width} 0 0 ${sweep} ${open.x} ${open.y} L ${hinge.x} ${hinge.y}`,
        stroke: color, fill: 'none', 'stroke-width': .018, 'data-object': opening.id});
    }
    shape('line', {...p, stroke: 'transparent', 'stroke-width': .28, 'data-object': opening.id});
    if(opening.kind==='door')shape('text',{x:(p.x1+p.x2)/2,y:(p.y1+p.y2)/2-.22,'font-size':.16,'text-anchor':'middle',fill:color,'paint-order':'stroke',stroke:'#fff','stroke-width':.045,'pointer-events':'none','data-door-type':opening.width},$('scene'),doorName(opening.width));
  }
  for(const column of state.document.columns||[]) {
    const active=column.id===state.selected, color=column.column_type==='C'?'#287b63':'#8b527c';
    const group=shape('g',{'data-object':column.id,cursor:'move','data-column-type':column.column_type});
    shape('title',{},group,`${column.label} · arrastra para mover`);
    shape('circle',{cx:column.x,cy:column.y,r:.23,fill:'transparent','pointer-events':'all'},group);
    shape('rect',{x:column.x-.105,y:column.y-.105,width:.21,height:.21,rx:.025,fill:active?color:'#fff',stroke:color,'stroke-width':active?.04:.025},group);
    shape('text',{x:column.x,y:column.y+.045,'text-anchor':'middle','font-size':.13,'font-weight':'bold',fill:active?'#fff':color,'pointer-events':'none'},group,column.column_type);
  }
  // Sobre las paredes y aberturas, para que también funcionen en esquinas compartidas.
  const activeObject = selected();
  if (activeObject && activeObject.kind!=='column' && state.tool === 'select') {
    const wall = activeObject.kind === 'wall' ? activeObject : walls().find(w=>w.id===activeObject.wall_id);
    const points = activeObject.kind === 'wall' ? activeObject : openingPoints(activeObject,wall);
    for (const n of [1,2]) {
      const handle = shape('g', {'data-object':activeObject.id,'data-endpoint':n,cursor:'ew-resize'});
      shape('title',{},handle,`Arrastrar ${n===1?'inicio':'final'} de ${typeName(activeObject.kind).toLowerCase()} para cambiar el largo`);
      shape('circle',{cx:points[`x${n}`],cy:points[`y${n}`],r:.18,fill:'transparent','pointer-events':'all'},handle);
      shape('circle',{cx:points[`x${n}`],cy:points[`y${n}`],r:.075,fill:'#fff',stroke:activeObject.kind==='wall'?'#4f8f6b':'#c48b4a','stroke-width':.025,'pointer-events':'none'},handle);
    }
    if(activeObject.kind!=='wall') {
      const grip=shape('g',{'data-object':activeObject.id,'data-handle':'move',cursor:'move'});
      shape('title',{},grip,'Arrastrar el centro para mover sin cambiar el largo');
      shape('rect',{x:(points.x1+points.x2)/2-.065,y:(points.y1+points.y2)/2-.065,width:.13,height:.13,rx:.025,fill:'#c48b4a',stroke:'#fff','stroke-width':.015},grip);
    }
  }
  $('download-image').disabled = downloadInProgress || !allObjects().length;
  $('object-count').textContent = `${allObjects().length} objetos`;
  const footprint=floorArea(walls());
  $('area-summary').textContent=footprint.area===null?'Área de la casa: cierra el contorno para calcularla':`${footprint.partial?'Área cerrada parcial':'Área de la casa'}: ${fmt(footprint.area)} m²`;
  $('area-summary').title='Superficie en planta sobre las líneas de referencia de las paredes; no es área útil ni área de paredes. Las divisiones interiores no se suman otra vez. Los contornos abiertos no aportan superficie.';
  $('geometry-summary').textContent = `${walls().length} paredes · ${fmt(walls().reduce((sum, w) => sum + length(w), 0))} m lineales`;
  $('undo').disabled = !state.history.length && !settingsDirty; $('redo').disabled = !state.future.length;
  $('object-list').replaceChildren();
  for (const obj of allObjects()) {
    const button = element('button', {class: obj.id === state.selected ? 'active' : ''}, objectName(obj));
    button.onclick = () => {state.selected = obj.id; tab('object'); setTool('select');}; $('object-list').append(button);
  }
  renderInspector(); renderModulation();
  if (!settingsDirty) {
  const settings = state.document.ticoblock || {};
  const drawn=Array.isArray(state.document.columns);
  for(const id of ['linear-columns','t-columns'])$(id).disabled=drawn;
  $('column-count-source').textContent=drawn?'Las cantidades C/E se toman de las columnas dibujadas. No se suman los números manuales.':'C: rectas. E: esquinas e intersecciones en cruz. Al colocar columnas en el dibujo se usarán sus cantidades.';
  const heights=[...new Set(walls().map(w=>w.height))];
  $('house-height').value = heights.length === 0 ? '2.5' : heights.length === 1 ? String(heights[0]) : '';
  const thicknesses=[...new Set(walls().map(w=>w.thickness))];
  $('house-thickness').value=thicknesses.length===0?(settings.block_family==='10'?'0.1':'0.12'):thicknesses.length===1?String(thicknesses[0]):'';
  $('floor-level').value=String(settings.floor_level||1);
  setFamilyControls();
  $('max-span').value = settings.max_span || '1.5';
  $('linear-columns').value = drawn?state.document.columns.filter(c=>c.column_type==='C').length:settings.linear_columns || 0;
  $('t-columns').value = drawn?state.document.columns.filter(c=>c.column_type==='E').length:settings.t_columns || 0;
  }
}
function renderDimensions() {
  const g=$('measurements');g.replaceChildren();
  if(!$('dimensions').checked)return;
  const objects=state.document.objects;
  const layout=dimensionLayout(walls(),state.estimate?.segments||[],objects.filter(o=>o.kind!=='wall'));
  for(const frame of layout){
    const {ux,uy,nx,ny}=frame;
    const draw=(part,distance,kind)=>{
      const offset=p=>({x:p.x+nx*distance,y:p.y+ny*distance});
      const a=offset(part.a),b=offset(part.b), color=kind==='part'?'#354e42':'#213d30';
      for(const p of [part.a,part.b])shape('line',{x1:p.x+nx*.12,y1:p.y+ny*.12,x2:p.x+nx*(distance+.1),y2:p.y+ny*(distance+.1),stroke:'#82958a','stroke-width':.014},g);
      shape('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:color,'stroke-width':.022},g);
      for(const p of [a,b])shape('line',{x1:p.x-ux*.04-nx*.065,y1:p.y-uy*.04-ny*.065,x2:p.x+ux*.04+nx*.065,y2:p.y+uy*.04+ny*.065,stroke:color,'stroke-width':.026},g);
      const x=(a.x+b.x)/2+nx*.12,y=(a.y+b.y)/2+ny*.12;
      const angle=Math.atan2(uy,ux)*180/Math.PI;
      shape('text',{x,y,fill:color,'font-size':kind==='part'?.17:.20,'font-weight':700,'font-family':'Arial, sans-serif','text-anchor':'middle','dominant-baseline':'central','paint-order':'stroke',stroke:'#fff','stroke-width':.055,transform:`rotate(${angle} ${x} ${y})`,'data-dimension-kind':kind,'data-length':+part.length.toFixed(6)},g,`${fmt(part.length)} m`);
    };
    for(const part of frame.parts)draw(part,.32,'part');
    draw(frame,frame.parts.length?.88:.45,'total');
  }
  const obj=selected();
  if(obj&&['door','window'].includes(obj.kind)){
    const wall=walls().find(w=>w.id===obj.wall_id);
    if(wall){const p=openingPoints(obj,wall);shape('text',{x:(p.x1+p.x2)/2,y:(p.y1+p.y2)/2+.32,fill:'#704b23','font-size':.20,'font-weight':700,'text-anchor':'middle','paint-order':'stroke',stroke:'#fff','stroke-width':.055},g,`${fmt(obj.width)} × ${fmt(obj.height)} m`);}
  }
}
function field(parent, key, label, value, options = {}) {
  const wrapper = element('label', {}, label);
  const input = element('input', {name: key, value, required: '', ...options});
  wrapper.append(input); parent.append(wrapper);
}
function renderInspector() {
  const obj = selected();
  $('empty-selection').hidden = Boolean(obj); $('selected-panel').hidden = !obj;
  $('save-object-template').disabled = obj?.kind !== 'wall';
  if (!obj) return;
  $('selected-title').textContent = objectName(obj);
  $('selection-label').textContent = obj.kind==='door'?doorName(obj.width):typeName(obj.kind);
  const fields = $('property-fields'); fields.replaceChildren();
  field(fields, 'label', 'Nombre', obj.label, {maxlength: 100});
  const grid = element('div', {class: 'field-grid'}); fields.append(grid);
  if(obj.kind==='column') {
    field(grid,'x','Posición X · m',obj.x,{type:'number',step:'.5',min:-100,max:100});
    field(grid,'y','Posición Y · m',obj.y,{type:'number',step:'.5',min:-100,max:100});
    const label=element('label',{},'Tipo de columna'), select=element('select',{name:'column_type','aria-label':'Tipo de columna'});
    for(const [value,text] of [['C','C · Lineal (pared recta)'],['E','E · Esquina o cruz']])select.append(element('option',{value},text));
    select.value=obj.column_type;label.append(select);fields.append(label,element('p',{class:'fine-print'},'Arrastra la columna para moverla. Se cuenta una vez, esté en una pared o independiente. Sobre una pared divide el paño; fuera de ella no cambia los bloques de pared.'));
  } else if (obj.kind === 'wall') {
    for (const [key, label] of [['x1','Inicio X · m'], ['y1','Inicio Y · m'], ['x2','Final X · m'], ['y2','Final Y · m']]) field(grid, key, label, obj[key], {type: 'number', step: '.01', min: -100, max: 100});
    field(grid, 'height', 'Altura · m', obj.height, {type: 'number', step: '.01', min: .1, max: 10});
    field(grid, 'thickness', 'Espesor · m', obj.thickness, {type: 'number', step: '.01', min: .05, max: 1});
    const info = element('p', {class:'fine-print'}, `Longitud: ${fmt(length(obj))} m. Para unir paredes, usa coordenadas de extremos iguales.`); fields.append(info);
  } else {
    for (const [key, label, min] of [['offset','Inicio del módulo · m',0],['width','Largo del módulo · m',.5],['height','Altura visual · m',.1],['sill','Desde piso · m',0]]) field(grid, key, label, obj[key], {type: 'number', step: ['offset','width'].includes(key) ? '.5' : '.01', min, max: key === 'offset' ? 200 : 20, ...(obj.kind === 'door' && key === 'sill' ? {readonly:''} : {})});
    if(obj.kind==='door') {
      const controls=element('div',{class:'button-pair spaced-small'});
      for(const [label,change] of [['↻ Rotar apertura',rotation=>(rotation+1)%4],['↔ Invertir apertura',rotation=>rotation^2]]) {
        const button=element('button',{type:'button'},label);
        button.onclick=()=>mutate(()=>{obj.door_rotation=change(obj.door_rotation||0);});
        controls.append(button);
      }
      fields.append(element('p',{class:'fine-print'},'Ajusta el módulo de puerta a 0,50, 1, 1,50 o 2 m arrastrando los extremos o escribiendo su largo. Se conserva también la Amplia de 3 m.'),controls,element('p',{class:'fine-print'},'Rotar apertura recorre las cuatro posiciones de bisagra y apertura. Invertir apertura cambia el lado hacia el que abre. Esto no cambia los materiales.'));
    }
    if (obj.kind === 'window') {
      const label=element('label',{},'Receta de ventana'), select=element('select',{name:'panel_type'});
      for (const [value,text] of [['regular','Regular'],['kitchen','Cocina'],['bath','Baño']]) select.append(element('option',{value},text));
      select.value=obj.panel_type || 'regular';label.append(select);fields.append(label);
    }
    fields.append(element('p',{class:'fine-print'},'Arrastra el cuerpo a lo largo de la pared o hasta otra pared, horizontal o vertical. Las bolitas cambian el largo dentro de la pared. El largo representa un módulo de la receta, no el ancho libre confirmado del vano. Las cotas verticales son visuales; no cambian la receta elegida.'));
  }
  $('assignments').replaceChildren();
  (obj.assignments||[]).forEach((assignment, index) => {
    const article = state.articles.find(a => a.id === assignment.article_id);
    const card = element('div', {class:'assignment-card'});
    card.append(element('strong', {}, article?.name || 'Artículo no disponible'), element('small', {}, `${assignment.factor} por ${basisName(assignment.basis)} · ${assignment.waste_percent}% adicional`));
    const remove = element('button', {type:'button', 'aria-label':'Quitar artículo'}, '×');
    remove.onclick = () => mutate(() => obj.assignments.splice(index, 1));
    card.append(remove); $('assignments').append(card);
  });
}
function queueEstimate() {
  state.estimate = null; state.estimateRequest++; $('pricing').replaceChildren();
  $('estimate-status').textContent = 'Cambios pendientes de calcular…';
  $('material-items').replaceChildren(); $('material-warnings').replaceChildren(); $('calculation-details').replaceChildren();
  $('material-count').textContent = '—'; $('export-csv').disabled = true;
  $('modulation').replaceChildren(); $('modulation-issues').replaceChildren();
  $('material-weight').textContent=''; $('beam-summary').textContent='';
  clearTimeout(state.estimateTimer); state.estimateTimer = setTimeout(() => estimate(), 400);
}
async function estimate() {
  $('pricing').replaceChildren();
  clearTimeout(state.estimateTimer);
  if(settingsDirty){$('estimate-status').textContent='Configuración pendiente: pulsa Aplicar configuración.';$('export-csv').disabled=true;return;}
  const request = ++state.estimateRequest;
  try {
    const result = await api('/api/ticoblock-estimate/', {method:'POST', body:JSON.stringify({document:state.document})});
    if (request !== state.estimateRequest) return;
    state.estimate = result; renderEstimate(); renderPricing(result.pricing);
  } catch (error) {
    if (request !== state.estimateRequest) return;
    state.estimate = null; $('estimate-status').textContent = 'No se pudo calcular. Corrige el croquis.';
    message(error.message, true);
  }
}
function renderEstimate() {
  const result = state.estimate;
  $('estimate-status').textContent = result.status === 'empty' ? 'Dibuja una pared para comenzar.' : result.status === 'ready' ? `${result.panels} paños propuestos · ${fmt(result.meters)} m · ${result.column_mode==='drawn'?`Columnas: ${result.drawn_column_count}${result.standalone_column_count?` · independientes: ${result.standalone_column_count}`:""} · ubicaciones pendientes: ${result.missing_column_positions.length}`:`${result.column_positions.length} ubicaciones de columna por clasificar`}` : 'Pendiente: revisa las medidas señaladas';
  $('material-count').textContent = result.items.length;
  $('material-items').replaceChildren(); $('material-warnings').replaceChildren(); $('calculation-details').replaceChildren();
  $('modulation-issues').replaceChildren();
  for (const issue of result.issues || []) {
    const button=element('button',{class:'modulation-issue',type:'button'},`${issue.label}: ${issue.message}`);
    button.onclick=()=>{if(issue.object_id){state.selected=issue.object_id;tab('object');render();}};
    $('modulation-issues').append(button);
  }
  for (const row of result.items) {
    const item = element('div', {class:'material-item'}), left = element('div'), qty = element('div', {class:row.quantity===null?'material-quantity pending':'material-quantity'}, row.quantity===null?'Pendiente':row.quantity);
    left.append(element('strong', {}, row.name)); qty.append(element('small', {}, row.unit)); item.append(left, qty); $('material-items').append(item);
  }
  if (!result.items.length) $('material-items').append(element('p', {class:'panel-copy'}, 'Completa las medidas modulares para obtener el desglose.'));
  for (const warning of result.warnings) $('material-warnings').append(element('div', {class:'material-warning'}, warning));
  for (const d of result.segments || []) {
    $('calculation-details').append(element('div', {class:'detail-row'}, `${d.label} · desde ${fmt(d.start)} m: ${d.kind}, ${fmt(d.length)} m → ${d.tp50} ${result.block_long_name} + ${d.tp37} ${result.block_short_name} (${d.source})`));
  }
  renderModulation();
  $('beam-summary').textContent = result.status!=='ready'?'':result.block_family==='10'?'10 cm: no lleva vigabloques; requiere perling o chorreado por cotizar.':`Viga de amarre: ${result.beam_layers} hilada(s). Se divide cada pared recta continua entre 0,40 m y se redondea hacia arriba, sin descontar puertas ni ventanas. No se vuelve a redondear en cada paño.`;
  for(const beam of result.beam_details||[])$('calculation-details').append(element('div',{class:'detail-row'},`Viga: ${fmt(beam.length)} m ÷ 0,40 → ${beam.pieces} piezas por hilada × ${result.beam_layers} hilada(s).`));
  $('material-weight').textContent = result.status !== 'ready' ? '' : result.weight === null ? (result.weight_note||'Peso pendiente de confirmar las cantidades de columnas.') : `Peso parcial según Excel: ${fmt(result.weight)} kg. Excluye vigabloques y acero.`;
  $('export-csv').disabled = !result.items.length;
}
function renderPricing(pricing) {
  const container=$('pricing');container.replaceChildren();if(!pricing)return;
  const cash=value=>Number(value).toLocaleString('es-CR',{style:'currency',currency:'CRC'});
  container.append(element('h3',{},'Precios de 3R'),element('p',{class:'fine-print'},`Lista ${pricing.price_level} · ${pricing.includes_tax?'precios con IVA incluido':'precios unitarios sin IVA; importes con IVA'}${pricing.fetched_display?' · Consultados: '+pricing.fetched_display:''}. Caché de hasta un minuto.`));
  if(pricing.error)container.append(element('p',{class:'material-warning'},pricing.error));
  for(const row of pricing.rows) {
    const card=element('div',{class:'material-item'}),left=element('div');
    left.append(element('strong',{},row.name));
    if(row.sku)left.append(element('small',{},`Código ${row.sku}`));
    if(row.status==='ready') {
      left.append(element('small',{},row.description),element('small',{},`${row.quantity} × ${cash(row.unit_price)}`));
      card.append(left,element('div',{class:'material-quantity'},cash(row.amount)));
    } else {
      left.append(element('small',{},row.reason),element('small',{},`Cantidad: ${row.quantity===null?'pendiente':row.quantity}`));
      card.append(left,element('div',{class:'material-quantity pending'},'Pendiente'));
    }
    container.append(card);
  }
  if(pricing.priced_count)container.append(element('p',{},`Subtotal con precio: ${cash(pricing.subtotal_with_prices)} · IVA incluido.`),element('p',{class:'fine-print'},`Base: ${cash(pricing.base_with_prices)} · IVA incluido en el subtotal: ${cash(pricing.tax_with_prices)}.`));
  else container.append(element('p',{},'Subtotal no disponible.'));
  if(pricing.pending_count)container.append(element('p',{class:'fine-print'},`${pricing.pending_count} renglón(es) pendiente(s); no se consideran cero.`));
  container.append(element('p',{class:'fine-print'},pricing.notice));
}
function renderModulation() {
  renderDimensions();
  $('modulation').replaceChildren();
  if (!$('show-panels').checked || state.estimate?.status !== 'ready') return;
  for (const p of state.estimate.column_positions) {
    if((state.document.columns||[]).some(c=>Math.hypot(c.x-p.x,c.y-p.y)<.00001))continue;
    const marker=shape('g',{},$('modulation'));
    shape('circle',{cx:p.x,cy:p.y,r:.055,fill:'#fff4d4',stroke:'#b18b42','stroke-width':.018},marker);
    shape('title',{},marker,'Límite de paño propuesto · tipo de columna por confirmar');
  }
}
function tab(which) {
  $('object-panel').hidden = which !== 'object'; $('materials-panel').hidden = which !== 'materials';
  $('tab-object').classList.toggle('active', which === 'object'); $('tab-materials').classList.toggle('active', which === 'materials');
}
function fit() {
  const points=[...walls().flatMap(w=>[{x:w.x1,y:w.y1},{x:w.x2,y:w.y2}]),...(state.document.columns||[])];
  if (!points.length) {state.view = [-2,-2,16,12]; applyView(); return;}
  const xs=points.map(p=>p.x),ys=points.map(p=>p.y);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  state.view=[minX-1.8,minY-1.8,Math.max(6,maxX-minX+3.6),Math.max(5,maxY-minY+3.6)];applyView();
}
function applyView() {svg.setAttribute('viewBox',state.view.join(' ')); $('zoom-label').textContent = `${Math.round(1600/state.view[2])}%`;}
function zoom(factor,anchor=null) {if(panDrag)finishPan();state.view=zoomView(state.view,factor,anchor);applyView();}
svg.addEventListener('wheel',event=>{
  event.preventDefault();
  const delta=event.deltaY*(event.deltaMode===1?20:event.deltaMode===2?300:1);
  zoom(Math.exp(Math.max(-300,Math.min(300,delta))*.002),rawPoint(event));
},{passive:false});

async function refreshLibrary() {
  const data = await api('/api/sketches/'); $('saved-list').replaceChildren(element('option', {value:''}, 'Seleccionar un croquis…'));
  for (const sketch of data.sketches) $('saved-list').append(element('option', {value:sketch.id}, `${sketch.is_template ? '◇ Plantilla · ' : ''}${sketch.name}`));
  const templates = await api('/api/object-templates/'); state.templates = templates.templates;
  const current = $('object-templates').value; $('object-templates').replaceChildren(element('option', {value:''}, 'Pared base · 2,50 m alto'));
  for (const t of state.templates) $('object-templates').append(element('option', {value:t.id}, t.name));
  $('object-templates').value = current;
}
let saving = false;
async function save(copy = false, isTemplate = false, overrideName = null) {
  if (saving) return;
  saving = true;
  const feedback = $('save-feedback');
  const buttons = ['save','save-copy','save-template'].map($);
  buttons.forEach(button => {button.disabled = true;});
  feedback.hidden = false; feedback.classList.remove('error'); feedback.setAttribute('role','status');
  feedback.textContent = 'Guardando en el servidor…';
  try {
    if(settingsDirty){tab('materials');document.querySelector('.modulation-config').open=true;throw new Error('Aplica la configuración pendiente antes de guardar el croquis.');}
    const name = (overrideName || $('project-name').value).trim();
    if (!name) throw new Error('Dale un nombre al croquis antes de guardarlo.');
    const update = state.id && !copy && !isTemplate;
    const body = {name, document:state.document, is_template:isTemplate, revision:state.revision};
    const original = JSON.stringify(state.document), originalName = $('project-name').value;
    const result = await api(update ? `/api/sketches/${state.id}/` : '/api/sketches/', {method:update?'PUT':'POST', body:JSON.stringify(body)});
    if (!isTemplate) {
      state.id = result.id; state.revision = result.revision; state.isTemplate = false;
      state.dirty = original !== JSON.stringify(state.document) || originalName !== $('project-name').value;
      $('save-status').textContent = state.dirty ? 'Cambios sin guardar' : `Guardado · revisión ${result.revision}`;
    }
    const savedMessage = isTemplate ? 'Plantilla guardada. Disponible en Proyectos.' : 'Croquis guardado en el servidor. Disponible en Proyectos.';
    feedback.textContent = savedMessage;
    message(savedMessage);
    try { await refreshLibrary(); }
    catch { feedback.textContent = `${savedMessage} No se pudo actualizar la biblioteca; puedes abrirlo desde Proyectos.`; }
  } catch (error) {
    feedback.classList.add('error'); feedback.setAttribute('role','alert');
    feedback.textContent = `No se pudo guardar. ${error.message}`;
    throw error;
  } finally {
    saving = false; buttons.forEach(button => {button.disabled = false;});
  }
}
async function requestName(title, suggestion) {
  const dialog = $('name-dialog'); $('dialog-title').textContent = title; $('dialog-name').value = suggestion; dialog.returnValue = '';
  dialog.showModal(); $('dialog-name').focus();
  return new Promise(resolve => dialog.addEventListener('close', () => resolve(dialog.returnValue === 'save' ? $('dialog-name').value.trim() : null), {once:true}));
}
function replaceDocument(document, name, saved = null) {
  settingsDirty = false;
  state.document = document; state.selected = null; state.history = []; state.future = []; state.id = saved?.id || null;
  state.revision = saved?.revision || null; state.isTemplate = false; state.dirty = !saved;
  $('project-name').value = name; $('save-status').textContent = saved ? `Guardado · revisión ${saved.revision}` : 'Sin guardar';
  setTool('select'); render(); fit(); queueEstimate(); message('');
}
function discardAllowed() {return !(state.dirty||settingsDirty) || confirm('Hay cambios sin guardar. ¿Quieres descartarlos?');}
function example() {
  const objects = [[0,0,4,0],[4,0,4,3],[4,3,0,3],[0,3,0,0]].map((v,i) => ({id:uid(),kind:'wall',label:`Pared ${i+1}`,x1:v[0],y1:v[1],x2:v[2],y2:v[3],height:2.5,thickness:.12,assignments:[]}));
  for (const [kind,index,offset,width,height,sill,sku] of [['door',2,1,2,2.1,0,'DEMO-PUERTA'],['window',0,1.5,1,1.2,1,'DEMO-VENTANA']]) {
    objects.push({id:uid(),kind,label:typeName(kind),wall_id:objects[index].id,offset,width,height,sill,assignments:[]});
  }
  replaceDocument({version:1,objects},'Casa de ejemplo'); state.selected = objects[2].id; render();
}

svg.addEventListener('pointerdown', action(event => {
  if (event.button !== 0 && event.button !== 1) return;
  const p = point(event), target = event.target.closest('[data-object]');
  const obj = target && allObjects().find(o => o.id === target.dataset.object);
  if(event.button===1 || state.tool==='pan' || (state.tool==='select' && !obj)) {
    event.preventDefault();
    panDrag={pointerId:event.pointerId,x:event.clientX,y:event.clientY,view:[...state.view],matrix:svg.getScreenCTM().inverse(),moved:false,clearOnClick:event.button===0&&state.tool==='select'&&!obj};
    svg.setPointerCapture(event.pointerId);svg.classList.add('dragging-view');return;
  }
  if(state.tool.startsWith('column_')) {
    const location=columnPoint(rawPoint(event),walls(),state.estimate?.column_positions||[],$('snap').checked);
    const existing=(state.document.columns||[]).find(c=>Math.hypot(c.x-location.x,c.y-location.y)<.00001);
    const columnType=state.tool.slice(-1);
    mutate(()=>{
      state.document.columns??=[];
      if(existing){if(/^Columna [CE] \d+$/.test(existing.label))existing.label=existing.label.replace(/Columna [CE]/,`Columna ${columnType}`);existing.column_type=columnType;state.selected=existing.id;}
      else {const column={id:uid(),kind:'column',label:`Columna ${columnType} ${state.document.columns.length+1}`,column_type:columnType,...location};state.document.columns.push(column);state.selected=column.id;}
    });
    message('Columna colocada. Puedes seguir colocando columnas o pulsar Esc para mover y editar. Se cuentan las dibujadas, sin sumar las cantidades manuales.');return;
  }
  if (state.tool === 'wall') {
    if (!state.start) {state.start = p; return;}
    const end = Math.abs(p.x-state.start.x) >= Math.abs(p.y-state.start.y) ? {x:p.x,y:state.start.y} : {x:state.start.x,y:p.y};
    if (Math.hypot(end.x-state.start.x,end.y-state.start.y) < .1) throw new Error('La pared debe medir al menos 10 cm.');
    const wall = {...wallDefaults(),id:uid(),kind:'wall',label:`Pared ${walls().length+1}`,x1:state.start.x,y1:state.start.y,x2:end.x,y2:end.y};
    mutate(() => {state.document.objects.push(wall);state.selected=wall.id;}); state.start = null; $('preview').replaceChildren(); return;
  }
  if (state.tool === 'door' || state.tool === 'window') {
    const wall = obj?.kind === 'wall' ? obj : walls().find(w => w.id === obj?.wall_id);
    if (!wall) throw new Error('Haz clic en una pared para colocar la abertura.');
    addOpening(wall,state.tool,p); return;
  }
  state.selected = obj?.id || null; render();
  if (obj) {
    const endpoint = Number(target?.dataset.endpoint) || null;
    drag = {id:obj.id,endpoint,start:obj.kind==='wall'?point(event,obj.id):rawPoint(event),before:snapshot(),original:clone(obj),moved:false};
    svg.setPointerCapture(event.pointerId);
  }
}));
svg.addEventListener('pointermove', event => {
  if(panDrag && panDrag.pointerId===event.pointerId) {
    const dx=event.clientX-panDrag.x,dy=event.clientY-panDrag.y,m=panDrag.matrix;
    if(Math.hypot(dx,dy)>4)panDrag.moved=true;
    state.view=[panDrag.view[0]-dx*m.a-dy*m.c,panDrag.view[1]-dx*m.b-dy*m.d,...panDrag.view.slice(2)];applyView();return;
  }
  const p = drag && drag.original.kind !== 'wall' ? rawPoint(event) : point(event, drag?.id);
  if (state.tool === 'wall' && state.start) {
    const end = Math.abs(p.x-state.start.x) >= Math.abs(p.y-state.start.y) ? {x:p.x,y:state.start.y} : {x:state.start.x,y:p.y};
    $('preview').replaceChildren(); shape('line',{x1:state.start.x,y1:state.start.y,x2:end.x,y2:end.y,stroke:'#7ba57b','stroke-width':.08,'stroke-dasharray':'.15 .08'},$('preview'));
  }
  if (!drag) return;
  const obj = selected(); if (!obj) return;
  let dx = p.x-drag.start.x, dy = p.y-drag.start.y;
  if (Math.hypot(dx,dy) < .03 && !drag.moved) return;
  drag.moved = true;
  if(obj.kind==='column') {
    const location=columnPoint({x:drag.original.x+dx,y:drag.original.y+dy},walls(),state.estimate?.column_positions||[],$('snap').checked);
    if((state.document.columns||[]).some(c=>c.id!==obj.id&&Math.hypot(c.x-location.x,c.y-location.y)<.00001))return;
    Object.assign(obj,location);
  } else if (obj.kind === 'wall' && drag.endpoint) {
    const n = drag.endpoint;
    const minimumLength = Math.max(.1, ...state.document.objects.filter(o=>o.wall_id===obj.id).map(o=>o.offset+o.width));
    const resized = resizeEndpoint(drag.original,n,{x:drag.original[`x${n}`]+dx,y:drag.original[`y${n}`]+dy},walls(),$('snap').checked,minimumLength);
    if (!resized) return;
    Object.assign(obj,resized);
  } else if (obj.kind === 'wall') {
    const snapped = snapPoint({x:drag.original.x1+dx,y:drag.original.y1+dy},walls(),$('snap').checked,obj.id);
    dx = snapped.x-drag.original.x1; dy = snapped.y-drag.original.y1;
    for (const n of [1,2]) {obj[`x${n}`]=+(drag.original[`x${n}`]+dx).toFixed(3); obj[`y${n}`]=+(drag.original[`y${n}`]+dy).toFixed(3);}
  } else {
    const wall = walls().find(w=>w.id===drag.original.wall_id), l = length(wall);
    const distance = (dx*(wall.x2-wall.x1)+dy*(wall.y2-wall.y1))/l;
    const candidate=(!drag.endpoint && transferOpening(drag.original,p,walls(),state.document.objects,$('snap').checked)) || editOpening(drag.original,wall,drag.endpoint,distance,state.document.objects,$('snap').checked);
    if(!candidate)return;
    Object.assign(obj,candidate);
  }
  render();
});
function finishDrag() {
  const finished=drag;drag=null;
  if(finished?.moved){
    commit(finished.before);
    const obj=selected();
    if(obj?.kind==='column')message(`Columna ${obj.column_type}: X ${fmt(obj.x)} m · Y ${fmt(obj.y)} m.`);
    else if(obj && obj.kind!=='wall') message(`${obj.kind==='door'?doorName(obj.width):typeName(obj.kind)}: módulo de ${fmt(obj.width)} m, inicio a ${fmt(obj.offset)} m de la pared. Puedes deshacer el ajuste.`);
  } else if(finished)render();
}
function finishPan() {const finished=panDrag;panDrag=null;svg.classList.remove('dragging-view');if(finished?.clearOnClick&&!finished.moved){state.selected=null;render();}}
svg.addEventListener('pointerup',()=>{finishPan();finishDrag();});
svg.addEventListener('lostpointercapture',finishPan);
svg.addEventListener('pointercancel',() => {finishPan();if(drag){state.document=drag.before;drag=null;render();}});
document.querySelectorAll('[data-tool]').forEach(button => button.onclick=action(()=>{
  const tool=button.dataset.tool, obj=selected();
  if(['door','window'].includes(tool) && obj?.kind==='wall' && !state.document.objects.some(o=>o.wall_id===obj.id)) {
    addOpening(obj,tool,{x:(obj.x1+obj.x2)/2,y:(obj.y1+obj.y2)/2});
  } else setTool(tool);
}));
$('properties').onsubmit=action(async event=>{
  event.preventDefault();const obj=selected(),replacement=clone(obj),data=new FormData(event.target);
  for (const [key,value] of data) replacement[key]=['label','panel_type','column_type'].includes(key)?value:Number(value);
  if(obj.kind==='door' && ![.5,1,1.5,2,3].includes(replacement.width))throw new Error('Usa un módulo de puerta de 0,50, 1, 1,50, 2 o 3 m.');
  if(obj.kind==='column' && replacement.label===obj.label && /^Columna [CE] \d+$/.test(obj.label))replacement.label=obj.label.replace(/Columna [CE]/,`Columna ${replacement.column_type}`);
  const candidate=snapshot();if(obj.kind==='column')candidate.columns=candidate.columns.map(o=>o.id===obj.id?replacement:o);
  else candidate.objects=candidate.objects.map(o=>o.id===obj.id?replacement:o);
  await api('/api/estimate/',{method:'POST',body:JSON.stringify({document:candidate})});
  mutate(()=>{state.document=candidate;});message(replacement.kind==='door'?`${objectName(replacement)}: medidas actualizadas.`:'Medidas actualizadas.');
});
$('assignment-form').onsubmit=action(event=>{
  event.preventDefault();const obj=selected(),aid=Number($('article-select').value);
  if (!obj) return;
  if(obj.kind==='column')throw new Error('Las columnas usan las recetas TicoBlock; no requieren artículos de ejemplo.');
  if(obj.assignments.some(a=>a.article_id===aid))throw new Error('Este artículo ya está vinculado. Quítalo para cambiar su regla.');
  mutate(()=>obj.assignments.push({article_id:aid,basis:$('basis').value,factor:$('factor').value,waste_percent:$('waste').value}));
});
$('basis').onchange=()=>{if($('basis').value==='object'){$('factor').value='1';$('waste').value='0';}};
$('duplicate').onclick=action(async()=>{
  const obj=selected();if(!obj)return;
  if(obj.kind==='column'){setTool(`column_${obj.column_type}`);message('Haz clic donde quieres colocar la nueva columna.');return;}
  const copies=duplicateObjects(state.document.objects,obj);
  const candidate=snapshot();candidate.objects.push(...copies);
  await api('/api/estimate/',{method:'POST',body:JSON.stringify({document:candidate})});
  mutate(()=>{state.document=candidate;state.selected=copies[0].id;});
});
$('delete').onclick=()=>{const obj=selected();if(obj)mutate(()=>{if(obj.kind==='column')state.document.columns=state.document.columns.filter(c=>c.id!==obj.id);
  else state.document.objects=state.document.objects.filter(o=>o.id!==obj.id&&o.wall_id!==obj.id);state.selected=null;});};
$('undo').onclick=()=>{if(settingsDirty){settingsDirty=false;render();queueEstimate();message('Configuración pendiente descartada.');return;}if(!state.history.length)return;state.future.push(snapshot());state.document=state.history.pop();state.selected=null;markDirty();render();message("Cambio deshecho.");};
$('redo').onclick=()=>{if(!state.future.length)return;state.history.push(snapshot());state.document=state.future.pop();state.selected=null;markDirty();render();message("Cambio rehecho.");};
$('save').onclick=action(()=>save());$('save-copy').onclick=action(()=>save(true));
$('save-template').onclick=action(async()=>{const name=await requestName('Guardar plantilla de croquis',$('project-name').value);if(name)await save(true,true,name);});
$('save-object-template').onclick=action(async()=>{const obj=selected();if(obj?.kind!=='wall')throw new Error('Selecciona una pared.');const name=await requestName('Guardar plantilla de pared',obj.label);if(!name)return;await api('/api/object-templates/',{method:'POST',body:JSON.stringify({name,specification:obj})});await refreshLibrary();message('Plantilla de pared guardada. Selecciónala en la biblioteca antes de dibujar.');});
$('open').onclick=action(async()=>{const id=$('saved-list').value;if(!id)throw new Error('Selecciona un croquis de la biblioteca.');if(!discardAllowed())return;const data=await api(`/api/sketches/${id}/`);replaceDocument(data.document,data.is_template?`${data.name} · copia`:data.name,data.is_template?null:data);});
$('new').onclick=()=>{if(discardAllowed())replaceDocument({version:1,objects:[]},'Nuevo croquis');};
$('example').onclick=()=>{if(discardAllowed())example();};
$('project-name').oninput=markDirty;
$('tab-object').onclick=()=>tab('object');$('tab-materials').onclick=()=>tab('materials');
$('recalculate').onclick=()=>estimate();$('dimensions').onchange=render;
$('show-panels').onchange=renderModulation;
function setFamilyControls(){
  const narrow=$('house-thickness').value==='0.1';
  for(const option of $('house-height').options)option.disabled=narrow&&option.value!=='2.5';
  $('floor-level').querySelector('option[value="2"]').disabled=narrow;
  $('house-thickness').querySelector('option[value="0.1"]').disabled=$('floor-level').value==='2';
}
function markSettingsPending(){
  settingsDirty=true; state.estimateRequest++;clearTimeout(state.estimateTimer);
  $('undo').disabled=false;
  state.estimate=null;$('modulation').replaceChildren();$('material-items').replaceChildren();$('calculation-details').replaceChildren();
  $('material-weight').textContent=''; $('beam-summary').textContent='';
  $('material-count').textContent='—';$('export-csv').disabled=true;
  $('estimate-status').textContent='Configuración pendiente: pulsa Aplicar configuración.';
}
$('modulation-settings').addEventListener('input',event=>{if(event.target.id!=='max-span')markSettingsPending();});
$('modulation-settings').addEventListener('change',event=>{
  if(event.target.id==='house-thickness' && $('house-thickness').value==='0.1')$('house-height').value='2.5';setFamilyControls();markSettingsPending();
});
$('max-span').addEventListener('change',()=>{
  const maximum=$('max-span').value;
  mutate(()=>{state.document.ticoblock={...(state.document.ticoblock||{}),max_span:maximum};});
  message(settingsDirty?'Máximo actualizado. Aplica también los cambios pendientes de altura o columnas.':'Máximo de paño actualizado. Los materiales se actualizan automáticamente.');
});
$('modulation-settings').onsubmit=action(async event=>{
  event.preventDefault(); const candidate=snapshot();
  candidate.ticoblock={max_span:$('max-span').value,floor_level:Number($('floor-level').value),block_family:$('house-thickness').value==='0.1'?'10':'12'};
  for(const key of ['linear_columns','t_columns'])candidate.ticoblock[key]=Number($(key.replaceAll('_','-')).value);
  for(const wall of candidate.objects.filter(o=>o.kind==='wall')){wall.height=Number($('house-height').value);wall.thickness=Number($('house-thickness').value);}
  await api('/api/estimate/',{method:'POST',body:JSON.stringify({document:candidate})});
  settingsDirty=false;mutate(()=>{state.document=candidate;});message('Configuración aplicada. Revisa la propuesta en Materiales.');
});
$('zoom-in').onclick=()=>zoom(.8);$('zoom-out').onclick=()=>zoom(1.25);$('fit').onclick=fit;
$('download-project').onclick=action(()=>{
  if(settingsDirty)throw new Error('Aplica la configuración pendiente antes de descargar el proyecto.');
  const name=$('project-name').value;
  const exported=snapshot();exported.ticoblock={floor_level:1,...exported.ticoblock,max_span:$('max-span').value};
  downloadBlob(new Blob([packProject(name,exported,state.articles)],{type:'application/json;charset=utf-8'}),projectFilename(name,'.croquis3r.json'));
  message('Proyecto descargado. Puedes subir este archivo desde Proyectos para continuar como una copia.');
});
function requestDownloadFormat() {
  const dialog=$('download-dialog');dialog.returnValue='';dialog.showModal();
  return new Promise(resolve=>dialog.addEventListener('close',()=>resolve(
    ['pdf','png','materials-priced','materials-plain'].includes(dialog.returnValue)?dialog.returnValue:null),{once:true}));
}
$('download-image').onclick=action(async()=>{
  if(!allObjects().length)throw new Error('Dibuja un objeto antes de descargar el croquis.');
  const format=await requestDownloadFormat();if(!format)return;
  const button=$('download-image'),name=$('project-name').value.trim()||'Croquis sin nombre';downloadInProgress=true;button.disabled=true;button.textContent='Preparando…';
  try {
    if(format.startsWith('materials-')) {
      if(settingsDirty)throw new Error('Aplica la configuración pendiente antes de descargar materiales.');
      const cookieName=document.querySelector('meta[name="csrf-cookie-name"]').content;
      const response=await fetch('/api/export-materials-pdf/',{method:'POST',credentials:'same-origin',
        headers:{'Content-Type':'application/json','X-CSRFToken':cookieValue(document.cookie,cookieName)},
        body:JSON.stringify({name,document:snapshot(),with_prices:format==='materials-priced'})});
      if(!response.ok) {
        const details=await response.json().catch(()=>null);
        throw new Error(details?.error||'No se pudo descargar la lista. Revisa tu sesión e intenta de nuevo.');
      }
      if(!response.headers.get('Content-Type')?.startsWith('application/pdf'))throw new Error('El servidor no devolvió un PDF. Revisa tu sesión.');
      downloadBlob(await response.blob(),projectFilename(name,format==='materials-priced'?'-materiales-con-precios.pdf':'-materiales-sin-precios.pdf'));
      message('Lista de materiales descargada en PDF.');return;
    }
    const original=state.selected;let image;
    try {
      state.selected=null;render();
      image=drawingPng(svg,name,$('area-summary').textContent);
    } finally {state.selected=original;render();}
    const png=await image;
    const csrfName=document.querySelector('meta[name="csrf-cookie-name"]').content;
    const blob=format==='pdf'?await pdfFromPng(png,name,cookieValue(document.cookie,csrfName)):png;
    downloadBlob(blob,projectFilename(name,`.${format}`));
    message(`Croquis descargado en ${format.toUpperCase()}. Para continuar editando, descarga también el proyecto.`);
  } finally {downloadInProgress=false;button.disabled=!allObjects().length;button.textContent='Descargar';}
});
$('export-csv').onclick=()=>{
  if(!state.estimate)return;
  const cell=value=>`"${String(value).replace(/^[=+\-@\t\r]/,"'$&").replaceAll('"','""')}"`;
  if(state.estimate.status!=='ready')return;
  const rows=[['Croquis3R · Recetas TicoBlock · Modulación propuesta para revisión'],[state.estimate.notice],...state.estimate.warnings.map(w=>['Observación',w]),['Referencia','Material','Unidad','Cantidad'],...state.estimate.items.map(r=>[state.estimate.version,r.name,r.unit,r.quantity??'Pendiente']),['Pared','Tipo de paño','Largo modular m',state.estimate.block_long_name,state.estimate.block_short_name],...state.estimate.segments.map(s=>[s.label,s.kind,s.length,s.tp50,s.tp37])];
  const url=URL.createObjectURL(new Blob(['\uFEFF'+rows.map(r=>r.map(cell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'}));
  const a=element('a',{href:url,download:'croquis3r-materiales-ticoblock.csv'});a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
window.addEventListener('keydown',event=>{
  if(['INPUT','SELECT','TEXTAREA'].includes(event.target.tagName)||$('name-dialog').open||$('download-dialog').open)return;
  if(event.key==='Escape'){if(drag){state.document=drag.before;drag=null;render();}setTool('select');}
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='z'){event.preventDefault();$(event.shiftKey?'redo':'undo').click();}
  else if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='y'){event.preventDefault();$('redo').click();}
  else if(!event.ctrlKey&&!event.metaKey&&event.key.toLowerCase()==='p')setTool('wall');
  else if(event.key.toLowerCase()==='v')setTool('select');
  else if(event.key==='Delete')$('delete').click();
});
window.addEventListener('beforeunload',event=>{if(state.dirty||settingsDirty){event.preventDefault();event.returnValue='';}});
async function init(){
  try{
    const catalog=await api('/api/catalog/');state.articles=catalog.articles;
    for(const a of state.articles)$('article-select').append(element('option',{value:a.id},`${a.sku} · ${a.name}`));
    await refreshLibrary();
    const requested=new URLSearchParams(location.search).get('sketch');
    if(requested){
      if(!/^\d{1,18}$/.test(requested))throw new Error('La referencia del croquis no es válida. Abre uno desde Proyectos.');
      const saved=await api(`/api/sketches/${requested}/`);
      replaceDocument(saved.document,saved.name,saved.is_template?null:saved);
      if(new URLSearchParams(location.search).get('imported')==='1')message('Proyecto importado como copia en tu cuenta. Puedes continuar editándolo; sus materiales se recalculan con las reglas actuales.');
    }else{
      replaceDocument({version:1,objects:[]},'Nuevo croquis');state.dirty=false;$('save-status').textContent='Nuevo croquis · sin cambios';
      message('Dibuja las paredes o pulsa Ver ejemplo para practicar. Cada cuadro representa 0,50 m.');
    }
  }catch(error){message(error.message,true);render();}
}
init();
