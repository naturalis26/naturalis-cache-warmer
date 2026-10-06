#!/usr/bin/env python3
"""Vigilancia semanal de soynaturalis.com (H97, 2026-10-06).

Falla (exit 1) si algo de lo desplegado el 6-oct deja de cumplirse, para que GitHub avise por correo:
  A. Tema Merto: version o hojas CSS originales distintas de las usadas para la hoja recortada de portada.
  B. Portada: debe usar la hoja recortada (naturalis-merto-portada-css) y no las 4 originales.
  C. Cloudflare: paginas clave en HIT (2.a peticion), sin Set-Cookie, con X-Nat-Borde; con cookie de
     carrito -> no cacheado; movil y escritorio con su version (botones "Vista rapida" solo en escritorio).
  D. Poppins: la etiqueta del tema lleva data-no-async y no hay onload duplicado.
  E. Imagenes: la imagen principal (precargada) de cada ficha <= LIMITE_IMG_KB.
Solo hace peticiones GET publicas, sin credenciales.
"""
import json
import re
import sys
import urllib.request

BASE = "https://soynaturalis.com"
LIMITE_IMG_KB = 30  # 5 fichas ya al maximo de compresion pesan 25-29 KB (6-oct)
TEMA_VERSION = "1.0.5"
# Ficheros de LiteSpeed de las 4 hojas de Merto cuando se genero la hoja recortada (6-oct).
MERTO_ESPERADO = {
    "merto-reset-css": "c9809486711bf69976663b59480dbe19",
    "merto-style-css": "7e95dbbed62f361a60e94e27e93644ab",
    "merto-responsive-css": "468d4b49bde8669adec9a259b6b74202",
    "merto-dynamic-css-css": "e23136a24ca5c5f9ac95c48b2133441e",
}
UA_PC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 NaturalisVigilancia/1.0"
UA_MOVIL = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1 NaturalisVigilancia/1.0"
ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
PAGINAS = ["/", "/tienda-2/", "/categoria-producto/nutricion-deportiva/", "/producto/titan-army-x-5-libras-sabor-vainilla/"]

fallos = []


def get(url, ua=UA_PC, cookie=None, accept=ACCEPT):
    h = {"User-Agent": ua, "Accept": accept, "Accept-Language": "es-CO,es;q=0.9"}
    if cookie:
        h["Cookie"] = cookie
    r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60)
    return r, r.read()


def fallo(msg):
    fallos.append(msg)
    print("FALLO:", msg)


def tema_y_portada():
    _, css = get(BASE + "/wp-content/themes/merto/style.css", accept="text/css,*/*")
    m = re.search(rb"Version:\s*([\d.]+)", css)
    ver = m.group(1).decode() if m else "?"
    if ver != TEMA_VERSION:
        fallo(f"A: version de Merto {ver} (esperada {TEMA_VERSION}); la portada ha vuelto a las hojas originales: regenerar la hoja recortada")
    _, html = get(BASE + "/tienda-2/")
    for ident, fichero in MERTO_ESPERADO.items():
        m = re.search(rf"id='{ident}' href='[^']*/css/([0-9a-f]{{32}})\.css".encode(), html)
        actual = m.group(1).decode() if m else None
        if actual != fichero:
            fallo(f"A: hoja {ident} cambio ({actual} != {fichero}): opciones o CSS de Merto modificados, regenerar la hoja recortada de portada")
    for ua, nombre in ((UA_PC, "escritorio"), (UA_MOVIL, "movil")):
        _, home = get(BASE + "/", ua=ua)
        if b"naturalis-merto-portada-css" not in home:
            fallo(f"B: la portada ({nombre}) no usa la hoja recortada")
        if re.search(rb"id='merto-(reset|style|responsive)-css'", home):
            fallo(f"B: la portada ({nombre}) carga hojas originales de Merto")


