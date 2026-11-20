// Recalculate must use the visible settings, after their validation succeeds.
export async function recalculateWithSettings(pending, applySettings, calculate) {
  if(pending && await applySettings()===false)return;
  return calculate();
}
