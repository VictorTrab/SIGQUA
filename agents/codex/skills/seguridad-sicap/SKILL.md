---
name: seguridad-sicap
description: Revisar y reforzar la seguridad practica de SICAP en cambios de autenticacion, SQLite, PySide6, manejo de rutas, reportes, logs, variables de entorno y permisos. Usar cuando Codex vaya a crear, modificar o auditar codigo que toque datos sensibles, consultas SQL, roles, mantenimiento tecnico, exportaciones, archivos locales, configuracion o credenciales del proyecto.
---

# Seguridad SICAP

## Herencia
Asumir siempre las reglas globales de `agents.md`.

## Objetivo
Reducir riesgos reales de SICAP sin meter controles exagerados ni abstracciones innecesarias.

## Cuando usarla
Usar esta skill cuando la tarea implique:
- autenticacion, usuarios, permisos o recuperacion administrativa de acceso;
- consultas SQLite, repositorios o filtros dinamicos;
- formularios PySide6 que capturen o muestren datos sensibles;
- exportaciones, reportes o escritura de archivos;
- logs, errores o trazas con informacion operativa;
- variables de entorno, configuracion sensible o rutas de salida;
- revision de seguridad antes de cerrar una tarea importante.

## Riesgos prioritarios en SICAP
- SQL construido con concatenacion o con columnas dinamicas sin lista blanca.
- logica sensible expuesta en la UI.
- secretos, tokens o correos reales guardados en codigo, logs o repositorio.
- rutas hardcodeadas o escritura fuera de `gestor_rutas.py`.
- permisos de usuario insuficientes o validaciones omitidas.
- reportes o exportaciones que filtren informacion no necesaria.
- reintroducir recuperacion por correo, Resend o codigo muerto de un flujo desactivado.

## Controles obligatorios
- mantener SQL dentro de repositorios;
- mantener reglas de negocio dentro de servicios;
- validar entradas en controlador y volver a validar reglas sensibles en servicio;
- usar parametros en consultas SQLite y lista blanca si un nombre de columna o tabla debe variar;
- no guardar contrasenas en texto plano;
- no exponer tokens, API keys, datos personales o rutas sensibles en logs;
- centralizar rutas en `src/comun/configuracion/gestor_rutas.py`;
- aplicar minimo privilegio en acciones administrativas o de configuracion;
- separar `ADMINISTRADOR` operativo de `SUPERADMINISTRADOR` tecnico;
- dejar pruebas o verificaciones claras cuando se toque autenticacion, permisos o persistencia sensible.

## Procedimiento minimo
1. Leer `agents.md`.
2. Identificar si el cambio toca autenticacion, persistencia, archivos, reportes o permisos.
3. Revisar que cada responsabilidad quede en su capa correcta:
   - vista sin SQL ni reglas criticas;
   - servicio con reglas de negocio;
   - repositorio con acceso SQLite.
4. Buscar entradas no confiables:
   - texto de formularios;
   - filtros;
   - rutas;
   - parametros de reportes.
5. Confirmar controles de seguridad proporcionales:
   - validacion;
   - saneamiento;
   - parametrizacion SQL;
   - permisos;
   - manejo prudente de errores;
   - proteccion de secretos.
6. Verificar que la salida final no deje fuga de datos en UI, logs, archivos o configuracion.

## Checklist por area

### SQLite y repositorios
- usar `?` u otro mecanismo parametrizado soportado por SQLite;
- no interpolar texto del usuario en `WHERE`, `ORDER BY` o nombres de columnas;
- si el orden o filtro es dinamico, usar lista blanca definida en codigo;
- limitar columnas consultadas a lo necesario.

### PySide6 y controladores
- no confiar en validaciones solo visuales;
- mostrar mensajes de error utiles sin revelar detalles internos;
- no pasar datos sensibles completos a tablas, dialogs o tooltips si no hace falta.

### Servicios y reglas de negocio
- revalidar permisos antes de ejecutar acciones sensibles;
- impedir cambios de estado inconsistentes o cobros fuera de reglas;
- preferir fallar de forma segura cuando falte contexto o permiso.

### Archivos, rutas y reportes
- resolver rutas solo desde `gestor_rutas.py`;
- validar nombres de archivo y extensiones esperadas;
- evitar sobrescribir archivos sin una decision explicita;
- no exportar mas datos personales de los necesarios.

### Logs, errores y configuracion
- no registrar contrasenas, tokens, correos completos, DNI completos ni payloads sensibles;
- usar `.env.example` como referencia y nunca subir secretos reales;
- si una excepcion contiene datos sensibles, resumirla antes de mostrarla o guardarla.

### Integraciones futuras
- no asumir la existencia de `src/apis/`;
- si vuelve un proveedor externo, aislarlo con contratos claros;
- no acoplar reglas de negocio a respuestas crudas del proveedor;
- manejar fallos externos sin romper integridad local.

## Criterio de cierre
Un cambio pasa esta skill solo si:
- no mezcla UI, negocio y persistencia;
- no introduce SQL inseguro;
- no expone secretos ni datos sensibles;
- respeta rutas centralizadas;
- mantiene permisos y validaciones acordes al riesgo;
- no deja dependencias muertas del flujo por correo;
- deja el codigo claro y defendible para mantenimiento y tesis.
