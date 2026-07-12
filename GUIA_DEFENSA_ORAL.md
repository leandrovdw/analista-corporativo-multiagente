# Guía de Defensa Oral — Analista Corporativo Multiagente (PALERMIA S.A.)

Guía de apoyo para la defensa del TP Final. Está organizada alrededor de los seis
puntos que evalúa la cátedra, con una **estrategia narrativa** sugerida, los
**puntos clave** para decir en cada tramo, y una nota **📁 En el código** que te
indica en qué archivo mirar mientras explicás.

---

## Estrategia general (cómo contar la historia)

La defensa se entiende mejor si seguís el mismo camino que hace una consulta real,
en vez de listar componentes sueltos. Recomendación de recorrido (10–12 min):

1. **El problema** (30 s) — qué resuelve el sistema y por qué importa.
2. **Demo en vivo** (2–3 min) — mostrar el sistema funcionando primero engancha.
3. **Qué pasó por dentro** (3–4 min) — coordinación entre agentes + decisiones de diseño.
4. **Cómo sé que funciona** (2 min) — métricas de la evaluación.
5. **Tecnologías y límites** (2 min) — stack y limitaciones honestas.
6. **Cierre** (30 s) — qué aprendiste / qué mejorarías.

> Regla de oro: **mostrar antes que explicar**. Primero la demo, después el porqué.

---

## 1. Funcionamiento del sistema

**Idea central para decir en voz alta:**
> "Es un analista corporativo que responde consultas de compras y contrataciones
> como lo haría un integrante de una comisión evaluadora: interpreta la normativa,
> consulta datos vivos del sistema y fundamenta cada respuesta."

**Caso de uso estrella (el que conviene demostrar):**
> *"Necesito comprar notebooks por $15.000.000. ¿Qué procedimiento corresponde?"*

Qué hace el sistema, paso a paso:
1. Detecta objeto (notebooks) y monto ($15.000.000).
2. Consulta el **Valor Módulo vigente** en la base (vía MCP).
3. Calcula cuántos Valores Módulo representa la compra (tool determinística).
4. Consulta la **normativa** (RAG) con esa cantidad de VM.
5. Determina el **procedimiento** y el **nivel de aprobación**.
6. Si aprueba un cargo, busca **quién lo ocupa** (vía MCP).
7. Responde con fundamento documental.

**Por qué este flujo es interesante:** el umbral de la normativa está en Valores
Módulo, no en pesos. Sin convertir pesos → VM con el valor vigente, la respuesta
sería incorrecta. El sistema **nunca** decide el procedimiento solo por el monto en pesos.

> 📁 **En el código:** el plan de pasos vive en `app/prompts/orchestrator_prompt.py`
> (instrucción del orquestador) y se ejecuta desde `app/agents/orchestrator.py`.
> El punto de entrada es `app/agent.py` (expone `root_agent`).

---

## 2. Decisiones de diseño (lo que más se valora)

| Decisión | Por qué |
|---|---|
| **Subagentes como `AgentTool`** (no `sub_agents`) | El orquestador mantiene el control: cada especialista resuelve su tarea y **devuelve** el resultado, sin quedarse con la conversación. |
| **Especialistas con responsabilidad única** | RAG, Valor Módulo y Personal hacen una sola cosa. Más fácil de razonar, testear y explicar. |
| **Cálculo en una tool determinística, no en el LLM** | La matemática debe ser exacta y reproducible. Usa `Decimal`, no depende del modelo. |
| **Guardrail como `before_model_callback`** | Barrera **determinística** en código: si detecta fraccionamiento, el modelo ni se ejecuta. Es más fuerte que "pedirle" al prompt que no lo haga. |
| **Reglas de guardrail como plantillas (datos)** | Agregar una regla nueva no toca la lógica; además se pueden testear. |
| **RAG con chunking por artículo** | La normativa está organizada en artículos; respetar esa unidad mejora la recuperación. |
| **State separado del historial** | El `state` guarda datos estructurados (monto, objeto) que persisten entre turnos de forma confiable, sin depender de que el LLM "recuerde". |
| **Evaluación con LLM-as-a-Judge** | No se puede comparar texto exacto con un LLM; un juez evalúa contra criterios. |

