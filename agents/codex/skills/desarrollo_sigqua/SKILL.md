# Skill: Desarrollo SIGQUA

## Cuando usar
Usar esta skill cuando la tarea implique crear, mover o ajustar codigo del proyecto y se necesite un flujo corto de trabajo.

## Flujo
1. Leer `agents.md`.
2. Revisar primero la documentacion interna relevante antes de consultar fuentes externas.
   Si la tarea toca reglas de negocio de pagos, morosidad, casas, abonados, planes de pago, comprobantes, reportes, configuracion o usuarios, revisar tambien la boveda en `C:\Users\User\Documents\SIGQUA DOCUMENTACION\Documentacion\`, priorizando `01_Requerimientos\Reglas_de_Negocio_Cerradas_v1\` cuando aplique.
3. Si el area de codigo no esta clara, usar `zoom-out` para obtener un mapa de modulos, llamadas y dependencias antes de cambiar archivos.
4. Si el plan, alcance o diseno tiene decisiones abiertas, usar `interrogar` o `grill-with-docs` antes de implementar:
   - `interrogar` para resolver decisiones con el usuario sin documentacion adicional.
   - `grill-with-docs` cuando la conversacion deba actualizar `docs/agents/CONTEXT.md` o `docs/agents/adr/`.
5. Cargar 1 rol principal segun la naturaleza de la tarea.
6. Usar 0 o 1 skill de apoyo adicional solo si agrega valor real al flujo.
7. Implementar el cambio respetando la arquitectura modular vigente y las reglas activas del rol elegido.
8. Si hubo investigacion externa o una decision reutilizable, persistir el aprendizaje en la skill, rol, `docs/agents/CONTEXT.md` o ADR mas cercano al tema.
9. Antes de cerrar, pasar por la checklist de `cierre_tarea_sigqua` cuando la tarea sea relevante.

## Skills globales recomendadas
- `zoom-out`: entender un area antes de tocarla.
- `diagnose`: depurar bugs dificiles con ciclo reproducible.
- `tdd`: trabajar test-first cuando el comportamiento puede especificarse antes.
- `improve-codebase-architecture`: detectar oportunidades de arquitectura y testabilidad.
- `to-prd` y `to-issues`: convertir planes en Markdown local dentro de `docs/agents/`.

## Resultado esperado
El cambio debe quedar claro, corto de mantener, coherente con SOLID practico y sin duplicar reglas ya definidas en `agents.md`.
