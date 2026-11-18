#!/usr/bin/env python3
"""Batería de 34 frases: 24 con error plantado + 10 correctas.

Mide dos cosas, y la segunda importa tanto como la primera:
  - aciertos: el error desaparece y aparece la forma correcta
  - daño: en las frases que ya estaban bien, el corrector no debe tocar NADA

Uso:
  python run_tests.py                # todos los casos
  python run_tests.py --limite 8     # primeros 8
  python run_tests.py --verbose
Devuelve 0 si aciertos >= 90 % y daño == 0; 1 en caso contrario.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corrector_ca.correct import corregir  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))


def puntua(caso, salida):
    if caso["limpia"]:
        return salida.strip() == caso["texto"].strip()
    return (all(p not in salida for p in caso["prohibido"])
            and all(o in salida for o in caso["obligatorio"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limite", type=int, default=0)
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()

    casos = json.load(open(os.path.join(AQUI, "tests", "frases.json"), encoding="utf-8"))
    if a.limite:
        casos = casos[: a.limite]

    ok_err = tot_err = ok_clean = tot_clean = 0
    fallos = []

    for i, caso in enumerate(casos, 1):
        res = corregir(caso["texto"], forzar_idioma=True)
        salida = res["corregido"]
        bien = puntua(caso, salida)
        if caso["limpia"]:
            tot_clean += 1
            ok_clean += bien
        else:
            tot_err += 1
            ok_err += bien
        if not bien:
            fallos.append((i, caso, salida, res["estado"], res["avisos"]))
        if a.verbose:
            marca = "ok " if bien else "FALLO"
            print("%2d %s [%s] %s" % (i, marca, caso["tipo"], salida))
            if res["cambios"]:
                print("     cambios:", res["cambios"][:4])

    print("\n== resultado ==")
    print("errores corregidos : %d/%d" % (ok_err, tot_err))
    print("frases intactas    : %d/%d" % (ok_clean, tot_clean))
    if fallos:
        print("\n-- fallos --")
        for i, caso, salida, estado, avisos in fallos:
            print("%2d [%s] %s\n   → %s\n   estado=%s avisos=%s"
                  % (i, caso["tipo"], caso["texto"], salida, estado, avisos))
    pct = 100.0 * ok_err / tot_err if tot_err else 0
    bien = pct >= 90 and ok_clean == tot_clean
    print("\n%s" % ("APTO" if bien else "NO APTO (exige 90% de aciertos y 0 daño)"))
    return 0 if bien else 1


if __name__ == "__main__":
    sys.exit(main())
