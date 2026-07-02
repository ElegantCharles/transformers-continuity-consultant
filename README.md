# Consultor de Continuidad Narrativa — Transformers v2.0

> **Sistema RAG + Agente Deliberativo con Memoria y Planificacion Multi-Etapa**  
> Curso ISY0101 — Ingenieria de Soluciones con Inteligencia Artificial  
> Duoc UC · Profesor Roberto Eduardo Vega Araneda :D · Evaluacion Parcial N°2

---

## Descripcion del Proyecto

Este proyecto implementa un **Consultor de Continuidad Narrativa** para la saga cinematografica Transformers (universo Michael Bay, 2007–2017). La segunda entrega (EP2) evoluciona el sistema de un agente reactivo ReAct basico hacia un **agente deliberativo** que integra herramientas de consulta y escritura, memoria conversacional, planificacion multi-etapa y toma de decisiones adaptativa.

### Problema que resuelve

Los estudios de produccion de franquicias cinematograficas largas enfrentan el problema de la **incoherencia narrativa**: personajes que actuan fuera de su arco establecido, objetos que "reaparecen" despues de ser destruidos, protagonistas de distintas epocas que se cruzan sin justificacion. Validar manualmente cada guion contra el lore acumulado de 6 peliculas es costoso y propenso a errores humanos.

### Solucion propuesta

Un **agente deliberativo** que, dado un fragmento de guion:
1. **Planifica** una secuencia de 5 etapas de validacion antes de actuar
2. **Recupera** automaticamente fragmentos relevantes del lore canonico
3. **Valida** comparando el guion contra el lore con distintas herramientas especializadas
4. **Persiste** un dictamen estructurado con veredicto, inconsistencias, severidad y recomendacion
5. **Recuerda** el contexto de validaciones anteriores para responder preguntas de seguimiento

---

## Arquitectura del Sistema

### Diagrama de Orquestacion de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORQUESTACION DE COMPONENTES                        │
│                           Agente Deliberativo v2.0                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │   planning_     │     │   agent_v2.     │     │  memory_system  │       │
│   │   agent.ipynb   │     │      ipynb      │     │    .ipynb       │       │
│   │                 │     │  Agente funcional│     │                 │       │
│   │  Plan-and-Exec  │◄──►│  con memoria y  │◄───►│  3 estrategias  │       │
│   │  5 etapas       │     │  herramientas   │     │  de memoria     │       │
│   │                 │     │                 │     │                 │       │
│   └────────┬────────┘     └────────┬────────┘     └─────────────────┘       │
│            │                       │                                         │
│            │  Plan generado        │  Ejecucion adaptativa                  │
│            │  (JSON secuencial)    │  (tools + memory)                       │
│            │                       │                                         │
│            └───────────────────────┘                                         │
│                       │                                                      │
│                       ▼                                                      │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                     CAPA DE HERRAMIENTAS                        │       │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │       │
│   │  │ search_lore │  │validate_char│  │check_timelin│  │ write_ │ │       │
│   │  │             │  │   acter     │  │    e        │  │report  │ │       │
│   │  │  Consulta   │  │  Consulta   │  │  Consulta   │  │Escritura│ │       │
│   │  │  semantica  │  │  personajes │  │  temporal   │  │        │ │       │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───┬────┘ │       │
│   │         └─────────────────┴────────────────┴─────────────┘      │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                     INFRAESTRUCTURA RAG (EP1)                   │       │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │       │
│   │  │lore_database│  │transformers_│  │  evaluate   │  │ reports│ │       │
│   │  │    .py      │  │    rag.py   │  │    .py      │  │  /     │ │       │
│   │  │  20+ fragm  │  │ Embeddings  │  │  Metricas   │  │Output  │ │       │
│   │  │  dataclasses│  │  FAISS/GPT  │  │  TP/FP/FN   │  │  .md  │ │       │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘ │       │
│   └─────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Trabajo Automatizado (5 Etapas)

```
Entrada: Fragmento de guion
    │
    ▼
┌─────────────────────────────────────────┐
│ ETAPA 1: EXTRACCION                    │
│ Identifica personajes, eventos, objetos │
│ y ano usando LLM + parsing estructurado │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ ETAPA 2: RECUPERACION                  │
│ Para cada elemento extraido, busca     │
│ lore canonico relevante (top-k)        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ ETAPA 3: VALIDACION                    │
│ Compara guion vs lore. Detecta         │
│ inconsistencias con severidad          │
│ (CRITICA / MODERADA / MENOR)           │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    CRITICA            CONSISTENTE
         │                 │
         ▼                 ▼
   Salta a Dictamen   Salta a Dictamen
         │                 │
         └────────┬────────┘
                  ▼
┌─────────────────────────────────────────┐
│ ETAPA 4: DICTAMEN                        │
│ Emite veredicto + recomendacion          │
│ basado en evidencia acumulada            │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ ETAPA 5: PERSISTENCIA                  │
│ Guarda reporte Markdown en /reports      │
│ y plan de validacion en /plans           │
└─────────────────────────────────────────┘
```

