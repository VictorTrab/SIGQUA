# Skill: interfaz_visual_premium_pyside6

Fecha de actualizacion: 2026-05-07

## Herencia
- Esta skill asume las reglas globales de `AGENTS.md`.
- Usar junto con la skill de mejora UI basada en Figma MCP.
- Aplicar antes de implementar cualquier pantalla nueva o al refactorizar una existente.
- Pensada para SICAP, PySide6, escritorio administrativo y desarrollo por fases.

## Objetivo
Guiar a Codex para crear interfaces bonitas, agradables, consistentes y sin errores de visualizacion.
La meta no es copiar Figma Make literalmente, sino mejorar el diseno antes de implementarlo.

## Cuando usarla
Usar esta skill cuando:
- se implemente una pantalla nueva;
- se traduzca un diseno de Figma a PySide6;
- existan problemas de espaciado, jerarquia, contraste o estados;
- una interfaz se vea plana, rigida, saturada o poco profesional;
- haya errores al redimensionar o al usar resoluciones distintas.

## Principios obligatorios

### 1. No copiar Figma Make a ciegas
Antes de implementar, analizar:
- que ayuda al flujo;
- que sobra;
- que se repite;
- que rompe la jerarquia visual;
- que puede simplificarse.

Siempre decidir:
- dejar;
- modificar;
- eliminar.

### 2. No usar tamanos fijos como base del diseno
- No disenar para una sola resolucion.
- No fijar geometrias manuales si un layout puede resolverlo.
- Usar layouts, stretch, spacers, sizePolicy, sizeHint y minimumSizeHint.
- La interfaz debe mantenerse usable al maximizar, restaurar o cambiar de resolucion.
- Si una zona puede crecer demasiado, limitarla con un ancho maximo razonable.

### 3. Usar neutros con temperatura, no grises puros como fondo principal
- Evitar fondos `#FFFFFF`, `#000000` y grises puros como base visual general.
- Templar los neutros con un ligero matiz de la marca o del contexto visual.
- Usar superficies vivas, no "grises muertos".
- Mantener el matiz sutil; no convertir el fondo en un color de marca saturado.
- Sombras, bordes suaves y texto secundario deben sentirse parte del mismo sistema cromatico.

### 4. Separar color por roles
Definir siempre colores por funcion:
- fondo base;
- superficie;
- texto principal;
- texto secundario;
- borde;
- acento de marca;
- exito;
- advertencia;
- error;
- estado deshabilitado;
- foco;
- hover;
- pressed;
- selected.

No elegir colores sueltos por intuicion en cada pantalla.
Crear primero una mini escala visual reutilizable.

### 5. Mantener contraste suficiente
- Todo texto normal debe conservar contraste legible.
- No sacrificar legibilidad por estetica.
- Si un color se ve bonito pero reduce lectura, corregirlo.
- El texto secundario debe seguir siendo legible, no "fantasma".

### 6. Hacer visible el estado interactivo
Todo control interactivo debe mostrar claramente:
- reposo;
- hover;
- foco;
- pressed;
- deshabilitado;
- error;
- exito si aplica.

Nunca depender solo del color para comunicar estado.
Acompanar con borde, grosor, fondo, icono o texto de apoyo cuando haga falta.

### 7. Respetar foco de teclado y accesibilidad
- Todo input, boton, combo, tabla y control navegable debe tener foco visible.
- El foco no debe desaparecer por estilos decorativos.
- Si el diseno usa borde muy sutil, reforzar el foco con un anillo o borde mas marcado.
- Validar navegacion por teclado en formularios importantes.

### 8. Construir jerarquia visual real
Antes de implementar cada pantalla, identificar:
- accion principal;
- accion secundaria;
- informacion primaria;
- informacion de apoyo;
- alertas o estados criticos.

La jerarquia se construye con:
- tamano;
- peso tipografico;
- contraste;
- espacio;
- agrupacion;
- elevacion;
- alineacion.

No usar color de marca para todo.
La accion principal debe destacar, pero no contaminar toda la pantalla.

### 9. Usar espacio con sistema
- Mantener una escala consistente de espaciado.
- Preferir multiplos estables.
- Repetir el mismo patron de margenes y padding entre pantallas similares.
- Evitar bloques apretados o con separacion arbitraria.
- El espacio debe ayudar a leer y agrupar.

### 10. Agrupar por intencion, no solo por proximidad
Cada pantalla debe dividirse en bloques claros:
- encabezado;
- filtros;
- resumen;
- formulario;
- tabla;
- acciones;
- mensajes de estado.

