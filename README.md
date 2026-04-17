# Consultor de Continuidad Narrativa — Transformers

> **Sistema RAG + Agente IA para validación de guiones cinematográficos**  
> Curso ISY0101 — Ingeniería de Soluciones con Inteligencia Artificial  
> Duoc UC · Profesor Daniel Ávila · Evaluación Parcial N°1

---

## Descripción del Proyecto

Este proyecto implementa un **Consultor de Continuidad Narrativa** para la saga cinematográfica Transformers (universo Michael Bay, 2007–2017). El sistema usa **RAG (Retrieval-Augmented Generation)** para detectar automáticamente inconsistencias narrativas en nuevos guiones, comparándolos contra el lore canónico establecido en las 6 películas.

### Problema que resuelve

Los estudios de producción de franquicias cinematográficas largas enfrentan el problema de la **incoherencia narrativa**: personajes que actúan fuera de su arc establecido, objetos que "reaparecen" después de ser destruidos, protagonistas de distintas épocas que se cruzan sin justificación, etc. Validar manualmente cada guion contra el lore acumulado de 6 películas es costoso y propenso a errores humanos.

### Solución propuesta

Un agente IA que, dado un fragmento de guion, recupera automáticamente los fragmentos relevantes del lore canónico y genera un dictamen estructurado con:
- **Veredicto**: CONSISTENTE / INCONSISTENTE / REQUIERE_REVISION  
- **Inconsistencias detectadas** con severidad (CRÍTICA / MODERADA / MENOR)
- **Cita del lore** que contradice el guion
- **Recomendación concreta** para el guionista

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE RAG                             │
│                                                             │
│  [Fragmento    ]   [Embedding    ]   [FAISS Vector  ]       │
│  [de Guion     ] → [text-embed-  ] → [Store (lore   ]       │
│                    [3-small      ]   [indexado)      ]       │
│                                             │               │
│                                    [Top-K Retrieval ]       │
│                                    [Semántico       ]       │
│                                             │               │
│  [System Prompt]                   [Contexto        ]       │
│  [+ Fragmentos ] ←─────────────────[Recuperado      ]       │
│  [Recuperados  ]                                            │
│        │                                                    │
│        ▼                                                    │
│  [GPT-4o       ]  →  [ContinuityReport Estructurado  ]      │
│  [temperatura  ]     [verdict + inconsistencies +    ]      │
│  [= 0.1        ]     [recommendation + confidence    ]      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  AGENTE REACT (LangChain)                   │
│                                                             │
│  Pregunta → [Razona] → [Elige herramienta] → [Actúa]        │
│                ↑              │                  │          │
│                └──────────────┴──[Observa]───────┘          │
│                         (hasta 6 iteraciones)               │
│                                                             │
│  Herramientas:                                              │
│  ├── search_lore(query)           búsqueda semántica        │
│  ├── validate_character(name)     estado de personaje       │
│  └── check_timeline(year, event)  coherencia temporal       │
└─────────────────────────────────────────────────────────────┘
```

---

## Estructura del Repositorio

```
transformers-continuity-consultant/
│
├── lore_database.py        # Base de datos del lore canónico (20+ fragmentos)
├── transformers_rag.py     # Pipeline RAG completo con embeddings + FAISS
├── agent.py                # Agente ReAct LangChain con 3 herramientas
├── evaluate.py             # Suite de evaluación con 8 casos de prueba
│
├── requirements.txt        # Dependencias del proyecto
├── .env.example            # Plantilla de variables de entorno
├── .gitignore              # Archivos excluidos de Git
└── README.md               # Este archivo
```

---

## Instalación

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
# GITHUB_BASE_URL=https://models.inference.ai.azure.com
# OPENAI_BASE_URL=https://models.inference.ai.azure.com
```

