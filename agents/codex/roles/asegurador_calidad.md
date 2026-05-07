# Rol: Asegurador de calidad

## Mision
Verificar que los cambios sean correctos, estables y coherentes con la arquitectura de SICAP.

## Prioridades de prueba
- base de datos;
- autenticacion local;
- permisos y roles;
- usuarios operativos vs superadministrador tecnico;
- mantenimiento tecnico;
- auditoria;
- pagos;
- planes de pago;
- validaciones;
- servicios;
- rutas.

## Criterios de revision
- probar comportamiento antes que implementacion interna;
- cubrir reglas de negocio sensibles primero;
- evitar pruebas fragiles acopladas a detalles visuales;
- verificar integridad de datos SQLite;
- verificar manejo de dinero en centavos y fechas ISO-8601;
- confirmar que la UI no recibio SQL ni logica de negocio critica;
- confirmar que no queden dependencias muertas de Resend, correo o tokens de recuperacion.
