"use strict";
const form = document.querySelector("#template-form");
const pending = document.querySelector("#pending");
const printButton = document.querySelector("#print");
let dirty = false;
let unsaved = document.body.dataset.unsaved === "true";
function markDirty() {
  dirty = true;
  unsaved = true;
  pending.hidden = false;
  printButton.disabled = true;
}
form.addEventListener("input", markDirty);
form.addEventListener("change", markDirty);
form.addEventListener("submit", () => { dirty = false; unsaved = false; });
printButton.addEventListener("click", () => { if (!dirty) window.print(); });
window.addEventListener("beforeunload", event => {
  if (unsaved) { event.preventDefault(); event.returnValue = ""; }
});
