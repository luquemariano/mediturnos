# MediTurnos API

API para la gestión de turnos médicos, profesionales, pacientes, prestaciones, disponibilidades y pagos online mediante Mercado Pago Checkout Pro.

El proyecto fue desarrollado con FastAPI, PostgreSQL y Docker, aplicando una arquitectura organizada por capas y reglas de negocio orientadas a un sistema real de atención médica.

## Funcionalidades

- Gestión de especialidades médicas.
- Gestión de profesionales.
- Relación entre profesionales y especialidades.
- Duración personalizada de turnos por profesional y especialidad.
- Gestión de pacientes.
- Gestión de prestaciones médicas.
- Configuración de disponibilidad semanal.
- Generación dinámica de horarios libres.
- Reserva, cancelación y reprogramación de turnos.
- Prevención de reservas superpuestas.
- Integración con Mercado Pago Checkout Pro.
- Creación de preferencias de pago.
- Procesamiento de Webhooks firmados.
- Confirmación automática de turnos cuando el pago es aprobado.
- Consulta del estado de pago de cada turno.
- Migraciones de base de datos con Alembic.

## Tecnologías

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- PostgreSQL
- Docker
- Docker Compose
- Mercado Pago SDK
- Pytest
- Ngrok para pruebas locales de Webhooks

## Arquitectura

El proyecto está organizado en capas:

```text
app/
├── core/
├── database/
├── models/
├── repositories/
├── routers/
├── schemas/
├── services/
└── main.py