### Por que un agente DELIBERATIVO (vs reactivo)

| Criterio | Agente Reactivo (EP1) | Agente Deliberativo (EP2) |
|---|---|---|
| **Razonamiento** | Decide la siguiente accion sobre la marcha (ReAct) | Planifica toda la secuencia antes de ejecutar |
| **Complejidad** | Adecuado para tareas simples de 1-2 pasos | Requerido para validacion multi-facetica |
| **Adaptabilidad** | Se pierde facilmente si un paso falla | Puede re-planificar o saltar etapas segun resultados |
| **Explicabilidad** | Dificil explicar por que tomo una decision | Cada etapa es observable y justificable |

La validacion de continuidad narrativa es inherentemente **deliberativa**: no basta con reaccionar al fragmento; es necesario descomponerlo en entidades, consultar multiples fuentes de lore, ponderar evidencias y emitir un dictamen estructurado.

---

## Estructura del Repositorio

```
transformers-continuity-consultant/
│
├── lore_database.py              # Base de datos del lore canonico (20+ fragmentos)
├── transformers_rag.py           # Pipeline RAG: embeddings + FAISS + GPT-4o
├── evaluate.py                   # Suite de evaluacion: 8 casos de prueba + metricas
│
├── agent_v2.ipynb                # Agente funcional con memoria + herramientas de escritura
├── planning_agent.ipynb          # Agente deliberativo: Plan-and-Execute 5 etapas
├── memory_system.ipynb           # 3 estrategias de memoria (Buffer, Window, Summary)
│
├── reports/                      # Reportes de continuidad generados (Markdown)
├── plans/                        # Planes de validacion ejecutados (JSON)
│
├── requirements.txt              # Dependencias del proyecto
├── .env.example                  # Plantilla de variables de entorno
├── .gitignore                    # Archivos excluidos de Git
└── README.md                     # Este archivo
```

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/transformers-continuity-consultant.git
cd transformers-continuity-consultant
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar la plantilla
cp .env.example .env

