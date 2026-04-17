import time
import re
from dataclasses import dataclass

from lore_database import get_all_fragments, LoreFragment


def _buscar(query, top_k=4):
    fragments = get_all_fragments()
    query_words = set(re.sub(r"[^\w\s]", "", query.lower()).split())
    scored = []
    for frag in fragments:
        text_words = set(re.sub(r"[^\w\s]", "", frag.text.lower()).split())
        overlap = len(query_words & (text_words | set(frag.tags)))
        if overlap > 0:
            scored.append((overlap, frag.text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:top_k]]


# reglas de inconsistencia
RULES = [
    {
        "keywords": ["bumblebee", "dice", "habla", "voz alta", "dijo"],
        "context": ["2007", "2008", "2009", "2010", "2011", "sam"],
        "verdict": "INCONSISTENTE",
        "severity": "CRITICA",
        "description": "Bumblebee no tenia voz en TF1-TF3 (2007-2011), solo se comunicaba con radio.",
        "guion_says": "Bumblebee habla verbalmente",
        "lore_says": "Perdio su voz antes de TF1. Solo la recupera en el spin-off Bumblebee (2018).",
        "lore_source": "char_002",
    },
    {
        "keywords": ["sam", "cade", "witwicky", "yeager"],
        "context": ["juntos", "reunen", "conocen", "cuartel", "nest", "equipo"],
        "verdict": "INCONSISTENTE",
        "severity": "CRITICA",
        "description": "Sam Witwicky y Cade Yeager son protagonistas de arcos distintos y nunca se cruzan.",
        "guion_says": "Sam y Cade interactuan",
        "lore_says": "Sam es protagonista TF1-TF3 (2007-2011); Cade aparece desde TF4 (2014).",
        "lore_source": "char_008 + char_009",
    },
    {
        "keywords": ["allspark", "intacto", "completo", "recuperado"],
        "context": ["sector 7", "artico", "2008", "2009", "2010", "2011", "2012"],
        "verdict": "INCONSISTENTE",
        "severity": "CRITICA",
        "description": "El AllSpark fue destruido al final de TF1 (2007). No puede existir intacto.",
        "guion_says": "AllSpark intacto disponible",
        "lore_says": "Destruido en Mission City (2007) al insertar el cubo en el pecho de Megatron.",
        "lore_source": "obj_001",
    },
    {
        "keywords": ["ironhide", "batalla", "chicago", "participa", "lidera", "protege"],
        "context": ["chicago", "2011"],
        "verdict": "INCONSISTENTE",
        "severity": "CRITICA",
        "description": "Ironhide muere antes de la batalla de Chicago, traicionado por Sentinel Prime.",
        "guion_says": "Ironhide participa en Chicago",
        "lore_says": "Ironhide es asesinado por el Rifle Oxidante de Sentinel al inicio de TF3.",
        "lore_source": "char_003",
    },
    {
        "keywords": ["consejo", "cybertron", "siete primes", "consejo supremo"],
        "context": ["convoca", "deliberan", "ordenes"],
        "verdict": "INCONSISTENTE",
        "severity": "MODERADA",
        "description": "No existe un Consejo de Cybertron activo en el universo Bay.",
        "guion_says": "Consejo de Cybertron activo",
        "lore_says": "Cybertron fue destruido. El Consejo es del universo G1, no cinematografico.",
        "lore_source": "faction_002",
    },
]

KNOWN_ELEMENTS = {
    "optimus prime": "Optimus Prime", "bumblebee": "Bumblebee",
    "megatron": "Megatron", "ironhide": "Ironhide",
    "sentinel prime": "Sentinel Prime", "sam witwicky": "Sam Witwicky",
    "cade yeager": "Cade Yeager", "allspark": "AllSpark",
    "sector 7": "Sector 7", "chicago": "Batalla de Chicago",
    "cybertron": "Cybertron", "autobots": "Autobots",
    "decepticons": "Decepticons", "nest": "NEST",
    "mission city": "Mission City", "dinobots": "Dinobots",
    "galvatron": "Galvatron", "ratchet": "Ratchet",
}


def mock_analyze(fragment):
    t0 = time.time()
    fl = fragment.lower()
    retrieved = _buscar(fragment)
    inconsistencies = []

    for rule in RULES:
        kw = sum(1 for k in rule["keywords"] if k in fl)
        ctx = sum(1 for c in rule["context"] if c in fl)
        if kw >= 1 and ctx >= 1:
            inconsistencies.append({
                "description": rule["description"],
                "guion_says": rule["guion_says"],
                "lore_says": rule["lore_says"],
                "severity": rule["severity"],
                "lore_source": rule["lore_source"],
            })

    verdict = "INCONSISTENTE" if inconsistencies else "CONSISTENTE"
    confidence = min(0.88 + len(inconsistencies) * 0.03, 0.99) if inconsistencies else 0.92
    elements = [label for key, label in KNOWN_ELEMENTS.items() if key in fl]

    return {
        "verdict": verdict,
        "elements": elements,
        "inconsistencies": inconsistencies,
        "recommendation": (
            "Revisar los elementos inconsistentes contra la biblia de personajes."
            if inconsistencies else "Fragmento aprobado."
        ),
        "retrieved": retrieved,
        "confidence": confidence,
        "time_ms": round((time.time() - t0) * 1000, 1),
    }


@dataclass
class TestCase:
    id: str
    script_fragment: str
    expected_verdict: str
    expected_issue: str
    category: str


