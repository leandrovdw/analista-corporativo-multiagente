"""
Orquestador principal de PALERMIA S.A.

Los especialistas se invocan como AgentTool:
- siguen siendo agentes;
- conservan sus propias tools y prompts;
- devuelven el resultado al orquestador;
- no toman el control permanente de la conversación.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from app.agents.rag_agent import rag_agent
from app.agents.valor_modulo_agent import valor_modulo_agent
from app.agents.personal_agent import personal_agent
from app.guardrails.compliance_guardrail import compliance_guardrail
from app.prompts.orchestrator_prompt import ORCHESTRATOR_INSTRUCTION
from app.tools.calculo_tools import calcular_cantidad_modulos


load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")


modelo = LiteLlm(
    model=MODEL_NAME,
    api_key=os.getenv("OPENAI_API_KEY"),
)


root_agent = Agent(
    name="analista_corporativo_orquestador",
    model=modelo,
    description=(
        "Orquesta especialistas de normativa, Valor Módulo "
        "y estructura organizacional."
    ),
    instruction=ORCHESTRATOR_INSTRUCTION,
    # Guardrail de compliance: barrera determinística previa al modelo.
    before_model_callback=compliance_guardrail,
    tools=[
        AgentTool(agent=rag_agent),
        AgentTool(agent=valor_modulo_agent),
        AgentTool(agent=personal_agent),
        calcular_cantidad_modulos,
    ],
)