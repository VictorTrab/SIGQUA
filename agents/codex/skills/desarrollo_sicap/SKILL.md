# Skill: Desarrollo SICAP

## Cuando usar
Usar esta skill cuando la tarea implique crear, mover o ajustar codigo del proyecto y se necesite un flujo corto de trabajo.

## Flujo
1. Leer `agents.md`.
2. Cargar 1 rol principal segun la naturaleza de la tarea.
3. Confirmar que el cambio respeta la arquitectura modular:
   - `src/comun/`
   - `src/modulos/`
4. Trabajar con archivos simples por modulo:
   - `entidades.py`
   - `repositorio.py`
   - `servicio.py`
   - `controlador.py`
   - `vista.py`
5. Evitar:
   - SQL en vistas;
   - logica de negocio en ventanas;
   - rutas hardcodeadas;
   - acoplamiento directo con proveedores externos;
   - reintroducir `src/apis/` o Resend sin una decision explicita.

## Resultado esperado
El cambio debe quedar claro, corto de mantener y coherente con SOLID practico.
