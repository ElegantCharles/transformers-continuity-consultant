"""
run_evaluation_with_logs.py
Ejecuta los 8 casos de prueba del sistema y registra cada ejecución
en logs/execution_log.jsonl con todas las métricas de observabilidad.

Modos de ejecución:
  python run_evaluation_with_logs.py          → usa la API real (requiere .env)
  python run_evaluation_with_logs.py --mock   → genera datos simulados realistas
"""

import sys
import random
import time
from pathlib import Path

# Agrega el directorio raíz al path si es necesario
sys.path.insert(0, str(Path(__file__).parent))

from observability import ObservabilityLogger, ExecutionTimer, make_record, LOGS_DIR

# ── Casos de prueba (mismos que evaluate.py) ──────────────────────────────────
TEST_CASES = [
    {
        "id": "TC_001",
        "fragment": "Escena 14. 2007. Bumblebee se gira hacia Sam y dice en voz alta: 'Sam, debes llevar el AllSpark al Secretario de Defensa.'",
        "expected": "INCONSISTENTE",
        "category": "INCONSISTENCIA_PERSONAJE",
    },
    {
        "id": "TC_002",
        "fragment": "Año 2010. Sam Witwicky y Cade Yeager se reúnen en el cuartel de NEST para analizar fragmentos del AllSpark recuperados del océano.",
        "expected": "INCONSISTENTE",
        "category": "INCONSISTENCIA_TEMPORAL",
    },
    {
        "id": "TC_003",
        "fragment": "Los científicos del Sector 7 presentan el AllSpark intacto recuperado del fondo del Ártico ante el Presidente.",
        "expected": "INCONSISTENTE",
        "category": "INCONSISTENCIA_OBJETO",
    },
    {
        "id": "TC_004",
        "fragment": "Ironhide lidera el contingente Autobot en la batalla de Chicago 2011 y protege a los civiles durante la evacuación.",
        "expected": "INCONSISTENTE",
        "category": "INCONSISTENCIA_EVENTO",
    },
    {
        "id": "TC_005",
        "fragment": "El Consejo Supremo de Cybertron convoca a Optimus Prime. Los Siete Primes deliberan sobre las órdenes para los Autobots en la Tierra.",
        "expected": "INCONSISTENTE",
        "category": "INCONSISTENCIA_LORE",
    },
    {
        "id": "TC_006",
        "fragment": "Optimus Prime despliega su espada energética y enfrenta a Megatron en las calles de Mission City. Sam corre sosteniendo el AllSpark.",
        "expected": "CONSISTENTE",
        "category": "CASO_CONSISTENTE",
    },
    {
        "id": "TC_007",
        "fragment": "Cinco años después de Chicago, Cade Yeager encuentra un camión oxidado en Texas. Al repararlo descubre que es Optimus Prime, quien lleva años escondido porque el gobierno cazó a los Autobots.",
        "expected": "CONSISTENTE",
        "category": "CASO_CONSISTENTE",
    },
    {
        "id": "TC_008",
        "fragment": "En 1987, Bumblebee llega a la Tierra y se convierte en un escarabajo amarillo. Una joven mecánica lo descubre y lo ayuda a reparar sus sistemas.",
        "expected": "CONSISTENTE",
        "category": "CASO_PREQUEL",
    },
]


# ── Modo MOCK: simula respuestas realistas sin llamar a la API ────────────────

def run_mock():
    """
    Genera datos de log simulados con variabilidad realista.
    Útil para desarrollar/evaluar el dashboard sin API.
    """
    print("Ejecutando en modo MOCK (sin API)...\n")
    logger = ObservabilityLogger()

    # Simula 3 rondas de ejecución para generar suficiente variabilidad
    for ronda in range(1, 4):
        print(f"  Ronda {ronda}/3")
        for tc in TEST_CASES:
            # Simula latencia variable por categoría
            base_lat = {
                "INCONSISTENCIA_PERSONAJE": 1800,
                "INCONSISTENCIA_TEMPORAL": 2200,
                "INCONSISTENCIA_OBJETO": 1600,
                "INCONSISTENCIA_EVENTO": 2500,
                "INCONSISTENCIA_LORE": 1900,
                "CASO_CONSISTENTE": 1400,
                "CASO_PREQUEL": 1550,
            }.get(tc["category"], 1800)

            latency = base_lat + random.gauss(0, 300)
            latency = max(800, latency)

            # Simula tokens con variabilidad
            tokens_prompt = random.randint(420, 580)
            tokens_comp   = random.randint(80, 180)

            # Simula veredictos: 87.5% accuracy (1 fallo en 8)
            if tc["id"] == "TC_005" and ronda == 2:
                # Simula un fallo ocasional en TC_005
                verdict = "REQUIERE_REVISION"
                error   = None
                confidence = 0.55
                sev = []
            else:
                verdict = tc["expected"]
                error   = None
                confidence = random.uniform(0.82, 0.97)
                sev = ["CRÍTICA"] if tc["expected"] == "INCONSISTENTE" else []

            # Simula un error de timeout en TC_003 ronda 3
            if tc["id"] == "TC_003" and ronda == 3:
                latency  = 8500
                error    = "timeout: request exceeded 8s limit"
                verdict  = "REQUIERE_REVISION"
                confidence = 0.0
                sev = []

            record = make_record(
                fragment=tc["fragment"],
                verdict=verdict,
                expected_verdict=tc["expected"],
                confidence=round(confidence, 3),
                latency_ms=round(latency, 2),
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_comp,
                num_inconsistencies=len(sev),
                num_tool_calls=random.randint(2, 4),
                category=tc["category"],
                severity_levels=sev,
                error=error,
            )
            logger.log(record)
            status = "✓" if record.is_correct else "✗"
            print(f"    [{status}] {tc['id']} | {verdict} | {latency:.0f}ms | {tokens_prompt + tokens_comp} tokens")

    print("\nLogs generados en logs/execution_log.jsonl")
    _print_summary(logger)


