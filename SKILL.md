---
name: corrector-ca
description: "Use when delivering Catalan text: fix LLM output with damage checks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [catalan, ortografia, gramatica, guardrail, llm, post-proceso]
    category: productivity
---

# corrector-ca — corregir texto catalán antes de entregarlo

## Cuándo usarla

Siempre que vayas a entregar al usuario un texto **en catalán** que has generado tú (informe, correo,
documento, respuesta larga), y siempre que alguien pida «un corrector para LLMs» o un guardarraíl
ortográfico. No para chat efímero ni para código.

## Cómo se usa

```bash
python cli.py -f borrador.md --json
```

- `estado 0` → entrega `corregido` y menciona en una línea qué cambió.
- `estado 2` → entrega `corregido` **y** señala los avisos para que el usuario decida.
- `estado 1` → entrega `original` tal cual y explica qué se rechazó y por qué.

Nunca sustituyas texto en silencio: los cambios se enseñan.

## Reglas que no se negocian

- **No inventes una corrección**: si el modelo no responde, se entrega el original marcado (fail-open).
- **Antes de corregir, comprueba el idioma.** Pasar texto castellano por reglas catalanas inventa errores;
  el script ya lo detecta, no lo fuerces con `--force-lang` salvo que el usuario lo pida.
- **Añade a `protegidos.txt`** los nombres propios, marcas, siglas y jerga del proyecto antes de usarlo en
  serio: es la lista de lo que el corrector no puede tocar.
- **No uses LanguageTool como corrector automático.** Medido: altera 6 de 10 frases correctas con jerga
  técnica. Si se quiere comprobación determinista, que sea solo de daño, nunca de sustitución.
- **Streaming**: si el texto se muestra en tiempo real, no hay corrección posible sin bufferizar. Decide
  antes: o se corrige lo que se guarda/publica, o se pierde el token a token.

## Verificación antes de decir que funciona

```bash
python run_tests.py
```

Exige 90 % de aciertos y 0 daño sobre las 34 frases. Es el mismo banco que se usó para descartar el
corrector determinista; sirve para comparar modelos cambiando `CORRECTOR_MODEL`.

## Fricción conocida

La clave del modelo es el único paso incómodo (`.env`). Si el usuario no quiere claves, la alternativa es
Ollama local (`CORRECTOR_BASE_URL=http://localhost:11434/v1`), a cambio de calidad y de tener el modelo
descargado.
