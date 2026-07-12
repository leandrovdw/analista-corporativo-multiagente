"""
Tests de gestión de state y sesiones.

Demuestran el punto central de la consigna "uso de state":
- extracción de monto y objeto desde el texto del usuario;
- persistencia del state entre turnos de una MISMA sesión.

Las funciones async se ejecutan con asyncio.run() para no depender de plugins.
"""

import asyncio

from app.sessions.session_manager import (
    APP_NAME,
    USER_ID,
    SESSION_ID,
    crear_session_service,
    crear_sesion,
)
from app.sessions.state_utils import (
    actualizar_state_desde_consulta,
    extraer_monto,
    extraer_objeto,
)


def test_extraer_monto():
    assert extraer_monto("Necesito comprar notebooks por $15.000.000") == 15_000_000
    assert extraer_monto("¿Y si fueran $80.000.000?") == 80_000_000
    assert extraer_monto("sin monto acá") is None


def test_extraer_objeto():
    assert extraer_objeto("Necesito comprar notebooks por $15.000.000") == "notebooks"
    # Sin "... por $", no se detecta objeto (y por eso persiste el anterior).
    assert extraer_objeto("¿Y si fueran $80.000.000?") is None


def test_state_persiste_entre_turnos():
    """
    Turno 1 fija objeto='notebooks' y monto=15.000.000.
    Turno 2 solo cambia el monto; el objeto DEBE persistir desde el state.
    """

    async def _run():
        session_service = await crear_session_service()
        await crear_sesion(session_service)

        estado_1 = await actualizar_state_desde_consulta(
            session_service=session_service,
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            consulta="Necesito comprar notebooks por $15.000.000.",
        )
        assert estado_1["monto_ultima_consulta"] == 15_000_000
        assert estado_1["objeto_ultima_consulta"] == "notebooks"

        estado_2 = await actualizar_state_desde_consulta(
            session_service=session_service,
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            consulta="¿Y si fueran $80.000.000?",
        )
        assert estado_2["monto_ultima_consulta"] == 80_000_000
        # El objeto se conserva del turno anterior: esto es el STATE en acción.
        assert estado_2["objeto_ultima_consulta"] == "notebooks"

    asyncio.run(_run())
