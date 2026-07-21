# Informe — Analista Corporativo Multiagente (PALERMIA S.A.)

**Trabajo Práctico Final — Maestría en Inteligencia Artificial**

Sistema multiagente que asiste en consultas sobre compras y contrataciones,
simulando el criterio de un integrante de una comisión evaluadora: interpreta la
normativa institucional, consulta datos vivos del sistema corporativo y fundamenta
cada respuesta con trazabilidad documental.

**Caso de uso de referencia:**
> *"Necesito comprar notebooks por $15.000.000. ¿Qué procedimiento corresponde?"*

El sistema obtiene el Valor Módulo (VM) vigente, convierte el monto en pesos a VM,
consulta la normativa con esa cantidad y determina el procedimiento y el nivel de
aprobación, citando la fuente documental.

---

## 1. Arquitectura general

El sistema sigue un patrón **orquestador + especialistas**. Los subagentes se
exponen al orquestador como herramientas (`AgentTool`): cada uno resuelve una
tarea acotada y devuelve el resultado, sin tomar el control de la conversación.

```text
Usuario
  │
  ▼
Orquestador (root_agent)
  │  tool propia: calcular_cantidad_modulos (determinística)
  │
  ├─ AgentTool ─► Agente RAG          ─► Qdrant (búsqueda semántica)
  ├─ AgentTool ─► Agente Valor Módulo ─► MCP ─► NeonDB
  └─ AgentTool ─► Agente Personal     ─► MCP ─► NeonDB
  │
  ▼
Respuesta final integrada
```

### Componentes

| Componente | Ubicación | Rol |
|---|---|---|
| Orquestador | `app/agents/orchestrator.py` | Coordina el flujo e integra la respuesta |
| Agente RAG | `app/agents/rag_agent.py` | Interpreta la normativa vía RAG |
| Agente Valor Módulo | `app/agents/valor_modulo_agent.py` | Consulta el VM vigente vía MCP |
| Agente Personal | `app/agents/personal_agent.py` | Consulta quién ocupa un cargo vía MCP |
| Tool de cálculo | `app/tools/calculo_tools.py` | Cálculo determinístico de VM (`Decimal`) |
| Guardrail | `app/guardrails/compliance_guardrail.py` | Barrera de compliance previa al modelo |
| Cliente RAG | `app/rag/client.py`, `app/rag/ingest.py` | Embeddings y búsqueda en Qdrant |
| Servidor MCP | `mcp_server/server.py` | Expone NeonDB como herramientas (lectura) |
| Sesiones / state | `app/sessions/` | Memoria estructurada entre turnos |
| Evaluación | `evaluations/` | Golden cases + LLM-as-a-Judge |

### Flujo para una compra con monto

1. El orquestador detecta objeto y monto.
2. Delega al **Agente Valor Módulo** → obtiene VM vigente, acta y fecha (MCP → NeonDB).
3. Ejecuta la tool **`calcular_cantidad_modulos`** → convierte pesos a VM.
4. Delega al **Agente RAG** con la cantidad exacta de VM → procedimiento y nivel de aprobación.
5. Si la aprobación recae en un cargo, delega al **Agente Personal** → busca la persona.
6. Integra todo en una respuesta con fundamento documental.

### Stack tecnológico

Google ADK 2.4 · LiteLLM · OpenAI (gpt-4o-mini) · Qdrant Cloud · NeonDB (PostgreSQL)
· MCP (HTTP, FastMCP) · pytest · Python 3.13.

---

## 2. Decisiones de diseño y trade-offs

Cada decisión se tomó equilibrando un beneficio contra un costo asumido de forma
consciente.

