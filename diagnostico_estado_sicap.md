# Diagnostico del estado actual del proyecto SICAP

Fecha: 2026-05-15

## Criterio usado

Se reviso el codigo actual, la estructura modular, migraciones, base SQLite, vistas, controladores, servicios, repositorios, pruebas existentes y composicion de la aplicacion. No se modifico codigo. Figma queda como apoyo visual secundario; la fuente principal de verdad es el estado real del repositorio y la base local.

Los modulos se clasifican separando UI, logica, persistencia, integracion real y datos. Un modulo se considera realmente funcional solo si tiene flujo usable de punta a punta: vista conectada, controlador, servicio, repositorio SQLite, datos persistidos, validaciones minimas, filtros/listados/acciones y ausencia de placeholders criticos.

## 1. Resumen ejecutivo

SICAP tiene una base arquitectonica solida para prototipo. Autenticacion, dashboard, barrios, abonados, casas, usuarios, configuracion y parte de planes de pago siguen el patron modular esperado y mantienen una separacion razonable entre UI, controlador, servicio y repositorio.

El riesgo principal es que el proyecto ya tiene una presentacion visual avanzada, pero todavia no tiene cerrado el nucleo operativo de cobro. Pagos, morosidad y reportes no estan funcionales como modulos reales. La base SQLite si tiene tablas y vistas para cargos, pagos, deuda, planes y reportes, pero la aplicacion todavia no expone esos flujos de forma completa.

La base actual contiene datos de prueba/desarrollo: `abonados=5`, `casas=5`, `cargos=5`, `pagos=1`, `planes_pago=0`, `cuotas_plan_pago=0`. Esto confirma que hay soporte de datos, pero no operacion completa viva.

## 2. Inventario de modulos

| Modulo | Estado actual | Avance | Conexion BD | Prioridad | Observaciones |
|---|---:|---:|---|---|---|
| Autenticacion | Funcional para prototipo | 85% | Si | Alta | Login local, bloqueo, sesion y cambio obligatorio. |
| Principal / dashboard | Funcional con pendientes | 75% | Si | Alta | Dashboard consulta datos reales, pero depende de pagos/deuda. |
| Atencion al abonado | No iniciado | 0% | No | Media | No existe como modulo separado; parte vive en abonados/casas. |
| Barrios | Funcional para prototipo | 85% | Si | Alta | CRUD operativo, filtros, tabla, detalle, exportacion. |
| Abonados | Funcional con pendientes | 80% | Si | Alta | CRUD, filtros, detalle y relacion con casas. Falta cerrar impacto financiero. |
| Casas | Funcional con pendientes | 80% | Si | Alta | CRUD, detalle, cambio de dueno, deuda visible. Depende de pagos/morosidad. |
| Pagos | Estructura creada | 10% | Solo esquema BD | Critica | Codigo es esqueleto; app muestra placeholder. |
| Morosidad | UI parcial / placeholder | 15% | Vistas SQL parciales | Critica | No hay carpeta de modulo; solo navegacion y soporte SQL. |
| Planes de pago | Conectado parcialmente a BD | 65% | Si | Alta | UI/servicio/repositorio existen; falta integracion con pagos/cuotas reales. |
| Reportes | Estructura creada | 10% | Solo esquema BD | Media | Codigo es esqueleto; app muestra placeholder. |
| Usuarios | Funcional con pendientes | 70% | Si | Alta | Gestion administrativa limitada: listar, restablecer, desbloquear. |
| Configuracion | Funcional para prototipo | 75% | Si | Media | Edita junta/cobro; seguridad es informativa. |
| Mantenimiento tecnico | UI parcial conectada | 45% | Si parcial | Media | Reservado a superadmin; solo resume estado tecnico. |

## 3. Diagnostico por modulo

### Autenticacion

Esta bien encaminado. Tiene entidades, repositorio SQLite, servicio, controlador y vista PySide6. Maneja login local, sesiones, intentos fallidos, bloqueo, cierre de sesion, restablecimiento local y cambio obligatorio.

Estado recomendado: **Funcional para prototipo**.

Pendientes:
- Limpiar o controlar usuarios/credenciales de desarrollo antes de cualquier uso real.
- Validar politica final de contrasenas y bloqueo.
- Confirmar flujo exacto para cambio obligatorio de contrasena.

### Principal / Dashboard

Existe y esta integrado. Usa contenedor persistente, registra modulos operativos y consulta metricas reales desde SQLite. La UI esta bastante madura.

Estado recomendado: **Funcional con pendientes**.

Pendientes:
- El dashboard depende de pagos, deuda y morosidad, que aun no estan cerrados.
- Puede dar sensacion de avance mayor al real porque algunos indicadores se apoyan en datos de prueba.
- Pagos, morosidad y reportes aparecen como navegacion, pero se muestran como placeholders.

### Atencion al abonado

