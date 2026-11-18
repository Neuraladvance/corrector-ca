# corrector-ca

Corrector de catalán para texto generado por un LLM: **corrige después de generar** y verifica que no ha
tocado nada que no debía.

```
antes:  El govern ha de fer frente a la sequera. Els indicadors economics van millorar al març.
        Hem migrat la base de dades a PostgreSQL 17 amb pgvector.

después: El govern ha de fer front a la sequera. Els indicadors econòmics van millorar al març.
         Hem migrat la base de dades a PostgreSQL 17 amb pgvector.
```

`pgvector`, `npm`, `Sapiens-7B` o `eu-south-2` salen intactos: esos fragmentos se enmascaran antes de
enviar el texto y se restauran después, así que el modelo ni los ve.

## Por qué existe

Los correctores deterministas (LanguageTool y compañía) están escritos para errores humanos y **destrozan
el texto técnico**: en una batería de 34 frases convirtieron `pgvector` en `pg. vector`, `npm install` en
`NPM instal`, `AWS eu-south-2` en `eu-sota-2` y `fer frente` en `fer França`, alterando 6 de 10 frases que
ya estaban bien. Un LLM corrigiendo con instrucciones estrictas acertó 24 de 24 sin tocar ninguna correcta.
Este proyecto envuelve esa segunda vía con la protección que le faltaba.

## Instalación (sin dependencias)

Solo necesita Python 3.9 o superior. Nada de `pip install`.

```bash
git clone https://github.com/Neuraladvance/corrector-ca.git
cd corrector-ca
cp .env.example .env      # pon tu clave y el modelo
python cli.py --test      # comprueba que responde
```

Sin instalar nada, con `uv`:

```bash
uvx --from git+https://github.com/Neuraladvance/corrector-ca corrector-ca "Els nens va anar al museu."
```

## Uso

```bash
python cli.py "La importancia de la formació és clara."
python cli.py -f informe.md
cat informe.md | python cli.py
python cli.py -f informe.md --json          # original, corregido, cambios, avisos, estado
python cli.py -f informe.md -o limpio.md
python cli.py -f informe.md --check         # solo verificador, sin llamar al modelo
```

Códigos de salida: **0** corregido · **2** corregido con dudas (mirar avisos) · **1** bloqueado, se
devuelve el original intacto.

Ese es el contrato para integrarlo en cualquier app: si sale 1, no publiques; si sale 2, revisa.

## Cómo funciona

1. **Enmascara** código, URLs, emails, rutas, cifras, siglas, CamelCase y lo que pongas en `protegidos.txt`.
2. **Corrige** con el modelo: solo ortografía, acentos, gramática y castellanismos. Instrucción explícita
   de no reescribir.
3. **Restaura** los fragmentos protegidos y comprueba que están todos.
4. **Verifica el daño**: reescritura excesiva (>35 % de palabras avisa, >60 % bloquea), longitud, número
   de frases y fragmentos perdidos.
5. **Fail-open**: ante cualquier duda grave devuelve el original, nunca una corrección inventada.

## Batería de pruebas

```bash
python run_tests.py --verbose
```

34 frases: 24 con error plantado y 10 correctas con nombres propios, comandos y jerga. Exige **90 % de
aciertos y 0 daño** para darse por apto. Sirve para comparar modelos: cambia `CORRECTOR_MODEL` y repite.

## Limitaciones honestas

- Necesita un modelo con buena catalana. Uno flojo corrige mal y el verificador no siempre lo detecta.
- Añade una llamada por texto (1-3 s) y **no corrige en streaming**: hay que acumular la respuesta.
- El verificador mide daño estructural (qué cambió y cuánto), no si el resultado es semánticamente fiel.
- No incluye diccionario ni reglas de terceros: no hay dependencias con licencias contagiosas.

## Licencia

MIT. Ver `LICENSE`.
