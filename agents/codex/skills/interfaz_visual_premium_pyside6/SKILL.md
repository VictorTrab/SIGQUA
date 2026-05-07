# Skill: interfaz_visual_premium_pyside6

Fecha de actualización: 2026-05-06

## Herencia
- Esta skill asume las reglas globales de `agents.md`.
- Usar junto con la skill de mejora UI basada en Figma MCP.
- Aplicar antes de implementar cualquier pantalla nueva o al refactorizar una existente.
- Pensada para SICAP, PySide6, escritorio administrativo y desarrollo por fases.

## Objetivo
Guiar a Codex para crear interfaces bonitas, agradables, consistentes y sin errores de visualización.
La meta no es copiar Figma Make literalmente, sino mejorar el diseño antes de implementarlo.

## Cuándo usarla
Usar esta skill cuando:
- se implemente una pantalla nueva;
- se traduzca un diseño de Figma a PySide6;
- existan problemas de espaciado, jerarquía, contraste o estados;
- una interfaz se vea plana, rígida, saturada o poco profesional;
- haya errores al redimensionar o al usar resoluciones distintas.

## Principios obligatorios

### 1. No copiar Figma Make a ciegas
Antes de implementar, analizar:
- qué ayuda al flujo;
- qué sobra;
- qué se repite;
- qué rompe la jerarquía visual;
- qué puede simplificarse.

Siempre decidir:
- dejar;
- modificar;
- eliminar.

### 2. No usar tamaños fijos como base del diseño
- No diseñar para una sola resolución.
- No fijar geometrías manuales si un layout puede resolverlo.
- Usar layouts, stretch, spacers, sizePolicy, sizeHint y minimumSizeHint.
- La interfaz debe mantenerse usable al maximizar, restaurar o cambiar de resolución.
- Si una zona puede crecer demasiado, limitarla con un ancho máximo razonable.

### 3. Usar neutros con temperatura, no grises puros como fondo principal
- Evitar fondos `#FFFFFF`, `#000000` y grises puros como base visual general.
- Templar los neutros con un ligero matiz de la marca o del contexto visual.
- Usar superficies vivas, no “grises muertos”.
- Mantener el matiz sutil; no convertir el fondo en un color de marca saturado.
- Sombras, bordes suaves y texto secundario deben sentirse parte del mismo sistema cromático.

### 4. Separar color por roles
Definir siempre colores por función:
- fondo base;
- superficie;
- texto principal;
- texto secundario;
- borde;
- acento de marca;
- éxito;
- advertencia;
- error;
- estado deshabilitado;
- foco;
- hover;
- pressed;
- selected.

No elegir colores sueltos por intuición en cada pantalla.
Crear primero una mini escala visual reutilizable.

### 5. Mantener contraste suficiente
- Todo texto normal debe conservar contraste legible.
- No sacrificar legibilidad por estética.
- Si un color se ve bonito pero reduce lectura, corregirlo.
- El texto secundario debe seguir siendo legible, no “fantasma”.

### 6. Hacer visible el estado interactivo
Todo control interactivo debe mostrar claramente:
- reposo;
- hover;
- foco;
- pressed;
- deshabilitado;
- error;
- éxito si aplica.

Nunca depender solo del color para comunicar estado.
Acompañar con borde, grosor, fondo, icono o texto de apoyo cuando haga falta.

### 7. Respetar foco de teclado y accesibilidad
- Todo input, botón, combo, tabla y control navegable debe tener foco visible.
- El foco no debe desaparecer por estilos decorativos.
- Si el diseño usa borde muy sutil, reforzar el foco con un anillo o borde más marcado.
- Validar navegación por teclado en formularios importantes.

### 8. Construir jerarquía visual real
Antes de implementar cada pantalla, identificar:
- acción principal;
- acción secundaria;
- información primaria;
- información de apoyo;
- alertas o estados críticos.

La jerarquía se construye con:
- tamaño;
- peso tipográfico;
- contraste;
- espacio;
- agrupación;
- elevación;
- alineación.

