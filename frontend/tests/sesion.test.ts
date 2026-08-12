import assert from "node:assert/strict";
import { test } from "vitest";

import { AxiosError } from "axios";

import { manejarErrorDeApi } from "../src/api/manejoSesion.ts";
import { restaurarSesion } from "../src/utils/sesion.ts";
import type { UsuarioActual } from "../src/types/auth.ts";


function crearAlmacenamiento(token: string | null) {
  let valor = token;

  return {
    getItem: () => valor,
    removeItem: () => {
      valor = null;
    },
    valor: () => valor,
  };
}


function errorHttp(estado: number) {
  return new AxiosError(
    "Error HTTP",
    undefined,
    undefined,
    undefined,
    {
      status: estado,
      statusText: "Error",
      headers: {},
      config: { headers: {} },
      data: {},
    },
  );
}


test("restaura una sesión válida", async () => {
  const almacenamiento = crearAlmacenamiento("jwt-valido");
  const usuario: UsuarioActual = {
    id: 1,
    nombre: "Admin",
    email: "admin@example.com",
    rol: "administrador",
    activo: true,
    creado_en: "2026-08-11T12:00:00Z",
  };

  assert.deepEqual(
    await restaurarSesion(
      async () => usuario,
      almacenamiento,
    ),
    usuario,
  );
  assert.equal(almacenamiento.valor(), "jwt-valido");
});


test("descarta un token inválido o vencido", async () => {
  const almacenamiento = crearAlmacenamiento("jwt-vencido");

  assert.equal(
    await restaurarSesion(
      async () => Promise.reject(errorHttp(401)),
      almacenamiento,
    ),
    null,
  );
  assert.equal(almacenamiento.valor(), null);
});


test("un 401 limpia el token y notifica una vez", async () => {
  const almacenamiento = crearAlmacenamiento("jwt-invalido");
  let notificaciones = 0;

  await assert.rejects(
    manejarErrorDeApi(
      errorHttp(401),
      almacenamiento,
      () => {
        notificaciones += 1;
      },
    ),
  );
  await assert.rejects(
    manejarErrorDeApi(
      errorHttp(401),
      almacenamiento,
      () => {
        notificaciones += 1;
      },
    ),
  );

  assert.equal(almacenamiento.valor(), null);
  assert.equal(notificaciones, 1);
});


test("un 403 no limpia el token ni cierra la sesión", async () => {
  const almacenamiento = crearAlmacenamiento("jwt-valido");
  let notificaciones = 0;

  await assert.rejects(
    manejarErrorDeApi(
      errorHttp(403),
      almacenamiento,
      () => {
        notificaciones += 1;
      },
    ),
  );

  assert.equal(almacenamiento.valor(), "jwt-valido");
  assert.equal(notificaciones, 0);
});
