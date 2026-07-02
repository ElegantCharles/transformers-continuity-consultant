"""
dashboard.py
Dashboard de monitoreo de observabilidad para el Consultor de Continuidad Narrativa.
Ejecutar con: streamlit run dashboard.py

Requiere haber generado logs primero:
  python run_evaluation_with_logs.py --mock
"""

import json
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from observability import ObservabilityLogger, LOGS_DIR, METRICS_FILE

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Observabilidad — Transformers RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta de colores ─────────────────────────────────────────────────────────
COLORS = {
    "INCONSISTENTE": "#EF4444",
    "CONSISTENTE":   "#22C55E",
    "REQUIERE_REVISION": "#F59E0B",
    "ok":    "#22C55E",
    "warn":  "#F59E0B",
    "error": "#EF4444",
    "blue":  "#3B82F6",
    "bg":    "#0F172A",
}

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_data():
    logger = ObservabilityLogger()
    records = logger.load_records()
    if not records:
        return None, None, None
    metrics = logger.compute_metrics()
    analysis = logger.analyze_logs()
    df = pd.DataFrame([{
        "run_id":           r.run_id,
        "timestamp":        r.timestamp,
        "fragment":         r.fragment[:70] + "...",
        "verdict":          r.verdict,
        "expected":         r.expected_verdict,
        "is_correct":       r.is_correct,
        "confidence":       r.confidence_score,
        "latency_ms":       r.latency_ms,
        "tokens_total":     r.tokens_total,
        "tokens_prompt":    r.tokens_prompt,
        "tokens_completion":r.tokens_completion,
        "num_inconsistencies": r.num_inconsistencies,
        "num_tool_calls":   r.num_tool_calls,
        "error":            r.error,
        "category":         r.category,
    } for r in records])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    return df, metrics, analysis


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://raw.githubusercontent.com/ElegantCharles/transformers-continuity-consultant/master/arquitectura_sistema.png",
             use_container_width=True, caption="Arquitectura del sistema")

    st.markdown("## ⚙️ Controles")
    if st.button("🔄 Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### Filtros")
    filter_cat = st.multiselect(
        "Categorías",
        options=["INCONSISTENCIA_PERSONAJE", "INCONSISTENCIA_TEMPORAL",
                 "INCONSISTENCIA_OBJETO", "INCONSISTENCIA_EVENTO",
                 "INCONSISTENCIA_LORE", "CASO_CONSISTENTE", "CASO_PREQUEL"],
        default=[]
    )
    filter_verdict = st.multiselect(
        "Veredictos",
        options=["INCONSISTENTE", "CONSISTENTE", "REQUIERE_REVISION"],
        default=[]
    )
    only_errors = st.checkbox("Solo ejecuciones con error")

    st.divider()
    st.markdown("### 📂 Archivos de log")
    log_path = LOGS_DIR / "execution_log.jsonl"
    if log_path.exists():
        with open(log_path) as f:
            lines = f.readlines()
        st.success(f"{len(lines)} registros en log")
        st.download_button("⬇ Descargar JSONL", "".join(lines),
                           file_name="execution_log.jsonl", mime="application/json")
    else:
        st.warning("Sin logs. Ejecuta:\n```\npython run_evaluation_with_logs.py --mock\n```")

    st.divider()
    st.caption("ISY0101 — Ingeniería de Soluciones con IA\nDuoc UC — 2026")


# ── Carga principal ───────────────────────────────────────────────────────────
df_raw, metrics, analysis = load_data()

if df_raw is None:
    st.title("🤖 Dashboard de Observabilidad — Transformers RAG")
    st.warning("⚠️ No hay datos de log disponibles.")
    st.code("python run_evaluation_with_logs.py --mock", language="bash")
    st.stop()

# Aplica filtros
df = df_raw.copy()
if filter_cat:
    df = df[df["category"].isin(filter_cat)]
if filter_verdict:
    df = df[df["verdict"].isin(filter_verdict)]
if only_errors:
    df = df[df["error"].notna()]


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.title("🤖 Observabilidad — Consultor de Continuidad Narrativa Transformers")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
           f"{len(df)} registros mostrados de {len(df_raw)} totales")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1: KPIs principales
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📊 Métricas Clave")
k1, k2, k3, k4, k5, k6 = st.columns(6)

