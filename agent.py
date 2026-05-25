import os
import re
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent

# FIX #4: Importaciones actualizadas desde langchain_core (LangChain 0.2+).
# Las rutas antiguas `langchain.tools` y `langchain.prompts` fueron deprecadas
# y pueden generar warnings o fallar en versiones recientes del framework.
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate

from lore_database import get_all_fragments, get_fragments_by_category, LoreFragment


def _buscar(query: str, fragments: list[LoreFragment], top_k=3) -> list[str]:
    query_words = set(re.sub(r"[^\w\s]", "", query.lower()).split())
    scored = []
    for frag in fragments:
        text_words = set(re.sub(r"[^\w\s]", "", frag.text.lower()).split())
        tag_words = set(frag.tags)
        overlap = len(query_words & (text_words | tag_words))
        if overlap > 0:
            scored.append((overlap, frag.text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:top_k]]


@tool
def search_lore(query: str) -> str:
    """Busca informacion en el lore canonico de Transformers. Usa para verificar hechos generales."""
    results = _buscar(query, get_all_fragments(), top_k=3)
    if not results:
        return "No se encontraron resultados para esa consulta."
    out = f"Lore recuperado para '{query}':\n\n"
    for i, t in enumerate(results, 1):
        out += f"[{i}] {t}\n\n"
    return out.strip()


@tool
def validate_character(character_name: str) -> str:
    """Verifica el estado canonico de un personaje: apariciones, habilidades, muerte, afiliacion."""
    frags = get_fragments_by_category("PERSONAJE")
    name_lower = character_name.lower()
    relevant = [
        f.text for f in frags
        if name_lower in f.text.lower() or any(name_lower in tag for tag in f.tags)
    ]
    if not relevant:
        relevant = _buscar(character_name, get_all_fragments(), top_k=2)
    if not relevant:
        return f"Personaje '{character_name}' no encontrado en el lore."
    return f"Estado canonico de '{character_name}':\n\n" + "\n\n".join(f"- {t}" for t in relevant)


@tool
def check_timeline(year_and_event: str) -> str:
    """Valida si un evento es coherente con la linea temporal de la saga. Formato: '2009 - descripcion del evento'."""
    frags = get_fragments_by_category("TIMELINE") + get_fragments_by_category("EVENTO")
    results = _buscar(year_and_event, frags, top_k=4)
    if not results:
        return "No se encontraron eventos canonicos para ese periodo."
    return f"Timeline canonico para '{year_and_event}':\n\n" + "\n\n".join(
        f"[{i+1}] {t}" for i, t in enumerate(results)
    )


REACT_TEMPLATE = """Eres el Consultor de Continuidad de la saga Transformers (Michael Bay, 2007-2017).
Analiza fragmentos de guion y determina si son consistentes con el lore canonico.

Herramientas disponibles:
{tools}

Formato:
Pregunta: el fragmento o consulta a analizar
Pensamiento: que herramienta necesito y por que
Accion: [{tool_names}]
Entrada de Accion: input para la herramienta
Observacion: resultado
... (repite hasta tener suficiente info)
Pensamiento: tengo suficiente informacion
Respuesta Final:
  VEREDICTO: [CONSISTENTE / INCONSISTENTE / REQUIERE_REVISION]
  ELEMENTOS: [lista]
  INCONSISTENCIAS: [descripcion o ninguna]
  RECOMENDACION: [accion para el guionista]

Usa al menos 2 herramientas antes del veredicto. Cita el lore que contradice el guion.

Pregunta: {input}
Pensamiento: {agent_scratchpad}"""

PROMPT = PromptTemplate.from_template(REACT_TEMPLATE)


class ContinuityAgent:
    def __init__(self, verbose=True):
        self.llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("GITHUB_TOKEN"),
            model="gpt-4o",
            temperature=0.1,
        )
        self.tools = [search_lore, validate_character, check_timeline]
        self.executor = AgentExecutor(
            agent=create_react_agent(self.llm, self.tools, PROMPT),
            tools=self.tools,
            verbose=verbose,
            max_iterations=6,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

    def run(self, fragment: str):
        print(f"\n{'='*60}\nAnalizando: \"{fragment[:70]}...\"\n{'='*60}")
        result = self.executor.invoke({"input": fragment})
        print(f"\nVeredicto final:\n{result['output']}\n{'='*60}\n")
        return result


if __name__ == "__main__":
    agent = ContinuityAgent(verbose=True)

    agent.run(
        "Escena 3 - 2007: Bumblebee se dirige a Sam y dice claramente: "
        "'Sam, debes proteger el AllSpark. Confia en mi.'"
    )
    agent.run(
        "2009. Sam Witwicky y Cade Yeager trabajan juntos en el cuartel de NEST "
        "para analizar los fragmentos del AllSpark."
    )
