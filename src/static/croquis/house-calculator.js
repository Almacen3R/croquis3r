"use strict";
const form = document.querySelector("#calculator");
const mode = document.querySelector("#id_column_mode");
const pending = document.querySelector("#pending");
const printButton = document.querySelector("#print");
let dirty = false;
let unsaved = document.body.dataset.unsaved === "true";
function setColumnMode() {
  const chain = mode.value === "chain";
  // Se conservan las entradas manuales para poder volver a usarlas.
  document.querySelectorAll("#manual-columns input").forEach(input => {
    input.readOnly = chain;
    input.setAttribute("aria-describedby", "column-help");
  });
}
function markDirty() {
  dirty = true;
  unsaved = true;
  pending.hidden = false;
  printButton.disabled = true;
}
mode.addEventListener("change", setColumnMode);
form.addEventListener("input", markDirty);
form.addEventListener("change", markDirty);
form.addEventListener("submit", () => { dirty = false; unsaved = false; });
document.querySelector("#example").addEventListener("click", () => {
  form.querySelectorAll('input[type="number"]').forEach(input => { input.value = "0"; });
  document.querySelector("#id_project").value = "Ejemplo · 7 paños completos";
  document.querySelector("#id_panel_4").value = "6";
  document.querySelector("#id_panel_5").value = "1";
  document.querySelector("#id_height").value = "1";
  mode.value = "chain";
  familyField.value='12';floorField.value='1';setFamilyControls();
  setColumnMode();
  markDirty();
  document.querySelector("#id_panel_4").focus();
});
printButton.addEventListener("click", () => { if (!dirty) window.print(); });
window.addEventListener("beforeunload", event => {
  if (unsaved) { event.preventDefault(); event.returnValue = ""; }
});
setColumnMode();
if (document.querySelector(".empty")) printButton.disabled = true;

// Asistente por metros: el servidor propone; aplicar no guarda ni calcula sin revisión.
const distributionForm=document.querySelector('#distribution-form');
const distributionResult=document.querySelector('#distribution-result');
const distributionActions=document.querySelector('#distribution-actions');
let suggestion=null, suggestionRequest=0;
function clearSuggestion(){
  suggestion=null; suggestionRequest++; distributionActions.hidden=true;
  distributionResult.hidden=true; distributionResult.replaceChildren();
}
distributionForm.addEventListener('input',clearSuggestion);
distributionForm.addEventListener('change',clearSuggestion);
distributionForm.addEventListener('submit',async event=>{
  event.preventDefault(); clearSuggestion(); const request=suggestionRequest;
  try {
    const token=distributionForm.querySelector('[name=csrfmiddlewaretoken]').value;
    const response=await fetch('/api/suggest-panels/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':token},body:JSON.stringify(Object.fromEntries(new FormData(distributionForm)))});
    const body=await response.json();
    if(request!==suggestionRequest)return;
    if(!response.ok)throw Error(body.error||'No se pudo proponer la distribución.');
    suggestion=body;
    const summary=document.createElement('p');
    summary.textContent=`${body.meters.replace('.',',')} m = ${body.rows.map(row=>`${row.quantity} paño${row.quantity===1?'':'s'} de ${row.length.replace('.',',')} m`).join(' + ')}. Total: ${body.panels} paños.`;
    distributionResult.append(summary); distributionActions.hidden=false;
  } catch(error){if(request!==suggestionRequest)return;distributionResult.textContent=error.message;}
  distributionResult.hidden=false;
});
function applySuggestion(add){
  if(!suggestion)return;
  const rows={'2':4,'1.5':5,'1':6,'0.5':7};
  const updates=Object.entries(rows).map(([length,row])=>{
    const input=document.querySelector(`#id_panel_${row}`);
    const quantity=suggestion.rows.find(r=>r.length===length)?.quantity||0;
    return {input,value:quantity+(add?Number(input.value):0)};
  });
  if(updates.some(({input,value})=>!Number.isInteger(value)||value<0||value>Number(input.max))){
    distributionResult.textContent='La distribución supera el límite de 100 paños por clase del calculador. Divide el cálculo en atenciones separadas o usa otra medida preferida.';
    return;
  }
  for(const {input,value} of updates)input.value=String(value);
  markDirty();
  distributionResult.textContent=`Distribución ${add?'agregada':'aplicada'}. Revisa los paños, las aberturas y las columnas, y pulsa Calcular materiales.`;
  suggestion=null;distributionActions.hidden=true;
}
document.querySelector('#distribution-replace').onclick=()=>applySuggestion(false);
document.querySelector('#distribution-add').onclick=()=>applySuggestion(true);

const familyField=document.querySelector('#id_block_family');
const heightField=document.querySelector('#id_height');
const floorField=document.querySelector('#id_floor_level');
function setFamilyControls(){
  const narrow=familyField.value==='10';
  for(const option of heightField.options)option.disabled=narrow&&option.value!=='0';
  if(narrow)heightField.value='0';
  floorField.querySelector('option[value="2"]').disabled=narrow;
  familyField.querySelector('option[value="10"]').disabled=floorField.value==='2';
}
familyField.addEventListener('change',setFamilyControls);
floorField.addEventListener('change',setFamilyControls);
setFamilyControls();