No existe como modulo independiente. Parte de su posible alcance esta repartido entre abonados y casas: consulta de abonado, casas asociadas, deuda, detalle y estado.

Estado recomendado: **No iniciado**.

Pendientes:
- Definir si sera un modulo separado o una vista compuesta dentro de abonados/casas.
- Aclarar si su objetivo sera consulta rapida, ventanilla de atencion, historial completo o soporte operativo.

### Barrios

Es uno de los modulos mas completos. Tiene CRUD real, filtros rapidos, tabla, acciones por fila, detalle, edicion, cambio de estado y exportacion CSV.

Estado recomendado: **Funcional para prototipo**.

Pendientes:
- Revisar reglas finales al inactivar barrios con abonados o casas asociadas.
- Mantenerlo como base estable para abonados y casas.

### Abonados

Tiene UI avanzada, filtros, listado, detalle, edicion, exportacion y cambio de estado. Ademas, al inactivar un abonado puede suspender casas asociadas.

Estado recomendado: **Funcional con pendientes**.

Pendientes:
- Definir impacto financiero y operativo de inactivar abonado con deuda, casas, planes o pagos pendientes.
- Confirmar si un abonado inactivo puede conservar historial visible.
- Evitar que el modulo avance mas sin cerrar pagos/morosidad.

### Casas

Esta avanzado. Maneja listado, filtros, detalle, cambio de estado, cambio de dueno, historial de propietarios y migracion de deuda/plan activo.

Estado recomendado: **Funcional con pendientes**.

Pendientes:
- Cerrar reglas de estados de servicio.
- Confirmar reglas de traspaso cuando existan pagos, deuda, mora o plan activo.
- Depende directamente de pagos y morosidad para que sus indicadores financieros sean confiables.

### Pagos

No esta funcional. La base tiene tablas `pagos`, `pagos_detalle`, `comprobantes`, `metodos_pago` y vistas de ingresos, pero el modulo Python solo tiene contratos/esqueleto. La aplicacion muestra un placeholder.

Estado recomendado: **Estructura creada**.

Pendientes:
- Crear vista real de registro de pagos.
- Listar cargos pendientes por casa/abonado.
- Aplicar pagos desde el cargo mas antiguo.
- Registrar detalle del pago.
- Actualizar saldos de cargos.
- Generar o registrar comprobante basico.
- Definir anulacion y auditoria.

### Morosidad

No existe como modulo independiente en `src/modulos`. Hay permisos, vistas SQL y navegacion, pero no hay UI operativa, filtros, detalle por abonado/casa ni acciones.

Estado recomendado: **UI parcial / placeholder**.

Pendientes:
- Crear modulo real o vista dedicada.
- Definir diferencia entre deuda pendiente, meses vencidos, mora y multa.
- Mostrar deuda por casa, abonado y barrio.
- Conectar con pagos y planes de pago.

### Planes de pago

Tiene UI avanzada, repositorio, servicio, filtros, detalle, creacion/edicion y conexion SQLite. Sin embargo, esta incompleto como flujo real porque aun no se integra con pagos de cuotas, aplicacion de abonos, cancelacion operativa y seguimiento vivo de cuotas.

Estado recomendado: **Conectado parcialmente a base de datos**.

Pendientes:
- Integrar pago de cuotas.
- Definir estados finales de plan: activo, finalizado, cancelado, anulado.
- Conectar saldos con pagos reales.
- Confirmar reglas para vincular cargos financiados.
- Revisar por que la base actual tiene `planes_pago=0` y `cuotas_plan_pago=0`.

### Reportes

No esta funcional. Existe carpeta con archivos base, pero solo como punto de extension. La base tiene `reportes_generados` y vistas utiles, pero no hay generacion real desde UI.

Estado recomendado: **Estructura creada**.

Pendientes:
- Definir reportes indispensables para prototipo.
- Generar reportes desde datos confiables.
- Decidir si se guardan en `reportes_generados` o se generan bajo demanda.
- Esperar a que pagos y morosidad esten cerrados.

### Usuarios

Esta funcional parcialmente. Lista usuarios visibles segun perfil, separa operativo/tecnico, permite restablecer contrasena y desbloquear. No es CRUD completo.

Estado recomendado: **Funcional con pendientes**.

Pendientes:
- Crear usuarios desde UI si el prototipo lo requiere.
- Editar roles/permisos si sera parte del alcance.
- Mantener separacion entre `ADMINISTRADOR` y `SUPERADMINISTRADOR`.

### Configuracion

Esta conectada y guarda datos reales en `configuracion_sistema`. Maneja datos de junta y parametros de cobro. La pestaña de seguridad es principalmente informativa.

Estado recomendado: **Funcional para prototipo**.

Pendientes:
- Definir que parametros son realmente editables.
- Confirmar reglas de mora, multa, corte automatico y pago adelantado.
- Evitar configuraciones visibles que todavia no tengan efecto real.

