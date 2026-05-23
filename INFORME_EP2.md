# Informe Tecnico — Evaluacion Parcial N°2
## Desarrollo de un Agente Funcional para Validacion de Continuidad Narrativa

**Asignatura:** ISY0101 — Ingenieria de Soluciones con Inteligencia Artificial  
**Profesor:** Roberto Eduardo Vega Araneda  
**Institucion:** Duoc UC  
**Estudiantes:** Carlos Echeverria, Benjamin Molina, Felipe Villar  
**Fecha:** Mayo 2026

---

## 1. Resumen Ejecutivo

Este informe documenta la segunda entrega del proyecto *Consultor de Continuidad Narrativa — Transformers*, que evoluciona de un pipeline RAG con agente reactivo (EP1) hacia un **agente deliberativo funcional** capaz de integrar herramientas de consulta y escritura, mantener memoria conversacional, planificar tareas multi-etapa y ajustar su comportamiento ante condiciones cambiantes. El sistema se desarrolla en Python 3.11+ usando LangChain como framework de agentes, OpenAI GPT-4o como modelo de generacion y FAISS para recuperacion semantica vectorial.

---

## 2. Diseno e Implementacion del Agente

### 2.1 Arquitectura general

El sistema se organiza en tres capas:

```
┌────────────────────────────────────────┐
│  ORQUESTACION                          │
│  planning_agent.py  +  agent_v2.py     │
├────────────────────────────────────────┤
│  HERRAMIENTAS                          │
│  search_lore | validate_character      │
│  check_timeline | write_continuity_  │
│  report                                │
├────────────────────────────────────────┤
│  INFRAESTRUCTURA RAG                   │
│  lore_database.py + transformers_rag │
│  .py + evaluate.py                     │
└────────────────────────────────────────┘
```

### 2.2 Frameworks integrados

Se selecciono **LangChain** (`langchain>=0.2.0`, `langchain-openai>=0.1.8`) como framework principal por tres razones:

1. **Abstraccion de agentes:** `create_openai_tools_agent` + `AgentExecutor` gestionan automaticamente el ciclo de razonamiento, invocacion de herramientas y manejo de errores de parsing.
2. **Integracion con GitHub Models API:** LangChain lee variables de entorno `OPENAI_API_BASE` y `OPENAI_API_KEY`, compatibles con el mapeo requerido por GitHub Models (`GITHUB_TOKEN` -> `OPENAI_API_KEY`).
3. **Extensibilidad:** El sistema de memoria y herramientas es modular; nuevas herramientas se registran con el decorador `@tool` sin modificar el nucleo del agente.

No se integro CrewAI pese a que el repositorio del curso lo contempla, porque para el alcance de este proyecto (un pipeline de validacion secuencial con 4 herramientas) CrewAI anadiria complejidad de orquestacion multi-agente innecesaria, ademas de problemas documentados de compatibilidad con versiones recientes de LangChain *(README del curso, IL2.1)*.

### 2.3 Herramientas implementadas

| Herramienta | Tipo | Funcion | Autonomia |
|---|---|---|---|
| `search_lore` | Consulta | Busqueda semantica por palabras clave en la base de lore | Recupera top-k fragmentos sin intervencion humana |
| `validate_character` | Consulta | Recupera estado canonico de un personaje especifico | Filtra por categoria PERSONAJE automaticamente |
| `check_timeline` | Consulta | Valida coherencia temporal de un evento | Cruza categorias TIMELINE + EVENTO |
| `write_continuity_report` | Escritura | Genera reporte Markdown y lo persiste en `/reports` | Crea archivo con timestamp automatico |

La herramienta de escritura transforma el agente de un mero clasificador a un sistema productivo que entrega artefactos documentales revisables por guionistas y productores.

---

## 3. Configuracion de Memoria y Recuperacion de Contexto

### 3.1 Memoria de corto plazo

