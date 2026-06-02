# ADR: Avisos de cobro y cambio de responsable por casa

Fecha: 2026-05-28

## Estado

Aceptada para el prototipo SIGQUA.

## Contexto

Las entrevistas recientes confirmaron que una persona puede tener mas de una casa y que el control real de deuda, pagos, planes y cortes debe hacerse por casa. Tambien se identifico la necesidad administrativa de registrar tres avisos antes del corte y conservar trazabilidad cuando el abonado original fallece o se cambia el responsable de la vivienda.

## Decision

- La deuda permanece vinculada a `casas`.
- Los cambios de responsable se registran en `historial_propietarios_casa` con motivo, observacion, fecha y usuario.
- Se agrega el motivo canonico `FALLECIMIENTO_DEL_ABONADO`.
- Las casas guardan la etapa manual de aviso de cobro: `SIN_AVISO`, `PRIMER_AVISO`, `SEGUNDO_AVISO`, `TERCER_AVISO`, `LISTO_PARA_CORTE`, `CORTADO`.
- Morosidad permite registrar avisos, pero no corta automaticamente.
- El estado `CORTADO` se sincroniza desde el corte manual del modulo de casas.

## Consecuencias

- Los reportes y filtros deben preferir casa como unidad operativa.
- El estado de cuenta puede mostrar la etapa de aviso sin convertirla en accion automatica.
- La UI debe separar comprobantes termicos de reportes PDF administrativos.
- Egresos queda fuera de alcance hasta que exista un modulo de gastos.
