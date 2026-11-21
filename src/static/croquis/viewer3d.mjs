import * as THREE from './vendor/three/three.module.js';
import {OrbitControls} from './vendor/three/OrbitControls.js';
const {buildHouseScene}=await import(`./scene3d.mjs${new URL(import.meta.url).search}`);
const {presentationSettings,buildRoof,findWalkStart,walkStep}=await import(`./presentation3d.mjs${new URL(import.meta.url).search}`);
const {setupRenders}=await import(`./renders3d.mjs${new URL(import.meta.url).search}`);

const {openingDetails}=await import(`./visual-details3d.mjs${new URL(import.meta.url).search}`);

function floorTexture(finish) {
  if(finish==='concrete')return null;
  const canvas=document.createElement('canvas');canvas.width=canvas.height=256;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle=finish==='wood'?'#b2865c':'#e8e0cf';ctx.fillRect(0,0,256,256);
  ctx.strokeStyle=finish==='wood'?'#785133':'#b5ac9b';ctx.lineWidth=finish==='wood'?2:3;
  if(finish==='wood') {
    for(let y=0;y<256;y+=64) {
      ctx.strokeRect(0,y,256,64);ctx.beginPath();const x=y%128===0?85:170;ctx.moveTo(x,y);ctx.lineTo(x,y+64);ctx.stroke();
      ctx.globalAlpha=.12;for(let line=y+7;line<y+64;line+=9){ctx.beginPath();ctx.moveTo(0,line);ctx.bezierCurveTo(65,line-5,180,line+5,256,line);ctx.stroke();}ctx.globalAlpha=1;
    }
  } else ctx.strokeRect(0,0,256,256);
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
  texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
  texture.repeat.set(finish==='wood'?1:1/.6,finish==='wood'?1:1/.6);
  return texture;
}

function surfaceTexture(kind) {
  const canvas=document.createElement('canvas');canvas.width=canvas.height=128;
  const ctx=canvas.getContext('2d');
  if(kind==='wood') {
    ctx.fillStyle='#97694a';ctx.fillRect(0,0,128,128);
    for(let x=0;x<128;x+=3){ctx.strokeStyle=`rgba(48,23,10,${.07+(x%7)*.015})`;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,0);ctx.bezierCurveTo(x+4,40,x-3,80,x+1,128);ctx.stroke();}
  } else if(kind==='roof') {
    const gradient=ctx.createLinearGradient(0,0,128,0);gradient.addColorStop(0,'#666');gradient.addColorStop(.45,'#ddd');gradient.addColorStop(1,'#666');ctx.fillStyle=gradient;ctx.fillRect(0,0,128,128);
  } else {
    let seed=1729;const pixels=ctx.createImageData(128,128);
    for(let i=0;i<pixels.data.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const value=180+(seed%50);pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=value;pixels.data[i+3]=255;}ctx.putImageData(pixels,0,0);
  }
  const texture=new THREE.CanvasTexture(canvas);texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
  if(kind==='wood')texture.colorSpace=THREE.SRGBColorSpace;
  texture.repeat.set(kind==='roof'?8:kind==='plaster'?4:1,kind==='plaster'?4:1);
  return texture;
}