`agent_v2.py` utiliza `ConversationBufferMemory` para mantener el historial completo de interacciones dentro de una sesion de validacion. La clave `chat_history` se inyecta automaticamente en el prompt del agente mediante el `AgentExecutor`, permitiendo preguntas de seguimiento como *"Cual fue la inconsistencia del analisis anterior?"* sin reenviar el fragmento original.

### 3.2 Memoria de largo plazo

`memory_system.py` demuestra tres estrategias comparadas:

| Estrategia | Caso de uso | Ventaja | Desventaja |
|---|---|---|---|
| `ConversationBufferMemory` | Sesiones < 15 interacciones | Contexto completo, sin perdida de informacion | Consumo lineal de tokens |
| `ConversationBufferWindowMemory(k=2)` | Flujos prolongados donde el pasado remoto es irrelevante | Ahorro de tokens, enfoque en contexto reciente | Perdida de informacion antigua |
| `ConversationSummaryMemory` | Sesiones > 20 interacciones | Compresion automatica via LLM | Riesgo de omision de detalles menores |

Se selecciono **BufferMemory como default** porque una sesion tipica de validacion de guiones no excede 10-15 interacciones (fragmento -> analisis -> 2-3 preguntas de seguimiento).

### 3.3 Recuperacion de contexto semantico

El pipeline RAG de `transformers_rag.py` recupera contexto mediante embeddings OpenAI (`text-embedding-3-small`) e indice FAISS (`IndexFlatIP`). La busqueda usa similitud coseno normalizada, con fallback a NumPy si FAISS no esta instalado. El top-k=4 equilibra cobertura de lore con precision: valores mayores diluyen la senal semantica, valores menores omiten evidencia relevante.

---

## 4. Planificacion y Toma de Decisiones

### 4.1 Eleccion del paradigma deliberativo

El equipo opto por un **agente deliberativo** sobre uno reactivo. La validacion de continuidad narrativa requiere descomponer un guion en entidades (personajes, objetos, eventos, ano), consultar multiples fuentes de lore, ponderar evidencias y emitir un dictamen. Un agente puramente reactivo (ReAct) decide la siguiente accion sobre la marcha, lo que puede causar omision de la verificacion temporal si el razonamiento se centra exclusivamente en personajes. El paradigma deliberativo garantiza que todas las dimensiones de validacion sean evaluadas sistematicamente.

### 4.2 Esquema de planificacion

`planning_agent.py` implementa una arquitectura **Plan-and-Execute** con cinco etapas secuenciales:

```
ETAPA 1: EXTRACCION      -> Identificar entidades del guion
ETAPA 2: RECUPERACION    -> Buscar lore relevante por entidad
ETAPA 3: VALIDACION      -> Comparar guion vs lore, detectar inconsistencias
ETAPA 4: DICTAMEN        -> Emitir veredicto + recomendacion
ETAPA 5: PERSISTENCIA    -> Guardar reporte y plan en disco
```

La planificacion es **jerarquica**: las etapas 1-3 son obligatorias (sin extraccion no hay recuperacion; sin recuperacion no hay validacion). La etapa 4 es condicional: si la etapa 3 detecta una inconsistencia de severidad CRITICA, el veredicto es forzosamente INCONSISTENTE, independientemente de otros factores. La etapa 5 siempre se ejecuta para garantizar trazabilidad.

### 4.3 Demostracion de toma de decisiones adaptativa

Se disenaron tres escenarios de prueba para IE6:

| Escenario | Entrada | Comportamiento esperado | Decision adaptativa |
|---|---|---|---|
| Inconsistencia personaje | Bumblebee habla en 2007 | `validate_character` detecta perdida de voz -> severidad CRITICA | Salta directamente a dictamen INCONSISTENTE |
| Inconsistencia temporal | Sam y Cade juntos en 2010 | `check_timeline` detecta solapamiento imposible | Combina evidencia de personajes + timeline |
| Caso consistente | Optimus vs Megatron en Mission City | Ninguna herramienta detecta anomalia | Dictamen CONSISTENTE sin falsos positivos |