def kpi(col, label, value, delta=None, good_threshold=None, fmt="{:.1%}"):
    color = "normal"
    if good_threshold is not None:
        color = "normal" if isinstance(value, float) and value >= good_threshold else "inverse"
    col.metric(label, fmt.format(value) if isinstance(value, float) else str(value),
               delta=delta, delta_color=color)

kpi(k1, "Accuracy",     metrics.accuracy,          fmt="{:.1%}")
kpi(k2, "Precision",    metrics.precision,          fmt="{:.1%}")
kpi(k3, "Recall",       metrics.recall,             fmt="{:.1%}")
kpi(k4, "F1-Score",     metrics.f1_score,           fmt="{:.1%}")
kpi(k5, "Consistencia", metrics.consistency_rate,   fmt="{:.1%}")
kpi(k6, "Tasa de Error",metrics.error_rate,         fmt="{:.1%}")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# FILA 2: Latencia + Distribución de veredictos
# ══════════════════════════════════════════════════════════════════════════════
col_lat, col_verd = st.columns([3, 2])

with col_lat:
    st.subheader("⏱ Distribución de Latencia")

    fig_lat = go.Figure()
    fig_lat.add_trace(go.Histogram(
        x=df["latency_ms"], nbinsx=20,
        marker_color=COLORS["blue"], opacity=0.8,
        name="Latencia (ms)"
    ))
    fig_lat.add_vline(x=metrics.latency_avg, line_dash="dash",
                      line_color=COLORS["ok"],
                      annotation_text=f"Media: {metrics.latency_avg:.0f}ms",
                      annotation_position="top right")
    fig_lat.add_vline(x=metrics.latency_p90, line_dash="dot",
                      line_color=COLORS["warn"],
                      annotation_text=f"P90: {metrics.latency_p90:.0f}ms",
                      annotation_position="top left")
    fig_lat.update_layout(
        xaxis_title="Latencia (ms)", yaxis_title="Frecuencia",
        height=320, margin=dict(t=10, b=40),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_lat, use_container_width=True)

    # Tabla de percentiles
    p_data = {
        "Percentil": ["P50 (mediana)", "P90", "P95", "Mínimo", "Máximo"],
        "Latencia (ms)": [
            f"{metrics.latency_p50:.0f}",
            f"{metrics.latency_p90:.0f}",
            f"{metrics.latency_p95:.0f}",
            f"{metrics.latency_min:.0f}",
            f"{metrics.latency_max:.0f}",
        ]
    }
    st.dataframe(pd.DataFrame(p_data), hide_index=True, use_container_width=True)


