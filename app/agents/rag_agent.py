"""
Agente RAG.

Especialista en recuperación de documentación corporativa.
Utiliza Qdrant + OpenAI embeddings mediante la tool consultar_documentacion_corporativa.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from app.prompts.rag_prompt import RAG_AGENT_INSTRUCTION
from app.tools.rag_tools import consultar_documentacion_corporativa


load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")


modelo_openai = LiteLlm(
    model=MODEL_NAME,
    api_key=os.getenv("OPENAI_API_KEY"),
)


rag_agent = Agent(
    name="agente_rag_documental",
    model=modelo_openai,
    instruction=RAG_AGENT_INSTRUCTION,
    description=(
        "Agente especializado en consultar documentación corporativa "
        "mediante RAG sobre Qdrant."
    ),
    tools=[
        consultar_documentacion_corporativa,
    ],
)