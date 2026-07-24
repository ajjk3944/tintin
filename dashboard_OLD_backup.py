"""
Tensor Titan — Complete Dashboard
DIU CSE AI Research Lab GPU Cluster Intelligence System
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import random
from datetime import datetime

from data_simulator import generate_metrics, trigger_chaos, reset_history, clear_all_chaos
from sensor_ai import predict_risk, load_models
from scheduler_ai import add_job, assign_job, queue_length, check_migration
from cost_ai import get_cost_summary, get_idle_nodes, start_scanner
from database import init_db, insert_metrics, insert_prediction, log_job, get_recent_jobs
from cluster_config import CLUSTER_NODES, COST_PER_GPU_PER_HOUR_BDT, COST_PER_GPU_PER_HOUR_USD, CO2_PER_KWH_KG

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TensorTitan",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="collapsed"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: "";
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #6366f1, #06b6d4, #10b981);
}
.hero-title {
    font-size: 1.9rem; font-weight: 800; color: #f1f5f9; margin: 0;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    font-size: 0.95rem; color: #94a3b8; margin: 4px 0 16px 0;
}
.hero-problem {
    background: rgba(239,68,68,0.1); border-left: 3px solid #ef4444;
    padding: 10px 14px; border-radius: 6px; color: #fca5a5;
    font-size: 0.85rem; margin-bottom: 8px;
}
.hero-solution {
    background: rgba(16,185,129,0.1); border-left: 3px solid #10b981;
    padding: 10px 14px; border-radius: 6px; color: #6ee7b7;
    font-size: 0.85rem;
}

.node-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #334155;
    height: 100%;
}
.node-card-normal  { border-top: 4px solid #10b981; }
.node-card-warning { border-top: 4px solid #f59e0b; }
.node-card-critical { border-top: 4px solid #ef4444; box-shadow: 0 0 16px rgba(239,68,68,0.2); }
.node-card-idle    { border-top: 4px solid #6366f1; }

.node-hostname { font-size: 0.7rem; color: #64748b; font-family: monospace; }
.node-gpu { font-size: 0.85rem; font-weight: 700; color: #e2e8f0; margin: 2px 0; }
.node-job { font-size: 0.78rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.node-researcher { font-size: 0.72rem; color: #64748b; }

.metric-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.metric-chip {
    background: #0f172a; border-radius: 6px; padding: 5px 10px;
    font-size: 0.8rem; color: #cbd5e1; border: 1px solid #334155;
    flex: 1; text-align: center; min-width: 60px;
}
.metric-chip .label { font-size: 0.65rem; color: #64748b; display: block; }

.status-badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; margin-bottom: 6px;
}
.badge-normal   { background: rgba(16,185,129,0.15); color: #34d399; }
.badge-warning  { background: rgba(245,158,11,0.15); color: #fbbf24; }
.badge-critical { background: rgba(239,68,68,0.15); color: #f87171; }
.badge-idle     { background: rgba(99,102,241,0.15); color: #a5b4fc; }

.chaos-panel {
    background: #0f172a; border: 1px dashed #334155;
    border-radius: 10px; padding: 14px 20px;
}
.chaos-title { font-size: 0.9rem; font-weight: 700; color: #f59e0b; margin-bottom: 2px; }
.chaos-desc  { font-size: 0.77rem; color: #64748b; margin-bottom: 12px; }

.section-header {
    font-size: 1.05rem; font-weight: 700; color: #e2e8f0;
    border-bottom: 1px solid #334155; padding-bottom: 8px; margin-bottom: 16px;
}
.savings-row {
    background: linear-gradient(90deg, rgba(16,185,129,0.05), transparent);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 10px; padding: 16px 20px; margin-top: 12px;
}
.alert-item {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
    font-size: 0.83rem; color: #fca5a5;
}
.job-item {
    background: #0f172a; border-radius: 8px; padding: 10px 14px;
    margin-bottom: 8px; font-size: 0.82rem; color: #94a3b8;
    font-family: monospace; border: 1px solid #1e293b;
}
</style>
""", unsafe_allow_html=True)

# ─── ROBUST SESSION STATE INIT ────────────────────────────────────────────────
# Use setdefault so every key is always safe — even on hot-reloads / file changes
if "initialized" not in st.session_state:
    init_db()
    load_models()
    start_scanner()
    # Seed realistic AI job queue
    jobs = [
        ("ResNet-152 ImageNet Pre-train", 5),
        ("GPT-4 RLHF Fine-tune", 5),
        ("Bangla OCR CNN Training", 4),
        ("Face Recognition — Campus Security", 4),
        ("ViT-B/16 Medical Imaging", 3),
    ]
    for name, pri in jobs:
        add_job(name, priority=pri)
    st.session_state["initialized"] = True

