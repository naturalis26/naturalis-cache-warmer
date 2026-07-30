# Cache warmer - soynaturalis.com

Mantiene caliente la cache de soynaturalis.com. Cada 2 horas hace peticiones GET
publicas a las URLs listadas en urls.txt, las mismas que haria cualquier visitante.

No usa credenciales ni secrets.

## Uso

Se ejecuta solo. Para lanzarlo a mano: pestana Actions, boton Run workflow.

## Mantenimiento

- urls.txt es una lista manual: si cambia una URL del sitio, hay que actualizarla aqui.
- El workflow sigue las redirecciones y avisa, en vez de fallar.
- GitHub desactiva los workflows programados si el repo pasa 60 dias sin commits.
