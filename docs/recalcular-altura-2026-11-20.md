# Recalcular después de cambiar altura — 20 de noviembre de 2026

Caso reportado: una pared de 13 metros calcula materiales a 2,50 m; cambiar la altura general a 2,70 m y pulsar Recalcular deja el desglose vacío.

Se reprodujo la diferencia entre el motor y la interfaz: el motor devuelve ready y 8 partidas a 2,50, 2,70 y 2,90 m para 12 cm. La interfaz borraba el resultado al editar la configuración y Recalcular se detenía por settingsDirty, exigiendo un segundo botón, Aplicar configuración.

## Cambio

Recalcular valida y aplica la configuración visible pendiente y luego solicita los materiales. Comparte la función de aplicación con el formulario existente. Si la validación falla, no calcula con la altura anterior ni deja aplicada una configuración parcial. Si el croquis o los campos cambian durante la solicitud, pide volver a recalcular. Aplicar configuración sigue disponible y mantiene su recálculo automático.

La modificación no cambia las recetas ni habilita alturas nuevas para 10 cm. No hay migraciones ni cambios automáticos en proyectos guardados.

## Validación

Prueba de la pared de 13 m en las tres alturas y ambas preferencias de paño (1,50 y 2 m): 8 partidas, 13 metros modulados y una hilada de viga a 2,50/2,70 o dos a 2,90. Pruebas de flujo: aplicar antes de calcular, configuración inválida/rechazada y recálculo directo sin cambios pendientes.

Comprobación completa aprobada: 156 pruebas Django y 72 JavaScript (228). Estado: pendiente de aplicar en producción; incluye las mejoras anteriores de texto y giro.