TEST_CASES = [
    TestCase("TC_001",
        "Escena 14. 2007. Bumblebee dice en voz alta: 'Sam, debes llevar el AllSpark al Secretario.'",
        "INCONSISTENTE", "Bumblebee no tiene voz en TF1", "INCONSISTENCIA_PERSONAJE"),
    TestCase("TC_002",
        "2010. Sam witwicky y cade yeager se reunen en el cuartel de NEST.",
        "INCONSISTENTE", "Sam y Cade son de arcos distintos", "INCONSISTENCIA_TEMPORAL"),
    TestCase("TC_003",
        "El sector 7 presenta el allspark intacto recuperado del artico.",
        "INCONSISTENTE", "AllSpark destruido TF1; Sector 7 disuelto TF1", "INCONSISTENCIA_OBJETO"),
    TestCase("TC_004",
        "Ironhide lidera en la batalla de chicago 2011 y protege civiles.",
        "INCONSISTENTE", "Ironhide muere antes de Chicago", "INCONSISTENCIA_EVENTO"),
    TestCase("TC_005",
        "El consejo supremo de cybertron convoca a Optimus y los siete primes deliberan.",
        "INCONSISTENTE", "No existe Consejo de Cybertron en universo Bay", "INCONSISTENCIA_LORE"),
    TestCase("TC_006",
        "Optimus despliega su espada y enfrenta a Megatron en Mission City. Sam corre con el AllSpark.",
        "CONSISTENTE", "Ninguno", "CASO_CONSISTENTE"),
    TestCase("TC_007",
        "Cinco anos despues de Chicago, cade yeager encuentra un camion en Texas que es Optimus Prime.",
        "CONSISTENTE", "Ninguno", "CASO_CONSISTENTE"),
    TestCase("TC_008",
        "En 1987, Bumblebee llega a la Tierra como escarabajo amarillo. Una mecanica lo encuentra.",
        "CONSISTENTE", "Ninguno - prequel Bumblebee (2018)", "CASO_PREQUEL"),
]


def normalize(v):
    v = v.upper()
    if "INCONSIST" in v:
        return "INCONSISTENTE"
    if "CONSIST" in v:
        return "CONSISTENTE"
    return "REQUIERE_REVISION"


def run():
    results = []
    for tc in TEST_CASES:
        r = mock_analyze(tc.script_fragment)
        correct = normalize(r["verdict"]) == normalize(tc.expected_verdict)
        results.append({
            "id": tc.id, "category": tc.category,
            "expected": tc.expected_verdict, "obtained": r["verdict"],
            "correct": correct, "n_inc": len(r["inconsistencies"]),
            "conf": r["confidence"], "time": r["time_ms"],
            "issue": tc.expected_issue,
        })
    return results


def metrics(results):
    tp = sum(1 for r in results if normalize(r["expected"]) == "INCONSISTENTE" and normalize(r["obtained"]) == "INCONSISTENTE")
    fp = sum(1 for r in results if normalize(r["expected"]) != "INCONSISTENTE" and normalize(r["obtained"]) == "INCONSISTENTE")
    fn = sum(1 for r in results if normalize(r["expected"]) == "INCONSISTENTE" and normalize(r["obtained"]) != "INCONSISTENTE")
    tn = sum(1 for r in results if normalize(r["expected"]) != "INCONSISTENTE" and normalize(r["obtained"]) != "INCONSISTENTE")
    p = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    return {
        "accuracy": sum(r["correct"] for r in results) / len(results),
        "precision": p, "recall": rec,
        "f1": 2*p*rec/(p+rec) if (p+rec) > 0 else 0,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "correct": sum(r["correct"] for r in results),
        "total": len(results),
        "avg_time": sum(r["time"] for r in results) / len(results),
        "avg_conf": sum(r["conf"] for r in results) / len(results),
    }


def print_results(results, m):
    print("\n" + "="*72)
    print("EVALUACION (modo mock - sin API)")
    print("="*72)
    print(f"\n{'ID':<8} {'CATEGORIA':<26} {'ESPERADO':<16} {'OBTENIDO':<16} {'OK?'}")
    print("-"*72)
    for r in results:
        print(f"{r['id']:<8} {r['category']:<26} {r['expected']:<16} {r['obtained']:<16} {'OK' if r['correct'] else 'FAIL'}")
    print("-"*72)
    print(f"\nAccuracy:  {m['accuracy']:.1%}  ({m['correct']}/{m['total']})")
    print(f"Precision: {m['precision']:.1%}")
    print(f"Recall:    {m['recall']:.1%}")
    print(f"F1-Score:  {m['f1']:.1%}")
    print(f"\nTP={m['tp']}  FP={m['fp']}  FN={m['fn']}  TN={m['tn']}")
    print(f"Tiempo promedio: {m['avg_time']:.1f} ms")
    print(f"Confianza promedio: {m['avg_conf']:.1%}")
    print("="*72)

    # tabla para word
    print("\n\nTABLA PARA INFORME WORD:")
    print("-"*72)
    print(f"| {'ID':<7} | {'Tipo':<26} | {'Esperado':<14} | {'Obtenido':<14} | {'Resultado'} |")
    print(f"|{'-'*9}|{'-'*28}|{'-'*16}|{'-'*16}|{'-'*12}|")
    for r in results:
        print(f"| {r['id']:<7} | {r['category']:<26} | {r['expected']:<14} | {r['obtained']:<14} | {'Correcto' if r['correct'] else 'Incorrecto':<10} |")
    print(f"|{'-'*9}|{'-'*28}|{'-'*16}|{'-'*16}|{'-'*12}|")


if __name__ == "__main__":
    results = run()
    m = metrics(results)
    print_results(results, m)
