# F11 · Centro de Ayuda — Auditoría funcional

## 1. Objetivo

Este documento es el contrato funcional de F11.1–F11.11. Describe sólo capacidades demostrables en el estado auditado del repositorio; distingue frontend, backend, configuración y operación productiva. F11.0 no implementa `/ayuda`, screenshots, PDF, email de bienvenida ni cambios de runtime.

## 2. Estado Git auditado

- Base actualizada: `main`, `origin/main` actualizado con `git fetch --prune` y `git pull --ff-only`.
- HEAD auditado: `f254641` (`Merge pull request #18 from luquemariano/feature/f10-week-readability`).
- Fecha de auditoría: 2026-08-30 (America/Argentina/Buenos_Aires).
- Rama de trabajo: `feature/f11-help-audit`.
- El árbol ya tenía archivos no trackeados ajenos a F11 (`scripts/` y `tests/test_debug_preapproval_payload.py`); se preservan y no forman parte de esta fase.
- Alcance: lectura de frontend, backend, tests, migraciones, configuración y documentación canónica. No se ejecutaron migraciones, seed ni servicios externos.

## 3. Convención de estados

- **IMPLEMENTADO Y EXPUESTO:** existe código y el profesional dispone de una UI usable.
- **IMPLEMENTADO SIN UI COMPLETA:** existe backend/tests, pero no se encontró flujo profesional completo en frontend.
- **CONFIGURADO:** declarado en configuración, sin prueba operativa.
- **NO VERIFICADO EN PRODUCCIÓN:** hay código/configuración/tests, pero no evidencia de ejecución real.
- **NO INCORPORADO:** no existe capacidad usable en el estado auditado.
- **BLOQUEADO PARA DOCUMENTACIÓN:** una decisión de producto, precio o comportamiento debe resolverse antes de publicar el artículo.

## 4. Mapa funcional del Centro de Ayuda

| Área | Funcionalidad | Estado | Documentar | Evidencia |
|---|---|---|---|---|
| Acceso | Registro, login, logout, restauración de sesión | IMPLEMENTADO Y EXPUESTO | Sí | `frontend/src/App.tsx`, `authService.ts`, tests de auth |
| Acceso | Recuperación y cambio de contraseña | IMPLEMENTADO Y EXPUESTO | Sí | `/forgot-password`, `/reset-password`, `app/services/auth_service.py` |
| Primeros pasos | Onboarding perfil → prestaciones → disponibilidad → listo | IMPLEMENTADO Y EXPUESTO | Sí | `OnboardingProfesional.tsx`, `onboarding_service.py` |
| Perfil | Consulta/edición de datos profesionales y duración | IMPLEMENTADO Y EXPUESTO | Sí | `PerfilPropio.tsx`, `profesional_service.py` |
| Prestaciones | Alta, edición, activar/desactivar, especialidad, duración, precio y modalidad | IMPLEMENTADO Y EXPUESTO | Sí | `MisPrestaciones.tsx`, `ModalPrestacion.tsx` |
| Disponibilidad | Semana habitual y excepciones | IMPLEMENTADO Y EXPUESTO | Sí | `MiDisponibilidad.tsx`, `ExcepcionesDisponibilidad.tsx` |
| Agenda | Día, semana, mes, Hoy, navegación, estados y acciones | IMPLEMENTADO Y EXPUESTO | Sí | `AgendaPropia.tsx`, `AgendaSemana.tsx`, `AgendaMes.tsx`, F10 tests |
| Turnos | Crear, reprogramar, cancelar, finalizar y ausente | IMPLEMENTADO Y EXPUESTO | Sí | `NuevoTurnoProfesional.tsx`, `GestionTurnoProfesional.tsx` |
| Pacientes | Listar, buscar, alta, editar, desactivar, historial | IMPLEMENTADO Y EXPUESTO | Sí | `Pacientes.tsx`, `pacienteService.ts` |
| Historia clínica | Resumen clínico y evoluciones | IMPLEMENTADO Y EXPUESTO | Sí | `PatientDocuments.tsx`, componentes de paciente, servicios/tests |
| Documentos | Adjuntar, ver/descargar y eliminar | IMPLEMENTADO Y EXPUESTO | Sí, con límites | MIME permitido y máximo 10 MB en `validation.py` |
| Estudios | Solicitud, enlace tokenizado, carga pública, revisión y devolución | IMPLEMENTADO Y EXPUESTO | Sí, prioritario | `PatientStudyRequests.tsx`, `StudyUploadAccess.tsx`, routers/services/tests |
| Recordatorios | Worker de email, confirmación/cancelación pública | CONFIGURADO / NO VERIFICADO EN PRODUCCIÓN | Sí, con cautela | `render.yaml`, `appointment_reminder_service.py` |
| Suscripción | Trial, planes, tarjeta Mercado Pago, retorno y sincronización | IMPLEMENTADO Y EXPUESTO / BLOQUEADO PARA DOCUMENTACIÓN | Sí, después de resolver plan | `ActivarSuscripcion.tsx`, servicios/tests |
| Ayuda | Centro web, renderer Markdown, buscador, PDF | NO INCORPORADO | No en F11.0 | No hay implementación |