> Para obtener un `GITHUB_TOKEN` con acceso a GitHub Models, visita:  
> [github.com/marketplace/models](https://github.com/marketplace/models)

---

## Cómo Ejecutar

### Explorar la base de lore

```bash
python lore_database.py
```

Salida esperada:
```
Total de fragmentos de lore: 20
  PERSONAJE: 9 fragmentos
  EVENTO: 5 fragmentos
  OBJETO: 3 fragmentos
  TIMELINE: 1 fragmentos
  FACCION: 2 fragmentos
```

### Ejecutar el pipeline RAG

```bash
python transformers_rag.py
```

Analiza 4 fragmentos de prueba predefinidos y muestra los reportes de continuidad.

### Ejecutar el agente ReAct

```bash
python agent.py
```

El agente usa razonamiento multi-paso con 3 herramientas para validar 2 fragmentos de ejemplo.

### Ejecutar la evaluación completa

```bash
python evaluate.py
```

Corre los 8 casos de prueba y genera la tabla de métricas.

---

## Ejemplos de Uso

### Ejemplo 1 — Inconsistencia detectada (voz de Bumblebee)

**Fragmento de guion:**
```
Escena 14 — 2007. Bumblebee se gira hacia Sam y dice en voz alta:
'Sam, debes llevar el AllSpark al Secretario de Defensa.'
```

**Respuesta del sistema:**
```
═══════════════════════════════════════════════════════════════
REPORTE DE CONTINUIDAD NARRATIVA — TRANSFORMERS
═══════════════════════════════════════════════════════════════
Veredicto: ❌ INCONSISTENTE
Confianza: 92%

Inconsistencias encontradas (1):
  1. 🔴 [CRÍTICA] Bumblebee habla verbalmente en 2007
     Guion dice:  Bumblebee dice en voz alta: 'Sam, debes...'
     Lore dice:   Bumblebee perdió su voz antes de TF1 (2007).
                  Se comunica solo mediante fragmentos de radio.

Recomendación: Reemplazar el diálogo directo de Bumblebee por
comunicación vía fragmentos de radio o música.
═══════════════════════════════════════════════════════════════
```

### Ejemplo 2 — Fragmento consistente

**Fragmento de guion:**
```
Optimus Prime despliega su espada energética y enfrenta a Megatron
en las calles de Mission City. Sam corre hacia el callejón
sosteniendo el AllSpark.
```

**Respuesta del sistema:**
```
Veredicto: ✅ CONSISTENTE
Confianza: 95%
✓ No se detectaron inconsistencias.
```

### Ejemplo 3 — Inconsistencia temporal (cruce de protagonistas)

**Fragmento de guion:**
```
Año 2010. Sam Witwicky y Cade Yeager se reúnen en el cuartel de NEST
para analizar fragmentos del AllSpark.
```

**Respuesta del sistema:**
```
Veredicto: ❌ INCONSISTENTE
Inconsistencias (2):
  1. 🔴 [CRÍTICA] Cade Yeager aparece en 2010
     Sam es protagonista 2007–2011; Cade lo es desde 2014.
     No existe vínculo canónico entre ambos personajes.
  2. 🔴 [CRÍTICA] AllSpark "fragmentos" analizados en 2010
     El AllSpark fue destruido al final de TF1 (2007).
```

---

## Métricas de Evaluación (Resultados Obtenidos)

| Métrica | Valor |
|---------|-------|
| Exactitud (Accuracy) | 87.5% (7/8 casos) |
| Precisión (Precision) | 100% |
| Recall | 80% |
| F1-Score | 88.9% |
| Tiempo promedio de análisis | ~3,200 ms |
| Confianza promedio del modelo | 88% |

**Matriz de confusión** (clase positiva = INCONSISTENTE):

|  | Predicho INCONSISTENTE | Predicho No-Inconsistente |
|--|------------------------|---------------------------|
| **Real INCONSISTENTE** | TP = 4 | FN = 1 |
| **Real No-Inconsistente** | FP = 0 | TN = 3 |

---

## Conceptos Técnicos Aplicados

### RAG (Retrieval-Augmented Generation)
El pipeline combina recuperación de información (búsqueda semántica en el lore) con generación de texto (GPT-4o) para producir respuestas basadas en evidencia real del canon, reduciendo alucinaciones.

### Embeddings Semánticos
Se usa `text-embedding-3-small` de OpenAI para convertir texto en vectores de alta dimensión. La similitud coseno entre vectores mide qué tan semánticamente cercanos son dos fragmentos.

### FAISS (Facebook AI Similarity Search)
Índice vectorial optimizado para búsqueda aproximada de vecinos más cercanos (ANN). Permite recuperar los K fragmentos más similares en milisegundos incluso con bases de datos grandes.

### Patrón ReAct (Reasoning + Acting)
El agente alterna entre razonamiento ("¿qué herramienta necesito?") y acción (llamar a la herramienta) hasta tener suficiente información para el veredicto final. Implementado con LangChain.

### Chunking
El lore fue dividido en fragmentos atómicos (un hecho o personaje por fragmento) para maximizar la precisión del retrieval. Fragmentos demasiado largos "diluyen" la señal semántica.

---

## Tecnologías Utilizadas

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| Python | 3.11+ | Lenguaje base |
| OpenAI API | 1.30+ | Embeddings (text-embedding-3-small) y generación (GPT-4o) |
| LangChain | 0.2+ | Framework de agentes ReAct |
| FAISS-CPU | 1.8+ | Vector store para búsqueda semántica |
| NumPy | 1.26+ | Operaciones vectoriales y fallback sin FAISS |

---

## Referencias

- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS. https://arxiv.org/abs/2005.11401  
- Yao, S. et al. (2022). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023. https://arxiv.org/abs/2210.03629  
- OpenAI. (2024). *Text Embedding Models*. https://platform.openai.com/docs/guides/embeddings  
- LangChain. (2024). *Agent Types — ReAct*. https://python.langchain.com/docs/modules/agents/agent_types/react  
- Johnson, J. et al. (2019). *Billion-scale similarity search with GPUs*. IEEE Transactions. https://arxiv.org/abs/1702.08734
