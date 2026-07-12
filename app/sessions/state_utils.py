"""
Utilidades para trabajar con state en ADK.

Importante:
No modificamos session.state directamente.
En ADK, la forma correcta es crear un Event con EventActions(state_delta=...)
y anexarlo a la sesión usando session_service.append_event().
"""

import re
import time

from google.adk.events import Event, EventActions


def extraer_monto(texto: str):
    patron = r"\$?\s?([\d\.]+)"
    coincidencias = re.findall(patron, texto)

    for valor in coincidencias:
        valor_limpio = valor.replace(".", "")

        if valor_limpio.isdigit():
            numero = int(valor_limpio)

            if numero >= 1000:
                return numero

    return None


def extraer_objeto(texto: str):
    texto_lower = texto.lower()

    patron_comprar = r"comprar\s+(.+?)\s+por\s+\$?"
    match = re.search(patron_comprar, texto_lower)

    if match:
        return match.group(1).strip()

    patron_fueran = r"fueran\s+(.+?)\s+por\s+\$?"
    match = re.search(patron_fueran, texto_lower)

    if match:
        return match.group(1).strip()

    return None


async def actualizar_state_desde_consulta(
    session_service,
    app_name: str,
    user_id: str,
    session_id: str,
    consulta: str,
):
    """
    Actualiza el state de la sesión usando EventActions(state_delta).

    Esto permite que ADK registre formalmente el cambio de estado.
    """

    session = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    monto = extraer_monto(consulta)
    objeto = extraer_objeto(consulta)

    state_delta = {}

    if monto is not None:
        state_delta["monto_ultima_consulta"] = monto

    if objeto is not None:
        state_delta["objeto_ultima_consulta"] = objeto

    if not state_delta:
        return session.state

    evento_state = Event(
        invocation_id=f"state_update_{int(time.time())}",
        author="system",
        actions=EventActions(state_delta=state_delta),
        timestamp=time.time(),
    )

    await session_service.append_event(session, evento_state)

    session_actualizada = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    return session_actualizada.state