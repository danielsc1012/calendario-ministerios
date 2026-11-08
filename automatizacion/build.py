#!/usr/bin/env python3
"""
Calendario de Ministerios · Iglesia Northwood
Lee de Planning Center Services quién está en cada equipo de los ministerios
definidos en ministerios.json y guarda la lista CIFRADA en equipos.enc.json.

Sin la contraseña de edición nadie puede leer los nombres, aunque abra el archivo.

Variables de entorno:
  PCO_APP_ID, PCO_SECRET   Personal Access Token de Planning Center
  EDIT_PASSWORD            la misma contraseña que usan los directores en la página

Uso local (sin Planning Center), para generar una vista previa:
  python3 build.py --desde-txt roster.txt --salida equipos.enc.json
"""
import base64, json, os, sys, time, urllib.request, urllib.error, datetime, argparse
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

API = "https://api.planningcenteronline.com/services/v2"
ITER = 250000  # igual que la página (WebCrypto PBKDF2-SHA256)


def cifrar(obj, password):
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(password.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "salt": b(salt), "iv": b(iv), "ct": b(ct)}


def pco_get(url, auth):
    for intento in range(5):
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", "20")) + 1)
                continue
            raise
    raise RuntimeError("Planning Center no respondió (límite de consultas)")


def paginate(path, auth):
    url = API + path
    while url:
        j = pco_get(url, auth)
        yield j
        url = (j.get("links") or {}).get("next")


def mapa_equipos(config):
    """nombre de equipo en Planning Center (minúsculas) -> 'ministerio:equipo'"""
    m = {}
    for min_ in config["ministerios"]:
        for eq in min_["equipos"]:
            for nombre in eq["pco"]:
                m[nombre.strip().lower()] = f'{min_["id"]}:{eq["id"]}'
    return m


def desde_pco(config):
    auth = base64.b64encode(f"{os.environ['PCO_APP_ID']}:{os.environ['PCO_SECRET']}".encode()).decode()
    mapa = mapa_equipos(config)
    personas = {}
    equipos = 0
    for page in paginate("/teams?per_page=100", auth):
        for t in page["data"]:
            a = t["attributes"]
            if a.get("archived_at"):
                continue
            tag = mapa.get((a.get("name") or "").strip().lower())
            if not tag:
                continue
            equipos += 1
            for pp in paginate(f"/teams/{t['id']}/people?per_page=100", auth):
                for p in pp["data"]:
                    pa = p["attributes"]
                    nombre = (pa.get("full_name") or pa.get("name") or "").strip()
                    reg = personas.setdefault(p["id"], {"n": nombre, "t": []})
                    if tag not in reg["t"]:
                        reg["t"].append(tag)
    print(f"Equipos leídos: {equipos} · personas: {len(personas)}")
    return list(personas.values())


def desde_txt(path, config):
    # formato: id|Nombre|WB,WV  (W=worship, E=experience; B/V/S/P/L/C = equipo)
    cod = {"WB": "worship:Band", "WV": "worship:Vocals", "WS": "worship:Sound",
           "EP": "experience:Projection", "EL": "experience:Lights", "EC": "experience:Livestream/Camera Ops"}
    out = []
    for line in open(path, encoding="utf-8"):
        if line.strip():
            _, n, t = line.rstrip("\n").split("|")
            out.append({"n": n, "t": [cod[x] for x in t.split(",")]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="ministerios.json")
    ap.add_argument("--salida", default="equipos.enc.json")
    ap.add_argument("--desde-txt")
    args = ap.parse_args()
    password = os.environ.get("EDIT_PASSWORD")
    if not password:
        sys.exit("Falta EDIT_PASSWORD")
    config = json.load(open(args.config, encoding="utf-8"))
    personas = desde_txt(args.desde_txt, config) if args.desde_txt else desde_pco(config)
    if not personas:
        sys.exit("No se encontró ninguna persona; no se reemplaza el archivo.")
    personas.sort(key=lambda p: p["n"].lower())
    payload = {"actualizado": datetime.date.today().isoformat(), "personas": personas}
    blob = cifrar(payload, password)
    blob["actualizado"] = payload["actualizado"]
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(blob, f, indent=2)
        f.write("\n")
    print(f"{args.salida} generado ({len(personas)} personas, cifrado).")


if __name__ == "__main__":
    main()
