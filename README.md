# Analista Corporativo Multiagente — PALERMIA S.A.

Trabajo Práctico Final. Sistema multiagente construido con **Google ADK** que responde
consultas sobre compras y contrataciones combinando:

- **RAG** sobre **Qdrant** (documentación institucional + embeddings de OpenAI),
- un **servidor MCP** propio que consulta **NeonDB (PostgreSQL)**,
- una **tool determinística** de cálculo,
- **LiteLLM** con modelos de **OpenAI**.

El sistema simula a un integrante de una comisión evaluadora: interpreta la normativa,
obtiene el Valor Módulo vigente, calcula la escala de la contratación y determina el
procedimiento y el nivel de aprobación que corresponden.

## Caso de uso principal

> Necesito comprar notebooks por $15.000.000. ¿Qué procedimiento corresponde?

Flujo real que ejecuta el sistema:

1. El orquestador detecta objeto y monto.
2. Consulta el **Valor Módulo vigente** en NeonDB vía MCP (`agente_valor_modulo`).
3. Calcula la cantidad de VM con la tool determinística `calcular_cantidad_modulos`.
4. Consulta la normativa en el RAG con la cantidad exacta de VM (`agente_rag_documental`).
5. Si la aprobación recae en un cargo individual, busca a la persona vía MCP (`agente_personal`).
6. Integra todo en una respuesta con fundamento documental.

## Arquitectura

Los especialistas se invocan como `AgentTool`: siguen siendo agentes con sus propias
tools y prompts, resuelven su tarea y devuelven el resultado al orquestador, que
mantiene el control de la conversación.

```text
Usuario
  |
  v
Orquestador (analista_corporativo_orquestador)
  |  tool propia: calcular_cantidad_modulos
  |
  |-- AgentTool --> agente_rag_documental   -> RAG sobre Qdrant
  |-- AgentTool --> agente_valor_modulo     -> MCP -> NeonDB
  |-- AgentTool --> agente_personal         -> MCP -> NeonDB
  |
  v
Respuesta final integrada
```

## Componentes

| Componente | Ubicación | Rol |
|---|---|---|
| Orquestador | `app/agents/orchestrator.py` (`root_agent`) | Coordina el flujo e integra la respuesta |
| Agente RAG | `app/agents/rag_agent.py` | Interpreta normativa vía RAG |
| Agente Valor Módulo | `app/agents/valor_modulo_agent.py` | Consulta el VM vigente vía MCP |
| Agente Personal | `app/agents/personal_agent.py` | Consulta quién ocupa un cargo vía MCP |
| Tool de cálculo | `app/tools/calculo_tools.py` | Cálculo determinístico de VM (`Decimal`) |
| Cliente RAG | `app/rag/client.py` | Conexión a Qdrant/OpenAI y búsqueda semántica |
| Ingesta RAG | `app/rag/ingest.py` | Chunking por artículo + embeddings + upsert |
| Servidor MCP | `mcp_server/server.py` | Tools HTTP sobre NeonDB (solo lectura) |

### Tools MCP disponibles (solo lectura)

- `consultar_valor_modulo` — Valor Módulo vigente, acta y fecha.
- `buscar_empleado_por_cargo` — empleado activo por cargo.
- `listar_valores_modulo` — historial de Valores Módulo.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # completar con claves reales
```

## Variables de entorno

Ver `.env.example`. Notas importantes:

- `MODEL_NAME` debe incluir el prefijo del proveedor para LiteLLM, p. ej. `openai/gpt-4o-mini`.
- `MCP_SERVER_URL` debe coincidir con el host/puerto/path de `mcp_server/server.py`
  (por defecto `http://127.0.0.1:8001/mcp`).

## Puesta en marcha

**1. Base de datos (NeonDB / PostgreSQL).** Crear el esquema y datos iniciales:

```bash
psql "$DATABASE_URL" -f mcp_server/schema.sql
```

**2. Ingesta de documentos al RAG.** Los documentos viven en `docs_rag/`:

```bash
python -m app.rag.ingest
```

**3. Servidor MCP** (en una terminal aparte):

```bash
python mcp_server/server.py
```

**4. Interfaz del agente (ADK Web).** ADK gestiona sesiones y state:

```bash
adk web
```

## Gestión de sesiones y uso de state

Una sesión agrupa la interacción de un usuario y contiene un **state**: un
diccionario estructurado que persiste entre turnos (monto, objeto de compra,
Valor Módulo, etc.). Se administra con `InMemorySessionService` de ADK y se
modifica de forma trazable con `EventActions(state_delta=...)` (nunca a mano).

- `app/sessions/session_manager.py` — servicio de sesiones y estado inicial.
- `app/sessions/state_utils.py` — extrae monto/objeto de la consulta y actualiza el state.

Demo de dos turnos que muestra la persistencia del state:

```bash
python -m scripts.run_demo
```

En el turno 1 (`comprar notebooks por $15.000.000`) el sistema guarda
`objeto="notebooks"` y `monto=15.000.000`. En el turno 2 (`¿Y si fueran
$80.000.000?`) solo cambia el monto: el objeto **persiste** desde el state.

## Guardrails (seguridad mínima)

`app/guardrails/compliance_guardrail.py` implementa un `before_model_callback`
que actúa como barrera **determinística** antes de cada llamada al modelo del
orquestador. Las reglas están definidas como plantillas (`REGLAS_COMPLIANCE`):

- **fraccionamiento**: bloquea pedidos de dividir/fraccionar una compra para
  eludir el procedimiento o el umbral.
- **revelar_instrucciones**: guardrail anti prompt-injection.

Si una regla se dispara, el modelo no se ejecuta y se devuelve una respuesta
institucional; además queda traza en `state["guardrail_activado"]`.

## Evaluación con Golden Cases (LLM-as-a-Judge)

- `evaluations/golden_cases.py` — casos de referencia con criterios esperados.
- `evaluations/judge.py` — juez semántico: un LLM evalúa si la respuesta cumple
  los criterios y devuelve veredicto (PASS/FAIL), puntaje y justificación.
- `evaluations/run_golden_cases.py` — ejecuta cada caso por el agente, lo evalúa
  y reporta métricas (tasa de aprobación y puntaje promedio).

```bash
# requiere servidor MCP corriendo + NeonDB + Qdrant
python -m evaluations.run_golden_cases
```

## Tests

Tests unitarios de la lógica determinística (no requieren servicios externos):

```bash
python -m pytest tests/ -q
```

Cubren: cálculo de VM, extracción y persistencia de state entre turnos,
detección del guardrail y parseo del veredicto del juez.

## Utilidades

Probar la búsqueda semántica del RAG de forma aislada:

```bash
python -m scripts.buscar_rag
```

## Documentos para RAG (`docs_rag/`)

- `Manual Simplificado de Compras y Contrataciones.docx`
- `Resolucion_Directorio_PALERMIA.docx`

## Estructura del proyecto

```text
app/
  agent.py               # expone root_agent para ADK Web
  agents/                # orquestador + 3 subagentes
  guardrails/            # guardrail de compliance (before_model_callback)
  prompts/               # prompts de orquestador y RAG
  rag/                   # client.py (conexión) + ingest.py
  tools/                 # calculo / mcp / rag tools
  sessions/              # gestión de sesiones y utilidades de state
evaluations/             # golden cases + LLM-as-a-Judge + runner de evaluación
mcp_server/              # servidor MCP + schema.sql
scripts/                 # run_demo.py (sesiones/state) + buscar_rag.py
tests/                   # tests unitarios (pytest)
docs_rag/                # documentación institucional para el RAG
```
