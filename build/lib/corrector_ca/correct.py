"""Orquestación: enmascarar → corregir con el modelo → restaurar → verificar daño."""

import re

from . import client, guard, mask

# palabras función que delatan catalán frente a castellano
CA = {"els", "les", "amb", "però", "perquè", "això", "aquest", "aquesta", "dels", "més",
      "també", "sense", "segons", "quan", "perquè", "nostre", "vostre", "per", "que", "és",
      "són", "ha", "han", "una", "un", "el", "la", "de", "i", "no", "es", "en", "al", "del"}
ES = {"los", "las", "con", "pero", "porque", "esto", "este", "esta", "de los", "más",
      "también", "sin", "según", "cuando", "nuestro", "vuestro", "para", "que", "es",
      "son", "ha", "han", "una", "un", "el", "la", "de", "y", "no", "se", "en", "al", "del"}


def parece_catalan(text):
    tokens = re.findall(r"[a-zàèéíòóúçïü]+", text.lower())
    if not tokens:
        return False
    ca = sum(1 for t in tokens if t in CA and t not in {"el", "la", "de", "i", "no", "es", "en", "al", "del", "que", "una", "un", "ha", "han", "son", "són", "per"})
    es = sum(1 for t in tokens if t in ES and t not in {"el", "la", "de", "y", "no", "se", "en", "al", "del", "que", "una", "un", "ha", "han", "son", "es"})
    # señales fuertes del catalán
    fuertes = len(re.findall(r"\b(l'|d'|els|les|amb|això|aquest|perquè|també|és|són)\b", text.lower()))
    return fuertes + ca > es


def corregir(text, cfg=None, solo_verificar=False, forzar_idioma=False):
    """Devuelve dict con original, corregido, cambios, avisos y estado.

    estado: 0 = corregido sin incidencias · 2 = corregido con dudas · 1 = bloqueado (texto original)
    """
    original = text
    res = {"original": original, "corregido": original, "cambios": [], "avisos": [], "estado": 0,
           "idioma": None, "motor": None}

    if not original or not original.strip():
        return res

    if not forzar_idioma and not parece_catalan(original):
        res["idioma"] = "no-ca"
        res["avisos"].append("el texto no parece catalán: no se corrige")
        return res
    res["idioma"] = "ca"

    if solo_verificar:
        res["motor"] = "verificador"
        return res

    enmascarado, mapping = mask.mask(original)
    try:
        cfg = cfg or client.config()
        salida = client.chat(enmascarado, cfg=cfg)
    except RuntimeError as e:
        res["estado"] = 2
        res["avisos"].append("corrector no disponible: %s" % e)
        return res

    restaurado, faltan = mask.unmask(salida, mapping)
    estado, avisos = guard.verificar(original, restaurado, faltan, mask.protected_tokens(mapping))
    res["motor"] = cfg.get("model")
    res["avisos"] = avisos
    res["cambios"] = guard.cambios(original, restaurado) if estado != 1 else []

    if estado == 1:
        res["corregido"] = original  # fail-open: se entrega el original
        res["estado"] = 1
    else:
        res["corregido"] = restaurado
        res["estado"] = estado
    return res
