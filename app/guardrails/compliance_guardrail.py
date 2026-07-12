"""
Guardrail de compliance (seguridad mínima) para el Analista Corporativo.

Se implementa como un `before_model_callback` de ADK: se ejecuta ANTES de cada
llamada al modelo del agente al que está asociado. Si detecta un pedido que
viola la política de compras (por ejemplo, fraccionar una contratación para
evadir el procedimiento que corresponde), corta la ejecución y devuelve una
respuesta institucional, sin que el modelo llegue a responder.

¿Por qué un callback y no solo instrucciones en el prompt?
- Las instrucciones del prompt son "blandas": el modelo puede ignorarlas.
- El callback es una barrera determinística en código: si se dispara,
  el modelo NO se ejecuta. Es la garantía dura del guardrail.

Referencia ADK: Agent(before_model_callback=...). Devolver un LlmResponse
desde el callback cortocircuita la llamada al modelo.
"""

from __future__ import annotations

import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types


# ---------------------------------------------------------------------------
# Definición de reglas de compliance como plantillas (templates)
#
# Cada regla tiene:
# - nombre: identificador legible para trazabilidad / logs.
# - patron: expresión regular que detecta la intención prohibida.
# - mensaje: respuesta institucional que se devuelve si la regla se dispara.
#
# Tener las reglas como datos (y no hardcodeadas en un if gigante) permite
# agregar nuevas reglas sin tocar la lógica, y usarlas también en los tests.
# ---------------------------------------------------------------------------

REGLAS_COMPLIANCE: list[dict] = [
    {
        "nombre": "fraccionamiento",
        # Detecta intención de dividir/partir/fraccionar una compra para
        # eludir un procedimiento o un umbral.
        "patron": re.compile(
            r"(fraccion\w*)"
            r"|((dividir|partir|separar|split\w*)\s+(la\s+)?(compra|contrataci[oó]n|monto|adquisici[oó]n))"
            r"|((evitar|eludir|esquivar|saltear|evadir)\s+(la\s+)?(licitaci[oó]n|el\s+procedimiento|el\s+concurso|el\s+umbral|los\s+controles))",
            re.IGNORECASE,
        ),
        "mensaje": (
            "No puedo asistir con el fraccionamiento de contrataciones ni con la "
            "evasión del procedimiento que corresponde. El fraccionamiento indebido "
            "—dividir una compra en partes para eludir el umbral o el procedimiento "
            "aplicable— está prohibido por la normativa de compras de PALERMIA S.A.\n\n"
            "Si me indicás el objeto y el monto total real de la contratación, puedo "
            "ayudarte a determinar el procedimiento correcto que corresponde aplicar."
        ),
    },
    {
        "nombre": "revelar_instrucciones",
        # Guardrail básico anti prompt-injection: pedidos de revelar el prompt
        # interno o ignorar las reglas del sistema.
        "patron": re.compile(
            r"(ignor\w*\s+(tus|las)\s+(instrucciones|reglas))"
            r"|(mostr\w*|revel\w*|decime|dame)\s+(tu\s+)?(prompt|instrucciones\s+del\s+sistema|system\s+prompt)",
            re.IGNORECASE,
        ),
        "mensaje": (
            "No puedo revelar mis instrucciones internas ni operar por fuera de la "
            "normativa de compras. Con gusto respondo consultas sobre procedimientos, "
            "Valor Módulo o normativa institucional."
        ),
    },
]


def evaluar_texto(texto: str) -> dict | None:
    """
    Evalúa un texto contra las reglas de compliance.

    Función pura y sin dependencias de ADK: por eso puede probarse de forma
    aislada en los tests. Es el corazón del guardrail.

    Args:
        texto: mensaje del usuario a inspeccionar.

    Returns:
        - La regla que se disparó (dict con nombre y mensaje), o
        - None si el texto no viola ninguna regla.
    """

    if not texto:
        return None

    for regla in REGLAS_COMPLIANCE:
        if regla["patron"].search(texto):
            return regla

    return None


def _extraer_texto_usuario(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> str:
    """
    Obtiene el texto del usuario a inspeccionar.

    Prioriza `user_content` (el mensaje que originó la invocación) y cae al
    último contenido del `llm_request` como respaldo.
    """

    partes: list[str] = []

    user_content = getattr(callback_context, "user_content", None)
    if user_content and getattr(user_content, "parts", None):
        for parte in user_content.parts:
            if getattr(parte, "text", None):
                partes.append(parte.text)

    if not partes and llm_request.contents:
        ultimo = llm_request.contents[-1]
        for parte in getattr(ultimo, "parts", []) or []:
            if getattr(parte, "text", None):
                partes.append(parte.text)

    return " ".join(partes)


def compliance_guardrail(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    """
    Callback `before_model_callback` de ADK.

    Se ejecuta antes de cada llamada al modelo del agente asociado.

    - Si el mensaje del usuario viola una regla de compliance, devuelve un
      LlmResponse con la respuesta institucional -> el modelo NO se ejecuta.
    - Si no hay violación, devuelve None -> la ejecución sigue con normalidad.
    """

    texto = _extraer_texto_usuario(callback_context, llm_request)
    regla = evaluar_texto(texto)

    if regla is None:
        return None

    # Dejamos traza del bloqueo en el state de la sesión (observabilidad básica).
    try:
        callback_context.state["guardrail_activado"] = regla["nombre"]
    except Exception:
        # El state puede no estar disponible en algunos contextos; no es crítico.
        pass

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=regla["mensaje"])],
        )
    )
