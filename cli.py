#!/usr/bin/env python3
"""corrector-ca — corrige texto catalán generado por un LLM y verifica el daño.

Uso:
  python cli.py "text a corregir"
  python cli.py -f texto.txt
  cat texto.txt | python cli.py
  python cli.py -f texto.txt --json
  python cli.py -f texto.txt --check          # solo verificación (sin modelo)
  python cli.py -f texto.txt --out corregido.txt
  python cli.py --test                        # comprueba la configuración

Códigos de salida: 0 corregido · 2 corregido con dudas · 1 bloqueado (texto original intacto)
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corrector_ca import client  # noqa: E402
from corrector_ca.correct import corregir  # noqa: E402


def leer_texto(args):
    if args.archivo:
        try:
            with open(args.archivo, encoding="utf-8") as fh:
                return fh.read()
        except OSError as e:
            print("No se pudo leer %s: %s" % (args.archivo, e), file=sys.stderr)
            sys.exit(1)
    if args.texto:
        return " ".join(args.texto)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def main():
    p = argparse.ArgumentParser(description="Corrector de catalán para salidas de LLM")
    p.add_argument("texto", nargs="*", help="texto a corregir")
    p.add_argument("-f", "--archivo", help="fichero de entrada (UTF-8)")
    p.add_argument("-o", "--out", help="escribir el resultado en un fichero")
    p.add_argument("--json", action="store_true", help="salida JSON completa")
    p.add_argument("--check", action="store_true", help="solo verificador, sin llamar al modelo")
    p.add_argument("--force-lang", action="store_true", help="corregir aunque no parezca catalán")
    p.add_argument("--test", action="store_true", help="probar la configuración del modelo")
    a = p.parse_args()

    if a.test:
        cfg = client.config()
        print("endpoint :", cfg["base_url"])
        print("modelo   :", cfg["model"] or "(sin definir)")
        print("clave    :", "definida (%d caracteres)" % len(cfg["api_key"]) if cfg["api_key"] else "FALTA")
        try:
            out = client.chat("La importancia de la formació és clara.", cfg=cfg)
            print("prueba   :", out)
            return 0 if "importància" in out or "importancia" not in out else 2
        except RuntimeError as e:
            print("error    :", e)
            return 1

    texto = leer_texto(a)
    if not texto.strip():
        p.print_help()
        return 1

    res = corregir(texto, solo_verificar=a.check, forzar_idioma=a.force_lang)

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(res["corregido"])
        sys.stdout.flush()  # que el texto salga antes que los avisos (que van a stderr)
        if res["avisos"]:
            print("\n--- avisos ---", file=sys.stderr)
            for av in res["avisos"]:
                print("· " + av, file=sys.stderr)
        if res["cambios"]:
            print("\n--- cambios (%d) ---" % len(res["cambios"]), file=sys.stderr)
            for c in res["cambios"]:
                print("· %r → %r" % (c["de"], c["a"]), file=sys.stderr)

    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(res["corregido"])
        print("\nescrito en %s" % a.out, file=sys.stderr)

    return res["estado"]


if __name__ == "__main__":
    sys.exit(main())
