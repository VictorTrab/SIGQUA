# Contexto de dominio SIGQUA

Este archivo resume el lenguaje de dominio que deben usar las skills globales de arquitectura, diagnostico, TDD y documentacion cuando trabajen en SIGQUA. No reemplaza `agents.md`; solo ayuda a mantener vocabulario comun.

## Producto

SIGQUA es una aplicacion de escritorio para la gestion administrativa de la Junta de Agua de Yarumela.

## Stack vigente

- Python.
- PySide6 para interfaz de escritorio.
- SQLite para persistencia local.
- python-dotenv para configuracion de entorno.

## Modulos funcionales actuales

- `abonados`: personas o titulares asociados al servicio.
- `barrios`: organizacion territorial usada por casas y abonados.
- `casas`: unidades atendidas por la junta de agua.
- `pagos`: registro y control de pagos.
- `historial_pagos`: consulta historica de pagos.
- `morosidad`: seguimiento de saldos vencidos y reportes asociados.
- `planes_pago`: acuerdos para regularizar deuda.
- `comprobantes`: soporte documental de pagos o movimientos.
- `documentos`: generacion o manejo de documentos.
- `reportes`: salidas administrativas y consultas agregadas.
- `usuarios`: gestion de usuarios operativos.
- `autenticacion`: acceso local, cambio obligatorio de contrasena y recuperacion administrativa.
- `configuracion`: preferencias y parametros del sistema.
- `mantenimiento`: tareas tecnicas reservadas a `SUPERADMINISTRADOR`.
- `principal`: shell o navegacion principal de la aplicacion.

## Reglas de arquitectura

- La UI no contiene SQL ni reglas de negocio criticas.
- SQLite se accede mediante repositorios.
- Las reglas de negocio viven en servicios.
- Los controladores conectan vistas con servicios.
- El codigo compartido vive en `src/comun/`.
- Cada modulo debe preferir archivos simples: `entidades.py`, `repositorio.py`, `servicio.py`, `controlador.py`, `vista.py`.

## Seguridad y acceso

- La autenticacion vigente es local.
- No existe recuperacion por correo en esta version.
- `ADMINISTRADOR` es operativo.
- `SUPERADMINISTRADOR` es tecnico, oculto y requerido para mantenimiento.
- No guardar secretos, contrasenas ni tokens sensibles en texto plano.

## Reglas de dominio vigentes

- La deuda, cargos, pagos historicos y planes activos pertenecen a la casa; el responsable actual puede cambiar sin reiniciar obligaciones.
- El cambio de responsable conserva historial con motivo, fecha, usuario y observacion. El motivo canonico para fallecimiento es `FALLECIMIENTO_DEL_ABONADO`.
- La morosidad usa etapas manuales de aviso: `SIN_AVISO`, `PRIMER_AVISO`, `SEGUNDO_AVISO`, `TERCER_AVISO`, `LISTO_PARA_CORTE` y `CORTADO`.
- `LISTO_PARA_CORTE` solo identifica candidatas; el corte del servicio sigue siendo una accion manual desde casas.
- Los comprobantes de pago siguen siendo termicos ESC/POS. Los reportes administrativos bajo demanda son PDF y no sustituyen comprobantes.
- Egresos/gastos quedan fuera del prototipo activo hasta que exista un modulo dedicado.

## Documentacion relacionada

- Reglas obligatorias: `agents.md`.
- Skills locales: `agents/codex/skills/`.
- Decisiones tecnicas nuevas: `docs/agents/adr/`.
- PRD locales: `docs/agents/prd/`.
- Issues locales: `docs/agents/issues/`.