## 5. Primeros pasos

El registro profesional solicita nombre, apellido, email, contraseña, teléfono opcional, matrícula y especialidad. Tras registrarse se inicia sesión y el onboarding conserva el paso actual. El orden confirmado es: perfil, prestaciones, disponibilidad y pantalla “Tu cuenta está lista”. El paso de prestaciones puede continuar sin cargar servicios; la disponibilidad puede configurarse después según el estado. El cierre exige pasos previos completos. La ayuda debe enseñar dónde volver a cada módulo desde el panel.

## 6. Perfil profesional

La UI permite consultar y editar nombre, apellido, teléfono, matrícula, especialidad y duración del turno según los controles existentes. La contraseña se gestiona por recuperación/cambio de contraseña, no como promesa de un editor dentro del perfil. El plan y el estado de suscripción se consultan en la pantalla específica de suscripción. No documentar campos de edición no visibles ni asumir que matrícula/especialidad puedan modificarse sin sus validaciones.

## 7. Prestaciones

El profesional puede crear y editar nombre, descripción, duración (10–240 minutos en onboarding), precio, modalidad y estado activo. Puede desactivar y reactivar desde “Mis prestaciones”. Una prestación inactiva deja de ser una opción normal para nuevos turnos; los turnos ya creados conservan su referencia y deben explicarse como históricos. La disponibilidad de horarios se calcula con prestación, duración, agenda y excepciones.

## 8. Disponibilidad

La semana habitual admite días y una o más franjas por día; las operaciones visibles son agregar, editar y eliminar, con validaciones de rango, orden y solapamiento. Las excepciones distinguen cierre de fecha, reapertura, horario extraordinario, vacaciones/rango de vacaciones y feriado/día no laborable, con motivo u origen cuando corresponde. Las excepciones afectan la generación de horarios futuros; no borran turnos previamente creados. Los turnos afectados deben revisarse y las reglas exactas de conflicto no deben prometerse más allá de lo cubierto por servicios/tests.

## 9. Agenda

F10 confirma vistas Día, Semana y Mes, navegación temporal y botón Hoy. Semana muestra solapamientos y legibilidad mejorada; Mes muestra cantidad de turnos y excepciones. El profesional puede abrir un turno, crear, reprogramar, cancelar, finalizar o marcar ausente según su estado. No se encontró un botón manual de confirmación profesional: “Confirmar turno” es el envío del formulario de creación; la confirmación pública pertenece al enlace del recordatorio.

## 10. Turnos

Crear turno requiere paciente, prestación, fecha y horario libre. Reprogramar vuelve a consultar disponibilidad y puede fallar si el horario dejó de estar disponible. Las acciones profesionales son cancelar, finalizar y marcar ausente, sujetas a estado y ownership. Los estados observados incluyen `reservado`, `confirmado`, `cancelado`, `finalizado` y `ausente`. La cancelación de pagos clínicos tiene lógica separada de la suscripción SaaS: no documentar reembolsos o devoluciones automáticas sin evidencia específica del flujo.

