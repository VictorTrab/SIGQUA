# Auditoria de paleta UI SIGQUA

Fecha: 2026-05-29

## Resumen ejecutivo

SIGQUA ya tiene una paleta central en `src/comun/ui/temas.py`, pero la implementacion visual todavia mezcla tokens semanticos con colores hardcodeados en vistas PySide6. La paleta propuesta por el usuario funciona bien como base azul institucional para fondos y texto claro, pero es demasiado monocromatica para resolver sola jerarquia, tablas, estados, botones destructivos, advertencias y graficas.

Recomendacion: no aplicar la paleta azul de forma literal. Usarla como base de marca y migrar a un sistema semantico con acentos funcionales: cian para accion principal, verde para exito, ambar para advertencia, rojo para error/corte y violeta o azul intenso solo para informacion secundaria o graficas.

Capturas offscreen generadas como evidencia no trackeada:

`C:\Users\User\Documents\SIGQUA\.codex-temp\auditoria_paleta_ui\`

## Referencias revisadas

- `qt-material`: themes Qt/PySide basados en variables y colores de rol.
- `QDarkStyleSheet`: framework de tema oscuro/claro para aplicaciones Qt.
- Primer/GitHub color usage: tokens semanticos por rol, no por valor visual.
- Admin dashboard dark mode references: contraste fuerte, superficies diferenciadas, acentos limitados y estados consistentes.

Criterio extraido: una UI administrativa oscura necesita separar fondo, superficie, borde, texto, foco, seleccion y estados. No basta una escala de un solo color.

## Estado actual

### Paleta central

Archivo central:

- `src/comun/ui/temas.py`

La paleta actual define tokens utiles para fondos, tablas, botones, modales, graficas e iconos. Esto es una buena base. El problema es que muchos modulos siguen declarando colores locales en `setStyleSheet()`, constantes o argumentos directos de iconos.

### Colores hardcodeados

Inspeccion estatica sobre `src/modulos` y `src/comun/ui`:

- Total de ocurrencias `#RRGGBB` o `rgba(...)`: 495.
- Archivos con mayor concentracion:
  - `src/comun/ui/temas.py`: 136 ocurrencias, esperable por ser paleta central.
  - `src/modulos/principal/vista.py`: 56.
  - `src/modulos/casas/vista.py`: 53.
  - `src/modulos/barrios/vista.py`: 46.
  - `src/modulos/abonados/vista.py`: 45.
  - `src/modulos/autenticacion/vista.py`: 38.
  - `src/comun/ui/componentes.py`: 32.
  - `src/modulos/historial_pagos/vista.py`: 25.
  - `src/modulos/usuarios/vista.py`: 23.

Conclusiones:

- La paleta esta centralizada, pero no gobierna toda la UI.
- Hay duplicacion entre abonados, barrios y casas: tarjetas, chips, tablas, badges y mensajes usan estilos casi equivalentes con colores escritos localmente.
- `principal/vista.py` mantiene acentos y fondos propios, incluido un `COLOR_FONDO_PRINCIPAL = "#2c2966"` que rompe la familia azul institucional.
- `configuracion/vista.py` contiene una zona clara con `#E4EACC` y texto `#111111`; puede ser intencional para previsualizacion, pero debe quedar aislada como excepcion documentada.

## Contraste y legibilidad

### Medicion de contraste

Resultados representativos:

| Par | Contraste | Resultado |
| --- | ---: | --- |
| Actual `#EAF2F8` sobre `#0A1728` | 15.91 | AA normal |
| Actual `#C9DBE9` sobre `#1D364E` | 8.75 | AA normal |
| Actual `#8FAFC7` sobre `#243F5A` | 4.72 | AA normal |
| Actual boton primario `#0A1728` sobre `#C9DBE9` | 12.69 | AA normal |
| Actual `#4E6A9C` sobre `#1D364E` | 2.29 | Falla |
| Propuesta `#F4FAFF` sobre `#001D39` | 16.17 | AA normal |
| Propuesta `#BDD8E9` sobre `#0A4174` | 7.01 | AA normal |
| Propuesta `#8FB7CF` sobre `#0A4174` | 4.87 | AA normal |
| Propuesta `#4E8EA2` sobre `#49769F` | 1.31 | Falla |
| Propuesta `#7BBDE8` sobre `#0A4174` | 5.09 | AA normal |

