"""
Punto de entrada del sistema.

ADK (y `adk web`) buscan una variable llamada `root_agent` para saber qué agente
ejecutar. Acá simplemente la re-exportamos desde el orquestador, que es el agente
principal que coordina a todos los especialistas.

Es decir: toda consulta entra por `root_agent` -> el orquestador decide a qué
subagente delegar (RAG, Valor Módulo o Personal) y arma la respuesta final.
"""

from app.agents.orchestrator import root_agent

__all__ = ["root_agent"]