## 11. Pacientes

El listado profesional permite búsqueda por texto (`q`), alta, edición y desactivación. La ficha reúne datos personales, historial de turnos, resumen clínico, evoluciones, documentos, solicitudes de estudios y notificaciones donde correspondan. La búsqueda y el acceso están limitados a pacientes vinculados al profesional; no es un buscador público.

## 12. Historia clínica

El resumen clínico es editable y contiene antecedentes, alergias, medicación habitual, condiciones relevantes y observaciones. Las evoluciones son entradas fechadas por profesional, se listan en orden del backend y se crean como nuevas entradas; el producto debe explicarlas como registro cronológico y no como edición del resumen. La autorización depende del profesional vinculado/rol; el artículo no debe afirmar acceso universal.

## 13. Documentos

Desde la ficha del paciente el profesional puede elegir categoría, adjuntar, confirmar carga, ver/descargar y eliminar documentos disponibles. Se aceptan PDF, JPEG, PNG y WebP; el máximo es 10 MB y el tamaño debe ser positivo. La carga usa almacenamiento configurable (R2 o fake de tests), por lo que disponibilidad productiva es **NO VERIFICADA EN PRODUCCIÓN**. Categorías: laboratorio, imágenes, orden, informe, receta, otro y resultado de estudio.

## 14. Estudios

El profesional crea una solicitud con título obligatorio, indicaciones opcionales y vencimiento opcional futuro; puede asociarla a un turno, generar enlace, cancelar o cerrar mientras está pendiente. El enlace público está firmado, tiene scope propio, vincula solicitud y paciente, expira por TTL/configuración y no sustituye autenticación profesional. El paciente abre el enlace, carga documentos permitidos, confirma/remueve archivos y finaliza el envío. El límite de cantidad y cualquier límite adicional deben tomarse de los schemas/tests vigentes antes de redactar el artículo final; no inventarlos en F11.0. El profesional revisa documentos recibidos y registra una devolución una sola vez, con resolución: respuesta online, requiere consulta presencial o requiere teleconsulta. La devolución cambia la solicitud a `reviewed` y genera una evolución clínica `study_review`.

## 15. Recordatorios

El worker busca turnos `reservado` o `confirmado` dentro de las próximas 24 horas y crea un recordatorio de email 24h antes. Omite email ausente/inválido, turnos cancelados, reprogramados o pasados; reintenta fallos hasta tres veces con backoff. El email contiene datos del turno y enlaces públicos de confirmar/cancelar. Render declara cron cada 15 minutos y Resend, pero entrega real, cron ejecutándose y dominio remitente son **NO VERIFICADOS EN PRODUCCIÓN**. La ayuda debe decir “podés recibir”/“el sistema intenta enviar”, no garantizar entrega.

## 16. Suscripción

La UI actual expone `Profesional` ($34.900) y `Consultorio` ($69.900), en ARS, y permite asociar tarjeta mediante Mercado Pago. El alta individual crea plan `profesional` en trial de 14 días; la UI informa que durante trial no se realiza cobro. Estados efectivos incluyen trial, active, past_due, cancelled y expired. El retorno y sincronización dependen de Mercado Pago y configuración. La estrategia solicitada prioriza documentar Profesional para independientes, pero la UI expone ambos planes y el precio/configuración operativa no está verificado. **BLOQUEO DOCUMENTAL:** definir plan objetivo, vigencia de precios, alcance de Consultorio y lenguaje de cobro antes de F11.6.

## 17. Restricciones y advertencias que debe conocer el usuario