No usar color de marca para todo.
La acción principal debe destacar, pero no contaminar toda la pantalla.

### 9. Usar espacio con sistema
- Mantener una escala consistente de espaciado.
- Preferir múltiplos estables.
- Repetir el mismo patrón de márgenes y padding entre pantallas similares.
- Evitar bloques apretados o con separación arbitraria.
- El espacio debe ayudar a leer y agrupar.

### 10. Agrupar por intención, no solo por proximidad
Cada pantalla debe dividirse en bloques claros:
- encabezado;
- filtros;
- resumen;
- formulario;
- tabla;
- acciones;
- mensajes de estado.

Si dos elementos no pertenecen al mismo bloque lógico, no deben competir visualmente.

### 11. Limitar ancho de lectura y formularios
- Formularios e inputs no deben expandirse indefinidamente en monitores grandes.
- Usar contenedores internos con ancho máximo razonable.
- Tablas sí pueden aprovechar más ancho, pero con columnas bien priorizadas.
- Los diálogos no deben ser ni claustrofóbicos ni gigantes sin necesidad.

### 12. Usar bordes, radios y sombras con moderación
- Bordes para separar y definir.
- Radios para suavizar.
- Sombras para elevación real, no para decorar todo.
- No mezclar bordes fuertes con sombras fuertes en todos los elementos.
- Si una tarjeta ya se separa por fondo y espacio, no agregar ruido extra.

### 13. Evitar ruido visual
Eliminar:
- decoraciones que no aportan;
- demasiados chips visibles al mismo tiempo;
- demasiados colores semánticos simultáneos;
- fondos con efectos innecesarios;
- líneas divisorias por costumbre;
- botones con el mismo nivel visual.

### 14. Diseñar modo claro y oscuro con intención
- Modo oscuro no es negro puro.
- Usar profundidad, no vacío.
- Revisar que el sistema mantenga contraste y jerarquía en ambos temas si aplica.
- No invertir colores manualmente sin revisar estados y elevación.

### 15. Pensar en escritorio real
Como SICAP es una app de escritorio:
- aprovechar ancho para claridad, no para llenar por llenar;
- usar paneles, tablas y formularios con buena distribución;
- evitar pantallas tipo móvil estiradas;
- mantener menús, encabezados y áreas de trabajo consistentes;
- priorizar productividad y lectura rápida.

## Procedimiento mínimo por pantalla
Antes de codificar, responder en breve:
1. propósito de la pantalla;
2. acción principal;
3. datos más importantes;
4. errores visuales del diseño fuente;
5. qué se deja;
6. qué se modifica;
7. qué se elimina.

Luego implementar.

## Checklist obligatorio antes de cerrar una pantalla
- ¿Se adapta al redimensionamiento?
- ¿Tiene jerarquía visual clara?
- ¿El contraste es legible?
- ¿Los estados interactivos son visibles?
- ¿El foco de teclado se ve?
- ¿Los formularios no están demasiado anchos?
- ¿La pantalla evita ruido visual?
- ¿Usa espacio consistente?
- ¿Se siente parte del mismo sistema que el resto?
- ¿Se ve mejor que el diseño fuente y no solo igual?

## Errores que Codex debe corregir automáticamente
- fondos planos con grises puros;
- formularios demasiado anchos;
- botones sin jerarquía;
- inputs sin foco visible;
- uso excesivo del color de marca;
- tablas sin aire visual;
- modales gigantes o muy pequeños;
- chips o filtros repetidos;
- secciones sin agrupación clara;
- layouts que se rompen al maximizar;
- textos secundarios demasiado débiles;
- ausencia de estados hover, focus o disabled.

## Resultado esperado
Interfaces de escritorio limpias, agradables, consistentes y profesionales, con buen uso del color, mejor jerarquía visual, espaciado sólido, estados claros y sin errores de visualización al cambiar tamaño o resolución.
