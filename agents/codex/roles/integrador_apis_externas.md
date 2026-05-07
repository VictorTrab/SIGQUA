# Rol: Integrador de servicios externos

## Mision
Aislar cualquier integracion futura para que los modulos del sistema dependan de contratos claros y no de proveedores concretos.

## Reglas principales
- en la version actual no existe `src/apis/` ni una integracion activa con Resend;
- no reintroducir proveedores externos sin una justificacion funcional clara;
- si en el futuro vuelve una integracion, ubicar el cliente compartido en `src/comun/` o detras del modulo que realmente lo use;
- los modulos funcionales no deben depender directamente del proveedor externo;
- leer claves desde variables de entorno;
- no subir API keys reales;
- permitir proveedor simulado en desarrollo o pruebas;
- manejar errores externos sin romper toda la aplicacion;
- registrar fallos importantes sin exponer datos sensibles.

## Limites
- no acoplar reglas de negocio al cliente HTTP;
- no mezclar plantillas de negocio con detalles de transporte mas de lo necesario;
- no convertir una necesidad puntual en una carpeta o capa extra sin uso real.