- La sesión usa token local y puede vencer; un 401 devuelve al login.
- La disponibilidad no elimina automáticamente turnos existentes.
- Un turno reprogramado invalida enlaces/recordatorios asociados al snapshot anterior.
- Los enlaces públicos de turnos y estudios son acotados a acción/scope y vencimiento.
- La carga clínica limita tipos y tamaño; nunca subir datos de otra persona.
- Un estudio no puede cancelarse/cerrarse después de salir de `pending`, y la devolución sólo procede con documentos disponibles.
- No confundir pagos de turnos con suscripción SaaS.
- Código/configuración/tests no equivalen a operación productiva verificada.

## 18. Contenido propuesto del Centro de Ayuda

Rutas futuras: `/ayuda`, `/ayuda/primeros-pasos`, `/ayuda/prestaciones`, `/ayuda/disponibilidad`, `/ayuda/agenda`, `/ayuda/turnos`, `/ayuda/pacientes`, `/ayuda/historia-clinica`, `/ayuda/documentos`, `/ayuda/estudios`, `/ayuda/recordatorios`, `/ayuda/suscripcion`, `/ayuda/guia-rapida`. Cada artículo debe incluir objetivo, pasos, estados, límites, errores frecuentes y “qué hacer si…”.

## 19. Guía rápida

`/ayuda/guia-rapida` será breve: 1) crear cuenta; 2) revisar perfil; 3) crear prestación; 4) configurar disponibilidad; 5) crear paciente; 6) crear primer turno; 7) interpretar la agenda. Como segunda sección resumida: 8) resumen clínico; 9) evoluciones; 10) solicitudes y resultados de estudios.

## 20. Inventario preliminar de screenshots

| ID | Área | Pantalla | Objetivo | Desktop | Mobile | Datos necesarios |
|---|---|---|---|---|---|---|
| S01 | Onboarding | Perfil | Mostrar primer paso | Sí | Sí | profesional ficticio |
| S02 | Prestaciones | Crear prestación | Campos y modalidad | Sí | Sí | consulta $ ficticia |
| S03 | Disponibilidad | Semana habitual | Franjas múltiples | Sí | Sí | lunes/miércoles |
| S04 | Disponibilidad | Excepciones | Vacaciones/feriado | Sí | Sí | fechas sintéticas |
| S05 | Agenda | Día | Detalle de turno | Sí | Sí | turno reservado |
| S06 | Agenda | Semana | Solapamientos/estados | Sí | Sí | 4 turnos ficticios |
| S07 | Agenda | Mes | Conteos/excepciones | Sí | Sí | mes sintético |
| S08 | Turnos | Crear | Selección de horario | Sí | Sí | paciente/prestación |
| S09 | Turnos | Reprogramar | Nuevo horario | Sí | Sí | turno reprogramable |
| S10 | Pacientes | Listado | Búsqueda y acciones | Sí | Sí | 3 pacientes ficticios |
| S11 | Pacientes | Ficha | Módulos clínicos | Sí | Sí | paciente demo |
| S12 | Clínica | Resumen | Diferencia del resumen | Sí | Sí | antecedentes sintéticos |
| S13 | Clínica | Evolución | Registro cronológico | Sí | Sí | 2 evoluciones |
| S14 | Documentos | Documentos | Categorías/acciones | Sí | Sí | PDF/PNG sintéticos |
| S15 | Estudios | Solicitud | Crear y generar enlace | Sí | Sí | solicitud pendiente |
| S16 | Estudios | Carga pública | Flujo paciente | Sí | Sí | token demo no real |
| S17 | Estudios | Revisión | Documentos y devolución | Sí | Sí | resultado sintético |

Nombres semánticos sugeridos: `onboarding-profile.webp`, `service-create.webp`, `availability-week.webp`, `availability-exceptions.webp`, `agenda-day.webp`, `agenda-week.webp`, `agenda-month.webp`, `appointment-create.webp`, `appointment-reschedule.webp`, `patient-list.webp`, `patient-detail.webp`, `clinical-summary.webp`, `clinical-evolution.webp`, `clinical-documents.webp`, `study-request.webp`, `study-upload-public.webp`, `study-review.webp`.