| Decisión | Se ganó | Trade-off asumido |
|---|---|---|
| **Subagentes como `AgentTool`** (en lugar de `sub_agents`) | El orquestador conserva el control y compone las respuestas | Más hops al modelo (mayor latencia y costo) y un prompt de orquestación más complejo |
| **Cálculo en tool determinística** (no en el LLM) | Exactitud y reproducibilidad garantizadas (`Decimal`) | Menos flexibilidad: requiere que el orquestador extraiga bien los números y llame a la tool |
| **Guardrail en código** (`before_model_callback`) | Barrera dura: si se dispara, el modelo no se ejecuta | La detección por reglas (regex) puede tener falsos positivos/negativos y exige mantenimiento |
| **Reglas de guardrail como plantillas de datos** | Se agregan reglas sin tocar la lógica; se pueden testear | Cobertura limitada a patrones definidos; no generaliza a redacciones nuevas |
| **RAG con chunking por artículo** | Respeta la unidad semántica de la normativa → mejor recuperación | Depende de que el documento tenga estructura de artículos (hay fallback por caracteres) |
| **Especialistas con responsabilidad única** | Código simple, testeable y explicable | Más agentes y archivos que coordinar |
| **Integración vía MCP** (no acceso directo a la BD) | Desacopla al agente de la fuente de datos | Una pieza más que debe estar corriendo (el servidor MCP) y algo de latencia |
| **`InMemorySessionService`** | Simplicidad; suficiente para demostrar sesiones y state | Las sesiones no persisten al cerrar el proceso |
| **Modelo gpt-4o-mini** | Bajo costo y buena velocidad | Menor capacidad de razonamiento que modelos mayores |
| **Evaluación con LLM-as-a-Judge** | Evalúa contra criterios semánticos, no texto exacto | Variabilidad y costo del juez; requiere calibrar los criterios |

**Principio rector:** separar lo que debe ser exacto (cálculo, guardrails) de lo que
es interpretativo (normativa, redacción). Lo exacto vive en código determinístico;
lo interpretativo, en los agentes.

---

## 3. Limitaciones encontradas

- **Sesiones no persistentes:** se usa `InMemorySessionService`; la sesión se pierde
  al terminar el proceso.
- **MCP de solo lectura:** el servidor expone consultas, no escritura. La tabla
  `consultas_compras` existe en el esquema pero aún no se registra la consulta.
- **Extracción por reglas:** el monto y el objeto se detectan con expresiones
  regulares; funciona para el dominio, pero no cubre redacciones muy libres.
- **Dependencia de servicios externos:** el flujo completo requiere el servidor MCP,
  NeonDB y Qdrant activos. Durante la evaluación, un caso (`vm_vigente`) falló por un
  **error MCP intermitente** en una llamada puntual; el mismo dato se obtuvo
  correctamente dentro de otro caso, lo que confirma que la consulta funciona.
- **Juez estricto:** con temperatura 0, el LLM-as-a-Judge puede penalizar detalles
  menores de formato; conviene calibrar los criterios para producción.
- **Guardrail acotado:** cubre únicamente fraccionamiento (regla de negocio) e
  inyección de prompt, mediante patrones. **No filtra bienes prohibidos o
  ilícitos**: por ejemplo, una consulta para comprar "uranio enriquecido" no se
  bloquea y se procesa como una compra normal. Es una decisión de alcance
  consciente (el guardrail apunta al compliance de compras, no a un clasificador
  general de legalidad).

### Métricas obtenidas

Evaluación con Golden Cases (`python -m evaluations.run_golden_cases`):

| Métrica | Valor |
|---|---|
| Casos evaluados | 5 |
| Aprobados | 4 / 5 |
| Tasa de aprobación | 80 % |
| Puntaje promedio | 8.40 / 10 |

---

## 4. Propuesta de trabajo futuro

- **Persistencia de sesiones** sobre NeonDB, reemplazando `InMemorySessionService`
  sin cambiar el resto del código (misma interfaz `BaseSessionService`).
- **Escritura vía MCP:** registrar cada consulta en la tabla `consultas_compras`
  (objeto, monto, VM, procedimiento, autoridad) para trazabilidad y auditoría.
- **Protocolo A2A:** simular la comunicación con un agente de otra organización
  (por ejemplo, un organismo de control externo).
- **Extracción robusta de datos:** reemplazar las reglas regex por extracción
  asistida por el modelo (structured output) para tolerar redacciones libres.
- **Observabilidad ampliada:** trazas por invocación, tiempos por agente y tablero
  de métricas de la evaluación a lo largo del tiempo.
- **Ampliar el set de golden cases** y calibrar el juez para reducir su rigidez.
- **Guardrail de bienes prohibidos/ilícitos:** sumar una regla (o un clasificador)
  que rechace consultas de objetos no permitidos —por ejemplo, uranio enriquecido,
  armas o sustancias controladas—, reutilizando el mismo mecanismo de plantillas
  (`REGLAS_COMPLIANCE`) que ya soporta el diseño.

---

## Reproducibilidad

Instrucciones completas de instalación, configuración y ejecución en el
[`README.md`](README.md). Resumen:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # completar con las claves reales

python mcp_server/server.py     # terminal 1: servidor MCP
adk web                         # terminal 2: interfaz del agente
python -m evaluations.run_golden_cases   # evaluación con métricas
python -m pytest tests/ -q      # tests (19)
```
