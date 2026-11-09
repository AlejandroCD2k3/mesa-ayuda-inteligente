/** Cabeceras del adaptador HTTP: nunca guardamos el token en almacenamiento web. */
export function authHeaders(token: string) {
  return { headers: { Authorization: `Bearer ${token}` } };
}
