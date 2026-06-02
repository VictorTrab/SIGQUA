# Domain docs

Las skills globales de Matt Pocock deben consumir la documentacion de dominio de SIGQUA con estas reglas.

## Antes de explorar

Leer primero:

- `agents.md`
- `docs/agents/CONTEXT.md`
- ADR relevantes en `docs/agents/adr/`
- Skills locales relevantes en `agents/codex/skills/`

## Layout

SIGQUA usa contexto unico:

```text
docs/
  agents/
    CONTEXT.md
    adr/
    prd/
    issues/
```

## Vocabulario

Usar los nombres de dominio definidos en `docs/agents/CONTEXT.md`. Si falta un concepto, proponerlo durante una sesion de `interrogar` o `grill-with-docs` antes de convertirlo en regla permanente.

## Conflictos

Si una recomendacion global contradice `agents.md`, prevalece `agents.md`. Si contradice un ADR vigente, marcarlo explicitamente antes de proponer el cambio.