# Editar .env con tus credenciales
# GITHUB_TOKEN=tu_token_de_github
# OPENAI_BASE_URL=https://models.inference.ai.azure.com
```

> Para obtener un `GITHUB_TOKEN` con acceso a GitHub Models, visita:  
> [github.com/marketplace/models](https://github.com/marketplace/models)

---

## Como Ejecutar

### Infraestructura RAG (EP1, reutilizada)

```bash
jupyter notebook 1-lore_database.ipynb    # Explorar base de lore (20 fragmentos)
jupyter notebook 2-rag_pipeline.ipynb     # Ejecutar pipeline RAG con 4 casos de prueba
jupyter notebook 4-evaluation.ipynb       # Correr suite completa: accuracy, precision, recall, F1
```

### Agente v2 — Memoria y herramientas de escritura

```bash
jupyter notebook agent_v2.ipynb
```

Demuestra:
- Herramientas de consulta (`search_lore`, `validate_character`, `check_timeline`)
- Herramienta de escritura (`write_continuity_report` -> genera Markdown en `/reports`)
- Memoria conversacional (preguntas de seguimiento sobre analisis anteriores)

### Agente deliberativo — Planificacion multi-etapa

```bash
jupyter notebook planning_agent.ipynb
```

Demuestra:
- Planificacion de 5 etapas antes de ejecutar
- Toma de decisiones adaptativa: si detecta inconsistencia CRITICA, veredicto INCONSISTENTE
- Explicabilidad: cada paso del razonamiento es observable
- Persistencia del plan ejecutado en `/plans`

### Sistemas de memoria

```bash
jupyter notebook memory_system.ipynb
```

Demuestra:
- `ConversationBufferMemory`: historial completo (corto plazo)
- `ConversationBufferWindowMemory(k=2)`: ventana deslizante (ahorro de tokens)
- `ConversationSummaryMemory`: resumen automatico (largo plazo)

---

## EP3 — Observabilidad

### Generar logs
```bash
python run_evaluation_with_logs.py --mock   # sin API
python run_evaluation_with_logs.py          # con API real
```

### Ejecutar dashboard
```bash
streamlit run dashboard.py
```

### Archivos nuevos
| Archivo | Descripción |
|---------|-------------|
| `observability.py` | Módulo de métricas y logging |
| `run_evaluation_with_logs.py` | Ejecuta casos de prueba y genera logs |
| `dashboard.py` | Dashboard de monitoreo con Streamlit |
| `logs/` | Registros de ejecución (JSONL) |

## Conceptos Tecnicos Aplicados

### RAG (Retrieval-Augmented Generation)
Pipeline que combina recuperacion semantica (FAISS + embeddings OpenAI) con generacion de texto (GPT-4o) para producir respuestas basadas en evidencia real del canon, reduciendo alucinaciones.

### Embeddings Semanticos
`text-embedding-3-small` convierte texto en vectores de alta dimension. La similitud coseno mide cercania semantica entre fragmentos de guion y lore.

### FAISS (Facebook AI Similarity Search)
Indice vectorial optimizado para busqueda aproximada de vecinos mas cercanos (ANN). Fallback a NumPy si FAISS no esta disponible.

### Agente Deliberativo (Plan-and-Execute)
A diferencia de agentes reactivos (ReAct), el agente deliberativo descompone el objetivo en un plan secuencial antes de actuar. Permite priorizar etapas y ajustar el flujo ante inconsistencias criticas detectadas en etapas intermedias.

### Memoria Conversacional
- **Buffer**: Almacena todo el historial. Ideal para sesiones cortas donde el contexto completo es relevante.
- **Window**: Conserva las ultimas *k* interacciones. Util para flujos prolongados donde el contexto remoto pierde relevancia.
- **Summary**: Resume automaticamente el historial cuando crece. Preserva tokens en conversaciones muy largas.

### Chunking Atomico
El lore fue dividido en fragmentos atomicos (un hecho o personaje por fragmento) para maximizar la precision del retrieval. Fragmentos demasiado largos "diluyen" la senal semantica.

---

## Tecnologias Utilizadas

| Tecnologia | Version | Proposito |
|-----------|---------|-----------|
| Python | 3.11+ | Lenguaje base |
| OpenAI API | 1.30+ | Embeddings (`text-embedding-3-small`) y generacion (`gpt-4o`) |
| LangChain | 0.2+ | Framework de agentes, herramientas, memoria y planificacion |
| FAISS-CPU | 1.8+ | Vector store para busqueda semantica |
| NumPy | 1.26+ | Operaciones vectoriales y fallback sin FAISS |

---

## Justificacion Tecnica de Componentes

| Componente | Eleccion | Justificacion |
|---|---|---|
| **LangChain AgentExecutor** | Framework oficial para agentes con herramientas | Abstrae el ciclo de observacion-decision-accion, maneja errores de parsing y limita iteraciones maximas. Compatible con GitHub Models API. |
| **ConversationBufferMemory** | Memoria de corto plazo | Las sesiones de validacion de guiones rara vez exceden 10-15 interacciones. Buffer completo garantiza coherencia sin perdida de contexto. |
| **Plan-and-Execute** | Planificacion deliberativa | La validacion requiere secuenciar etapas dependientes (no puedes validar sin antes recuperar lore). El plan se ajusta dinamicamente si una etapa detecta inconsistencias criticas. |
| **GPT-4o + temperatura=0.1** | Modelo generativo | Baja temperatura minimiza creatividad no deseada en tareas de verificacion factual. GPT-4o ofrece balance entre costo, velocidad y calidad de reasoning. |
| **FAISS + embeddings OpenAI** | Recuperacion semantica | FAISS reduce latencia de busqueda. Embeddings de OpenAI superan a modelos locales en calidad semantica para dominio cinematografico especifico. |

---

## Referencias

- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS. https://arxiv.org/abs/2005.11401
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023. https://arxiv.org/abs/2210.03629
- Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., ... & Wen, J. R. (2024). *A Survey on Large Language Model based Autonomous Agents*. Frontiers of Computer Science. https://doi.org/10.1007/s11704-024-40231-1
- OpenAI. (2024). *Text Embedding Models*. https://platform.openai.com/docs/guides/embeddings
- LangChain. (2024). *Agent Types — ReAct*. https://python.langchain.com/docs/modules/agents/agent_types/react
- LangChain. (2024). *Memory types*. https://python.langchain.com/docs/modules/memory/
- Johnson, J., Douze, M., & Jégou, H. (2019). *Billion-scale similarity search with GPUs*. IEEE Transactions on Big Data. https://arxiv.org/abs/1702.08734