**Frase para la defensa:**
> "Separé lo que debe ser exacto (cálculo, guardrails) de lo que es interpretativo
> (normativa, redacción). Lo exacto va en código determinístico; lo interpretativo,
> en los agentes."

> 📁 **En el código:** el orquestador y el uso de `AgentTool` en
> `app/agents/orchestrator.py`; el cálculo determinístico en
> `app/tools/calculo_tools.py`.

---

## 3. Coordinación entre agentes

```
Usuario
  │
  ▼
Orquestador ──(AgentTool)──► Agente Valor Módulo ──► MCP ──► NeonDB
  │           ──(AgentTool)──► Agente RAG          ──► Qdrant
  │           ──(AgentTool)──► Agente Personal     ──► MCP ──► NeonDB
  │           ──(tool)──────► calcular_cantidad_modulos
  ▼
Respuesta final integrada
```

**Cómo coordina el orquestador (lo dice su prompt):**
- Para una compra con monto: sigue un **plan obligatorio** (VM → cálculo → normativa → persona).
- Para consultas simples: delega a un solo especialista.
- Cada delegación lleva una **instrucción específica**, no la pregunta entera.

**Punto fuerte para destacar:** el orquestador no "sabe" de Qdrant ni de NeonDB.
Solo sabe *a quién preguntarle*. Eso es separación de responsabilidades real.

> 📁 **En el código:** orquestador en `app/agents/orchestrator.py`; los tres
> especialistas en `app/agents/rag_agent.py`, `app/agents/valor_modulo_agent.py` y
> `app/agents/personal_agent.py`.

---

## 4. Métricas obtenidas

De la corrida de **Golden Cases** con LLM-as-a-Judge:

| Métrica | Valor |
|---|---|
| Casos evaluados | 5 |
| Aprobados | 4/5 |
| Tasa de aprobación | **80 %** |
| Puntaje promedio | **8.40 / 10** |

**Qué se evaluó:** consulta simple de Valor Módulo, flujo completo de compra,
normativa pura, activación del guardrail y consulta de personal.

**Cómo se mide (para explicarlo):** cada caso define *criterios* que la respuesta
debe cumplir; un modelo evaluador (temperatura 0) decide PASS/FAIL, puntaje y
justificación. La lógica de parseo del veredicto está testeada de forma
determinística (sin llamar a la red).

> 📁 **En el código:** casos en `evaluations/golden_cases.py`; juez en
> `evaluations/judge.py`; corrida y métricas en `evaluations/run_golden_cases.py`.
> Para reproducir: `python -m evaluations.run_golden_cases`.

---

## 5. Tecnologías utilizadas

| Capa | Tecnología | Rol |
|---|---|---|
| Framework de agentes | **Google ADK 2.4** | Orquestación, tools, sesiones, callbacks |
| Acceso a modelos | **LiteLLM** | Abstracción sobre el proveedor |
| Modelo | **OpenAI (gpt-4o-mini)** | Razonamiento de los agentes y el juez |
| RAG | **Qdrant Cloud** + embeddings OpenAI | Búsqueda semántica en la normativa |
| Datos corporativos | **NeonDB (PostgreSQL)** | Valor Módulo, empleados |
| Integración de datos | **MCP (HTTP, FastMCP)** | Expone la base como tools |
| Testing | **pytest** | 19 tests de la lógica determinística |
| Config | **python-dotenv** | Variables de entorno |
| Lenguaje | **Python 3.13** | — |

**Por qué MCP y no consultar la base directo:** MCP desacopla al agente de la
base. Mañana la fuente podría cambiar (otra base, otra API) y los agentes no se
enteran: siguen llamando a la misma tool.

> 📁 **En el código:** servidor MCP en `mcp_server/server.py` (esquema en
> `mcp_server/schema.sql`); conexión del agente al MCP en `app/tools/mcp_tools.py`;
> RAG en `app/rag/client.py` y `app/rag/ingest.py`; dependencias en `requirements.txt`.