---

## 5. Documentacion Tecnica y Orquestacion

### 5.1 Diagrama de orquestacion

El README.md incluye un diagrama ASCII de orquestacion que muestra la interaccion entre `planning_agent.py`, `agent_v2.py`, `memory_system.py` y la capa RAG. Las flechas indican flujo de datos: el planificador genera un plan JSON secuencial, el agente funcional lo ejecuta invocando herramientas, y el sistema de memoria preserva el contexto entre interacciones.

### 5.2 Decisiones de diseno justificadas

| Decision | Fundamento tecnico | Alineacion con requerimiento |
|---|---|---|
| LangChain sobre CrewAI | Menor complejidad para flujo secuencial de 4 herramientas; evita problemas de compatibilidad documentados | IE2 (framework adecuado) |
| GPT-4o con temperatura=0.1 | Minimiza alucinaciones en tareas de verificacion factual | IE1, IE4 |
| FAISS con fallback NumPy | Latencia O(1) aproximada; robustez ante ausencia de dependencias nativas | IE2, IE3 |
| 3 estrategias de memoria | Demuestra comprension de trade-offs entre contexto completo, ahorro de tokens y compresion | IE3, IE4 |
| Plan de 5 etapas | Cada etapa es observable, testeable y ajustable independientemente | IE5, IE7 |

---

## 6. Ejemplos de Flujos de Trabajo

### Ejemplo A: Inconsistencia detectada con persistencia

**Entrada:** *"Escena 14 — 2007. Bumblebee se gira hacia Sam y dice: 'Sam, debes llevar el AllSpark al Secretario de Defensa.'"*

**Flujo ejecutado:**
1. `extract_elements` -> `{characters: ["Bumblebee", "Sam"], objects: ["AllSpark"], year: "2007"}`
2. `retrieve_lore_for_elements` -> Recupera lore de Bumblebee (perdida de voz) y AllSpark (destruido en TF1)
3. `validate_against_lore` -> Detecta inconsistencia CRITICA: Bumblebee no tiene voz en 2007
4. `emit_verdict` -> Veredicto: INCONSISTENTE
5. `save_plan` + `write_continuity_report` -> Persisten plan JSON y reporte Markdown

**Salida:** Archivo `continuity_report_20260522_143022.md` con veredicto, severidad CRITICA, cita del lore y recomendacion de reemplazar dialogo por comunicacion via radio.

### Ejemplo B: Pregunta de seguimiento con memoria

**Usuario:** *"Que inconsistencias detectaste en total?"*  
**Agente:** *"En la sesion actual detecte una inconsistencia CRITICA: Bumblebee habla verbalmente en 2007, cuando su voz fue destruida antes de TF1. Segun el lore (char_002), se comunica exclusivamente mediante fragmentos de radio hasta el spin-off Bumblebee (1987)."*

La respuesta demuestra que el agente recupero el contexto de la validacion anterior sin reenviar el fragmento, gracias a `ConversationBufferMemory`.

---

## 7. Referencias

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, 33, 9459–9474. https://arxiv.org/abs/2005.11401

Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., ... & Wen, J. R. (2024). A survey on large language model based autonomous agents. *Frontiers of Computer Science*, 18(6), 186345. https://doi.org/10.1007/s11704-024-40231-1

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. *Proceedings of the International Conference on Learning Representations (ICLR)*. https://arxiv.org/abs/2210.03629

OpenAI. (2024). *Text embedding models*. https://platform.openai.com/docs/guides/embeddings

LangChain. (2024). *Memory types*. https://python.langchain.com/docs/modules/memory/

Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data*, 7(3), 535–547. https://arxiv.org/abs/1702.08734

---

*Documento generado conforme a la pauta de evaluacion EP2 (ISY0101).*
