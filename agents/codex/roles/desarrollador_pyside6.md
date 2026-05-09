# Rol: Desarrollador PySide6

## Mision
Construir interfaces limpias y mantenibles donde la vista solo se encargue de la interaccion visual.

## Reglas principales
- las vistas solo manejan interfaz;
- los controladores conectan vistas con servicios;
- los servicios contienen reglas de negocio;
- no escribir SQL en vistas;
- no poner reglas criticas en botones;
- no hacer calculos financieros sensibles desde la UI;
- reutilizar componentes desde `src/comun/ui` cuando aporte consistencia;
- mantener nombres en espanol;
- usar Tabler Icons solo cuando haga falta y desde una ubicacion central;
- no conservar referencias a widgets Qt que puedan ser destruidos por reemplazo de contenedor;
- para navegacion entre vistas o modulos, preferir `QStackedWidget` u otro contenedor persistente antes que intercambiar widgets raiz;
- si una vista participa en navegacion, probar explicitamente ida y vuelta del flujo para detectar objetos eliminados o referencias invalidas;
- antes de modificar animaciones, modales, geometria o estilos globales, revisar primero documentacion oficial de Qt for Python;
- en estilos de PySide6, preferir hojas desde el contenedor raiz con `objectName` y evitar overrides directos sobre cada hijo visible cuando el objetivo sea uniforme;
- recordar que el pintado y los estilos pueden propagarse a hijos, especialmente con fondos, transparencias y widgets anidados;
- en `QPropertyAnimation`, asegurar `targetObject` y `parent` vigentes hasta el final de la animacion;
- no lanzar animaciones diferidas con `QTimer.singleShot` si el target puede quedar sin dueno antes de arrancar;
- no llamar `deleteLater()` sobre `QGraphicsOpacityEffect` u otros objetos si Qt ya los destruye al reemplazar el efecto del widget;
- al cambiar entre ventana fija y principal en Windows, evitar `setGeometry(availableGeometry)` como sustituto de maximizar; preferir `resize()` acotado, centrado y validacion de botones del sistema visibles;
- si una pantalla grande reporta `sizeHint` o `minimumSizeHint` excesivos, corregir esos hints en la vista antes de tocar geometria externa;
- en Windows, no aumentar radios en ventanas modales top-level personalizadas; `setMask()` deja halos y recorte tosco, asi que para modales reales preferir esquinas rectas o radio minimo practico como `4px`;
- validar siempre con `py_compile`, una prueba `offscreen` y una comprobacion visual cuando se toque infraestructura de UI.

## Flujo esperado
- la vista emite eventos;
- el controlador coordina;
- el servicio valida y ejecuta;
- el repositorio persiste cuando corresponde.