# Always safe defaults — no KeyError even after hot-reload
st.session_state.setdefault("job_logs", [])
st.session_state.setdefault("migration_logs", [])
st.session_state.setdefault("total_prevented_crashes", 0)
st.session_state.setdefault("session_start", datetime.now())

# ─── SESSION DURATION CALC ────────────────────────────────────────────────────
session_mins = max(1, int((datetime.now() - st.session_state["session_start"]).total_seconds() / 60))

# ─── DATA REFRESH ─────────────────────────────────────────────────────────────
metrics_df = generate_metrics()
risk_df = predict_risk(metrics_df)

# Merge for easy access
data = metrics_df.merge(risk_df[["node_id", "risk_score", "risk_level", "root_cause"]], on="node_id")

# Persist to DB
insert_metrics(metrics_df[["node_id","temperature","utilization","memory_used","power_draw","timestamp"]].to_dict("records"))
for _, r in risk_df.iterrows():
    insert_prediction(r["node_id"], r["risk_score"], r["risk_level"])

# SchedulerAI
job_name, best_node, reason = assign_job(metrics_df, risk_df)
if job_name:
    log_job(job_name, best_node, reason)
    node_cfg = CLUSTER_NODES.get(best_node, {})
    st.session_state["job_logs"].insert(0,
        f"{job_name}  →  {node_cfg.get('hostname','Node '+str(best_node))}  |  {reason}")

# Migration check
migrations = check_migration(metrics_df, risk_df)
for m in migrations:
    st.session_state["migration_logs"].insert(0,
        f"Node {m['node_id']} ({CLUSTER_NODES[m['node_id']]['hostname']}) — Risk {m['risk_score']}% — {m['action']}")
    st.session_state["total_prevented_crashes"] += 1

cost = get_cost_summary()

# ─── TOP KPI ROW ─────────────────────────────────────────────────────────────
active_jobs_count = sum(1 for _, r in data.iterrows() if r["job_type"] != "Idle")
k1, k2, k3, k4, k5 = st.columns(5)

avg_risk = risk_df["risk_score"].mean()
health_pct = max(0, round(100 - avg_risk, 1))
health_delta = "🟢 All Clear" if health_pct > 70 else ("🟡 Attention" if health_pct > 40 else "🔴 Action Needed")

k1.metric("Cluster Health", f"{health_pct}%", health_delta)
k2.metric("Active AI Jobs", f"{active_jobs_count} / 5 Nodes", f"{queue_length()} in queue")
k3.metric("Crashes Prevented", st.session_state["total_prevented_crashes"], "Auto-migrations fired")
k4.metric("Running Cost", f"${cost['hourly_cost']:.2f}/hr", f"Active: {cost['active_gpus']} GPUs")
k5.metric("CO₂ Prevented", f"{cost['co2_saved_kg']} kg", "vs. no idle management")

st.divider()

# ─── LIVE NODE CARDS ──────────────────────────────────────────────────────────
st.markdown('<p class="section-header">📡 Live Cluster Monitor — 5 GPU Workstations</p>', unsafe_allow_html=True)

cols = st.columns(5)
RISK_BADGE = {
    "Normal": ("badge-normal", "● Normal"),
    "Warning": ("badge-warning", "▲ Warning"),
    "Critical": ("badge-critical", "✕ Critical"),
}

