# Reglas globales del agente Codex para SICAP
Fecha de actualización: 2026-05-03

## Propósito
Este archivo define las reglas globales y obligatorias para trabajar SICAP con Codex.

## Contexto base
- Tipo de proyecto: aplicación de escritorio para gestión administrativa de la Junta de Agua de Yarumela.
- Stack principal: Python, PySide6, SQLite, Resend y python-dotenv.
- Estructura base del código:
  - `src/comun/`
  - `src/apis/`
  - `src/modulos/`

## Regla de jerarquía
Este archivo manda sobre cualquier otro archivo de `agents/codex/`.
Los archivos temáticos de `agents/codex/` amplían estas reglas y no deben contradecirlas.

## Regla de carga mínima
Para cada tarea:
- cargar solo el contexto realmente necesario;
- usar `agents.md` como punto de entrada por defecto;
- cargar solo 1 rol principal desde `agents/codex/roles/`;
- cargar 0 o 1 skill de apoyo desde `agents/codex/skills/`;
- evitar leer reglas completas no relacionadas con la tarea actual.

## Reglas obligatorias
1. Usar arquitectura modular con módulos dentro de `src/modulos/`.
2. No volver a la estructura interna obligatoria `dominio/`, `aplicacion/`, `infraestructura/` y `presentacion/` dentro de cada módulo.
3. Aplicar SOLID de forma práctica y sin abstracciones innecesarias.
4. Cada módulo funcional debe preferir archivos simples y claros:
   - `entidades.py`
   - `repositorio.py`
   - `servicio.py`
   - `controlador.py`
   - `vista.py`
5. La UI no debe contener SQL.
6. La UI no debe contener reglas de negocio críticas.
7. La persistencia SQLite debe pasar por repositorios.
8. Las reglas de negocio deben vivir en servicios.
9. Los controladores deben conectar vistas con servicios.
10. El código compartido debe vivir en `src/comun/`.
11. Las integraciones externas deben vivir en `src/apis/`.
12. Los módulos deben depender de contratos cuando se integren con servicios externos.
13. Toda ruta del sistema debe centralizarse en `src/comun/configuracion/gestor_rutas.py`.
14. No usar rutas absolutas hardcodeadas del equipo del desarrollador.
15. Mantener nombres en español, claros y autodescriptivos.
16. No guardar secretos reales, contraseñas ni tokens sensibles en texto plano.
17. Mantener documentación breve, útil y defendible para tesis.
18. Cuando se usen iconos en la UI, preferir Tabler Icons descargados localmente y centralizados en `src/comun/ui/recursos/iconos/tabler/`.

## Documentos temáticos
Consultar según el tipo de tarea:
- `agents/codex/roles/arquitecto_software.md`
- `agents/codex/roles/desarrollador_datos_sqlite.md`
- `agents/codex/roles/desarrollador_pyside6.md`
- `agents/codex/roles/integrador_apis_externas.md`
- `agents/codex/roles/especialista_soporte_operativo.md`
- `agents/codex/roles/documentador_tecnico.md`
- `agents/codex/roles/asegurador_calidad.md`
- `agents/codex/skills/desarrollo_sicap/SKILL.md`
- `agents/codex/skills/cierre_tarea_sicap/SKILL.md`
- `agents/codex/skills/seguridad-sicap/SKILL.md`
- `agents/codex/skills/mejora_ui_faseada_figma_mcp/SKILL.md`
- `agents/codex/skills/documentacion_en_boveda/SKILL.md`

## Criterio de aceptación
Un cambio se considera correcto solo si:
- respeta la arquitectura modular actual;
- mantiene bajo acoplamiento;
- no mezcla interfaz, negocio y persistencia;
- usa contratos cuando toca integraciones externas;
- centraliza rutas;
- cuida seguridad básica;
- deja el código claro, mantenible y escalable.