### Mantenimiento tecnico

Existe y esta protegido para `SUPERADMINISTRADOR`. Lee tablas tecnicas como respaldos y eventos, pero la propia vista avisa que esta en desarrollo.

Estado recomendado: **UI parcial conectada**.

Pendientes:
- Agregar respaldo real.
- Agregar restauracion controlada.
- Agregar revision de logs/eventos.
- Mantenerlo reservado a superadmin.

## 4. Dependencias entre modulos

- Barrios es base para abonados y casas.
- Abonados depende de barrios.
- Casas depende de abonados y barrios.
- Pagos depende de casas, abonados, cargos, metodos de pago, periodos y conceptos de cobro.
- Morosidad depende de cargos, pagos, casas, abonados y configuracion de cobro.
- Planes de pago depende de casas, abonados, cargos pendientes y luego pagos/cuotas.
- Reportes depende de pagos, morosidad, casas, abonados, usuarios y configuracion.
- Dashboard depende de pagos, cargos, casas, abonados y morosidad.
- Usuarios depende de autenticacion, roles, permisos y auditoria.
- Mantenimiento depende de usuarios tecnicos, auditoria, respaldos, eventos y seguridad.

## 5. Riesgos actuales

- Hay modulos visualmente presentes pero funcionalmente vacios: pagos, reportes y morosidad.
- El sistema tiene deuda/cargos en BD, pero no tiene todavia un modulo de pagos que aplique cobros desde el cargo mas antiguo.
- Planes de pago esta adelantado frente a pagos; puede crear estructura de plan, pero no cerrar ciclo de cobro.
- Dashboard puede aparentar mas madurez de la real porque muestra metricas de BD con datos de prueba.
- La relacion deuda, mora, multa, corte y plan de pago todavia necesita reglas finales.
- Usuarios no es CRUD completo; es administracion de acceso limitada.
- La base local contiene datos de prueba y algunos registros manuales; deben tratarse como no productivos.
- `pytest` no esta instalado ni en Python global ni en `.venv`, asi que la suite no se pudo ejecutar sin cambiar dependencias.

## 6. Proximos modulos o frentes de trabajo

Orden recomendado:

1. Cerrar pagos: registro, aplicacion a cargos antiguos, detalle, comprobante basico y anulacion.
2. Cerrar morosidad: consulta por casa/abonado, filtros, deuda vencida, meses pendientes y acciones.
3. Ajustar planes de pago contra pagos reales: pago de cuotas, saldo, estados y cargos vinculados.
4. Consolidar casas/abonados con reglas de deuda, suspension, corte e inactivacion.
5. Crear reportes solo cuando pagos y morosidad ya sean confiables.
6. Completar usuarios si el prototipo exige creacion/edicion de cuentas.
7. Expandir mantenimiento tecnico al final: respaldos, logs y restauracion.

## 7. Plan recomendado por fases

### Fase 1: Cerrar modulos base

Barrios, abonados y casas quedan como base. Revisar reglas de estados, dependencia entre abonado/casa y consistencia de deuda visible.

### Fase 2: Conectar cobro real

Implementar pagos completo: seleccionar casa/abonado, listar cargos pendientes, aplicar pago desde el cargo mas antiguo, registrar comprobante y actualizar saldos.

### Fase 3: Terminar deuda, mora y planes

Crear morosidad como modulo real. Luego conectar planes de pago con cuotas pagables, estados y saldo pendiente.

### Fase 4: Reportes y dashboard confiable

Con pagos y morosidad ya cerrados, generar reportes operativos y ajustar dashboard para que muestre indicadores defendibles.

### Fase 5: Pruebas, seguridad y empaquetado

Ejecutar pruebas, completar dependencias de test, validar UI offscreen, revisar roles/permisos, limpiar datos de prueba y preparar empaquetado.

## 8. Decisiones pendientes

- Estados definitivos de casa: `ACTIVO`, `CORTADO`, `SUSPENDIDO`, `INACTIVO` y sus transiciones permitidas.
- Que significa exactamente mora: meses vencidos, recargo, multa automatica o combinacion.
- Si la multa por mora sera automatica, manual o solo informativa.
- Como se aplica un pago parcial: siempre cargo mas antiguo, seleccion manual o mixto.
- Que pasa al inactivar un abonado con deuda, casa activa o plan pendiente.
- Si planes de pago financian deuda mensual, reconexion, conexion, prima u otros conceptos.
- Si reportes deben guardarse en `reportes_generados` o generarse bajo demanda.
- Que modulos son indispensables para el prototipo de tesis y cuales pueden quedar como en desarrollo.

## Verificacion

- `python -m compileall src tests`: correcto usando el entorno virtual.
- `pytest`: no ejecutado porque `pytest` no esta instalado ni en Python global ni en `.venv`.
