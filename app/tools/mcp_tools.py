"""
Configuración compartida del MCP.

Todos los agentes que necesiten acceder al servidor MCP
importarán este archivo.

De esta forma evitamos duplicar código y eliminamos
el antiguo mcp_agent.py.
"""

import os

from dotenv import load_dotenv

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)

load_dotenv()

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:8001/mcp",
)

mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL
    )
)