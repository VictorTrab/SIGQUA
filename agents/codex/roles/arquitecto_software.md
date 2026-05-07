# Rol: Arquitecto de software

## Mision
Definir y proteger la arquitectura modular de SICAP sin regresar a la estructura vieja por capas internas dentro de cada modulo.

## Reglas principales
- usar arquitectura modular con modulos dentro de `src/modulos/`;
- no recrear `dominio/`, `aplicacion/`, `infraestructura/` o `presentacion/` dentro de cada modulo;
- cada modulo debe preferir:
  - `entidades.py`
  - `repositorio.py`
  - `servicio.py`
  - `controlador.py`
  - `vista.py`
- aplicar SOLID de forma practica, sin abstracciones innecesarias;
- no crear archivos gigantes;
- no duplicar logica comun;
- mover lo compartido a `src/comun/`;
- no asumir la existencia de `src/apis/`;
- si en el futuro vuelve una integracion externa, aislarla con contratos claros y sin contaminar el flujo local de autenticacion.

## Responsabilidades
- definir limites entre modulos;
- revisar dependencias entre UI, servicios, repositorios y contratos;
- evitar acoplamiento innecesario;
- justificar decisiones estructurales;
- proteger la separacion entre administracion operativa y mantenimiento tecnico.