# ── Modo REAL: llama al agente real vía API ───────────────────────────────────

def run_real():
    """
    Ejecuta los casos de prueba contra el pipeline RAG real.
    Requiere .env configurado con GITHUB_TOKEN.
    """
    print("Ejecutando en modo REAL (API)...\n")
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from transformers_rag import ContinuityConsultant
    except ImportError as e:
        print(f"Error importando transformers_rag: {e}")
        print("Cambia a modo mock con: python run_evaluation_with_logs.py --mock")
        sys.exit(1)

    logger = ObservabilityLogger()
    consultant = ContinuityConsultant()
    consultant.initialize()

    for tc in TEST_CASES:
        print(f"  Ejecutando {tc['id']}...")
        timer = ExecutionTimer()
        error = None
        report = None

        try:
            with timer:
                report = consultant.analyze(tc["fragment"])
        except Exception as e:
            error = str(e)

        if report:
            record = make_record(
                fragment=tc["fragment"],
                verdict=report.verdict,
                expected_verdict=tc["expected"],
                confidence=report.confidence_score,
                latency_ms=report.processing_time_ms or timer.elapsed_ms,
                tokens_prompt=0,      # La API de GitHub Models no expone usage en todos los modelos
                tokens_completion=0,
                num_inconsistencies=len(report.inconsistencies),
                num_tool_calls=0,
                category=tc["category"],
                severity_levels=[i.get("severity", "") for i in report.inconsistencies],
                error=error,
            )
        else:
            record = make_record(
                fragment=tc["fragment"],
                verdict="REQUIERE_REVISION",
                expected_verdict=tc["expected"],
                confidence=0.0,
                latency_ms=timer.elapsed_ms,
                tokens_prompt=0,
                tokens_completion=0,
                num_inconsistencies=0,
                num_tool_calls=0,
                category=tc["category"],
                error=error,
            )

        logger.log(record)
        status = "✓" if record.is_correct else "✗"
        print(f"    [{status}] {tc['id']} | {record.verdict} | {record.latency_ms:.0f}ms")

    print("\nLogs generados en logs/execution_log.jsonl")
    _print_summary(logger)


# ── Imprime resumen en consola ────────────────────────────────────────────────

def _print_summary(logger):
    m = logger.compute_metrics()
    print(f"""
╔══════════════════════════════════════════════╗
║       RESUMEN DE MÉTRICAS DE OBSERVABILIDAD  ║
╠══════════════════════════════════════════════╣
║  Total ejecuciones : {m.total_runs:<25}║
║  Accuracy          : {m.accuracy:.1%:<25}║
║  Precision         : {m.precision:.1%:<25}║
║  Recall            : {m.recall:.1%:<25}║
║  F1-Score          : {m.f1_score:.1%:<25}║
║  Consistencia      : {m.consistency_rate:.1%:<25}║
╠══════════════════════════════════════════════╣
║  Latencia promedio : {m.latency_avg:.0f} ms{'':<20}║
║  Latencia p90      : {m.latency_p90:.0f} ms{'':<20}║
║  Latencia p95      : {m.latency_p95:.0f} ms{'':<20}║
╠══════════════════════════════════════════════╣
║  Tokens totales    : {m.tokens_total:<25}║
║  Tokens promedio   : {m.tokens_avg:.0f}{'':<25}║
║  Tasa de errores   : {m.error_rate:.1%:<25}║
╚══════════════════════════════════════════════╝
""")
    analysis = logger.analyze_logs()
    if analysis.get("bottlenecks"):
        print(f"⚠  Cuellos de botella detectados (latencia > p90 = {analysis['p90_latency_ms']}ms):")
        for b in analysis["bottlenecks"]:
            print(f"   run_id={b['run_id']} | {b['latency_ms']}ms | {b['fragment'][:50]}...")
    if analysis.get("errors"):
        print(f"\n✗  Errores registrados: {len(analysis['errors'])}")
        for e in analysis["errors"]:
            print(f"   run_id={e['run_id']} | {e['error']}")
    if analysis.get("false_negatives"):
        print(f"\n⚡ Falsos negativos (inconsistencias no detectadas): {len(analysis['false_negatives'])}")
        for fn in analysis["false_negatives"]:
            print(f"   {fn['fragment'][:60]}...")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--mock" in sys.argv:
        run_mock()
    else:
        run_real()
