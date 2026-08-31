---
slug: turnos
title: Turnos
description: Creá, reprogramá, cancelá y actualizá el estado de los turnos de tu agenda.
category: agenda
order: 50
---

## Crear un turno

1. Ingresá a **Mi agenda**.
2. Seleccioná **+ Nuevo turno**.
3. Elegí un **Paciente**.
4. Elegí una **Prestación**.
5. Seleccioná una **Fecha**.
6. Elegí un **Horario disponible**.
7. Si querés, completá **Observaciones**.
8. Seleccioná **Confirmar turno** para guardar.

La prestación debe estar activa, el paciente debe estar disponible para tu cuenta y el horario debe seguir libre al guardar.

## Cómo se muestran los horarios disponibles

Turnelia calcula los horarios según la disponibilidad habitual, la duración de la prestación, los turnos ocupados, las excepciones y la hora actual cuando elegís el día de hoy. Los horarios pasados aparecen deshabilitados.

## Si el horario deja de estar disponible

Turnelia vuelve a validar el horario al guardar. Si otra reserva ocupó ese horario, verás un aviso y tendrás que elegir otro horario disponible.

## Reprogramar un turno

1. Abrí el turno desde **Mi agenda**.
2. Seleccioná **Reprogramar**.
3. Elegí una nueva fecha.
4. Seleccioná un nuevo horario disponible.
5. Confirmá con **Confirmar cambio**.

## Cancelar un turno

Desde el detalle del turno, seleccioná **Cancelar** y luego confirmá la acción. El turno queda en estado **Cancelado**; no se elimina físicamente.

## Marcar como ausente

Seleccioná **Marcar ausente** cuando el paciente no se haya presentado. El turno queda en estado **Ausente** y deja de comportarse como un turno activo.

## Finalizar un turno

Seleccioná **Finalizar** cuando la atención haya terminado. El turno queda en estado **Finalizado**. Esta acción no crea automáticamente una evolución clínica.

## Turnos pasados

Los turnos pasados pueden consultarse desde la agenda. Las acciones disponibles dependen de su estado; los estados terminales **Cancelado**, **Ausente** y **Finalizado** no permiten las mismas acciones que un turno activo.

## Conflictos y solapamientos

Turnelia evita guardar una reserva cuando el horario ya está ocupado o se superpone con otro turno incompatible. La duración de la prestación también se tiene en cuenta.

## Prestaciones inactivas

Una prestación **Inactiva** no debe utilizarse para nuevas reservas. Desactivarla no modifica los turnos que ya fueron creados.

## Errores frecuentes

- **Horario ya no disponible:** volvé a consultar y elegí otro.
- **Prestación inactiva:** reactivá la prestación antes de crear una nueva reserva.
- **Paciente inválido:** verificá que el paciente esté registrado y vinculado a tu cuenta.
- **Slot pasado:** elegí un horario futuro.
- **Fecha u horario inválido:** revisá la fecha y la disponibilidad configurada.

Si necesitás cambiar tus horarios habituales, consultá [Disponibilidad](/ayuda/disponibilidad).