## 21. Contenido excluido

Quedan fuera de F11: implementación de `/ayuda`, renderer, buscador, categorías visuales, screenshots, PDF, emails de bienvenida, dependencias nuevas, migraciones, cambios de producto, Mercado Pago y promesas operativas de producción. También se excluyen capacidades administrativas salvo que un futuro artículo tenga audiencia explícita.

## 22. Bloqueos documentales

1. Resolver el alcance comercial Profesional vs Consultorio, precios y vigencia.
2. Confirmar en F11.1 el límite exacto de cantidad de archivos por solicitud de estudio.
3. Verificar operativamente cron, Resend, R2, Mercado Pago y dominios antes de usar lenguaje de garantía.
4. Definir si la ayuda será pública completa o si algún artículo requerirá sesión.

## 23. Inconsistencias detectadas

- `docs/ROADMAP.md` todavía marca calendario semanal/mensual como pendiente, aunque F10 lo implementa y tiene tests; se actualiza únicamente esa línea.
- `docs/CURRENT_STATE.md` conserva un snapshot histórico de `feature/mvp`, no coincide con el HEAD auditado; se mantiene porque está fechado como snapshot, pero no debe usarse como estado actual.
- La estrategia de ayuda prioriza Profesional, mientras `ActivarSuscripcion.tsx` muestra también Consultorio y precios concretos.
- El branding técnico `mediturnos/MediTurnos` convive con Turnelia por decisión documentada; no se renombra en esta fase.
- Recordatorios, Resend, R2, Render y Mercado Pago están implementados/declarados, pero no verificados operativamente.

## 24. Contrato para F11.1

La fuente única futura será Markdown canónico versionado. Flujo aprobado: Markdown → renderer React → Centro de Ayuda web → misma composición imprimible → Playwright/Chromium → PDF reproducible. `frontend/package.json` y `playwright.config.ts` demuestran que Playwright ya forma parte del proyecto; no agregar React Router: integrar la ayuda en el routing manual de `App.tsx` y extender `routeMetadata.ts`. Las rutas públicas de ayuda deberán ser `index, follow` con canonical absoluto; `/app`, onboarding, login, reset, retorno, carga pública y PDF deben ser `noindex` según su sensibilidad. Actualizar sitemap sólo con rutas públicas aprobadas. El PDF llevará `@media print` y no competirá en SEO con el artículo web.

El email de bienvenida queda para una fase posterior: commit exitoso del registro → cuenta creada → intentar Resend → ante fallo registrar error sanitizado, sin rollback ni 500. Debe enlazar `/ayuda` y un PDF versionado, inicialmente sin adjuntar el archivo.

## 25. Criterio de salida de F11.0

F11.0 queda aprobable cuando este documento clasifica las capacidades, separa frontend/backend/configuración/producción, define artículos, guía rápida, screenshots, dataset demo, bloqueos, SEO y pipeline Markdown→React→PDF, sin cambios de runtime ni dependencias. La validación mínima es `git diff --check`; el árbol final debe dejar explícitos sólo los documentos F11 de esta fase además de los archivos no trackeados preexistentes.

### Dataset ficticio requerido para F11.7

Profesional: “Dra. Valentina Ríos”, especialidad clínica médica, matrícula sintética `DEMO-001`. Prestaciones: consulta inicial presencial 30 min, control virtual 20 min y consulta extendida 60 min, con precios ficticios. Disponibilidad: lunes/miércoles/viernes con dos franjas. Excepciones: vacaciones de cinco días, feriado y horario extraordinario. Pacientes: “Ana Pereyra”, “Bruno Acosta” y “Carla Medina”, todos ficticios. Turnos: reservado, confirmado, finalizado, cancelado y ausente. Historia: antecedentes, alergias, medicación, dos evoluciones sintéticas. Documentos: PDF/PNG generados sin datos reales. Estudio: solicitud pendiente, carga pública con archivos sintéticos, revisión y devolución en cada disposición. Nunca usar datos reales.