with col_verd:
    st.subheader("🏷 Distribución de Veredictos")
    verd_counts = df["verdict"].value_counts()
    fig_pie = go.Figure(go.Pie(
        labels=verd_counts.index,
        values=verd_counts.values,
        marker_colors=[COLORS.get(v, "#94A3B8") for v in verd_counts.index],
        hole=0.45,
        textinfo="label+percent",
    ))
    fig_pie.update_layout(
        height=320, margin=dict(t=10, b=10),
        showlegend=True,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Conteos
    for v, c in verd_counts.items():
        color = COLORS.get(v, "#94A3B8")
        st.markdown(f"<span style='color:{color}'>■</span> **{v}**: {c}", unsafe_allow_html=True)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3: Latencia por categoría + Uso de tokens
# ══════════════════════════════════════════════════════════════════════════════
col_cat, col_tok = st.columns(2)

with col_cat:
    st.subheader("📂 Latencia por Categoría")
    lat_cat = df.groupby("category")["latency_ms"].agg(["mean", "max", "min"]).reset_index()
    lat_cat.columns = ["Categoría", "Promedio (ms)", "Máxima (ms)", "Mínima (ms)"]
    lat_cat = lat_cat.sort_values("Promedio (ms)", ascending=True)

    fig_bar = go.Figure(go.Bar(
        x=lat_cat["Promedio (ms)"], y=lat_cat["Categoría"],
        orientation="h",
        marker_color=COLORS["blue"],
        text=lat_cat["Promedio (ms)"].apply(lambda x: f"{x:.0f}ms"),
        textposition="outside",
    ))
    fig_bar.update_layout(
        xaxis_title="Latencia promedio (ms)",
        height=320, margin=dict(t=10, b=40),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_bar, use_container_width=True)


with col_tok:
    st.subheader("🪙 Uso de Tokens")
    if df["tokens_total"].sum() > 0:
        fig_tok = go.Figure()
        fig_tok.add_trace(go.Box(
            y=df["tokens_prompt"], name="Prompt",
            marker_color=COLORS["blue"], boxpoints="all"
        ))
        fig_tok.add_trace(go.Box(
            y=df["tokens_completion"], name="Completion",
            marker_color=COLORS["ok"], boxpoints="all"
        ))
        fig_tok.update_layout(
            yaxis_title="Tokens",
            height=320, margin=dict(t=10, b=40),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_tok, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Tokens totales",    f"{metrics.tokens_total:,}")
        c2.metric("Prompt avg",        f"{metrics.tokens_prompt_avg:.0f}")
        c3.metric("Completion avg",    f"{metrics.tokens_completion_avg:.0f}")
    else:
        st.info("Tokens no disponibles (modo API real sin usage tracking).")
        # Muestra estimación de coste
        est_tokens = len(df_raw) * 550
        est_cost   = est_tokens * 0.000005
        st.metric("Tokens estimados", f"{est_tokens:,}")
        st.metric("Costo estimado (USD)", f"${est_cost:.4f}")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# FILA 4: Evolución temporal de latencia + Correctitud
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📈 Evolución Temporal")
col_evo1, col_evo2 = st.columns(2)

with col_evo1:
    fig_evo = go.Figure()
    fig_evo.add_trace(go.Scatter(
        x=df["timestamp"], y=df["latency_ms"],
        mode="lines+markers",
        marker=dict(color=[COLORS["ok"] if c else COLORS["error"] for c in df["is_correct"]],
                    size=8),
        line=dict(color=COLORS["blue"], width=1),
        name="Latencia (ms)"
    ))
    fig_evo.add_hline(y=metrics.latency_p90, line_dash="dot",
                      line_color=COLORS["warn"],
                      annotation_text=f"Umbral P90 ({metrics.latency_p90:.0f}ms)")
    fig_evo.update_layout(
        title="Latencia en el tiempo (🟢 correcto / 🔴 incorrecto)",
        xaxis_title="Timestamp", yaxis_title="ms",
        height=300, margin=dict(t=40, b=40),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_evo, use_container_width=True)

with col_evo2:
    # Tasa de acierto acumulada
    df_sorted = df.sort_values("timestamp").copy()
    df_sorted["cum_correct"] = df_sorted["is_correct"].cumsum()
    df_sorted["cum_total"]   = range(1, len(df_sorted) + 1)
    df_sorted["cum_accuracy"] = df_sorted["cum_correct"] / df_sorted["cum_total"]

    fig_acc = go.Figure()
    fig_acc.add_trace(go.Scatter(
        x=df_sorted["timestamp"],
        y=df_sorted["cum_accuracy"],
        mode="lines", fill="tozeroy",
        line=dict(color=COLORS["ok"], width=2),
        fillcolor="rgba(34,197,94,0.15)",
        name="Accuracy acumulada"
    ))
    fig_acc.add_hline(y=0.80, line_dash="dash", line_color=COLORS["warn"],
                      annotation_text="Umbral mínimo (80%)")
    fig_acc.update_layout(
        title="Accuracy acumulada en el tiempo",
        yaxis_tickformat=".0%", yaxis_range=[0, 1.05],
        height=300, margin=dict(t=40, b=40),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_acc, use_container_width=True)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# FILA 5: Análisis de logs — Cuellos de botella y errores
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("🔍 Análisis de Logs y Trazabilidad")

col_bot, col_err = st.columns(2)

with col_bot:
    st.markdown(f"**Cuellos de botella** (latencia > P90 = {analysis['p90_latency_ms']:.0f}ms)")
    if analysis["bottlenecks"]:
        df_bot = pd.DataFrame(analysis["bottlenecks"])
        st.dataframe(df_bot[["run_id", "latency_ms", "verdict", "fragment"]],
                     hide_index=True, use_container_width=True)
    else:
        st.success("Sin cuellos de botella detectados.")

    if analysis.get("false_negatives"):
        st.markdown(f"**⚡ Falsos negativos:** {len(analysis['false_negatives'])}")
        df_fn = pd.DataFrame(analysis["false_negatives"])
        st.dataframe(df_fn[["run_id", "verdict", "expected", "fragment"]],
                     hide_index=True, use_container_width=True)

with col_err:
    st.markdown(f"**Errores registrados:** {len(analysis.get('errors', []))}")
    if analysis.get("errors"):
        df_err = pd.DataFrame(analysis["errors"])
        st.dataframe(df_err, hide_index=True, use_container_width=True)
    else:
        st.success("Sin errores en los logs.")

    st.markdown("**Latencia promedio por categoría**")
    lat_cat_data = analysis.get("latency_by_category", {})
    if lat_cat_data:
        df_lcat = pd.DataFrame(list(lat_cat_data.items()),
                               columns=["Categoría", "Latencia promedio (ms)"])
        df_lcat = df_lcat.sort_values("Latencia promedio (ms)", ascending=False)
        st.dataframe(df_lcat, hide_index=True, use_container_width=True)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# FILA 6: Matriz de confusión + Confianza
# ══════════════════════════════════════════════════════════════════════════════
col_conf, col_ci = st.columns(2)

with col_conf:
    st.subheader("🎯 Matriz de Confusión")
    from sklearn.metrics import confusion_matrix
    import numpy as np

    labels = ["INCONSISTENTE", "CONSISTENTE", "REQUIERE_REVISION"]
    y_true = [v if v in labels else "REQUIERE_REVISION" for v in df["expected"]]
    y_pred = [v if v in labels else "REQUIERE_REVISION" for v in df["verdict"]]
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig_cm = px.imshow(
        cm, text_auto=True,
        x=labels, y=labels,
        color_continuous_scale="Blues",
        labels=dict(x="Predicho", y="Real", color="Conteo"),
    )
    fig_cm.update_layout(height=300, margin=dict(t=10, b=40))
    st.plotly_chart(fig_cm, use_container_width=True)

with col_ci:
    st.subheader("📉 Distribución de Confianza")
    fig_conf = go.Figure()
    for verdict, color in COLORS.items():
        if verdict not in ["INCONSISTENTE", "CONSISTENTE", "REQUIERE_REVISION"]:
            continue
        subset = df[df["verdict"] == verdict]["confidence"]
        if not subset.empty:
            fig_conf.add_trace(go.Violin(
                y=subset, name=verdict,
                fillcolor=color, opacity=0.7,
                box_visible=True, meanline_visible=True,
                line_color=color,
            ))
    fig_conf.update_layout(
        yaxis_title="Score de confianza",
        yaxis_range=[0, 1.05],
        height=300, margin=dict(t=10, b=40),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_conf, use_container_width=True)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# FILA 7: Tabla de registros completa
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📋 Registros de Ejecución")

def color_row(row):
    bg = ""
    if not row["is_correct"]:
        bg = "background-color: rgba(239,68,68,0.15)"
    elif row["error"]:
        bg = "background-color: rgba(245,158,11,0.15)"
    return [bg] * len(row)

cols_show = ["run_id", "timestamp", "category", "verdict", "expected",
             "is_correct", "confidence", "latency_ms", "tokens_total", "error"]
df_show = df[cols_show].copy()
df_show["timestamp"] = df_show["timestamp"].dt.strftime("%H:%M:%S")
df_show["confidence"] = df_show["confidence"].map("{:.2f}".format)
df_show["latency_ms"] = df_show["latency_ms"].map("{:.0f}ms".format)

st.dataframe(
    df_show.style.apply(color_row, axis=1),
    hide_index=True, use_container_width=True, height=350
)

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.caption("🤖 Consultor de Continuidad Narrativa — Transformers | ISY0101 Duoc UC 2026 | "
           "Dashboard construido con Streamlit + Plotly")