for i, (_, row) in enumerate(data.iterrows()):
    cfg = CLUSTER_NODES[row["node_id"]]
    rl = row["risk_level"]
    is_idle = cfg["job_type"] == "Idle"

    if is_idle:
        card_class = "node-card-idle"
        badge_class, badge_text = "badge-idle", "◌ Idle"
    else:
        card_class = f"node-card-{rl.lower()}"
        badge_class, badge_text = RISK_BADGE.get(rl, ("badge-normal", "Normal"))

    util_bar = int(row["utilization"])
    mem_pct = round(row["memory_used"] / cfg["gpu_vram_gb"] * 100, 1)

    with cols[i]:
        st.markdown(f"""
        <div class="node-card {card_class}">
          <span class="status-badge {badge_class}">{badge_text}</span>
          <div class="node-hostname">{cfg["hostname"]}</div>
          <div class="node-gpu">{cfg["gpu_model"]} ({cfg["gpu_vram_gb"]}GB)</div>
          <div class="node-job" title="{cfg['current_job']}">📋 {cfg['current_job']}</div>
          <div class="node-researcher">👤 {cfg['assigned_researcher']}</div>
          <div class="metric-row">
            <div class="metric-chip"><span class="label">Risk</span>{row["risk_score"]}</div>
            <div class="metric-chip"><span class="label">Temp</span>{row["temperature"]}°C</div>
            <div class="metric-chip"><span class="label">GPU%</span>{row["utilization"]}%</div>
            <div class="metric-chip"><span class="label">VRAM</span>{row["memory_used"]:.1f}GB</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if rl == "Critical" and not is_idle:
            st.error(f"⚠️ {row['root_cause']}")
        elif rl == "Warning" and not is_idle:
            st.warning(f"⚡ {row['root_cause']}")

st.divider()

# ─── MAIN TABS ────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🔬 Risk Analysis",
    "⚙️ Smart Scheduler",
    "💰 Cost & Energy"
])

# ── TAB 1: AI RISK ANALYSIS ───────────────────────────────────────────────────
with tab1:
    st.markdown("**SensorAI** uses Isolation Forest (anomaly detection) + Random Forest (failure prediction) trained on GPU telemetry patterns.")

    col_a, col_b = st.columns(2)
    with col_a:
        fig1 = go.Figure()
        for _, row in data.iterrows():
            color = "#ef4444" if row["risk_level"] == "Critical" else "#f59e0b" if row["risk_level"] == "Warning" else "#10b981"
            fig1.add_trace(go.Bar(
                x=[CLUSTER_NODES[row["node_id"]]["hostname"]],
                y=[row["risk_score"]],
                text=[f"{row['risk_score']}%"],
                textposition="auto",
                marker_color=color,
                showlegend=False,
                name=CLUSTER_NODES[row["node_id"]]["hostname"]
            ))
        fig1.update_layout(
            title="Failure Risk Score per Node (0 = Safe, 100 = Imminent Failure)",
            yaxis_range=[0, 100],
            height=320,
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font=dict(color="#94a3b8"),
            xaxis_tickangle=-20,
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        fig2 = go.Figure()
        colors = ["#ef4444" if t > 80 else "#f59e0b" if t > 70 else "#10b981"
                  for t in data["temperature"]]
        fig2.add_trace(go.Bar(
            x=[CLUSTER_NODES[r["node_id"]]["hostname"] for _, r in data.iterrows()],
            y=data["temperature"].tolist(),
            text=[f"{t}°C" for t in data["temperature"]],
            textposition="auto",
            marker_color=colors,
        ))
        fig2.add_hline(y=80, line_dash="dash", line_color="#f59e0b",
                       annotation_text="Warning Threshold (80°C)")
        fig2.add_hline(y=87, line_dash="dash", line_color="#ef4444",
                       annotation_text="Critical Threshold (87°C)")
        fig2.update_layout(
            title="GPU Temperature — Thermal Safety Monitor",
            yaxis_range=[30, 100], height=320,
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="#94a3b8"), xaxis_tickangle=-20,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Root cause table
    st.markdown("#### 🔍 Explainable AI — Root Cause Breakdown per Node")
    xai_data = []
    for _, row in data.iterrows():
        xai_data.append({
            "Workstation": CLUSTER_NODES[row["node_id"]]["hostname"],
            "Active Job": CLUSTER_NODES[row["node_id"]]["current_job"],
            "Risk Level": row["risk_level"],
            "Risk Score": f"{row['risk_score']}%",
            "Root Cause Identified": row["root_cause"],
        })
    st.dataframe(pd.DataFrame(xai_data), use_container_width=True, hide_index=True)

# ── TAB 2: SMART SCHEDULER ────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    **SchedulerAI** scores every node using a weighted formula:
    `Score = (1 − Risk) × 0.5 + Free VRAM Ratio × 0.3 + Thermal Headroom × 0.2`
    Jobs are placed on the highest-scoring node. If a node becomes Critical mid-job, the workload is automatically migrated.
    """)

    c1, c2, c3 = st.columns(3)
    c1.metric("Jobs Waiting in Queue", queue_length())
    c2.metric("Auto-Migrations Fired", len(st.session_state["migration_logs"]))
    c3.metric("Training Crashes Prevented", st.session_state["total_prevented_crashes"])

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 📋 Job Assignment Log")
        if st.session_state["job_logs"]:
            for log in st.session_state["job_logs"][:8]:
                st.markdown(f'<div class="job-item">✅ {log}</div>', unsafe_allow_html=True)
        else:
            st.info("Queue is processing — job assignments will appear here.")

    with col_r:
        st.markdown("#### 🚨 Auto-Migration Alerts")
        if st.session_state["migration_logs"]:
            for log in st.session_state["migration_logs"][:6]:
                st.markdown(f'<div class="alert-item">🔴 {log}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:16px;color:#10b981;font-size:0.85rem;">✅ All nodes operating within safe thresholds. No migrations needed.</div>', unsafe_allow_html=True)

    st.divider()

    # ── ASSIGN JOB FORM ──────────────────────────────────────────────────────
    st.markdown('<p class="section-header">➕ Assign Job</p>', unsafe_allow_html=True)
    with st.form("assign_job_form", clear_on_submit=True):
        fa, fb, fc = st.columns([3, 1, 1])
        with fa:
            job_input = st.text_input(
                "Job Name",
                placeholder="e.g. GPT-4 Bangla Finetune, YOLOv9 Training...",
                label_visibility="collapsed"
            )
        with fb:
            priority_input = st.selectbox(
                "Priority",
                options=[5, 4, 3, 2, 1],
                format_func=lambda x: f"Priority {x}" + (" ⭐ Highest" if x == 5 else " 🔻 Lowest" if x == 1 else ""),
                label_visibility="collapsed"
            )
        with fc:
            submitted = st.form_submit_button("⚡ Assign Job", use_container_width=True)

        if submitted:
            if job_input.strip():
                add_job(job_input.strip(), priority=priority_input)
                # Immediately try to assign from queue
                j_name, b_node, reason = assign_job(metrics_df, risk_df)
                if j_name and b_node:
                    log_job(j_name, b_node, reason)
                    node_cfg = CLUSTER_NODES.get(b_node, {})
                    entry = f"{j_name}  →  {node_cfg.get('hostname', 'Node '+str(b_node))}  |  {reason}"
                    st.session_state["job_logs"].insert(0, entry)
                    st.success(f"✅ **{j_name}** assigned to `{node_cfg.get('hostname','Node '+str(b_node))}` | Score: {reason.split('=')[1].split('|')[0].strip()}")
                else:
                    st.warning("⏳ Job queued — all nodes currently busy or critical.")
            else:
                st.error("Please enter a job name.")

