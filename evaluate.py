import time
from dataclasses import dataclass

from transformers_rag import ContinuityConsultant, ContinuityReport


@dataclass
class TestCase:
    id: str
    script_fragment: str
    expected_verdict: str
    expected_issue: str
    category: str


TEST_CASES = [
    TestCase(
        id="TC_001",
        script_fragment=(
            "Escena 14. 2007. Bumblebee se gira hacia Sam y dice en voz alta: "
            "'Sam, debes llevar el AllSpark al Secretario de Defensa.'"
        ),
        expected_verdict="INCONSISTENTE",
        expected_issue="Bumblebee no tiene voz en TF1; usa solo radio",
        category="INCONSISTENCIA_PERSONAJE",
    ),
    TestCase(
        id="TC_002",
        script_fragment=(
            "Año 2010. Sam Witwicky y Cade Yeager se reunen en el cuartel de NEST "
            "para analizar fragmentos del AllSpark recuperados del oceano."
        ),
        expected_verdict="INCONSISTENTE",
        expected_issue="Sam (TF1-TF3) y Cade (TF4-TF5) nunca comparten escena",
        category="INCONSISTENCIA_TEMPORAL",
    ),
    TestCase(
        id="TC_003",
        script_fragment=(
            "Los cientificos del Sector 7 presentan el AllSpark intacto "
            "recuperado del fondo del Artico ante el Presidente."
        ),
        expected_verdict="INCONSISTENTE",
        expected_issue="AllSpark destruido en TF1; Sector 7 disuelto en TF1",
        category="INCONSISTENCIA_OBJETO",
    ),
    TestCase(
        id="TC_004",
        script_fragment=(
            "Ironhide lidera el contingente Autobot en la batalla de Chicago 2011 "
            "y protege a los civiles durante la evacuacion."
        ),
        expected_verdict="INCONSISTENTE",
        expected_issue="Ironhide muere antes de la batalla de Chicago en TF3",
        category="INCONSISTENCIA_EVENTO",
    ),
    TestCase(
        id="TC_005",
        script_fragment=(
            "El Consejo Supremo de Cybertron convoca a Optimus Prime. "
            "Los Siete Primes deliberan sobre las ordenes para los Autobots en la Tierra."
        ),
        expected_verdict="INCONSISTENTE",
        expected_issue="No existe Consejo de Cybertron en el universo Bay",
        category="INCONSISTENCIA_LORE",
    ),
    TestCase(
        id="TC_006",
        script_fragment=(
            "Optimus Prime despliega su espada energetica y enfrenta a Megatron "
            "en las calles de Mission City. Sam corre sosteniendo el AllSpark."
        ),
        expected_verdict="CONSISTENTE",
        expected_issue="Ninguno",
        category="CASO_CONSISTENTE",
    ),
    TestCase(
        id="TC_007",
        script_fragment=(
            "Cinco anos despues de Chicago, Cade Yeager encuentra un camion oxidado en Texas. "
            "Al repararlo descubre que es Optimus Prime, quien lleva anos escondido "
            "porque el gobierno cazo a los Autobots."
        ),
        expected_verdict="CONSISTENTE",
        expected_issue="Ninguno",
        category="CASO_CONSISTENTE",
    ),
    TestCase(
        id="TC_008",
        script_fragment=(
            "En 1987, Bumblebee llega a la Tierra y se convierte en un escarabajo amarillo. "
            "Una joven mecanica lo descubre y lo ayuda a reparar sus sistemas."
        ),
        expected_verdict="CONSISTENTE",
        expected_issue="Ninguno - consistente con spin-off Bumblebee (2018)",
        category="CASO_PREQUEL",
    ),
]


def normalize(v):
    v = v.upper().strip()
    if "INCONSIST" in v:
        return "INCONSISTENTE"
    if "CONSIST" in v:
        return "CONSISTENTE"
    return "REQUIERE_REVISION"


def run_evaluation(consultant):
    results = []
    for tc in TEST_CASES:
        print(f"\nEvaluando {tc.id}: {tc.category}")
        report = consultant.analyze(tc.script_fragment)
        correct = normalize(report.verdict) == normalize(tc.expected_verdict)
        results.append({
            "id": tc.id,
            "category": tc.category,
            "expected": tc.expected_verdict,
            "obtained": report.verdict,
            "correct": correct,
            "inconsistencies": len(report.inconsistencies),
            "confidence": report.confidence_score,
            "time_ms": report.processing_time_ms,
            "expected_issue": tc.expected_issue,
        })
        status = "OK" if correct else "FAIL"
        print(f"  esperado={tc.expected_verdict} | obtenido={report.verdict} -> {status}")
    return results


def compute_metrics(results):
    tp = sum(1 for r in results if normalize(r["expected"]) == "INCONSISTENTE" and normalize(r["obtained"]) == "INCONSISTENTE")
    fp = sum(1 for r in results if normalize(r["expected"]) != "INCONSISTENTE" and normalize(r["obtained"]) == "INCONSISTENTE")
    fn = sum(1 for r in results if normalize(r["expected"]) == "INCONSISTENTE" and normalize(r["obtained"]) != "INCONSISTENTE")
    tn = sum(1 for r in results if normalize(r["expected"]) != "INCONSISTENTE" and normalize(r["obtained"]) != "INCONSISTENTE")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = sum(r["correct"] for r in results) / len(results)

    return {
        "total": len(results), "correct": sum(r["correct"] for r in results),
        "accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "avg_time": sum(r["time_ms"] for r in results) / len(results),
        "avg_conf": sum(r["confidence"] for r in results) / len(results),
    }


def print_report(results, metrics):
    print("\n" + "="*72)
    print("EVALUACION - CONSULTOR DE CONTINUIDAD TRANSFORMERS")
    print("="*72)
    print(f"\n{'ID':<8} {'CATEGORIA':<26} {'ESPERADO':<16} {'OBTENIDO':<16} {'OK?'}")
    print("-"*72)
    for r in results:
        ok = "OK" if r["correct"] else "FAIL"
        print(f"{r['id']:<8} {r['category']:<26} {r['expected']:<16} {r['obtained']:<16} {ok}")
    print("-"*72)
    print(f"\nAccuracy:  {metrics['accuracy']:.1%}")
    print(f"Precision: {metrics['precision']:.1%}")
    print(f"Recall:    {metrics['recall']:.1%}")
    print(f"F1-Score:  {metrics['f1']:.1%}")
    print(f"\nTP={metrics['tp']}  FP={metrics['fp']}  FN={metrics['fn']}  TN={metrics['tn']}")
    print(f"Tiempo promedio: {metrics['avg_time']:.0f} ms")
    print(f"Confianza promedio: {metrics['avg_conf']:.1%}")
    print("="*72)


if __name__ == "__main__":
    consultant = ContinuityConsultant()
    consultant.initialize()
    results = run_evaluation(consultant)
    metrics = compute_metrics(results)
    print_report(results, metrics)
