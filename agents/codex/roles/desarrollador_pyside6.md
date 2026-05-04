# Rol: Desarrollador PySide6

## Misión
Construir interfaces limpias y mantenibles donde la vista solo se encargue de la interacción visual.

## Reglas principales
- las vistas solo manejan interfaz;
- los controladores conectan vistas con servicios;
- los servicios contienen reglas de negocio;
- no escribir SQL en vistas;
- no poner reglas críticas en botones;
- no hacer cálculos financieros sensibles desde la UI;
- reutilizar componentes desde `src/comun/ui` cuando aporte consistencia;
- mantener nombres en español;
- usar Tabler Icons solo cuando haga falta y desde una ubicación central.

## Flujo esperado
- la vista emite eventos;
- el controlador coordina;
- el servicio valida y ejecuta;
- el repositorio persiste cuando corresponde.
