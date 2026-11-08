# Pruebas de aceptación — Mesa de Ayuda Inteligente

## Objetivo

Verificar que el prototipo permite registrar, clasificar,
atender y resolver solicitudes mediante Angular y FastAPI.

## Componentes evaluados

- Frontend: Angular 22.
- Backend: FastAPI.
- Persistencia: SQLite mediante SQLModel.
- Sistemas de demostración: MAIA, EvaluIA y Moodle.

## Escenarios de aceptación

| Caso | Escenario | Resultado esperado |
|---|---|---|
| 1 | Solución automática aceptada | AUTO -> PENDIENTE_CONFIRMACION -> RESUELTO |
| 2 | Solución automática rechazada | AUTO -> FUNCIONAL -> EN_ATENCION -> RESUELTO |
| 3 | Atención funcional directa | FUNCIONAL -> EN_ATENCION -> RESUELTO |
| 4 | Atención técnica directa | TÉCNICO -> EN_ATENCION -> RESUELTO |
| 5 | Operaciones inválidas | Respuestas HTTP 409, 422 y 404 |

## Resultados de las pruebas automatizadas

Ejecución local:

- Aceptación FastAPI: 5 pruebas aprobadas.
- Backend completo: 39 pruebas aprobadas.
- Angular: 7 pruebas aprobadas.
- Compilación Angular de producción: exitosa.

## Comprobación manual

Se recorrieron y reportaron como aprobados los cuatro
escenarios funcionales desde la interfaz.

El escenario automático debe demostrarse utilizando
una consulta reconocida por el clasificador, por ejemplo:

Sistema: MAIA
Asunto: ¿Dónde encuentro mis actividades?
Descripción: Quiero consultar las actividades del curso.

El nombre asignado a un ticket no implica que haya sido
clasificado como AUTO.

## Reproducción de pruebas

Desde backend:

    uv run --locked python -m pytest -q

Desde frontend:

    npm test -- --watch=false
    npm run build

## Limitaciones conocidas

- El prototipo no dispone de autenticación ni autorización
  real para solicitantes y personal de soporte.
- La clasificación usa reglas para escenarios definidos,
  no un modelo general de inteligencia artificial.
- La sugerencia automática cubre un caso concreto de MAIA.
- Los responsables funcionales y técnicos representan
  equipos de demostración.
- No debe exponerse la API públicamente sin controles
  adicionales de acceso.

## Conclusión

Los escenarios contemplados por las pruebas automatizadas
funcionan correctamente y sus cambios persisten en SQLite.

El prototipo cumple el flujo funcional implementado.
Su utilización en producción requiere resolver las
limitaciones indicadas anteriormente.
