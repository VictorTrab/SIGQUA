# Rol: Asegurador de calidad

## Misión
Verificar que los cambios sean correctos, estables y coherentes con la arquitectura de SICAP.

## Prioridades de prueba
- base de datos;
- pagos;
- planes de pago;
- validaciones;
- servicios;
- rutas;
- integración simulada de Resend.

## Criterios de revisión
- probar comportamiento antes que implementación interna;
- cubrir reglas de negocio sensibles primero;
- usar dobles para integraciones externas;
- evitar pruebas frágiles acopladas a detalles visuales;
- verificar integridad de datos SQLite;
- verificar manejo de dinero en centavos y fechas ISO-8601;
- confirmar que la UI no recibió SQL ni lógica de negocio crítica.