Diagnostico:

- La paleta propuesta sirve muy bien para fondo oscuro y texto claro.
- Los tonos intermedios son demasiado cercanos entre si. No deben usarse como texto sobre superficie, filas alternas entre si, bordes importantes o estados.
- La paleta actual ya cumple contraste en texto principal, texto secundario, tabla y boton primario.
- El mayor riesgo esta en graficas, iconos, hover, badges y estados donde se usan tonos de acento con contraste menor.

### Capturas offscreen

Vistas instanciadas y capturadas:

- Abonados.
- Barrios.
- Casas.
- Morosidad.
- Pagos.
- Planes de pago.
- Reportes.
- Usuarios.
- Historial de pagos.
- Configuracion.

Muestreo dominante de color:

- La mayoria de pantallas esta dominada por `#1D364E`, `#243F5A`, `#102A40` y `#0A1728`.
- La interfaz se percibe consistente pero plana: muchas superficies comparten valores muy cercanos.
- En listas vacias o vistas sin datos, los bloques se ven demasiado similares entre contenedor, tabla y tarjeta.
- Las acciones por icono usan varios acentos locales (`#4fa3ff`, `#8de8c7`, `#f7cc7a`, `#ff625c`, `#b48bff`) sin token semantico comun.

## Revision por areas

### Tablas

Pantallas revisadas: abonados, barrios, casas, pagos, morosidad, planes, reportes, usuarios, historial.

Hallazgos:

- Encabezados y filas tienen buena legibilidad base.
- Las filas alternas y contenedores cercanos usan diferencias sutiles; en pantallas densas puede sentirse una sola masa azul.
- La seleccion y hover dependen de `rgba(78, 106, 156, ...)`, con baja separacion sobre algunas superficies.
- Acciones por fila usan iconos claros y tooltips, pero los colores de icono no estan semantizados.

Recomendacion:

- Mantener texto claro actual.
- Aumentar diferencia entre `fondo_tabla_cuerpo`, `fondo_tabla_fila`, `fondo_tabla_fila_alterna` y `fondo_tabla_header`.
- Crear tokens de icono por accion: `icono_ver`, `icono_editar`, `icono_cobrar`, `icono_historial`, `icono_peligro`, `icono_aviso`.

### Tarjetas y KPIs

Hallazgos:

- Valores principales se leen bien.
- Iconos por tarjeta usan colores locales repetidos.
- Algunos colores de estado mezclan exito y marca: `#8de8c7`, `#d9fff5`, `#35E6A8` aparecen con roles parecidos.

Recomendacion:

- Definir una sola escala de estado:
  - exito: verde.
  - advertencia: ambar.
  - error/corte: rojo.
  - informacion: cian.
  - neutro: azul grisaceo.

### Botones y chips

Hallazgos:

- El boton primario actual tiene contraste fuerte.
- Chips de filtro son consistentes en abonados, barrios y casas, pero estan definidos repetidamente.
- Hover y activo usan variaciones cercanas, suficientes para usuarios con buena vision pero mejorables.

Recomendacion:

- Centralizar estilos de chips y botones operativos en componentes o helpers compartidos.
- Usar borde/foco visible, no solo cambio de fondo.

### Modales

Modales revisados por codigo:

- Formularios y detalles de abonados, barrios, casas, usuarios, morosidad, planes, historial.
- Modales base en `src/comun/ui/componentes.py`.

