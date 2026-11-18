"""Cliente mínimo para cualquier endpoint compatible con OpenAI (stdlib, sin dependencias)."""

import json
import os
import urllib.error
import urllib.request

DEFAULTS = {
    "base_url": "https://openrouter.ai/api/v1",
    "model": "",
    "api_key": "",
    "timeout": "120",
}

SYSTEM = (
    "Ets un corrector professional de català. Corregeix NOMÉS errors d'ortografia, accentuació, "
    "gramàtica, concordança i lèxic incorrecte (castellanismes i calcs del castellà). "
    "No reescriguis l'estil, no canviïs l'ordre de les frases, no afegeixis ni treguis informació.\n\n"
    "Vigila especialment aquests errors freqüents en textos generats per màquines:\n"
    "- 'per a' + infinitiu → 'per' ('per a parlar' → 'per parlar').\n"
    "- 'ha sigut' → 'ha estat'.\n"
    "- gerundi de posterioritat → verb conjugat ('Va sortir corrent, agafant el metro' → "
    "'Va sortir corrent i va agafar el metro').\n"
    "- 'en base a' → 'segons' o 'a partir de'; 'a nivel de' → 'pel que fa a'; 'el mismo' → 'el mateix'; "
    "'darse cuenta' → 'adonar-se'.\n"
    "- accentuació diacrítica: 'es' → 'és' quan és el verb ser; 'si' → 'sí' quan és afirmació.\n"
    "- apostrofació davant de vocal: 'la empresa' → \"l'empresa\", 'la escola' → \"l'escola\", "
    "'de acord' → \"d'acord\".\n\n"
    "Conserva EXACTAMENT igual els fragments entre ⟦ i ⟧ (són dades protegides). "
    "Retorna només el text corregit, sense comentaris, sense cometes i sense cap introducció. "
    "Si el text ja és correcte, retorna'l exactament igual."
)


def load_env(paths=None):
    """Carga .env sin dependencias. No sobreescribe variables ya definidas."""
    if paths is None:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = [os.path.join(here, ".env"), os.path.join(os.getcwd(), ".env")]
    for p in paths:
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k.startswith("CORRECTOR_") and k not in os.environ:
                    os.environ[k] = v


def config():
    load_env()
    cfg = {
        "base_url": os.environ.get("CORRECTOR_BASE_URL") or DEFAULTS["base_url"],
        "model": os.environ.get("CORRECTOR_MODEL") or DEFAULTS["model"],
        "api_key": os.environ.get("CORRECTOR_API_KEY") or "",
        "timeout": float(os.environ.get("CORRECTOR_TIMEOUT") or DEFAULTS["timeout"]),
        # cabecera extra opcional (algunos gateways la exigen, p. ej. sesión de OpenCode)
        "extra_header": os.environ.get("CORRECTOR_EXTRA_HEADER") or "",
    }
    return cfg


def chat(text, cfg=None, system=SYSTEM, temperature=0):
    """Devuelve el texto corregido. Lanza RuntimeError con mensaje legible."""
    cfg = cfg or config()
    if not cfg["api_key"]:
        raise RuntimeError(
            "Falta CORRECTOR_API_KEY. Copia .env.example a .env y pon tu clave "
            "(o exporta CORRECTOR_API_KEY)."
        )
    if not cfg["model"]:
        raise RuntimeError("Falta CORRECTOR_MODEL (por ejemplo: google/gemini-2.5-flash-lite).")

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model"],
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + cfg["api_key"],
        # algunos gateways (Cloudflare delante) rechazan el User-Agent por defecto de urllib
        "User-Agent": "corrector-ca/0.1 (+https://github.com/)",
    }
    if cfg["extra_header"] and ":" in cfg["extra_header"]:
        k, v = cfg["extra_header"].split(":", 1)
        headers[k.strip()] = v.strip()

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout"]) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError("HTTP %s en %s: %s" % (e.code, url, body))
    except urllib.error.URLError as e:
        raise RuntimeError("No se pudo conectar con %s: %s" % (url, e.reason))

    try:
        out = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError("Respuesta inesperada del proveedor: %s" % json.dumps(data)[:300])
    return clean_output(out)


def clean_output(out):
    """Quita envoltorios que añaden algunos modelos."""
    out = (out or "").strip()
    if out.startswith("```"):
        lines = [l for l in out.splitlines() if not l.strip().startswith("```")]
        out = "\n".join(lines).strip()
    if len(out) >= 2 and out[0] == out[-1] and out[0] in "\"'«»“”":
        out = out[1:-1].strip()
    for prefix in ("Text corregit:", "Text corregit", "Correcció:", "Correcció"):
        if out.startswith(prefix):
            out = out[len(prefix):].strip()
    return out
