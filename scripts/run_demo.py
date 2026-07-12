"""
Demo de gestión de sesiones y uso de state.

Ejecuta una conversación de DOS turnos sobre la MISMA sesión para demostrar que:

1. El sistema escribe datos estructurados en el STATE (monto, objeto de compra).
2. Esos datos PERSISTEN entre turnos.
3. En el segundo turno, al no mencionarse el objeto, el sistema lo conserva
   desde el state y solo actualiza el monto.

Caso demostrado:
    Turno 1: "Necesito comprar notebooks por $15.000.000."
    Turno 2: "¿Y si fueran $80.000.000?"   -> objeto sigue siendo "notebooks"

Requisitos para el turno con agente (respuesta del LLM):
    - OPENAI_API_KEY en .env
    - Servidor MCP corriendo:  python mcp_server/server.py
    - NeonDB y Qdrant accesibles

Uso:
    python -m scripts.run_demo

La parte de STATE (escritura/lectura entre turnos) se imprime SIEMPRE, aunque
el agente falle por falta de servicios, porque es el punto central de la demo.
"""

import asyncio

from google.genai import types

from google.adk.runners import Runner

from app.agent import root_agent
from app.sessions.session_manager import (
    APP_NAME,
    USER_ID,
    SESSION_ID,
    crear_session_service,
    crear_sesion,
)
from app.sessions.state_utils import actualizar_state_desde_consulta


CONSULTAS = [
    "Necesito comprar notebooks por $15.000.000. ¿Qué procedimiento corresponde?",
    "¿Y si fueran $80.000.000?",
]


def _imprimir_state(titulo: str, state: dict) -> None:
    print(f"\n[STATE] {titulo}")
    for clave in (
        "objeto_ultima_consulta",
        "monto_ultima_consulta",
        "guardrail_activado",
    ):
        if clave in state:
            print(f"        {clave} = {state[clave]}")


async def _ejecutar_agente(runner: Runner, consulta: str) -> str:
    """Corre un turno del agente y devuelve el texto de la respuesta final."""
    mensaje = types.Content(role="user", parts=[types.Part(text=consulta)])

    respuesta_final = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=mensaje,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            respuesta_final = event.content.parts[0].text or ""

    return respuesta_final


async def main() -> None:
    session_service = await crear_session_service()
    await crear_sesion(session_service)

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    for i, consulta in enumerate(CONSULTAS, start=1):
        print("=" * 78)
        print(f"TURNO {i}  |  Usuario: {consulta}")
        print("=" * 78)

        # 1) Actualizamos el STATE a partir de la consulta (escritura vía state_delta).
        state = await actualizar_state_desde_consulta(
            session_service=session_service,
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            consulta=consulta,
        )
        _imprimir_state("Después de actualizar desde la consulta:", state)

        # 2) Ejecutamos el agente (requiere servicios externos).
        try:
            respuesta = await _ejecutar_agente(runner, consulta)
            print("\n[AGENTE] Respuesta:")
            print(respuesta or "(sin respuesta)")
        except Exception as exc:  # noqa: BLE001
            print("\n[AGENTE] No se pudo ejecutar el agente en este entorno.")
            print(f"         Motivo: {type(exc).__name__}: {exc}")
            print("         (La demostración de STATE de arriba es válida igual.)")

    print("\n" + "=" * 78)
    print("Observá que en el TURNO 2 'objeto_ultima_consulta' sigue siendo")
    print("'notebooks' aunque el usuario no lo repitió: eso es el STATE en acción.")
    print("=" * 78)


if __name__ == "__main__":
    asyncio.run(main())