---

## 6. Limitaciones encontradas (honestidad = puntos)

- **Sesiones en memoria:** se usa `InMemorySessionService`; la sesión se pierde al
  cerrar el proceso. Para producción se persistiría (p. ej. sobre NeonDB).
- **Escritura vía MCP no implementada:** el servidor MCP es de solo lectura. La
  tabla `consultas_compras` existe en el esquema pero todavía no se registra la consulta.
- **Extracción de monto/objeto por reglas (regex):** funciona para los casos del
  dominio, pero no cubre redacciones muy libres.
- **Dependencia de servicios externos:** el flujo completo necesita MCP + NeonDB +
  Qdrant arriba. En la evaluación, un caso falló por un **error MCP intermitente**
  en una llamada puntual (el mismo dato se obtuvo bien dentro de otro caso).
- **El juez es estricto:** con temperatura 0 puede penalizar detalles menores de
  formato; para producción se calibrarían los criterios.
- **Protocolo A2A no implementado:** quedó como mejora futura (simular la
  comunicación con un agente de otra organización).

**Frase de cierre:**
> "Prioricé que lo mínimo funcione bien y esté testeado, antes que sumar features a
> medio hacer. Las limitaciones que quedan son conscientes y tienen un camino claro
> de mejora."

> 📁 **En el código:** el `state` y su extracción en `app/sessions/state_utils.py`
> y `app/sessions/session_manager.py`; el esquema con la tabla aún no usada en
> `mcp_server/schema.sql`.

---

## Mapa rápido: funcionalidad → archivo

| Funcionalidad | Archivo(s) |
|---|---|
| Punto de entrada (`root_agent`) | `app/agent.py` |
| Orquestador y coordinación | `app/agents/orchestrator.py` + `app/prompts/orchestrator_prompt.py` |
| Subagente RAG | `app/agents/rag_agent.py` + `app/prompts/rag_prompt.py` |
| Subagente Valor Módulo | `app/agents/valor_modulo_agent.py` |
| Subagente Personal | `app/agents/personal_agent.py` |
| Cálculo determinístico (VM) | `app/tools/calculo_tools.py` |
| Guardrails (compliance) | `app/guardrails/compliance_guardrail.py` |
| Gestión de sesiones y state | `app/sessions/session_manager.py` + `app/sessions/state_utils.py` |
| Demo de sesiones/state | `scripts/run_demo.py` |
| RAG (conexión / ingesta) | `app/rag/client.py` + `app/rag/ingest.py` + `app/tools/rag_tools.py` |
| Servidor MCP + base | `mcp_server/server.py` + `mcp_server/schema.sql` |
| Conexión agente ↔ MCP | `app/tools/mcp_tools.py` |
| Evaluación (golden cases + juez) | `evaluations/golden_cases.py` + `evaluations/judge.py` + `evaluations/run_golden_cases.py` |
| Tests | `tests/test_calculo.py`, `test_state.py`, `test_guardrails.py`, `test_judge.py` |

---

## Preguntas conceptuales probables (preparate estas)

- ¿Diferencia entre `state` e historial de conversación?
- ¿Por qué `AgentTool` y no `sub_agents`? ¿Qué cambia?
- ¿Qué es MCP y qué problema resuelve?
- ¿Cómo funciona el RAG? ¿Qué es un embedding? ¿Por qué chunking por artículo?
- ¿Por qué el cálculo no lo hace el LLM?
- ¿Qué garantiza el guardrail que el prompt no garantiza?
- ¿Qué es LLM-as-a-Judge y por qué no comparar texto exacto?
- ¿Cómo escalarías esto a producción?

---

## Checklist para el día de la defensa

- [ ] Servidor MCP corriendo (`python mcp_server/server.py`).
- [ ] `adk web` abierto y probado con el caso de las notebooks.
- [ ] Tener a mano el reporte de golden cases (métricas).
- [ ] Saber señalar en el código: orquestador, un subagente, el guardrail, el juez.
- [ ] Tener lista la respuesta sobre la limitación del caso `vm_vigente`.
