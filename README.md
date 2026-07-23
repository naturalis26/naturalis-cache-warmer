# Cache warmer - soynaturalis.com

Precalienta la cache de LiteSpeed en soynaturalis.com haciendo curl publico a 43 URLs
clave (home, tienda y toda la categoria "Nutricion deportiva" con sus fichas de producto)
cada 4 horas, via un workflow programado de GitHub Actions. Sustituto del crawler nativo
de LiteSpeed, no disponible en el hosting compartido (BanaHosting).

Solo hace peticiones GET anonimas y publicas, sin credenciales, tokens ni acceso a
wp-admin. No requiere ningun secret configurado en el repo.

## Uso

- Corre solo automaticamente cada 4h (cron: "0 */4 * * *", hora UTC).
- Para lanzarlo a mano: pestana Actions, workflow "Precalentar cache soynaturalis.com",
  boton "Run workflow".
- El resultado de cada URL (codigo HTTP, tiempo, hit/miss) queda en el log de cada
  ejecucion, dentro de la pestana Actions.

## Editar la lista de URLs

Anadir o quitar lineas en urls.txt (una URL completa por linea) y hacer commit/push.

## Nota de mantenimiento

GitHub desactiva automaticamente los workflows programados si el repo lleva 60 dias
sin ningun commit. Basta con reactivarlo desde Actions o hacer un commit nuevo para
reanudarlo.
