"""
Gestión de sesiones del Analista Corporativo.

Una SESIÓN agrupa la interacción de un usuario con el sistema y contiene:
- el historial de eventos (mensajes y llamadas a tools),
- el STATE: un diccionario estructurado de datos que persiste entre turnos.

Acá usamos `InMemorySessionService` de ADK: las sesiones viven mientras el
proceso está corriendo. Es suficiente para el TP y para la defensa; para
producción se reemplazaría por un servicio persistente (p. ej. sobre NeonDB)
sin cambiar el resto del código, porque todos hablan contra la misma interfaz
`BaseSessionService`.

Diferencia clave (útil para la defensa oral):
- Historial  -> todos los mensajes en texto libre.
- State      -> datos puntuales (monto, objeto, valor módulo...) que el
                programa lee y escribe de forma explícita y confiable.
"""

from google.adk.sessions import InMemorySessionService


APP_NAME = "analista_corporativo_multiagente"
USER_ID = "usuario_demo"
SESSION_ID = "sesion_demo_001"


def estado_inicial() -> dict:
    """
    Devuelve el state inicial de una sesión de análisis de compras.

    Estas claves representan la "ficha de datos" de la contratación que el
    sistema va completando a lo largo de la conversación.
    """
    return {
        "monto_ultima_consulta": None,
        "objeto_ultima_consulta": None,
        "procedimiento_estimado": None,
        "valor_modulo": None,
        "cantidad_modulos": None,
    }


async def crear_session_service() -> InMemorySessionService:
    """
    Crea el servicio de sesiones en memoria (sin crear ninguna sesión todavía).
    """
    return InMemorySessionService()


async def crear_sesion(
    session_service: InMemorySessionService,
    app_name: str = APP_NAME,
    user_id: str = USER_ID,
    session_id: str = SESSION_ID,
):
    """
    Crea una sesión con el state inicial.

    Devuelve la sesión creada. Es idempotente a nivel de demo: siempre arranca
    con `estado_inicial()`.
    """
    return await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=estado_inicial(),
    )
