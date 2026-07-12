# Prompt para generar la presentación (IA visual)

Copiá y pegá el siguiente bloque en una herramienta de generación de slides con IA
(**Gamma**, **Beautiful.ai**, **Tome**, o **ChatGPT/Claude** pidiendo diapositivas).
El contenido ya está cargado; la IA solo debe maquetarlo con impacto visual.

---

```text
Actuá como diseñador de presentaciones. Generá una presentación profesional de 14
diapositivas para la defensa de un Trabajo Práctico Final de una Maestría en
Inteligencia Artificial. Tema: un sistema multiagente llamado "Analista Corporativo".

ESTILO VISUAL:
- Moderno, corporativo y limpio. Alto impacto visual.
- Paleta: azules profundos + un color de acento (turquesa o violeta) + fondos claros.
- Tipografía sans-serif legible. Mucho espacio en blanco.
- Usar iconos, diagramas de flujo y tablas en vez de párrafos largos.
- Cada slide: un título claro y 3–5 bullets cortos como máximo.
- Incluir diagramas donde se indique.

CONTENIDO POR DIAPOSITIVA:

1) PORTADA
Título: "Analista Corporativo Multiagente"
Subtítulo: "Sistema de asistencia para compras y contrataciones — PALERMIA S.A."
Pie: Trabajo Práctico Final — Maestría en IA. [Tu nombre].

2) EL PROBLEMA
Título: "¿Qué resuelve?"
- Las consultas de compras exigen cruzar normativa + datos vivos del sistema.
- El umbral de contratación se mide en "Valor Módulo" (VM), no en pesos.
- Se necesita fundamento documental y trazabilidad, como una comisión evaluadora.

3) CASO DE USO
Título: "Un ejemplo concreto"
Cita grande: "Necesito comprar notebooks por $15.000.000. ¿Qué procedimiento corresponde?"
- El sistema convierte pesos → VM con el valor vigente y decide el procedimiento.
- Nunca decide solo por el monto en pesos.

4) ARQUITECTURA GENERAL (diagrama)
Título: "Arquitectura multiagente"
Diagrama de flujo:
Usuario → Orquestador → (Agente RAG → Qdrant) + (Agente Valor Módulo → MCP → NeonDB)
+ (Agente Personal → MCP → NeonDB) + (Tool de cálculo) → Respuesta final.

5) LOS AGENTES
Título: "Un orquestador y tres especialistas"
Tabla:
- Orquestador: coordina e integra la respuesta.
- Agente RAG: interpreta la normativa.
- Agente Valor Módulo: consulta el VM vigente.
- Agente Personal: consulta quién ocupa un cargo.

6) COORDINACIÓN (diagrama de pasos)
Título: "Cómo trabajan juntos"
Flujo numerado para una compra:
1. Detecta objeto y monto → 2. Consulta VM (MCP) → 3. Calcula VM (tool) →
4. Consulta normativa (RAG) → 5. Busca responsable (MCP) → 6. Integra respuesta.
Nota: cada agente hace UNA cosa; el orquestador mantiene el control.

7) DECISIONES DE DISEÑO
Título: "Decisiones clave"
- Subagentes como herramientas (AgentTool): el orquestador no pierde el control.
- Cálculo en código determinístico (Decimal), no en el LLM.
- Guardrails como barrera en código, no solo en el prompt.
- Separar lo exacto (cálculo, reglas) de lo interpretativo (normativa, redacción).

8) RAG
Título: "Recuperación aumentada (RAG)"
- Documentos institucionales → chunking por artículo → embeddings (OpenAI).
- Búsqueda semántica en Qdrant Cloud.
- El agente responde citando la fuente documental.

9) MCP + BASE DE DATOS
Título: "Datos vivos vía MCP"
- Servidor MCP (HTTP) expone la base NeonDB como herramientas.
- Tools: consultar Valor Módulo, buscar empleado por cargo.
- Ventaja: desacopla al agente de la fuente de datos.

10) GUARDRAILS Y ESTADO
Título: "Seguridad y memoria"
- Guardrail de compliance: bloquea fraccionamiento y prompt-injection ANTES del modelo.
- State de sesión: recuerda monto y objeto entre turnos (ej.: "¿y si fueran $80M?").

11) EVALUACIÓN (destacar métricas)
Título: "¿Cómo sé que funciona?"
- Golden Cases + LLM-as-a-Judge (evalúa contra criterios, no texto exacto).
- Números grandes y visibles: 80% de aprobación · 8.40/10 promedio · 4 de 5 casos.

12) TECNOLOGÍAS
Título: "Stack tecnológico"
Iconos/logos: Google ADK, LiteLLM, OpenAI, Qdrant, NeonDB (PostgreSQL), MCP, Python 3.13, pytest.

13) LIMITACIONES Y FUTURO
Título: "Limitaciones y próximos pasos"
- Sesiones en memoria (no persistentes aún).
- Escritura en BD vía MCP y protocolo A2A: trabajo futuro.
- Extracción de datos por reglas; dependencia de servicios externos.

14) CIERRE
Título: "Conclusión"
- Un sistema multiagente que fundamenta cada respuesta en normativa y datos vivos.
- Prioridad: que lo esencial funcione bien y esté testeado.
- Frase: "Lo exacto en código; lo interpretativo, en los agentes."
```

---

## Consejos de uso

- En **Gamma**: pegá el bloque en "Pegar texto" → elegí un tema visual corporativo.
- Pedile explícitamente que **no** ponga párrafos largos; que use diagramas.
- Reemplazá `[Tu nombre]` y ajustá los números si volvés a correr la evaluación.
- Para los diagramas (slides 4 y 6), si la herramienta no los genera bien, pedí
  "diagrama de flujo horizontal con cajas y flechas".
```
