"""Corrector de catalán para texto generado por LLM.

Post-proceso: recibe un texto ya generado, lo corrige con un modelo y verifica
que no ha tocado nada que no debía (código, URLs, cifras, nombres propios).
"""

__version__ = "0.1.0"
