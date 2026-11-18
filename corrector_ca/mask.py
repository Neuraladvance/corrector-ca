"""Protege fragmentos que el modelo no debe tocar.

Se sustituyen por marcadores ⟦n⟧ antes de enviar el texto y se restauran después.
Así el modelo no puede "corregir" código, URLs, cifras ni nombres propios: no los ve.
"""

import os
import re

# Orden importante: primero lo grande, luego lo pequeño.
PATTERNS = [
    ("codeblock", re.compile(r"```.*?```", re.S)),
    ("codeblock", re.compile(r"~~~.*?~~~", re.S)),
    ("code", re.compile(r"`[^`\n]+`")),
    ("url", re.compile(r"https?://[^\s<>\"')]+")),
    ("url", re.compile(r"\bwww\.[^\s<>\"')]+")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("path", re.compile(r"\b[A-Za-z]:\\[^\s,;)\"']+")),
    ("path", re.compile(r"(?<![\w.])/(?:[\w.-]+/)*[\w.-]+")),
    ("ident", re.compile(r"\b[\w.+-]*\d[\w.+-]*\b")),        # contiene dígitos: 2.4, Q4_K_M, 12
    ("acronym", re.compile(r"\b[A-Z]{2,}\b")),                # API, CPU, AWS, SL
    ("camel", re.compile(r"\b[a-z]{2,}[A-Z]\w*\b")),          # pgVector, iOS
    ("camel", re.compile(r"\b[A-Z][a-z]+[A-Z]\w*\b")),        # PowerShell, Postgres
    ("handle", re.compile(r"[@#][\w-]{2,}")),
]

MARK = "⟦%d⟧"


def load_whitelist(path=None):
    """Lista blanca: una entrada por línea, # comenta. Nombres propios, marcas, jerga."""
    if path is None:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(here, "protegidos.txt")
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def _spans(text, whitelist):
    found = []
    for _, rx in PATTERNS:
        for m in rx.finditer(text):
            found.append((m.start(), m.end(), m.group(0)))
    for word in whitelist:
        for m in re.finditer(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text):
            found.append((m.start(), m.end(), m.group(0)))
    # sin solapamientos: gana el más largo que empieza antes
    found.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    chosen, last_end = [], -1
    for s, e, tok in found:
        if s >= last_end:
            chosen.append((s, e, tok))
            last_end = e
    return chosen


def mask(text, whitelist=None):
    """Devuelve (texto_con_marcadores, mapa) donde mapa es {marcador: original}."""
    whitelist = load_whitelist() if whitelist is None else whitelist
    spans = _spans(text, whitelist)
    if not spans:
        return text, {}
    out, prev, mapping = [], 0, {}
    for i, (s, e, tok) in enumerate(spans, 1):
        mark = MARK % i
        out.append(text[prev:s])
        out.append(mark)
        mapping[mark] = tok
        prev = e
    out.append(text[prev:])
    return "".join(out), mapping


def unmask(text, mapping):
    """Restaura los marcadores. Devuelve (texto, faltan) donde faltan son marcadores ausentes."""
    missing = [m for m in mapping if m not in text]
    for mark, original in mapping.items():
        text = text.replace(mark, original)
    return text, missing


def protected_tokens(mapping):
    return set(mapping.values())