Hallazgos:

- `DialogoBaseSigqua` da una base comun y reduce riesgos de inconsistencias.
- Algunos modales grandes agrupan secciones, pero no todos garantizan footer fijo si el contenido crece.
- La regla de Windows sobre radios y top-level modals ya esta contemplada por reglas del proyecto, pero conviene no aumentar radios.
- El uso de `QComboBox` es correcto para listas cortas de estados/metodos; es problematico para registros que pueden crecer.

### QComboBox en listas grandes

Riesgo alto:

- `DialogoFormularioCasa`: `_combo_abonado` y `_combo_barrio`.
- `DialogoCambioDuenoCasa`: `_combo_abonado`.
- `DialogoFormularioPlanPago`: `_combo_casa`.
- `DialogoFormularioAbonado`: `_combo_barrio`, si barrios crece mucho.

Riesgo bajo o aceptable:

- Estados, motivos, roles, metodos de pago, duracion de sesion, ancho termico, reimpresion.
- Filtros de reportes, siempre que el catalogo se mantenga acotado.

Recomendacion:

- Reemplazar primero combos de abonados y casas por buscador con resultados limitados.
- Mantener combos para valores enumerados.

## Paleta propuesta

### Opcion A: ajuste minimo sobre paleta azul del usuario

Uso recomendado de los hex entregados:

```python
PALETA_SIGQUA_AJUSTADA = {
    "fondo_app": "#001D39",
    "fondo_sidebar": "#001D39",
    "fondo_panel": "#0A4174",
    "fondo_superficie": "#0B355F",
    "fondo_superficie_suave": "#123F66",
    "fondo_tabla_header": "#0A4174",
    "fondo_tabla_fila": "#062C52",
    "fondo_tabla_fila_alterna": "#0D365D",
    "borde_suave": "#49769F",
    "borde_activo": "#7BBDE8",
    "texto_principal": "#F4FAFF",
    "texto_secundario": "#BDD8E9",
    "texto_muted": "#A9C8DA",
    "acento_principal": "#7BBDE8",
    "acento_secundario": "#6EA2B3",
    "estado_exito": "#35E6A8",
    "estado_advertencia": "#F2B84B",
    "estado_error": "#EF6B6B",
    "estado_info": "#7BBDE8",
}
```

Observacion: esta opcion conserva identidad azul, pero ya introduce verde, ambar y rojo para estados.

### Opcion B: alternativa profesional recomendada

```python
PALETA_SIGQUA_PROFESIONAL = {
    "fondo_app": "#071A2D",
    "fondo_sidebar": "#061525",
    "fondo_panel": "#0D2A45",
    "fondo_superficie": "#123553",
    "fondo_superficie_suave": "#183F5F",
    "fondo_input": "#082238",
    "fondo_tabla_header": "#0A3152",
    "fondo_tabla_fila": "#0E2B46",
    "fondo_tabla_fila_alterna": "#123655",
    "borde_suave": "rgba(126, 167, 196, 0.34)",
    "borde_activo": "#75C7F0",
    "texto_principal": "#F4FAFF",
    "texto_secundario": "#C5DDEE",
    "texto_muted": "#92B6CC",
    "acento_principal": "#75C7F0",
    "acento_hover": "#49A9DC",
    "estado_exito": "#37D399",
    "estado_advertencia": "#F5B84B",
    "estado_error": "#F27474",
    "estado_info": "#75C7F0",
    "estado_neutro": "#8EA8BC",
}
```

Esta alternativa mantiene el caracter azul de SIGQUA, pero mejora separacion de superficies y evita que todo dependa de una escala monocromatica.

## Orden recomendado de cambios

