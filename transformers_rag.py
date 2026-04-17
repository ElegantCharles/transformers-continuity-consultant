import os
import json
import time
from dataclasses import dataclass

import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from lore_database import get_all_fragments, LoreFragment


EMBEDDING_MODEL = "text-embedding-3-small"
GENERATION_MODEL = "gpt-4o"
TOP_K = 4
TEMPERATURE = 0.1


@dataclass
class ContinuityReport:
    fragment_analyzed: str
    verdict: str
    elements_detected: list[str]
    inconsistencies: list[dict]
    recommendation: str
    retrieved_lore: list[str]
    confidence_score: float
    processing_time_ms: float


@dataclass
class RetrievalResult:
    text: str
    similarity_score: float
    fragment_id: str
    category: str


class TransformersVectorStore:

    def __init__(self, client: OpenAI):
        self.client = client
        # cliente separado para embeddings
        self.embed_client = OpenAI(
            base_url=os.getenv("OPENAI_EMBEDDINGS_URL", os.getenv("OPENAI_BASE_URL")),
            api_key=os.getenv("GITHUB_TOKEN"),
        )
        self.fragments: list[LoreFragment] = []
        self.embeddings = None
        self._faiss_index = None
        self._use_faiss = False
        try:
            import faiss
            self._use_faiss = True
            print("FAISS disponible")
        except ImportError:
            print("FAISS no encontrado, usando numpy")

    def _get_embedding(self, text: str) -> np.ndarray:
        r = self.embed_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text.replace("\n", " "),
        )
        return np.array(r.data[0].embedding, dtype=np.float32)

    def _cosine_sim(self, a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def build_index(self):
        print("Construyendo indice...")
        self.fragments = get_all_fragments()
        embs = []
        for i, frag in enumerate(self.fragments):
            print(f"  [{i+1}/{len(self.fragments)}] {frag.id}")
            embs.append(self._get_embedding(frag.text))
        self.embeddings = np.vstack(embs)

        if self._use_faiss:
            import faiss
            dim = self.embeddings.shape[1]
            self._faiss_index = faiss.IndexFlatIP(dim)
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            self._faiss_index.add(self.embeddings / norms)

        print(f"Indice listo: {len(self.fragments)} fragmentos")

    def search(self, query: str, top_k: int = TOP_K) -> list[RetrievalResult]:
        if self.embeddings is None:
            raise RuntimeError("Llama a build_index() primero")

        qemb = self._get_embedding(query)

        if self._use_faiss:
            import faiss
            norm = np.linalg.norm(qemb)
            qnorm = (qemb / norm).reshape(1, -1)
            scores, indices = self._faiss_index.search(qnorm, top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:
                    frag = self.fragments[idx]
                    results.append(RetrievalResult(frag.text, float(score), frag.id, frag.category))
        else:
            sims = [self._cosine_sim(qemb, self.embeddings[i]) for i in range(len(self.fragments))]
            results = []
            for idx in np.argsort(sims)[::-1][:top_k]:
                frag = self.fragments[idx]
                results.append(RetrievalResult(frag.text, sims[idx], frag.id, frag.category))

        return results


SYSTEM_PROMPT = """Eres el Consultor de Continuidad Narrativa del universo cinematografico
Transformers (Michael Bay, 2007-2017). Analiza fragmentos de guion y detecta inconsistencias
con el lore canonico.

Reglas:
1. Basa tu analisis solo en el contexto de lore proporcionado.
2. Si el contexto no cubre algo, indicalo en vez de inventar.
3. Cita el fragmento exacto del lore que contradice el guion.
4. Severidades: CRITICA (rompe la trama), MODERADA (contradice hechos), MENOR (detalle).

Responde siempre en JSON puro:
{
  "verdict": "CONSISTENTE | INCONSISTENTE | REQUIERE_REVISION",
  "elements_detected": ["elemento1"],
  "inconsistencies": [
    {
      "description": "descripcion",
      "guion_says": "lo que dice el guion",
      "lore_says": "lo que dice el lore",
      "severity": "CRITICA | MODERADA | MENOR",
      "lore_source": "id del fragmento"
    }
  ],
  "recommendation": "accion para el guionista",
  "confidence_score": 0.95
}"""


class ContinuityConsultant:

    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("GITHUB_TOKEN"),
        )
        self.vector_store = TransformersVectorStore(self.client)
        self._ready = False

    def initialize(self):
        self.vector_store.build_index()
        self._ready = True
        print("Consultor listo\n")

    def _build_prompt(self, fragment, retrieved):
        context = "\n".join([
            f"[{r.fragment_id} | {r.category} | sim: {r.similarity_score:.2f}]\n{r.text}"
            for r in retrieved
        ])
        return f"CONTEXTO LORE:\n{context}\n\nGUION:\n{fragment}\n\nAnaliza y responde en JSON."

    def analyze(self, fragment: str) -> ContinuityReport:
        if not self._ready:
            raise RuntimeError("Llama a initialize() primero")

        t0 = time.time()
        retrieved = self.vector_store.search(fragment)
        prompt = self._build_prompt(fragment, retrieved)

        response = self.client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        elapsed = (time.time() - t0) * 1000

        try:
            p = json.loads(raw)
            return ContinuityReport(
                fragment_analyzed=fragment,
                verdict=p.get("verdict", "REQUIERE_REVISION"),
                elements_detected=p.get("elements_detected", []),
                inconsistencies=p.get("inconsistencies", []),
                recommendation=p.get("recommendation", ""),
                retrieved_lore=[r.text[:120] + "..." for r in retrieved],
                confidence_score=float(p.get("confidence_score", 0.5)),
                processing_time_ms=round(elapsed, 2),
            )
        except json.JSONDecodeError:
            return ContinuityReport(
                fragment_analyzed=fragment,
                verdict="REQUIERE_REVISION",
                elements_detected=[],
                inconsistencies=[{"description": raw, "severity": "DESCONOCIDA",
                                   "guion_says": "", "lore_says": "", "lore_source": ""}],
                recommendation="JSON invalido, revisar manualmente",
                retrieved_lore=[r.text[:120] + "..." for r in retrieved],
                confidence_score=0.0,
                processing_time_ms=round(elapsed, 2),
            )

    def print_report(self, report: ContinuityReport):
        print("\n" + "="*60)
        print(f"Fragmento: \"{report.fragment_analyzed[:70]}...\"")
        print(f"Veredicto: {report.verdict}  |  Confianza: {report.confidence_score:.0%}")
        print(f"Elementos: {', '.join(report.elements_detected) or 'ninguno'}")
        if report.inconsistencies:
            print(f"\nInconsistencias ({len(report.inconsistencies)}):")
            for inc in report.inconsistencies:
                print(f"  [{inc.get('severity')}] {inc.get('description')}")
                print(f"    guion: {inc.get('guion_says')}")
                print(f"    lore:  {inc.get('lore_says')}")
        else:
            print("Sin inconsistencias.")
        print(f"\nRecomendacion: {report.recommendation}")
        print("="*60)


if __name__ == "__main__":
    c = ContinuityConsultant()
    c.initialize()

    tests = [
        "Escena 12: Bumblebee mira a Sam y dice en voz alta: 'Sam, confia en mi, juntos podemos salvar el AllSpark.'",
        "El año es 2010. Sam Witwicky y Cade Yeager se encuentran en el hangar de la NEST.",
        "Los cientificos del Sector 7 presentan el AllSpark intacto recuperado del oceano Artico.",
        "Optimus Prime despliega su espada y enfrenta a Megatron en Mission City mientras Sam huye.",
    ]

    for t in tests:
        report = c.analyze(t)
        c.print_report(report)
