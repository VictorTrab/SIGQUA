# Skill: mejora_ui_faseada_figma_mcp
Fecha de actualización: 2026-05-03

## Herencia
Esta skill asume las reglas globales de `agents.md`.
Cuando la tarea implique implementar o refinar pantallas PySide6, conviene usarla junto con `agents/codex/skills/interfaz_visual_premium_pyside6/SKILL.md`.

## Objetivo
Guiar mejoras de UI de SIGQUA usando el MCP de Figma como referencia de contexto, no como diseño a copiar literalmente.

## Cuándo usarla
Úsala solo cuando se vaya a:
- revisar una pantalla o flujo existente en Figma Make
- corregir errores de diseño antes de implementar en PySide6
- simplificar navegación, filtros, jerarquía visual o acciones
- trabajar una fase concreta del sistema, por ejemplo login, shell principal o un módulo específico

## Regla principal
Figma Make es una base inicial.
No copiar de forma ciega.
Siempre decidir si cada elemento debe:
- quedarse
- modificarse
- eliminarse

## Criterios de análisis
Antes de implementar, evaluar:
- si el flujo es claro para el usuario real
- si existe redundancia de módulos, botones o filtros
- si hay identificadores duplicados o confusos
- si la jerarquía visual ayuda o estorba
- si la acción principal está clara
- si el diseño reduce errores operativos

## Procedimiento mínimo
1. leer la fase o pantalla actual desde Figma MCP
2. identificar objetivo real de la pantalla
3. detectar errores obvios de Figma Make
4. decidir qué conservar, qué simplificar y qué mover
5. proponer ajuste incremental, no rediseño total
6. implementar solo cuando el flujo ya tenga sentido

## Reglas operativas
- trabajar por fases, no intentar rehacer toda la app en una sola tarea
- priorizar pantallas principales antes que modales secundarios
- no duplicar flujos entre módulos
- no mantener un módulo solo porque existe en Figma Make
- mover la lógica al módulo correcto si mejora la experiencia
- preferir menos elementos visibles y mejor jerarquía

## Reglas de SIGQUA
- abonado = DNI como clave visible
- casa = código de casa como clave visible
- no usar número de cuenta si duplica código de casa
- no mostrar ids internos al usuario
- diferenciar meses pendientes, meses en mora y pago adelantado
- si hay mora, el cobro inicia desde el mes más antiguo

## Filtros y navegación
Cuando el problema sea visual o de uso:
- dejar visibles solo filtros frecuentes
- mover filtros variados a listas desplegables
- ocultar filtros avanzados por defecto
- usar vista personalizada solo donde aporte valor real
- reducir módulos redundantes en el menú principal

## Errores típicos de Figma Make
Corregir especialmente:
- flujos duplicados
- botones sin prioridad clara
- demasiados filtros visibles
- procesos partidos en módulos innecesarios
- nombres inconsistentes
- lógica operativa separada del contexto correcto
- formularios con campos redundantes

## Profundidad recomendada
Con tiempos cortos, limitar el análisis a:
- qué está bien
- qué estorba
- qué falta

No convertir cada pantalla en una auditoría larga.

## Resultado esperado
Una mejora incremental de UI más clara, más útil y más coherente con SIGQUA, donde Codex piense antes de implementar y use Figma como referencia crítica, no como fuente absoluta de verdad.
