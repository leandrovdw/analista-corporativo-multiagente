"""
LLM-as-a-Judge: juez semántico de respuestas.

En lugar de comparar la respuesta del agente contra un texto exacto (imposible
con un LLM, porque la redacción varía), le pedimos a un modelo que actúe como
EVALUADOR: recibe la pregunta, la respuesta del agente y los criterios que debe
cumplir, y emite un veredicto estructurado (PASS/FAIL + puntaje + justificación).

Diseño pensado para testear:
- `construir_prompt_juez` y `parsear_veredicto` son funciones puras (sin red),
  y por eso se prueban de forma aislada en tests/test_judge.py.
- Solo `evaluar_respuesta` hace la llamada real a OpenAI.
"""

from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


SYSTEM_PROMPT = (
    "Sos un evaluador riguroso de un asistente corporativo de compras. "
    "Recibís una PREGUNTA, la RESPUESTA del asistente y una lista de CRITERIOS. "
    "Tu tarea es decidir si la respuesta cumple TODOS los criterios. "
    "Devolvés EXCLUSIVAMENTE un objeto JSON válido, sin texto adicional, con las claves: "
    '"veredicto" (string: "PASS" o "FAIL"), '
    '"score" (entero de 0 a 10), '
    '"justificacion" (string breve), '
    '"criterios_cumplidos" (lista de booleanos, uno por criterio, en orden).'
)


def _modelo_juez() -> str:
    """Nombre de modelo para el SDK de OpenAI (sin el prefijo 'openai/' de LiteLLM)."""
    modelo = os.getenv("MODEL_NAME", "gpt-4o-mini")
    if modelo.startswith("openai/"):
        return modelo.split("/", 1)[1]
    return modelo


def construir_prompt_juez(
    pregunta: str,
    respuesta: str,
    criterios: list[str],
) -> str:
    """Construye el prompt de usuario para el juez. Función pura (testeable)."""
    criterios_texto = "\n".join(
        f"{i}. {c}" for i, c in enumerate(criterios, start=1)
    )
    return (
        f"PREGUNTA:\n{pregunta}\n\n"
        f"RESPUESTA DEL ASISTENTE:\n{respuesta}\n\n"
        f"CRITERIOS A VERIFICAR:\n{criterios_texto}\n\n"
        "Evaluá y devolvé el JSON del veredicto."
    )


def parsear_veredicto(texto: str) -> dict:
    """
    Extrae y normaliza el veredicto JSON devuelto por el juez. Función pura.

    Es tolerante: acepta JSON "pelado" o embebido en un bloque de código, y ante
    cualquier problema devuelve un veredicto FAIL con la justificación del error,
    para que la evaluación nunca se caiga por un formato inesperado.
    """
    if not texto:
        return _fallback("El juez no devolvió contenido.")

    # Quita cercos de código Markdown si los hubiera.
    limpio = texto.strip()
    limpio = re.sub(r"^```(?:json)?", "", limpio).strip()
    limpio = re.sub(r"```$", "", limpio).strip()

    # Si hay texto alrededor, nos quedamos con el primer objeto {...}.
    if not limpio.startswith("{"):
        match = re.search(r"\{.*\}", limpio, re.DOTALL)
        if match:
            limpio = match.group(0)

    try:
        data = json.loads(limpio)
    except json.JSONDecodeError:
        return _fallback(f"No se pudo parsear el JSON del juez: {texto[:120]!r}")

    veredicto = str(data.get("veredicto", "FAIL")).upper()
    if veredicto not in ("PASS", "FAIL"):
        veredicto = "FAIL"

    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(10, score))

    return {
        "veredicto": veredicto,
        "score": score,
        "justificacion": str(data.get("justificacion", "")),
        "criterios_cumplidos": data.get("criterios_cumplidos", []),
    }


def _fallback(motivo: str) -> dict:
    return {
        "veredicto": "FAIL",
        "score": 0,
        "justificacion": motivo,
        "criterios_cumplidos": [],
    }


def evaluar_respuesta(
    pregunta: str,
    respuesta: str,
    criterios: list[str],
    client: OpenAI | None = None,
) -> dict:
    """
    Evalúa una respuesta con el LLM-as-a-Judge.

    Args:
        pregunta / respuesta / criterios: el caso a evaluar.
        client: cliente OpenAI opcional (útil para inyectar uno en tests).

    Returns:
        Veredicto normalizado (ver parsear_veredicto).
    """
    client = client or OpenAI()

    completion = client.chat.completions.create(
        model=_modelo_juez(),
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": construir_prompt_juez(pregunta, respuesta, criterios),
            },
        ],
    )

    contenido = completion.choices[0].message.content or ""
    return parsear_veredicto(contenido)
