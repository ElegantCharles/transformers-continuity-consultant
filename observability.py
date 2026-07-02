"""
observability.py
Sistema de observabilidad para el Consultor de Continuidad Narrativa — Transformers.
Implementa métricas de: precisión, consistencia, latencia, frecuencia de errores
y uso de recursos (tokens). Compatible con evaluate.py y agent_v2.py.
"""

import json
import time
import uuid
import os
import platform
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Directorio de logs ────────────────────────────────────────────────────────
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "execution_log.jsonl"
METRICS_FILE = LOGS_DIR / "metrics_summary.json"


# ── Estructuras de datos ──────────────────────────────────────────────────────

@dataclass
class ExecutionRecord:
    """Registro completo de una ejecución del agente."""
    run_id: str
    timestamp: str
    fragment: str
    verdict: str
    expected_verdict: str
    is_correct: bool
    confidence_score: float
    latency_ms: float
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    num_inconsistencies: int
    num_tool_calls: int
    error: Optional[str]
    category: str
    severity_levels: list[str] = field(default_factory=list)


@dataclass
class MetricsSummary:
    """Resumen agregado de métricas de observabilidad."""
    total_runs: int = 0
    correct_runs: int = 0
    error_runs: int = 0

    # Precisión y consistencia
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    consistency_rate: float = 0.0   # % runs sin flip de veredicto en re-ejecución

    # Latencia (ms)
    latency_avg: float = 0.0
    latency_p50: float = 0.0
    latency_p90: float = 0.0
    latency_p95: float = 0.0
    latency_min: float = 0.0
    latency_max: float = 0.0

    # Recursos (tokens)
    tokens_avg: float = 0.0
    tokens_total: int = 0
    tokens_prompt_avg: float = 0.0
    tokens_completion_avg: float = 0.0

    # Errores
    error_rate: float = 0.0
    timeout_count: int = 0
    json_parse_errors: int = 0

    # Distribución de veredictos
    verdict_INCONSISTENTE: int = 0
    verdict_CONSISTENTE: int = 0
    verdict_REQUIERE_REVISION: int = 0

    # Timestamp del resumen
    computed_at: str = ""


# ── Logger principal ──────────────────────────────────────────────────────────

