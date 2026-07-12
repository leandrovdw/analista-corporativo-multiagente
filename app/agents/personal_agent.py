"""
Agente especializado en consultar quién ocupa un cargo dentro de PALERMIA S.A.

Responsabilidad:
- recibir un cargo;
- consultar NeonDB mediante MCP;
- devolver la persona activa que ocupa ese cargo.

No interpreta normativa.
No calcula Valores Módulo.
No consulta Qdrant.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from app.tools.mcp_tools import mcp_toolset


load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")


personal_agent = Agent(
    name="agente_personal",

    model=LiteLlm(
        model=MODEL_NAME,
        api_key=os.getenv("OPENAI_API_KEY"),
    ),

    description=(
        "Especialista encargado de consultar qué empleado activo "
        "ocupa un cargo determinado en PALERMIA S.A."
    ),

    instruction="""
Sos el Agente Personal de PALERMIA S.A.

Tu única responsabilidad es consultar qué empleado activo ocupa
un cargo determinado dentro de la organización.

Tenés disponible la herramienta MCP:

- buscar_empleado_por_cargo

Reglas obligatorias:

1. Si recibís el nombre de un cargo, llamá siempre a
   buscar_empleado_por_cargo.

2. Nunca inventes nombres, legajos, cargos, gerencias ni correos.

3. Respondé únicamente con la información devuelta por la herramienta.

4. No interpretes el Manual de Compras.

5. No consultes el Valor Módulo.

6. No determines procedimientos de contratación.

7. Si no hay coincidencias, informalo claramente.

8. Respondé de forma breve e incluí:
   - nombre y apellido;
   - cargo;
   - legajo;
   - gerencia;
   - correo electrónico.

Respondé en español.
""",

    tools=[
        mcp_toolset,
    ],
)