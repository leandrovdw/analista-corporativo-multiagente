"""
Manejador simple de sesiones para el TP.

En esta primera etapa usamos InMemorySessionService de ADK.
Esto significa que la sesión vive mientras el programa está corriendo.

Más adelante, cuando conectemos NeonDB mediante MCP, vamos a persistir:
- consultas del usuario,
- respuestas del agente,
- monto detectado,
- procedimiento recomendado,
- valor módulo utilizado,
- trazas de ejecución.

Por ahora queremos demostrar el concepto de sesión y state sin sumar complejidad.
"""

from google.adk.sessions import InMemorySessionService


APP_NAME = "analista_corporativo_multiagente"
USER_ID = "usuario_demo"
SESSION_ID = "sesion_demo_001"


async def crear_session_service():
    """
    Crea el servicio de sesiones en memoria.

    ADK utiliza este servicio para conservar el historial conversacional
    y permitir que un agente mantenga contexto entre mensajes.
    """
    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={
            "monto_ultima_consulta": None,
            "objeto_ultima_consulta": None,
            "procedimiento_estimado": None,
            "valor_modulo": None,
            "cantidad_modulos": None,
        },
    )

    return session_service