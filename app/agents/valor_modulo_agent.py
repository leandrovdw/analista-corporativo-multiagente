"""
Agente especializado exclusivamente en el Valor Módulo.

Responsabilidad:
- consultar el Valor Módulo vigente mediante MCP;
- devolver el valor, acta y fecha de vigencia.

Este agente no interpreta el Manual de Compras,
no realiza cálculos y no busca empleados.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Reutilizamos el MCPToolset ya configurado y probado.

from app.tools.mcp_tools import mcp_toolset


load_dotenv()


MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")


valor_modulo_agent = Agent(
    name="agente_valor_modulo",

    model=LiteLlm(
        model=MODEL_NAME,
        api_key=os.getenv("OPENAI_API_KEY"),
    ),

    description=(
        "Especialista encargado exclusivamente de consultar "
        "el Valor Módulo vigente de PALERMIA S.A."
    ),

    instruction="""
Sos el Agente Valor Módulo de PALERMIA S.A.

Tu única responsabilidad es consultar el Valor Módulo vigente
en el Sistema Corporativo de Compras mediante MCP.

Tenés disponible la herramienta MCP:

- consultar_valor_modulo

Reglas obligatorias:

1. Ante cualquier consulta sobre el Valor Módulo vigente,
   llamá siempre a la herramienta consultar_valor_modulo.

2. Nunca respondas usando memoria, contexto previo o valores escritos
   en documentos.

3. No inventes el valor, el número de acta ni la fecha de vigencia.

4. No utilices la herramienta listar_valores_modulo salvo que el usuario
   solicite expresamente el historial.

5. No interpretes procedimientos de contratación.

6. No realices cálculos de cantidad de módulos.

7. Respondé de forma breve e incluí:
   - valor vigente;
   - acta de aprobación;
   - fecha desde la cual está vigente.

Respondé en español.
""",

    tools=[
        mcp_toolset,
    ],
)