export function openHouseViewer(source, name, onSettingsChange=()=>{}, sketchId=null) {
  const dialog=document.getElementById('viewer3d-dialog');
  const host=document.getElementById('viewer3d-stage');
  const status=document.getElementById('viewer3d-status');
  const sceneData=buildHouseScene(source);
  let settings=presentationSettings(source),mode='orbit',yaw=0,pitch=0;
  const keys=new Set();let lookDrag=null,lastFrame=0;
  const interiorButton=document.getElementById('viewer3d-interior');
  const walkControls=document.getElementById('viewer3d-walk-controls');
  const instructions=document.getElementById('viewer3d-instructions');
  const hideRoof=document.getElementById('viewer3d-hide-roof');hideRoof.checked=false;
  document.getElementById('viewer3d-title').textContent=name||'Vista 3D';
  dialog.showModal();
  let renderer;
  try {renderer=new THREE.WebGLRenderer({antialias:true});}
  catch {dialog.close();throw new Error('No se pudo abrir la vista 3D. Revisa que la aceleración gráfica esté habilitada en el navegador.');}
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.setClearColor(0xece9df);
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.05;
  renderer.domElement.setAttribute('aria-label','Modelo 3D de la casa. Arrastra para girar y usa la rueda para acercar.');
  renderer.domElement.tabIndex=0;
  host.replaceChildren(renderer.domElement);
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(42,1,.02,2000);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true;
  controls.maxPolarAngle=Math.PI*.49;
  controls.minDistance=.3;
  controls.screenSpacePanning=true;
  const house=new THREE.Group();scene.add(house);
  const materials={
    wall:new THREE.MeshStandardMaterial({color:0xf5eddb,roughness:.85,side:THREE.DoubleSide}),
    frame:new THREE.MeshStandardMaterial({color:0x343a38,roughness:.5}),
    column:new THREE.MeshStandardMaterial({color:0xc3beb2,roughness:.95}),
    door:new THREE.MeshStandardMaterial({color:0x97694a,roughness:.65}),
    window:new THREE.MeshPhysicalMaterial({color:0xc9e1e5,transparent:true,opacity:.36,roughness:.07,metalness:0,clearcoat:.65,ior:1.45,depthWrite:false,side:THREE.DoubleSide}),
    metal:new THREE.MeshStandardMaterial({color:0xb8c0c3,roughness:.25,metalness:.75}),
    sill:new THREE.MeshStandardMaterial({color:0xdedbd2,roughness:.8}),
    base:new THREE.MeshStandardMaterial({color:0xc9c7be,roughness:.9}),
    floor:new THREE.MeshStandardMaterial({color:0xcbbba1,roughness:.8,side:THREE.DoubleSide}),
    roof:new THREE.MeshStandardMaterial({color:0x464b4b,roughness:.65,metalness:.2,side:THREE.DoubleSide}),
  };
  materials.wall.bumpMap=surfaceTexture('plaster');materials.wall.bumpScale=.004;
  materials.door.map=surfaceTexture('wood');
  materials.roof.bumpMap=surfaceTexture('roof');materials.roof.bumpScale=.008;
  const box=(spec,role,parent=house)=>{
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(...spec.size),materials[role]);
    mesh.position.fromArray(spec.position);mesh.rotation.y=spec.rotation;
    mesh.castShadow=role!=='window';mesh.receiveShadow=true;
    parent.add(mesh);return mesh;
  };
  for(const spec of sceneData.boxes)box(spec,spec.role);
  const doors=[];
  for(const spec of sceneData.openings) {
    const group=new THREE.Group();group.position.fromArray(spec.position);group.rotation.y=spec.rotation;house.add(group);
    box({...spec,position:[0,0,0],rotation:0},spec.kind,group);
    for(const detail of openingDetails(spec))box(detail,detail.role,group);
    if(spec.kind==='door')doors.push({mesh:group,spec});
  }
  for(const ring of sceneData.floors) {
    // Shape local XY -> horizontal world XZ. The same rings support concave plans.
    const shape=new THREE.Shape(ring.map(p=>new THREE.Vector2(p.x,-p.y)));
    const base=new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:.1,bevelEnabled:false}),materials.base);base.rotation.x=-Math.PI/2;base.position.y=-.12;base.castShadow=base.receiveShadow=true;house.add(base);
    const mesh=new THREE.Mesh(new THREE.ShapeGeometry(shape),materials.floor);
    mesh.rotation.x=-Math.PI/2;mesh.position.y=-.005;mesh.receiveShadow=true;house.add(mesh);
  }
  const roof=new THREE.Group();house.add(roof);
  const bounds=new THREE.Box3(),center=new THREE.Vector3(),size=new THREE.Vector3();let radius;
  const measure=()=>{bounds.setFromObject(house);bounds.getCenter(center);bounds.getSize(size);radius=Math.max(2,size.length()/2);};
  const roofMesh=(points,closure=false)=>{
    const positions=[];
    const add=(a,b,c)=>positions.push(...a,...b,...c);
    if(closure) {add(points[0],points[1],points[2]);add(points[0],points[2],points[3]);}
    else {
      const triangles=THREE.ShapeUtils.triangulateShape(points.map(p=>new THREE.Vector2(p[0],p[2])),[]);
      const lower=p=>[p[0],p[1]-.08,p[2]];
      for(const [a,b,c] of triangles){add(points[a],points[b],points[c]);add(lower(points[c]),lower(points[b]),lower(points[a]));}
      for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length];add(a,lower(a),b);add(b,lower(a),lower(b));}
    }
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.computeVertexNormals();
    const uvs=[];for(let i=0;i<positions.length;i+=3)uvs.push(positions[i],positions[i+2]);geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
    const mesh=new THREE.Mesh(geometry,closure?materials.wall:materials.roof);mesh.castShadow=mesh.receiveShadow=true;roof.add(mesh);
  };
  const rebuildRoof=()=>{
    for(const mesh of [...roof.children]){mesh.geometry.dispose();roof.remove(mesh);}
    const data=buildRoof(sceneData,settings);
    for(const face of data.surfaces)roofMesh(face);
    for(const face of data.closures)roofMesh(face,true);
    roof.visible=!hideRoof.checked;measure();
  };
  const applyFinishes=()=>{
    materials.wall.color.set(({ivory:'#f5eddb',white:'#ffffff',sand:'#d9bf9d',sage:'#a5b4a1'})[settings.wall_color]);
    materials.floor.map?.dispose();materials.floor.map=floorTexture(settings.floor_finish);
    materials.floor.color.set(settings.floor_finish==='concrete'?'#b8b8b2':'#ffffff');materials.floor.needsUpdate=true;
    materials.roof.color.set(({charcoal:'#42494c',terracotta:'#a95338',gray:'#9b9e9f'})[settings.roof_color]);
  };
  applyFinishes();rebuildRoof();
  controls.maxDistance=radius*12;
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(radius*80,radius*80),new THREE.MeshStandardMaterial({color:0xe0ddcf,roughness:1}));
  ground.rotation.x=-Math.PI/2;ground.position.set(center.x,-.145,center.z);ground.receiveShadow=true;scene.add(ground);
  scene.add(new THREE.HemisphereLight(0xe5efff,0xb3a38d,2.0));
  const sun=new THREE.DirectionalLight(0xfff4df,2.8);
  sun.position.copy(center).add(new THREE.Vector3(radius,2*radius,radius*.8));
  sun.target.position.copy(center);scene.add(sun,sun.target);
  sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
  sun.shadow.camera.left=sun.shadow.camera.bottom=-radius*1.3;
  sun.shadow.camera.right=sun.shadow.camera.top=radius*1.3;
  sun.shadow.camera.near=.1;sun.shadow.camera.far=radius*6;
  sun.shadow.normalBias=.025;
  const preset=view=>{
    mode='orbit';keys.clear();walkControls.hidden=true;interiorButton.setAttribute('aria-pressed','false');controls.enabled=true;
    instructions.textContent='Arrastra para girar. Rueda o pellizco para acercar; botón derecho o dos dedos para desplazar.';
    camera.fov=42;camera.updateProjectionMatrix();
    if(view==='top'){hideRoof.checked=true;roof.visible=false;}
    controls.target.copy(center);
    const direction=view==='top'?new THREE.Vector3(0,1,.001):view==='front'?new THREE.Vector3(0,.13,1):new THREE.Vector3(1,.8,1);
    const verticalFov=THREE.MathUtils.degToRad(camera.fov);
    const fov=Math.min(verticalFov,2*Math.atan(Math.tan(verticalFov/2)*camera.aspect));
    camera.position.copy(center).addScaledVector(direction.normalize(),radius/Math.sin(fov/2)*1.12);
    controls.update();
  };
  let previousAspect=0;
  const resize=()=>{
    const width=host.clientWidth,height=host.clientHeight;if(!width||!height)return;
    renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();
    if(!previousAspect)preset('perspective');previousAspect=camera.aspect;
  };
  const observer=new ResizeObserver(resize);observer.observe(host);resize();
  renderer.setAnimationLoop(time=>{
    const dt=Math.min((time-lastFrame)/1000,.05);lastFrame=time;
    if(mode==='orbit')controls.update();
    else {
      if(keys.has('ArrowLeft')||keys.has('left'))yaw+=dt*1.4;
      if(keys.has('ArrowRight')||keys.has('right'))yaw-=dt*1.4;
      let forward=(keys.has('w')||keys.has('ArrowUp')||keys.has('forward')?1:0)-(keys.has('s')||keys.has('ArrowDown')||keys.has('backward')?1:0);
      let side=(keys.has('d')?1:0)-(keys.has('a')?1:0);
      const scale=1.5*dt/Math.max(1,Math.hypot(forward,side));
      const delta={x:(-Math.sin(yaw)*forward+Math.cos(yaw)*side)*scale,z:(-Math.cos(yaw)*forward-Math.sin(yaw)*side)*scale};
      const next=walkStep(sceneData,{x:camera.position.x,z:camera.position.z},delta,open.checked);
      // Keep the visitor within the presentation ground, even outside the house.
      camera.position.x=THREE.MathUtils.clamp(next.x,center.x-radius*2.5,center.x+radius*2.5);
      camera.position.z=THREE.MathUtils.clamp(next.z,center.z-radius*2.5,center.z+radius*2.5);
      camera.rotation.set(pitch,yaw,0,'YXZ');
    }
    renderer.render(scene,camera);
  });
  const onLost=event=>{event.preventDefault();status.textContent='Se perdió la conexión con la tarjeta gráfica. Cierra la vista 3D e intenta abrirla nuevamente.';};
  renderer.domElement.addEventListener('webglcontextlost',onLost);
  const buttons=[...dialog.querySelectorAll('[data-camera]')];
  for(const button of buttons)button.onclick=()=>preset(button.dataset.camera);
  const cutaway=document.getElementById('viewer3d-transparent');
  cutaway.checked=false;
  cutaway.onchange=()=>{
    for(const role of ['wall','column']) {
      materials[role].transparent=cutaway.checked;materials[role].opacity=cutaway.checked?.22:1;
      materials[role].depthWrite=!cutaway.checked;materials[role].needsUpdate=true;
    }
  };
  const open=document.getElementById('viewer3d-doors');open.checked=false;
  open.onchange=()=>{for(const {mesh,spec} of doors){mesh.position.fromArray(open.checked?spec.openPosition:spec.position);mesh.rotation.y=open.checked?spec.openRotation:spec.rotation;}};
  hideRoof.onchange=()=>{roof.visible=!hideRoof.checked;};
  const settingsControls=new Map(['wall_color','floor_finish','roof_type','roof_color','ridge_axis','roof_rise','roof_overhang'].map(key=>[key,document.getElementById(`viewer3d-${key.replaceAll('_','-')}`)]));
  const syncSettings=()=>{
    for(const [key,input] of settingsControls)input.value=String(settings[key]);
    for(const key of ['roof_rise','ridge_axis'])settingsControls.get(key).disabled=settings.roof_type!=='gable';
    settingsControls.get('roof_color').disabled=settings.roof_type==='none';settingsControls.get('roof_overhang').disabled=settings.roof_type==='none';
  };
  syncSettings();
  const stopRenders=setupRenders({source,name:name||'Casa sin nombre',sceneData,getSettings:()=>settings,getView:()=>{const direction=new THREE.Vector3();camera.getWorldDirection(direction);return {position:camera.position.toArray(),target:mode==='orbit'?controls.target.toArray():camera.position.clone().add(direction).toArray(),fov:camera.fov,hideRoof:hideRoof.checked,doorsOpen:open.checked};},sketchId});
  for(const [key,input] of settingsControls)input.onchange=()=>{
    if(!input.checkValidity()){input.reportValidity();return;}
    settings={...settings,[key]:['roof_rise','roof_overhang'].includes(key)?Number(input.value):input.value};
    if(key==='roof_type')hideRoof.checked=false;
    applyFinishes();rebuildRoof();syncSettings();onSettingsChange({...settings});
    if(mode==='orbit')preset('perspective');
    if(settings.roof_type!=='none'&&!sceneData.floors.length)status.textContent='Cierra el contorno del croquis para proponer un techo.';
  };
  const enter=()=>{
    const start=findWalkStart(sceneData);
    if(!start){status.textContent='No se encontró un espacio interior libre. Cierra el contorno y verifica que haya espacio entre las paredes.';return;}
    mode='walk';keys.clear();controls.enabled=false;walkControls.hidden=false;interiorButton.setAttribute('aria-pressed','true');
    dialog.querySelector('.viewer3d-finishes').open=false;
    camera.fov=70;camera.updateProjectionMatrix();camera.position.set(start.x,1.6,start.z);yaw=pitch=0;camera.rotation.set(0,0,0);
    instructions.textContent='Dentro de la casa · altura de vista 1,60 m. Arrastra para mirar. Usa W/A/S/D, flechas o mantén pulsados los botones. Para salir del modo interior, pulsa Centrar casa.';
    renderer.domElement.focus();
  };
  interiorButton.onclick=enter;
  document.getElementById('viewer3d-restart').onclick=enter;
  const onKeyDown=event=>{
    if(mode!=='walk'||['INPUT','SELECT','TEXTAREA','BUTTON','SUMMARY'].includes(event.target.tagName))return;
    const key=event.key.length===1?event.key.toLowerCase():event.key;
    if(['w','a','s','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(key)){event.preventDefault();keys.add(key);}
  };
  const onKeyUp=event=>keys.delete(event.key.length===1?event.key.toLowerCase():event.key);
  const stop=()=>{keys.clear();lookDrag=null;};
  const onLookDown=event=>{if(mode!=='walk'||event.button!==0)return;renderer.domElement.focus();lookDrag={id:event.pointerId,x:event.clientX,y:event.clientY};renderer.domElement.setPointerCapture(event.pointerId);};
  const onLookMove=event=>{if(!lookDrag||lookDrag.id!==event.pointerId)return;yaw-=(event.clientX-lookDrag.x)*.004;pitch=THREE.MathUtils.clamp(pitch-(event.clientY-lookDrag.y)*.004,-1.25,1.25);lookDrag.x=event.clientX;lookDrag.y=event.clientY;};
  const onLookUp=event=>{if(lookDrag?.id===event.pointerId)lookDrag=null;};
  const walkButtons=[...dialog.querySelectorAll('[data-walk]')];
  for(const button of walkButtons) {
    button.onpointerdown=event=>{event.preventDefault();keys.add(button.dataset.walk);button.setPointerCapture(event.pointerId);};
    button.onpointerup=button.onpointercancel=button.onlostpointercapture=()=>keys.delete(button.dataset.walk);
    button.onkeydown=event=>{if([' ','Enter'].includes(event.key)){event.preventDefault();keys.add(button.dataset.walk);}};
    button.onkeyup=()=>keys.delete(button.dataset.walk);button.onblur=()=>keys.delete(button.dataset.walk);
  }
  window.addEventListener('keydown',onKeyDown);window.addEventListener('keyup',onKeyUp);window.addEventListener('blur',stop);
  const onVisibility=()=>{if(document.hidden)stop();};document.addEventListener('visibilitychange',onVisibility);
  renderer.domElement.addEventListener('pointerdown',onLookDown);renderer.domElement.addEventListener('pointermove',onLookMove);
  renderer.domElement.addEventListener('pointerup',onLookUp);renderer.domElement.addEventListener('pointercancel',onLookUp);
  renderer.domElement.addEventListener('lostpointercapture',onLookUp);
  const count=(n,singular,plural)=>`${n} ${n===1?singular:plural}`;
  status.textContent=[[count(source.objects.filter(o=>o.kind==='wall').length,'pared','paredes'),count(sceneData.openings.filter(o=>o.kind==='door').length,'puerta','puertas'),count(sceneData.openings.filter(o=>o.kind==='window').length,'ventana','ventanas')].join(' · '),...sceneData.warnings].join('. ');
  document.getElementById('viewer3d-close').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{
    observer.disconnect();renderer.setAnimationLoop(null);controls.dispose();stop();
    stopRenders();
    window.removeEventListener('keydown',onKeyDown);window.removeEventListener('keyup',onKeyUp);window.removeEventListener('blur',stop);document.removeEventListener('visibilitychange',onVisibility);
    renderer.domElement.removeEventListener('pointerdown',onLookDown);renderer.domElement.removeEventListener('pointermove',onLookMove);renderer.domElement.removeEventListener('pointerup',onLookUp);renderer.domElement.removeEventListener('pointercancel',onLookUp);renderer.domElement.removeEventListener('lostpointercapture',onLookUp);
    renderer.domElement.removeEventListener('webglcontextlost',onLost);
    const geometries=new Set(),usedMaterials=new Set(Object.values(materials));
    scene.traverse(object=>{if(object.geometry)geometries.add(object.geometry);if(object.material)usedMaterials.add(object.material);});
    for(const geometry of geometries)geometry.dispose();
    const textures=new Set();for(const material of usedMaterials){for(const key of ['map','bumpMap','roughnessMap'])if(material[key])textures.add(material[key]);material.dispose();}for(const texture of textures)texture.dispose();
    sun.shadow.dispose();renderer.dispose();renderer.forceContextLoss();host.replaceChildren();
    cutaway.onchange=open.onchange=hideRoof.onchange=null;for(const button of buttons)button.onclick=null;
    for(const input of settingsControls.values())input.onchange=null;
    for(const button of walkButtons)button.onpointerdown=button.onpointerup=button.onpointercancel=button.onlostpointercapture=button.onkeydown=button.onkeyup=button.onblur=null;
    interiorButton.onclick=document.getElementById('viewer3d-restart').onclick=null;
  },{once:true});
  return sceneData;
}
