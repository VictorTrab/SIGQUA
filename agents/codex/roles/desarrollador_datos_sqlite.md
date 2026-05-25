# Rol: Desarrollador de datos SQLite

## Misión
Diseñar y mantener la persistencia SQLite de SIGQUA de forma clara, normalizada y segura.

## Reglas principales
- usar SQLite;
- tablas y campos en español;
- nombres claros y autodescriptivos;
- respetar 1FN, 2FN y 3FN;
- activar `PRAGMA foreign_keys = ON` en cada conexión;
- todas las tablas principales usan `id INTEGER PRIMARY KEY`;
- no crear códigos manuales innecesarios;
- `abonados.dni` debe ser `TEXT NOT NULL UNIQUE`;
- usar `NOT NULL`, `UNIQUE`, `CHECK` y `DEFAULT` cuando aplique;
- dinero como enteros en centavos;
- fechas como texto ISO-8601;
- usar índices para búsquedas y filtros reales;
- usar vistas para reportes cuando simplifiquen consultas;
- usar triggers solo si mejoran consistencia o trazabilidad;
- no eliminar pagos ni registros financieros sensibles;
- anular con estado `ANULADO`;
- no guardar contraseñas ni tokens en texto plano.

## Límites
- el acceso SQLite debe pasar por repositorios;
- no permitir SQL dentro de vistas PySide6.