def cloudflare_y_poppins():
    for path in PAGINAS:
        vistas = {}
        for ua, nombre in ((UA_PC, "escritorio"), (UA_MOVIL, "movil")):
            get(BASE + path, ua=ua)
            r, html = get(BASE + path, ua=ua)
            cf = r.headers.get("cf-cache-status")
            if cf != "HIT":
                fallo(f"C: {path} {nombre} cf-cache-status={cf} (esperado HIT)")
            if r.headers.get_all("Set-Cookie"):
                fallo(f"C: {path} {nombre} lleva Set-Cookie en pagina cacheada")
            if r.headers.get("x-nat-borde") != "1":
                fallo(f"C: {path} {nombre} sin X-Nat-Borde")
            vistas[nombre] = html.count(b'class="quickshop')
            if b"fonts.googleapis.com/css?family=Poppins" in html and b"data-no-async" not in html:
                fallo(f"D: {path} {nombre} etiqueta de Poppins sin data-no-async")
            if re.search(rb"onload=\"this\.onload=null;this\.rel='stylesheet'\"[^>]*media=\"print\" onload=", html):
                fallo(f"D: {path} {nombre} onload duplicado en hoja con media=print (Poppins no se aplicaria)")
        if vistas["movil"] != 0 or vistas["escritorio"] == 0:
            fallo(f"C: {path} mezcla de versiones (vista rapida movil={vistas['movil']}, escritorio={vistas['escritorio']})")
    r, _ = get(BASE + PAGINAS[3], ua=UA_MOVIL, cookie="woocommerce_items_in_cart=1")
    if r.headers.get("cf-cache-status") in ("HIT", "MISS", "EXPIRED"):
        fallo(f"C: con cookie de carrito la ficha sale de cache ({r.headers.get('cf-cache-status')})")


def imagenes():
    prods = []
    for p in (1, 2):
        _, js = get(f"{BASE}/wp-json/wc/store/v1/products?per_page=100&page={p}", accept="application/json")
        prods += [x["permalink"] for x in json.loads(js)]
    pesadas = []
    for url in prods:
        r, _ = get(url, ua=UA_MOVIL)
        link = ",".join(v for k, v in r.headers.items() if k.lower() == "link" and "preload" in v)
        m = re.search(r"<([^>]+)>;\s*rel=preload", link)
        if not m:
            fallo(f"E: {url} sin preload de imagen principal")
            continue
        _, img = get(m.group(1), accept="image/webp,*/*")
        if len(img) > LIMITE_IMG_KB * 1024:
            pesadas.append(f"{len(img)//1024} KB {url} -> {m.group(1).split('/uploads/')[-1]}")
    for p in pesadas:
        fallo("E: imagen principal pesada: " + p)
    print(f"Imagenes revisadas: {len(prods)} fichas, {len(pesadas)} por encima de {LIMITE_IMG_KB} KB")


QUE_ARREGLAR = {
    "A": "regenerar CSS de portada (cambio en tema Merto)",
    "B": "revisar CSS recortado de portada",
    "C": "revisar cache de Cloudflare",
    "D": "arreglar fuente Poppins",
    "E": "corregir peso de fotos",
}


def escribir_aviso():
    """Titulo y cuerpo del aviso (issue de GitHub, llega por correo) con lo que hay que arreglar."""
    partes = []
    for letra, texto in QUE_ARREGLAR.items():
        n = sum(1 for f in fallos if f.startswith(letra + ":"))
        if n:
            partes.append(f"{texto} ({n})")
    otros = [f for f in fallos if f[:2] not in {k + ":" for k in QUE_ARREGLAR}]
    if otros:
        partes.append(f"revisar la vigilancia ({len(otros)} errores)")
    titulo = "Naturalis: " + " + ".join(partes)
    cuerpo = "Vigilancia semanal de soynaturalis.com. Hay que arreglar:\n\n" + "\n".join("- " + f for f in fallos)
    cuerpo += "\n\nPasarselo al auditor WP (proyecto naturalis-wp-auditor): CHANGELOG 2026-10-06 (9) explica cada comprobacion."
    with open("aviso_titulo.txt", "w") as f:
        f.write(titulo[:250])
    with open("aviso_cuerpo.txt", "w") as f:
        f.write(cuerpo)
    print("AVISO:", titulo)


if __name__ == "__main__":
    import os
    for paso in (tema_y_portada, cloudflare_y_poppins, imagenes):
        try:
            paso()
        except Exception as e:  # un fallo de red tambien debe avisar
            fallo(f"{paso.__name__}: error {e}")
    if os.environ.get("PRUEBA_AVISO") == "1":
        fallo("E: PRUEBA del aviso por correo (no hay nada que arreglar; cerrar este aviso)")
    print(f"RESUMEN: {len(fallos)} fallos")
    if fallos:
        escribir_aviso()
    sys.exit(1 if fallos else 0)
