# Skill: Cierre de tarea SIGQUA

## Cuando usar
Usar esta skill antes de cerrar una tarea tecnica relevante.

## Checklist
1. Confirmar que no reaparecio la estructura antigua por capas internas.
2. Confirmar que la UI no contiene SQL ni logica de negocio critica.
3. Confirmar que la persistencia sensible pasa por repositorios.
4. Confirmar que las reglas de negocio viven en servicios.
5. Confirmar que rutas y logs siguen centralizados.
6. Confirmar que integraciones externas dependen de contratos.
7. Confirmar que no se expusieron secretos o datos sensibles.
8. Confirmar que la documentacion quedo util si la tarea la requeria.
9. Confirmar que, si hubo investigacion externa, el aprendizaje reutilizable quedo reflejado en la skill o rol correspondiente y no solo en la respuesta puntual.
10. Confirmar que, si la tarea genero un plan, PRD, issue o decision duradera, quedo registrada en `docs/agents/` o en la boveda externa que corresponda.
11. Confirmar que el cierre menciona las pruebas ejecutadas o explica claramente por que no se ejecutaron.
12. Confirmar que cualquier uso de skills globales respeta la jerarquia: `agents.md` manda sobre `agents/codex/` y sobre skills globales.
