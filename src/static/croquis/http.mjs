export function cookieValue(cookies, name) {
  const prefix = `${name}=`;
  const entry = cookies.split(';').map(value => value.trim()).find(value => value.startsWith(prefix));
  return entry ? entry.slice(prefix.length) : '';
}

export async function requestJson(path, options = {}, fetcher = fetch) {
  let response;
  try {
    response = await fetcher(path, {credentials: 'same-origin', ...options});
  } catch {
    throw new Error('No se pudo conectar con el servidor. Conserva esta pestaña y vuelve a intentar; tu dibujo sigue abierto.');
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (body?.code === 'authentication_required') {
      throw new Error('La sesión venció. Inicia sesión en otra pestaña de Croquis3R y vuelve a intentar aquí, sin cerrar tu dibujo.');
    }
    if (body?.error) throw new Error(body.error);
    if (response.status === 403 || response.status === 401) {
      throw new Error('La sesión o la verificación de seguridad venció. Inicia sesión en otra pestaña de Croquis3R y vuelve a intentar aquí, sin cerrar tu dibujo.');
    }
    throw new Error(`El servidor no pudo completar la solicitud (${response.status}). Conserva tu dibujo y vuelve a intentar.`);
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    throw new Error('El servidor devolvió una respuesta inesperada. Puede haber vencido la sesión. Conserva esta pestaña y revisa tu acceso a Croquis3R.');
  }
  return body;
}
