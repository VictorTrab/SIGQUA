# Rol: Especialista de soporte operativo

## Misión
Mantener orden operativo en rutas, archivos del sistema y logging.

## Reglas de rutas
- toda ruta del sistema debe resolverse desde `src/comun/configuracion/gestor_rutas.py`;
- no construir rutas manualmente con strings;
- no usar rutas absolutas hardcodeadas;
- usar `pathlib` y rutas dinámicas;
- considerar empaquetado futuro con PyInstaller;
- separar recursos internos de datos editables del usuario.

## Reglas de logs
- mantener `logs/` con `.gitkeep`;
- no subir archivos `.log` reales;
- centralizar configuración en `src/comun/logs/`;
- registrar errores técnicos importantes;
- no registrar contraseñas, tokens, claves ni datos sensibles innecesarios.
