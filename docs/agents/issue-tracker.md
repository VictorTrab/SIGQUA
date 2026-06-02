# Issue tracker: Markdown local

El tracker operativo inicial de SIGQUA vive dentro del repositorio, en Markdown local.

## Ubicacion

- PRD: `docs/agents/prd/`
- Issues: `docs/agents/issues/`
- ADR: `docs/agents/adr/`

## Convenciones

- Un PRD debe describir objetivo, contexto, alcance, criterios de aceptacion y riesgos.
- Un issue debe representar una unidad implementable por un agente o desarrollador.
- Usar nombres numerados cuando haya secuencia: `001-nombre-corto.md`.
- Registrar estado con una linea `Estado:` cerca del inicio del archivo.
- Cuando una conversacion resuelva decisiones tecnicas duraderas, crear o actualizar un ADR.

## Cuando una skill diga "publicar en el tracker"

Crear o actualizar un archivo Markdown en `docs/agents/prd/` o `docs/agents/issues/`, segun corresponda. No crear issues en GitHub salvo que el usuario lo pida explicitamente.

## Cuando una skill diga "leer el ticket"

Leer el archivo Markdown indicado por el usuario o buscar el issue/PRD local mas cercano dentro de `docs/agents/`.