Si dos elementos no pertenecen al mismo bloque logico, no deben competir visualmente.

### 11. Limitar ancho de lectura y formularios
- Formularios e inputs no deben expandirse indefinidamente en monitores grandes.
- Usar contenedores internos con ancho maximo razonable.
- Tablas si pueden aprovechar mas ancho, pero con columnas bien priorizadas.
- Los dialogos no deben ser ni claustrofobicos ni gigantes sin necesidad.

### 12. Usar bordes, radios y sombras con moderacion
- Bordes para separar y definir.
- Radios para suavizar.
- Sombras para elevacion real, no para decorar todo.
- No mezclar bordes fuertes con sombras fuertes en todos los elementos.
- Si una tarjeta ya se separa por fondo y espacio, no agregar ruido extra.

### 13. Evitar ruido visual
Eliminar:
- decoraciones que no aportan;
- demasiados chips visibles al mismo tiempo;
- demasiados colores semanticos simultaneos;
- fondos con efectos innecesarios;
- lineas divisorias por costumbre;
- botones con el mismo nivel visual.

### 14. Disenar modo claro y oscuro con intencion
- Modo oscuro no es negro puro.
- Usar profundidad, no vacio.
- Revisar que el sistema mantenga contraste y jerarquia en ambos temas si aplica.
- No invertir colores manualmente sin revisar estados y elevacion.

### 15. Pensar en escritorio real
Como SICAP es una app de escritorio:
- aprovechar ancho para claridad, no para llenar por llenar;
- usar paneles, tablas y formularios con buena distribucion;
- evitar pantallas tipo movil estiradas;
- mantener menus, encabezados y areas de trabajo consistentes;
- priorizar productividad y lectura rapida.

## Procedimiento minimo por pantalla
Antes de codificar, responder en breve:
1. proposito de la pantalla;
2. accion principal;
3. datos mas importantes;
4. errores visuales del diseno fuente;
5. que se deja;
6. que se modifica;
7. que se elimina.

Luego implementar.

## Checklist obligatorio antes de cerrar una pantalla
- Se adapta al redimensionamiento?
- Tiene jerarquia visual clara?
- El contraste es legible?
- Los estados interactivos son visibles?
- El foco de teclado se ve?
- Los formularios no estan demasiado anchos?
- La pantalla evita ruido visual?
- Usa espacio consistente?
- Se siente parte del mismo sistema que el resto?
- Se ve mejor que el diseno fuente y no solo igual?

## Errores que Codex debe corregir automaticamente
- fondos planos con grises puros;
- formularios demasiado anchos;
- botones sin jerarquia;
- inputs sin foco visible;
- uso excesivo del color de marca;
- tablas sin aire visual;
- modales gigantes o muy pequenos;
- chips o filtros repetidos;
- secciones sin agrupacion clara;
- layouts que se rompen al maximizar;
- textos secundarios demasiado debiles;
- ausencia de estados hover, focus o disabled.

## Reglas tecnicas PySide6 para no repetir errores
- cuando una mejora toque modales, popovers, dialogs u overlays, estilizar desde un contenedor raiz comun y no con `setStyleSheet()` aislado sobre cada hijo visible;
- si se necesita cambiar el color base de un modal, verificar que encabezado, cuerpo, pie y bloques internos compartan la misma regla sin introducir bordes o lineas parasitas;
- recordar que `QWidget` propaga pintado y estilos a hijos; por eso un override mal dirigido puede contaminar `QLabel`, `QFrame` o celdas internas;
- para animaciones con `QPropertyAnimation`, asegurar que el target y su parent vivan toda la animacion;
- evitar `QTimer.singleShot(..., animacion.start)` si la animacion puede quedar sin target antes de arrancar;
- no liberar manualmente efectos graficos o animaciones si Qt ya toma propiedad de ellos por el parent o por `setGraphicsEffect()`;
- en Windows, no asumir que maximizar o usar `availableGeometry()` sobre toda la ventana es inocuo; validar que sigan visibles los botones del sistema y que el contenido no exceda el area util;
- si una pantalla se vuelve demasiado grande, corregir primero `sizeHint`, `minimumSizeHint`, anchos fijos y paneles laterales antes de forzar geometria externa.

## Resultado esperado
Interfaces de escritorio limpias, agradables, consistentes y profesionales, con buen uso del color, mejor jerarquia visual, espaciado solido, estados claros y sin errores de visualizacion al cambiar tamano o resolucion.