1. Crear o depurar tokens semanticos en `src/comun/ui/temas.py`.
2. Reemplazar colores locales repetidos en `src/comun/ui/componentes.py` y componentes de botones/chips.
3. Normalizar tablas y chips en abonados, barrios, casas, usuarios e historial.
4. Normalizar iconos de accion por rol semantico.
5. Ajustar dashboard/principal para eliminar colores que no pertenecen a la familia SIGQUA.
6. Revisar modales grandes y asegurar footer estable.
7. Reemplazar combos de abonado/casa por buscadores con resultados limitados.
8. Validar capturas offscreen y pruebas de instanciacion.
9. Documentar la composicion visual final en la boveda externa si se implementan cambios de UI.

## Criterios de aceptacion para una futura implementacion

- `src/comun/ui/temas.py` concentra la paleta real.
- No quedan colores hardcodeados repetidos en vistas salvo excepciones justificadas.
- Texto principal, secundario y muted mantienen contraste AA en fondos usados.
- Tablas distinguen encabezado, fila, fila alterna, hover y seleccion.
- Estados no dependen solo de color: mantienen texto, icono o etiqueta.
- Combos de listas grandes se reemplazan por buscadores.
- Las capturas offscreen no muestran fondos planos indistinguibles ni botones de bajo contraste.

## Decision recomendada

Usar la opcion B como norte de implementacion. La paleta original debe conservarse como inspiracion de marca, pero no como sistema completo. Su escala intermedia tiene contrastes demasiado bajos entre tonos adyacentes para una aplicacion administrativa densa.

## Implementacion aplicada

Fecha: 2026-05-29.

Se implemento la opcion B como tema predeterminado en `src/comun/ui/temas.py`, manteniendo la API de tokens existente y agregando aliases semanticos para estados, bordes, fondos informativos e iconos funcionales. La paleta queda centrada en fondos azul profundo con acentos diferenciados:

- Informacion y accion primaria: `#75C7F0`.
- Exito: `#37D399`.
- Advertencia/edicion: `#F5B84B`.
- Error/peligro: `#F27474`.
- Neutro/muted: `#8EA8BC` y `#92B6CC`.

Cambios principales:

- `src/comun/ui/componentes.py`: botones contextuales, botones operativos, modales y variantes de accion usan tokens semanticos en lugar de colores antiguos sueltos.
- `src/modulos/autenticacion/vista.py`: login alineado a la nueva base, foco de campos, botones, mensajes de exito/error y vidrio de tarjeta.
- `src/modulos/principal/vista.py`: shell principal, dashboard, graficas, marca y previews de modales alineados a la nueva paleta.
- Vistas operativas: abonados, barrios, casas, pagos, historial, planes, usuarios, reportes, morosidad y configuracion quedaron sin referencias directas a la paleta anterior auditada.
- `src/modulos/configuracion/servicio.py` y `database/migrations/025_paleta_ui_opcion_b_laboratorio_visual.sql`: defaults del laboratorio visual actualizados sin sobrescribir valores personalizados, solo cuando conservan los defaults antiguos.
- Pruebas actualizadas para reflejar los nuevos defaults.

Validacion ejecutada:

- `rg` confirmo que no quedan referencias directas a `#0A1728`, `#1D364E`, `#E4EACC`, `#C9DBE9`, `#8FAFC7`, `#4E6A9C`, `#22d3a6`, `#2c2966` ni sus `rgba` antiguos en `src` y `tests`.
- `python -m compileall src` finalizo correctamente.
- `.venv\Scripts\python.exe -m unittest discover -s tests` finalizo con 140 pruebas OK.
- Capturas offscreen generadas en `.codex-temp/auditoria_paleta_ui_post/` para login, principal, abonados, barrios, casas, pagos, morosidad, reportes y usuarios.
- Chequeo de dimensiones y muestras de color confirmo capturas no vacias de `1280x820`.

Excepcion mantenida:

El laboratorio visual de configuracion sigue permitiendo previsualizar fondos y modales porque su objetivo es precisamente probar configuracion visual. Sus valores predeterminados ya fueron alineados con la opcion B.