# ── TAB 3: COST & ENERGY ──────────────────────────────────────────────────────
with tab3:
    idle_nodes = get_idle_nodes()
    idle_count = len(idle_nodes)
    active_count = 5 - idle_count
    saved_usd = cost["total_savings"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Workstations", f"{active_count} / 5")
    c2.metric("Idle Machines Detected", idle_count, "Flagged for reassignment" if idle_count else "None wasted")
    c3.metric("Running Hourly Cost", f"${cost['hourly_cost']:.2f} USD")
    c4.metric("Potential Monthly Waste", f"${cost['monthly_waste']:.2f} USD" if cost["monthly_waste"] > 0 else "$0.00 saved ✓")

    st.markdown(f"""
    <div class="savings-row">
      <b style="color:#10b981">💰 Total Savings Since Monitoring Started ({session_mins} min session):</b><br/>
      <span style="font-size:1.4rem;font-weight:800;color:#34d399">${saved_usd:.2f} USD</span>
      &nbsp;&nbsp; | &nbsp;&nbsp;
      <span style="font-size:1.1rem;color:#6ee7b7">🌱 {cost['co2_saved_kg']} kg CO₂ prevented</span>
      <br/><span style="font-size:0.78rem;color:#64748b;margin-top:4px;display:block;">
        CostAI scans every 10 seconds. A GPU idle for 5+ minutes (below 5% utilization) is flagged and its workload is auto-reassigned from the queue.
      </span>
    </div>
    """, unsafe_allow_html=True)

    if idle_nodes:
        st.error(f"🔴 Idle GPU detected: Node(s) {idle_nodes} — CostAI has flagged these for job reassignment from queue.")
    else:
        st.success("✅ 100% GPU utilization efficiency. No idle capacity wasted.")

    col_p, col_b = st.columns(2)
    with col_p:
        fig_pie = go.Figure(go.Pie(
            labels=["Running AI Jobs", "Idle / Unallocated"],
            values=[max(active_count, 0.01), max(idle_count, 0.01)],
            hole=0.5,
            marker_colors=["#10b981", "#6366f1"],
        ))
        fig_pie.update_layout(
            title="GPU Cluster Allocation", height=300,
            paper_bgcolor="#0f172a", font=dict(color="#94a3b8"),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.markdown("#### ⚡ Electricity & Carbon Impact")
        total_power_kw = data["power_draw"].sum() / 1000
        hourly_kwh = total_power_kw
        daily_kwh = hourly_kwh * 24
        st.markdown(f"""
        | Metric | Value |
        |:---|:---|
        | Total Power Draw | {total_power_kw:.2f} kW |
        | Daily Energy Usage | {daily_kwh:.1f} kWh / day |
        | CO₂ (today estimate) | {daily_kwh * CO2_PER_KWH_KG:.1f} kg |
        | CO₂ prevented (idle mgmt) | **{cost['co2_saved_kg']} kg** |
        """)

# ─── AUTO-REFRESH ─────────────────────────────────────────────────────────────
time.sleep(4)
st.rerun()