class ObservabilityLogger:
    """
    Logger que registra cada ejecución del agente en JSONL
    y calcula métricas agregadas bajo demanda.
    """

    def __init__(self, log_file: Path = LOG_FILE):
        self.log_file = log_file

    # ── Escritura ─────────────────────────────────────────────────────────────

    def log(self, record: ExecutionRecord):
        """Persiste un ExecutionRecord en el archivo JSONL."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    # ── Lectura ───────────────────────────────────────────────────────────────

    def load_records(self) -> list[ExecutionRecord]:
        """Carga todos los registros desde el archivo JSONL."""
        records = []
        if not self.log_file.exists():
            return records
        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        d = json.loads(line)
                        records.append(ExecutionRecord(**d))
                    except Exception:
                        pass
        return records

    # ── Métricas ──────────────────────────────────────────────────────────────

    def compute_metrics(self) -> MetricsSummary:
        """Calcula todas las métricas de observabilidad a partir de los logs."""
        records = self.load_records()
        if not records:
            return MetricsSummary(computed_at=datetime.now().isoformat())

        m = MetricsSummary()
        m.computed_at = datetime.now().isoformat()
        m.total_runs = len(records)

        # ── Correctitud ───────────────────────────────────────────────────────
        m.correct_runs  = sum(1 for r in records if r.is_correct)
        m.error_runs    = sum(1 for r in records if r.error is not None)
        m.accuracy      = m.correct_runs / m.total_runs

        # ── Precisión / Recall / F1 (positivo = INCONSISTENTE) ───────────────
        tp = sum(1 for r in records if _norm(r.verdict) == "INCONSISTENTE" and _norm(r.expected_verdict) == "INCONSISTENTE")
        fp = sum(1 for r in records if _norm(r.verdict) == "INCONSISTENTE" and _norm(r.expected_verdict) != "INCONSISTENTE")
        fn = sum(1 for r in records if _norm(r.verdict) != "INCONSISTENTE" and _norm(r.expected_verdict) == "INCONSISTENTE")

        m.precision  = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        m.recall     = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        m.f1_score   = (2 * m.precision * m.recall / (m.precision + m.recall)
                        if (m.precision + m.recall) > 0 else 0.0)

        # ── Consistencia (misma entrada, mismo veredicto) ─────────────────────
        # Agrupa por fragmento y verifica que no haya flip
        from collections import defaultdict
        by_fragment: dict[str, set] = defaultdict(set)
        for r in records:
            by_fragment[r.fragment[:80]].add(_norm(r.verdict))
        stable = sum(1 for verdicts in by_fragment.values() if len(verdicts) == 1)
        m.consistency_rate = stable / len(by_fragment) if by_fragment else 1.0

        # ── Latencia ──────────────────────────────────────────────────────────
        latencies = sorted(r.latency_ms for r in records)
        m.latency_avg = sum(latencies) / len(latencies)
        m.latency_min = latencies[0]
        m.latency_max = latencies[-1]
        m.latency_p50 = _percentile(latencies, 50)
        m.latency_p90 = _percentile(latencies, 90)
        m.latency_p95 = _percentile(latencies, 95)

        # ── Tokens ────────────────────────────────────────────────────────────
        m.tokens_total          = sum(r.tokens_total for r in records)
        m.tokens_avg            = m.tokens_total / m.total_runs
        m.tokens_prompt_avg     = sum(r.tokens_prompt for r in records) / m.total_runs
        m.tokens_completion_avg = sum(r.tokens_completion for r in records) / m.total_runs

        # ── Errores ───────────────────────────────────────────────────────────
        m.error_rate        = m.error_runs / m.total_runs
        m.timeout_count     = sum(1 for r in records if r.error and "timeout" in r.error.lower())
        m.json_parse_errors = sum(1 for r in records if r.error and "json" in r.error.lower())

        # ── Distribución de veredictos ────────────────────────────────────────
        m.verdict_INCONSISTENTE    = sum(1 for r in records if _norm(r.verdict) == "INCONSISTENTE")
        m.verdict_CONSISTENTE      = sum(1 for r in records if _norm(r.verdict) == "CONSISTENTE")
        m.verdict_REQUIERE_REVISION = sum(1 for r in records if _norm(r.verdict) == "REQUIERE_REVISION")

        # Persiste el resumen
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(m), f, ensure_ascii=False, indent=2)

        return m

    # ── Análisis de logs ──────────────────────────────────────────────────────

    def analyze_logs(self) -> dict:
        """
        Examina los logs para identificar cuellos de botella,
        patrones de error y anomalías.
        """
        records = self.load_records()
        if not records:
            return {"error": "Sin registros disponibles"}

        latencies = [r.latency_ms for r in records]
        avg_lat   = sum(latencies) / len(latencies)
        p90_lat   = _percentile(sorted(latencies), 90)

        # Cuellos de botella: ejecuciones con latencia > p90
        bottlenecks = [
            {"run_id": r.run_id, "fragment": r.fragment[:60],
             "latency_ms": round(r.latency_ms, 1), "verdict": r.verdict}
            for r in records if r.latency_ms > p90_lat
        ]

        # Errores frecuentes
        errors = [
            {"run_id": r.run_id, "error": r.error,
             "fragment": r.fragment[:60], "latency_ms": round(r.latency_ms, 1)}
            for r in records if r.error
        ]

        # Falsos negativos (inconsistencia esperada pero no detectada)
        false_negatives = [
            {"run_id": r.run_id, "fragment": r.fragment[:60],
             "verdict": r.verdict, "expected": r.expected_verdict}
            for r in records
            if _norm(r.expected_verdict) == "INCONSISTENTE"
            and _norm(r.verdict) != "INCONSISTENTE"
        ]

        # Distribución de latencia por categoría
        from collections import defaultdict
        lat_by_cat: dict[str, list] = defaultdict(list)
        for r in records:
            lat_by_cat[r.category].append(r.latency_ms)
        lat_by_cat_avg = {
            cat: round(sum(lats) / len(lats), 1)
            for cat, lats in lat_by_cat.items()
        }

        return {
            "total_records": len(records),
            "avg_latency_ms": round(avg_lat, 1),
            "p90_latency_ms": round(p90_lat, 1),
            "bottlenecks": bottlenecks,
            "errors": errors,
            "false_negatives": false_negatives,
            "latency_by_category": lat_by_cat_avg,
            "anomaly_threshold_ms": round(p90_lat, 1),
        }


# ── Context manager para medir ejecuciones ────────────────────────────────────

class ExecutionTimer:
    """Context manager para medir latencia de una ejecución del agente."""

    def __init__(self):
        self.start = None
        self.elapsed_ms = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm(verdict: str) -> str:
    v = verdict.upper().strip()
    if "INCONSIST" in v:
        return "INCONSISTENTE"
    if "CONSIST" in v:
        return "CONSISTENTE"
    return "REQUIERE_REVISION"


def _percentile(sorted_data: list, p: int) -> float:
    if not sorted_data:
        return 0.0
    idx = int(len(sorted_data) * p / 100)
    idx = min(idx, len(sorted_data) - 1)
    return sorted_data[idx]


def make_record(
    fragment: str,
    verdict: str,
    expected_verdict: str,
    confidence: float,
    latency_ms: float,
    tokens_prompt: int,
    tokens_completion: int,
    num_inconsistencies: int,
    num_tool_calls: int,
    category: str,
    severity_levels: list[str] | None = None,
    error: str | None = None,
) -> ExecutionRecord:
    """Factory que construye un ExecutionRecord listo para loguear."""
    return ExecutionRecord(
        run_id=str(uuid.uuid4())[:8],
        timestamp=datetime.now().isoformat(),
        fragment=fragment,
        verdict=verdict,
        expected_verdict=expected_verdict,
        is_correct=_norm(verdict) == _norm(expected_verdict),
        confidence_score=confidence,
        latency_ms=round(latency_ms, 2),
        tokens_prompt=tokens_prompt,
        tokens_completion=tokens_completion,
        tokens_total=tokens_prompt + tokens_completion,
        num_inconsistencies=num_inconsistencies,
        num_tool_calls=num_tool_calls,
        error=error,
        category=category,
        severity_levels=severity_levels or [],
    )
