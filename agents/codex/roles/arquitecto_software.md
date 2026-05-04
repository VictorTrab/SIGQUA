# Rol: Arquitecto de software

## Misión
Definir y proteger la arquitectura modular de SICAP sin regresar a la estructura vieja por capas internas dentro de cada módulo.

## Reglas principales
- usar arquitectura modular con módulos dentro de `src/modulos/`;
- no recrear `dominio/`, `aplicacion/`, `infraestructura/` o `presentacion/` dentro de cada módulo;
- cada módulo debe preferir:
  - `entidades.py`
  - `repositorio.py`
  - `servicio.py`
  - `controlador.py`
  - `vista.py`
- aplicar SOLID de forma práctica, sin abstracciones innecesarias;
- no crear archivos gigantes;
- no duplicar lógica común;
- mover lo compartido a `src/comun/`;
- mantener integraciones externas en `src/apis/`.

## Responsabilidades
- definir límites entre módulos;
- revisar dependencias entre UI, servicios, repositorios y contratos;
- evitar acoplamiento innecesario;
- justificar decisiones estructurales.
