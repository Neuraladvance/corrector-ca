"""Orquestación: enmascarar → corregir con el modelo → restaurar → verificar daño."""

import re

from . import client, guard, mask

# Palabras que solo existen en una de las dos lenguas (las ambiguas quedan fuera a propósito:
# "un/una/de/que/no/en/al/del/el/la/es/son/ha/eran/entre/sobre/ver/general/un".
CA_ONLY = {
    "bon", "bona", "hola", "fet", "fer", "petit", "petita", "amb", "però", "perquè", "això",
    "aquest", "aquesta", "aquests", "aquestes", "també", "gairebé", "doncs", "els", "les",
    "dels", "pels", "als", "és", "són", "molt", "molta", "molts", "moltes", "cal", "vam",
    "vaig", "hem", "hi", "ho", "així", "llavors", "mentre", "sense", "quan", "nosaltres",
    "vosaltres", "ells", "elles", "meva", "teva", "seva", "nostre", "vostre", "serà", "eren",
    "estat", "sigut", "tingut", "tenir", "tinc", "té", "tenim", "tenen", "faig", "fas", "fem",
    "fan", "diu", "veig", "veu", "veure", "sap", "puc", "pots", "podem", "poden", "anem",
    "anar", "vinc", "gràcies", "ningú", "algú", "gaire", "força", "per", "com", "on", "qui",
}
ES_ONLY = {
    "los", "las", "con", "pero", "porque", "esto", "este", "esta", "estos", "estas",
    "también", "según", "cuando", "nuestro", "nuestra", "vuestro", "vuestra", "para", "muy",
    "más", "del", "al", "y", "hay", "hacer", "hecho", "pequeño", "pequeña", "nosotros",
    "vosotros", "ellas", "yo", "él", "ella", "eran", "hemos", "tengo", "tiene", "tenemos",
    "tienen", "hago", "hace", "hacen", "digo", "dice", "decir", "veo", "puedo", "puede",
    "podemos", "pueden", "voy", "fui", "fue", "fueron", "vengo", "sin", "por", "como",
}
# caracteres y dígrafos que deciden solos cuando el texto es corto
CA_CHARS = "àèòç·ï"
ES_CHARS = "ñ¿¡áíóú"


def parece_catalan(text):
    """Decide si el texto es catalán. Empate o texto sin pistas → no se corrige."""
    low = text.lower()
    tokens = re.findall(r"[a-zàèéíòóúçïü]+", low)
    if not tokens:
        return False

    ca = sum(1 for t in tokens if t in CA_ONLY)
    es = sum(1 for t in tokens if t in ES_ONLY)
    ca += 3 * len(re.findall(r"\b(l'|d'|s'|n'|els|les|dels)", low))
    ca += 2 * sum(low.count(c) for c in CA_CHARS)
    es += 3 * sum(low.count(c) for c in ES_CHARS)
    return ca > es



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
