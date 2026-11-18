"""Verificador de daño: decide si la corrección es aceptable.

No corrige nada. Solo comprueba que el modelo no se ha pasado:
  - no ha perdido fragmentos protegidos
  - no ha reescrito más de la cuenta
  - no ha cambiado el número de frases ni el tamaño
"""

import difflib
import re

# umbrales
MAX_CAMBIO_PALABRAS = 0.35   # fracción de palabras distintas (aviso)
MAX_CAMBIO_DURO = 0.60       # fracción de palabras distintas (bloqueo)
MAX_DELTA_LARGO = 0.30       # variación de longitud (bloqueo)
MAX_CAMBIOS_LISTA = 40       # cambios que se listan al usuario

WORD_RX = re.compile(r"\S+")


def words(t):
    return WORD_RX.findall(t)


def sentences(t):
    return [s for s in re.split(r"[.!?…]+", t) if s.strip()]


def cambios(original, corregido, limite=MAX_CAMBIOS_LISTA):
    """Lista legible de sustituciones palabra a palabra."""
    a, b = words(original), words(corregido)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        de, a_ = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if not de and not a_:
            continue
        out.append({"tipo": tag, "de": de, "a": a_})
        if len(out) >= limite:
            break
    return out


def verificar(original, corregido, mapping_marcadores_faltantes=None, protegidos=()):
    """Devuelve (estado, avisos).

    estado: 0 = limpio · 2 = dudas · 1 = bloqueado
    """
    avisos = []
    if not corregido or not corregido.strip():
        return 1, ["la corrección ha quedado vacía"]

    faltan = list(mapping_marcadores_faltantes or [])
    if faltan:
        avisos.append("el modelo perdió %d fragmento(s) protegido(s): %s"
                      % (len(faltan), ", ".join(faltan[:5])))
        return 1, avisos

    for tok in protegidos:
        if tok not in corregido:
            avisos.append("desapareció un fragmento protegido: %r" % tok)
            return 1, avisos

    a, b = words(original), words(corregido)
    ratio = 0.0
    if a:
        sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        iguales = sum(blk.size for blk in sm.get_matching_blocks())
        ratio = 1.0 - (iguales / max(len(a), len(b)))

    if ratio >= MAX_CAMBIO_DURO:
        avisos.append("reescritura excesiva: %.0f%% de las palabras cambiadas" % (ratio * 100))
        return 1, avisos
    if ratio >= MAX_CAMBIO_PALABRAS:
        avisos.append("cambios amplios: %.0f%% de las palabras" % (ratio * 100))

    delta = abs(len(corregido) - len(original)) / max(len(original), 1)
    if delta > MAX_DELTA_LARGO:
        avisos.append("longitud muy distinta (%+.0f%%)" % ((len(corregido) / max(len(original), 1) - 1) * 100))
        return 1, avisos

    s_orig, s_corr = len(sentences(original)), len(sentences(corregido))
    if s_orig and abs(s_corr - s_orig) > max(1, s_orig // 5):
        avisos.append("número de frases distinto: %d → %d" % (s_orig, s_corr))
        return 1, avisos

    return (2 if avisos else 0), avisos
