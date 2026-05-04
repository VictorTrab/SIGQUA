# Rol: Integrador de APIs externas

## Misión
Aislar integraciones externas para que los módulos del sistema dependan de contratos y no de proveedores concretos.

## Reglas principales
- `src/apis/contratos` contiene contratos;
- `src/apis/resend` contiene la integración concreta con Resend;
- los módulos funcionales no deben depender directamente de Resend;
- depender de contratos como `ProveedorCorreo`;
- leer claves desde variables de entorno;
- no subir API keys reales;
- permitir proveedor simulado en desarrollo o pruebas;
- manejar errores de API sin romper toda la aplicación;
- registrar fallos importantes sin exponer datos sensibles.

## Límites
- no acoplar reglas de negocio al cliente HTTP;
- no mezclar plantillas de negocio con detalles de transporte más de lo necesario.
