# Reglas globales del agente Codex para SICAP
Fecha de actualizacion: 2026-05-06

## Proposito
Este archivo define las reglas globales y obligatorias para trabajar SICAP con Codex.

## Contexto base
- Tipo de proyecto: aplicacion de escritorio para gestion administrativa de la Junta de Agua de Yarumela.
- Stack principal: Python, PySide6, SQLite y python-dotenv.
- La autenticacion activa es local:
  - sin recuperacion por correo;
  - sin Resend en el flujo activo;
  - con restablecimiento administrativo y cambio obligatorio de contrasena cuando aplique.
- Estructura base del codigo:
  - `src/comun/`
  - `src/modulos/`

## Regla de jerarquia
Este archivo manda sobre cualquier otro archivo de `agents/codex/`.
Los archivos tematicos de `agents/codex/` amplian estas reglas y no deben contradecirlas.

## Regla de carga minima
Para cada tarea:
- cargar solo el contexto realmente necesario;
- usar `agents.md` como punto de entrada por defecto;
- cargar solo 1 rol principal desde `agents/codex/roles/`;
- cargar 0 o 1 skill de apoyo desde `agents/codex/skills/`;
- evitar leer reglas completas no relacionadas con la tarea actual.

## Reglas obligatorias
1. Usar arquitectura modular con modulos dentro de `src/modulos/`.
2. No volver a la estructura interna obligatoria `dominio/`, `aplicacion/`, `infraestructura/` y `presentacion/` dentro de cada modulo.
3. Aplicar SOLID de forma practica y sin abstracciones innecesarias.
4. Cada modulo funcional debe preferir archivos simples y claros:
   - `entidades.py`
   - `repositorio.py`
   - `servicio.py`
   - `controlador.py`
   - `vista.py`
5. La UI no debe contener SQL.
6. La UI no debe contener reglas de negocio criticas.
7. La persistencia SQLite debe pasar por repositorios.
8. Las reglas de negocio deben vivir en servicios.
9. Los controladores deben conectar vistas con servicios.
10. El codigo compartido debe vivir en `src/comun/`.
11. En esta version no existe carpeta `src/apis/` ni integracion activa con Resend.
12. Si en el futuro se reintroducen integraciones externas, deben aislarse con contratos claros y sin acoplar la logica del modulo al proveedor.
13. Toda ruta del sistema debe centralizarse en `src/comun/configuracion/gestor_rutas.py`.
14. No usar rutas absolutas hardcodeadas del equipo del desarrollador.
15. Mantener nombres en espanol, claros y autodescriptivos.
16. No guardar secretos reales, contrasenas ni tokens sensibles en texto plano.
17. Mantener documentacion breve, util y defendible para tesis.
18. Cuando se usen iconos en la UI, preferir Tabler Icons descargados localmente y centralizados en `src/comun/ui/recursos/iconos/tabler/`.
19. Cuando un modulo aun no este completo, su vista debe mostrar un aviso visible y claro indicando que el modulo esta en desarrollo.
20. En PySide6, no reutilizar widgets que hayan sido reemplazados como `centralWidget` ni asumir que siguen vivos despues de cambios de contenedor.
21. Cuando haya navegacion entre pantallas o modulos en PySide6, preferir contenedores persistentes como `QStackedWidget` antes que reemplazar widgets raiz y conservar referencias fragiles.
22. Cuando un flujo dependa de ciclo de vida de widgets, registrar eventos relevantes con logs y verificar explicitamente el retorno de navegacion en pruebas.
23. La seguridad activa debe respetar la separacion entre `ADMINISTRADOR` operativo y `SUPERADMINISTRADOR` tecnico oculto.
24. El modulo de mantenimiento debe quedar reservado para `SUPERADMINISTRADOR`.
25. La recuperacion de acceso vigente es local y administrativa, nunca por correo en esta version.
26. Todo dato precargado, semilla, ejemplo o registro marcado para desarrollo dentro del repositorio o de la base local debe considerarse exclusivamente dato de prueba y nunca dato productivo real.

## Documentos tematicos
Consultar segun el tipo de tarea:
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
- `agents/codex/skills/interfaz_visual_premium_pyside6/SKILL.md`
- `agents/codex/skills/documentacion_en_boveda/SKILL.md`

## Criterio de aceptacion
Un cambio se considera correcto solo si:
- respeta la arquitectura modular actual;
- mantiene bajo acoplamiento;
- no mezcla interfaz, negocio y persistencia;
- usa contratos si en el futuro vuelve a tocar integraciones externas;
- centraliza rutas;
- cuida seguridad basica;
- respeta la separacion entre administracion operativa y mantenimiento tecnico;
- deja el codigo claro, mantenible y escalable.
