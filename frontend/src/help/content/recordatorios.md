---
slug: recordatorios
title: Recordatorios
description: Conocé cómo funcionan los recordatorios automáticos de turnos por correo electrónico.
category: agenda
order: 100
---

## Qué son los recordatorios

Turnelia puede procesar recordatorios automáticos por correo electrónico antes de determinados turnos. El procesamiento no garantiza que el mensaje llegue a la bandeja del destinatario.

## A qué turnos se aplican

Se consideran turnos futuros en estado **Pendiente** o **Confirmado**. Los turnos cancelados, ausentes y finalizados no forman parte de esta selección.

## Cuándo se envían

Turnelia busca turnos próximos dentro de una ventana configurada alrededor de las 24 horas previas. El proceso corre periódicamente, por lo que no significa que el correo se envíe exactamente a una hora fija.

## A qué email llega

El recordatorio se prepara para la dirección de email del paciente registrada en Turnelia.

## Qué pasa si no hay email

Si el paciente no tiene una dirección de correo disponible o la dirección no es válida, el recordatorio puede omitirse.

## Reintentos

Si ocurre un error temporal de envío, Turnelia puede volver a intentar el procesamiento. El estado final depende del resultado del proveedor de correo.

## ¿Está garantizada la entrega?

> Importante: Turnelia procesa y envía los recordatorios a través de un proveedor de correo, pero la entrega final también depende del servidor de destino, filtros antispam y disponibilidad del servicio.

## ¿Puedo enviar uno manualmente?

Actualmente no existe una acción manual desde la agenda para reenviar un recordatorio.

Consultá también [Turnos](/ayuda/turnos).
