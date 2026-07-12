"""
Corrida de evaluación con Golden Cases.

Para cada golden case:
1. Ejecuta la consulta a través del agente orquestador (sesión aislada por caso).
2. Evalúa la respuesta con el LLM-as-a-Judge (judge.py) contra los criterios.
3. Acumula métricas y al final imprime un reporte con la tasa de aprobación
   y el puntaje promedio.

Requisitos:
    - OPENAI_API_KEY en .env (agente + juez).
    - Servidor MCP corriendo:  python mcp_server/server.py
    - NeonDB y Qdrant accesibles (para los casos de MCP y RAG).

Uso:
    python -m evaluations.run_golden_cases

Las métricas ("métricas obtenidas") son justamente las que pide mostrar la
defensa oral.
"""

import asyncio
import logging

from google.genai import types
from google.adk.runners import Runner

from app.agent import root_agent
from app.sessions.session_manager import APP_NAME, crear_session_service, crear_sesion
from evaluations.golden_cases import GOLDEN_CASES
from evaluations.judge import evaluar_respuesta


# Observabilidad básica: log estructurado de cada paso de la evaluación.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("evaluacion")


async def _responder(runner: Runner, user_id: str, session_id: str, pregunta: str) -> str:
    mensaje = types.Content(role="user", parts=[types.Part(text=pregunta)])
    respuesta = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=mensaje,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            respuesta = event.content.parts[0].text or ""
    return respuesta


async def evaluar_caso(session_service, runner: Runner, caso: dict) -> dict:
    """Ejecuta un golden case y devuelve su resultado con veredicto."""
    user_id = f"eval_{caso['id']}"
    session_id = f"sesion_{caso['id']}"
    await crear_sesion(session_service, APP_NAME, user_id, session_id)

    logger.info("Ejecutando caso '%s' (%s)", caso["id"], caso["categoria"])
    respuesta = await _responder(runner, user_id, session_id, caso["pregunta"])

    veredicto = evaluar_respuesta(
        pregunta=caso["pregunta"],
        respuesta=respuesta,
        criterios=caso["criterios"],
    )
    logger.info(
        "Caso '%s' -> %s (score %s)",
        caso["id"],
        veredicto["veredicto"],
        veredicto["score"],
    )

    return {
        "id": caso["id"],
        "categoria": caso["categoria"],
        "pregunta": caso["pregunta"],
        "respuesta": respuesta,
        **veredicto,
    }


def _imprimir_reporte(resultados: list[dict]) -> None:
    total = len(resultados)
    aprobados = sum(1 for r in resultados if r["veredicto"] == "PASS")
    promedio = (sum(r["score"] for r in resultados) / total) if total else 0.0

    print("\n" + "=" * 78)
    print("REPORTE DE EVALUACIÓN — GOLDEN CASES")
    print("=" * 78)
    for r in resultados:
        marca = "PASS" if r["veredicto"] == "PASS" else "FAIL"
        print(f"[{marca}] {r['id']:<28} score {r['score']}/10  ({r['categoria']})")
        print(f"        {r['justificacion']}")
    print("-" * 78)
    print(f"Casos evaluados : {total}")
    print(f"Aprobados       : {aprobados}/{total}")
    print(f"Tasa de aprobación : {(aprobados / total * 100 if total else 0):.1f}%")
    print(f"Puntaje promedio   : {promedio:.2f}/10")
    print("=" * 78)


async def main() -> None:
    session_service = await crear_session_service()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    resultados = []
    for caso in GOLDEN_CASES:
        try:
            resultados.append(await evaluar_caso(session_service, runner, caso))
        except Exception as exc:  # noqa: BLE001
            logger.error("Caso '%s' falló al ejecutarse: %s", caso["id"], exc)
            resultados.append(
                {
                    "id": caso["id"],
                    "categoria": caso["categoria"],
                    "pregunta": caso["pregunta"],
                    "respuesta": "",
                    "veredicto": "FAIL",
                    "score": 0,
                    "justificacion": f"Error de ejecución: {exc}",
                    "criterios_cumplidos": [],
                }
            )

    _imprimir_reporte(resultados)


if __name__ == "__main__":
    asyncio.run(main())
