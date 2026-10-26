import test from 'node:test';
import assert from 'node:assert/strict';
import {cookieValue, requestJson} from '../src/static/croquis/http.mjs';

test('el token de Croquis3R se distingue del token de otras aplicaciones', () => {
  assert.equal(cookieValue('csrftoken=otro; croquis3r_csrftoken=propio; sessionid=ajeno', 'croquis3r_csrftoken'), 'propio');
  assert.equal(cookieValue('csrftoken=otro', 'croquis3r_csrftoken'), '');
});
test('un guardado JSON válido conserva identificación y usa la misma sesión', async () => {
  const result = await requestJson('/api/sketches/', {method:'POST'}, async (url, options) => {
    assert.equal(options.credentials, 'same-origin');
    return new Response(JSON.stringify({id:12,revision:1}), {status:201});
  });
  assert.deepEqual(result, {id:12,revision:1});
});
test('un rechazo con explicación conserva el error del servidor', async () => {
  await assert.rejects(requestJson('/api/sketches/12/', {}, async () => new Response(JSON.stringify({error:'Otra sesión modificó este croquis.'}), {status:409})), /Otra sesión modificó/);
});
test('CSRF o sesión vencida con HTML explica cómo recuperar sin perder el dibujo', async () => {
  await assert.rejects(requestJson('/api/sketches/', {}, async () => new Response('<html>403</html>', {status:403})), /otra pestaña.*sin cerrar tu dibujo/);
});
test('la respuesta de sesión vencida indica cómo volver a guardar', async () => {
  await assert.rejects(requestJson('/api/sketches/', {}, async () => new Response(JSON.stringify({code:'authentication_required',error:'Inicie sesión'}), {status:403})), /otra pestaña.*sin cerrar tu dibujo/);
});
test('una redirección a login no se interpreta como guardado correcto', async () => {
  await assert.rejects(requestJson('/api/sketches/', {}, async () => new Response('<html>Ingresar</html>', {status:200})), /respuesta inesperada/);
});
test('un fallo de red y un error 500 tienen mensajes visibles y recuperables', async () => {
  await assert.rejects(requestJson('/api/sketches/', {}, async () => {throw new TypeError('Failed to fetch');}), /dibujo sigue abierto/);
  await assert.rejects(requestJson('/api/sketches/', {}, async () => new Response('Error', {status:500})), /500/);
});
