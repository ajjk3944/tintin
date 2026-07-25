"""
TensorTitan — Cluster Intelligence Console
DIU CSE AI Research Lab · GPU Cluster Intelligence System

Redesigned control-room dashboard. Same backend, premium NOC-style UI.
Station #1 can mirror THIS machine's real hardware telemetry (live mode).
"""
import time
from datetime import datetime
from zoneinfo import ZoneInfo
DHAKA = ZoneInfo("Asia/Dhaka")
import base64
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

from data_simulator import (
    generate_metrics, trigger_chaos, clear_all_chaos, reset_history,
    set_live_mode, live_mode_info,
    assign_job_to_node, clear_node_job, clear_all_node_jobs, get_node_jobs,
)
from workload_runner import start_workload, stop_workload, workload_status
import loop_proof
from sensor_ai import predict_risk, load_models
from scheduler_ai import add_job, assign_job, queue_length, check_migration
from cost_ai import get_cost_summary, get_idle_nodes, start_scanner
from database import init_db, insert_metrics, insert_prediction, log_job
from cluster_config import (
    CLUSTER_NODES, CO2_PER_KWH_KG,
    ELECTRICITY_PER_KWH_BDT, COST_PER_GPU_PER_HOUR_USD, COST_PER_GPU_PER_HOUR_BDT,
)

# ─── PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="TensorTitan · Cluster Console",
    layout="wide",
    page_icon="assets/logo.png",
    initial_sidebar_state="collapsed",
)

# ─── DESIGN SYSTEM (CSS) ──────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{
  --bg:#0A0C12; --surface:#12151E; --surface2:#171B27; --raised:#1C2130;
  --line:#242A3A; --line-soft:#1B2130;
  --text:#EAEDF4; --muted:#8B93A7; --faint:#5A6274;
  --accent:#7C6BF5; --cyan:#2DD4BF; --green:#3FCF8E; --amber:#F5B451; --red:#F26D6D;
}
*{box-sizing:border-box;}
#MainMenu, footer, header {visibility:hidden;}
.stApp{background:radial-gradient(1200px 620px at 82% -12%, #151b2e 0%, var(--bg) 55%);}
.block-container{padding-top:1.1rem; padding-bottom:2.4rem; max-width:1440px;}
html, body, [class*="css"]{font-family:'Inter',sans-serif; color:var(--text);}

/* Header */
.top{display:flex; align-items:center; justify-content:space-between;
  padding:18px 24px; border:1px solid var(--line); border-radius:16px;
  background:linear-gradient(180deg,var(--surface2),var(--surface));
  margin-bottom:22px; position:relative; overflow:hidden;}
.top::before{content:""; position:absolute; top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg,var(--accent),var(--cyan),transparent);}
.brand{display:flex; align-items:center; gap:14px;}
.logo{width:44px; height:44px; border-radius:13px; display:grid; place-items:center;
  background:linear-gradient(135deg,var(--accent),#4f46e5); font-size:22px;
  box-shadow:0 8px 22px rgba(124,107,245,.35);}
.brand h1{font-size:1.2rem; font-weight:800; margin:0; letter-spacing:-.4px;}
.brand p{font-size:.75rem; color:var(--muted); margin:3px 0 0;}
.top-right{display:flex; align-items:center; gap:22px;}
.clock{font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:600; color:var(--text); text-align:right;}
.clock span{display:block; font-size:.66rem; color:var(--faint); font-family:'Inter',sans-serif; font-weight:400; margin-top:2px;}
.live{display:flex; align-items:center; gap:8px; font-size:.74rem; font-weight:600; color:var(--green);
  background:rgba(63,207,142,.1); padding:7px 13px; border-radius:20px; border:1px solid rgba(63,207,142,.25);}
.ldot{width:8px; height:8px; border-radius:50%; background:var(--green); animation:pulse 1.8s infinite;}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(63,207,142,.55);}70%{box-shadow:0 0 0 8px rgba(63,207,142,0);}100%{box-shadow:0 0 0 0 rgba(63,207,142,0);}}

/* KPI strip */
.kpi-strip{display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:24px;}
.kpi{background:var(--surface); border:1px solid var(--line); border-radius:15px; padding:17px 19px; transition:.2s ease;}
.kpi:hover{border-color:#333c54; transform:translateY(-2px);}
.kpi-row{display:flex; align-items:center; justify-content:space-between; margin-bottom:13px;}
.kpi-ico{width:35px; height:35px; border-radius:10px; display:grid; place-items:center; font-size:16px;}
.kpi-sub{font-size:.68rem; font-weight:600; padding:3px 9px; border-radius:20px;}
.t-up{color:var(--green); background:rgba(63,207,142,.12);}
.t-down{color:var(--red); background:rgba(242,109,109,.12);}
.t-neutral{color:var(--muted); background:rgba(139,147,167,.1);}
.kpi-val{font-size:1.72rem; font-weight:800; letter-spacing:-.6px; line-height:1;}
.kpi-lbl{font-size:.75rem; color:var(--muted); margin-top:7px;}

/* Section label */
.sec{display:flex; align-items:center; gap:11px; margin:4px 0 15px;}
.sec h3{font-size:.95rem; font-weight:700; margin:0; letter-spacing:-.2px;}
.sec .count{font-size:.7rem; color:var(--faint); background:var(--raised); padding:3px 10px; border-radius:20px; border:1px solid var(--line);}

/* Node grid */
.nodes{display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:6px;}
.node{background:var(--surface); border:1px solid var(--line); border-radius:15px; padding:16px; position:relative; overflow:hidden;}
.node::before{content:""; position:absolute; top:0; left:0; right:0; height:3px;}
.node.n-normal::before{background:var(--green);}
.node.n-warning::before{background:var(--amber);}
.node.n-critical::before{background:var(--red);}
.node.n-idle::before{background:var(--accent);}
.node.n-critical{box-shadow:0 0 26px rgba(242,109,109,.16);}
.node-head{display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:11px; gap:8px;}
.node-name{font-size:.9rem; font-weight:700; letter-spacing:-.2px;}
.node-host{font-size:.64rem; color:var(--faint); font-family:'JetBrains Mono',monospace; margin-top:3px;}
.livehw{display:inline-block; font-size:.54rem; font-weight:700; color:#04211c; background:var(--cyan);
  padding:2px 6px; border-radius:5px; letter-spacing:.5px; margin-top:6px;}
.pill{font-size:.6rem; font-weight:700; padding:4px 8px; border-radius:6px; letter-spacing:.5px; white-space:nowrap;}
.p-normal{color:var(--green); background:rgba(63,207,142,.12);}
.p-warning{color:var(--amber); background:rgba(245,180,81,.12);}
.p-critical{color:var(--red); background:rgba(242,109,109,.14);}
.p-idle{color:#a99ff9; background:rgba(124,107,245,.14);}
.node-gpu{font-size:.71rem; color:var(--muted); margin-bottom:3px;}
.node-job{font-size:.74rem; color:var(--text); font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:3px;}
.node-user{font-size:.65rem; color:var(--faint); margin-bottom:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.bar{height:6px; border-radius:4px; background:var(--raised); overflow:hidden; margin-bottom:13px;}
.bar-fill{height:100%; border-radius:4px; transition:width .4s ease;}
.node-metrics{display:grid; grid-template-columns:repeat(2,1fr); gap:7px;}
.chip{background:var(--surface2); border:1px solid var(--line-soft); border-radius:9px; padding:7px 9px;}
.chip .k{font-size:.58rem; color:var(--faint); text-transform:uppercase; letter-spacing:.6px;}
.chip .v{font-size:.86rem; font-weight:700; font-family:'JetBrains Mono',monospace; margin-top:2px;}
.cause{margin-top:11px; font-size:.67rem; padding:7px 10px; border-radius:8px; line-height:1.4;}
.cause.c-warn{color:var(--amber); background:rgba(245,180,81,.08); border:1px solid rgba(245,180,81,.2);}
.cause.c-crit{color:#ffb4b4; background:rgba(242,109,109,.08); border:1px solid rgba(242,109,109,.22);}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{gap:6px; background:var(--surface); padding:6px; border-radius:13px; border:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{height:40px; padding:0 20px; border-radius:9px; color:var(--muted); font-weight:600; font-size:.84rem;}
.stTabs [aria-selected="true"]{background:var(--raised)!important; color:var(--text)!important;}
.stTabs [data-baseweb="tab-highlight"]{display:none;}

/* Logs / alerts / banner */
.card-h{font-size:.82rem; font-weight:700; color:var(--text); margin:6px 0 12px; letter-spacing:-.2px;}
.log{background:var(--surface2); border:1px solid var(--line-soft); border-left:3px solid var(--green);
  border-radius:9px; padding:10px 13px; margin-bottom:8px; font-size:.76rem;
  font-family:'JetBrains Mono',monospace; color:var(--muted);}
.log b{color:var(--text); font-weight:600;}
.alert{background:rgba(242,109,109,.07); border:1px solid rgba(242,109,109,.2); border-left:3px solid var(--red);
  border-radius:9px; padding:10px 13px; margin-bottom:8px; font-size:.76rem; color:#ffbcbc; font-family:'JetBrains Mono',monospace;}
.empty{background:var(--surface2); border:1px dashed var(--line); border-radius:11px; padding:20px; text-align:center; color:var(--muted); font-size:.8rem;}
.banner{background:linear-gradient(100deg,rgba(63,207,142,.08),rgba(45,212,191,.03)); border:1px solid rgba(63,207,142,.22);
  border-radius:15px; padding:20px 24px; margin-top:16px;}
.banner .lbl{font-size:.8rem; color:var(--green); font-weight:600;}
.banner .big{font-size:2rem; font-weight:800; color:var(--green); letter-spacing:-.6px; margin:6px 0;}
.banner .co2{font-size:1rem; color:#7fe3b8; font-weight:600;}
.banner .note{font-size:.72rem; color:var(--faint); margin-top:8px; line-height:1.5;}
.desc{font-size:.8rem; color:var(--muted); line-height:1.55; margin-bottom:16px;}
.desc code{background:var(--raised); color:var(--cyan); padding:2px 7px; border-radius:6px; font-size:.76rem;}

.topalert{display:flex;align-items:center;gap:10px;background:rgba(242,109,109,.1);border:1px solid rgba(242,109,109,.35);border-left:4px solid var(--red);border-radius:12px;padding:12px 18px;margin-bottom:16px;color:#ffbcbc;font-size:.82rem;font-weight:600;}
.topalert .rdot{width:9px;height:9px;border-radius:50%;background:var(--red);}

/* Energy table */
.etable{width:100%; border-collapse:collapse; font-size:.79rem;}
.etable td{padding:11px 4px; border-bottom:1px solid var(--line-soft); color:var(--muted);}
.etable tr:last-child td{border-bottom:none;}
.etable td:last-child{text-align:right; color:var(--text); font-weight:600; font-family:'JetBrains Mono',monospace;}

/* Sidebar */
[data-testid="stSidebar"]{background:var(--surface); border-right:1px solid var(--line);}
[data-testid="stSidebar"] .stButton button{border-radius:9px; border:1px solid var(--line); background:var(--surface2); color:var(--text); font-size:.78rem; font-weight:600;}
[data-testid="stSidebar"] .stButton button:hover{border-color:var(--accent); color:#fff;}

/* ── Responsive ── */
@media (max-width:1100px){
  .kpi-strip{grid-template-columns:repeat(2,1fr)!important;}
  .nodes{grid-template-columns:repeat(2,1fr)!important;}
}
@media (max-width:640px){
  .kpi-strip{grid-template-columns:1fr!important;}
  .nodes{grid-template-columns:1fr!important;}
  .top{flex-direction:column; align-items:flex-start; gap:12px;}
  .top-right{width:100%; justify-content:space-between;}
  .clock{text-align:left;}
  .block-container{padding-left:.7rem!important; padding-right:.7rem!important;}
  .kpi-val{font-size:1.4rem;}
}

/* radio view-switcher-কে ট্যাবের মতো দেখানো */
div[role="radiogroup"]{gap:6px; background:var(--surface); padding:6px; border-radius:13px;
  border:1px solid var(--line); display:inline-flex; margin-bottom:14px;}
div[role="radiogroup"] label{margin:0!important; padding:8px 18px; border-radius:9px; cursor:pointer;
  color:var(--muted); font-weight:600; font-size:.84rem;}
div[role="radiogroup"] label:hover{color:var(--text);}
div[role="radiogroup"] label input{display:none;}
div[role="radiogroup"] label:has(input:checked){background:var(--raised); color:var(--text);}
</style>
""", unsafe_allow_html=True)

# ─── SESSION INIT ───────────────────────────────
if "initialized" not in st.session_state:
    init_db()
    load_models()
    start_scanner()
    for name, pri in [
        ("ResNet-152 ImageNet Pre-train", 5),
        ("GPT-4 RLHF Fine-tune", 5),
        ("Bangla OCR CNN Training", 4),
        ("Face Recognition — Campus Security", 4),
        ("ViT-B/16 Medical Imaging", 3),
    ]:
        add_job(name, priority=pri)
    loop_proof.reset()
    st.session_state["initialized"] = True

st.session_state.setdefault("job_logs", [])
st.session_state.setdefault("migration_logs", [])
st.session_state.setdefault("total_prevented_crashes", 0)
st.session_state.setdefault("session_start", datetime.now())

session_mins = max(1, int((datetime.now() - st.session_state["session_start"]).total_seconds() / 60))

# ─── STYLE HELPERS ──────────────────────────
LVL = {
    "normal":   ("n-normal",   "p-normal",   "NORMAL",   "#3FCF8E"),
    "warning":  ("n-warning",  "p-warning",  "WARNING",  "#F5B451"),
    "critical": ("n-critical", "p-critical", "CRITICAL", "#F26D6D"),
    "idle":     ("n-idle",     "p-idle",     "IDLE",     "#7C6BF5"),
}


def brand_fig(fig, height=310, title=None):
    fig.update_layout(
        height=height, title=title,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8B93A7", family="Inter, sans-serif", size=12),
        title_font=dict(color="#EAEDF4", size=14, family="Inter, sans-serif"),
        margin=dict(l=8, r=14, t=46 if title else 12, b=8),
        xaxis=dict(gridcolor="#1B2130", zerolinecolor="#1B2130", linecolor="#242A3A"),
        yaxis=dict(gridcolor="#1B2130", zerolinecolor="#1B2130", linecolor="#242A3A"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8B93A7")),
    )
    return fig


def kpi_card(icon, accent, value, label, sub, trend="neutral"):
    tcls = {"up": "t-up", "down": "t-down", "neutral": "t-neutral"}[trend]
    return (
        f'<div class="kpi"><div class="kpi-row">'
        f'<span class="kpi-ico" style="background:{accent}1f;color:{accent};">{icon}</span>'
        f'<span class="kpi-sub {tcls}">{sub}</span></div>'
        f'<div class="kpi-val">{value}</div><div class="kpi-lbl">{label}</div></div>'
    )


def mini_grid(items):
    cells = "".join(
        f'<div class="kpi"><div class="kpi-val" style="color:{a};font-size:1.5rem;">{v}</div>'
        f'<div class="kpi-lbl">{l}</div></div>'
        for l, v, a in items
    )
    st.markdown(
        f'<div class="kpi-strip" style="grid-template-columns:repeat({len(items)},1fr);margin-bottom:18px;">{cells}</div>',
        unsafe_allow_html=True,
    )


def node_card(row, live_badge=""):
    is_idle = row["job_type"] == "Idle"
    lvl = "idle" if is_idle else row["risk_level"].lower()
    ncls, pcls, plabel, color = LVL[lvl]
    util = int(round(row["utilization"]))
    vram = row["gpu_vram_gb"]
    mem_pct = int(round(row["memory_used"] / vram * 100)) if vram else 0
    badge = f'<div class="livehw">{live_badge}</div>' if (live_badge and row.get("data_source") == "live") else ""
    cause = ""
    if not is_idle and lvl in ("warning", "critical"):
        ccls = "c-crit" if lvl == "critical" else "c-warn"
        cause = f'<div class="cause {ccls}">⚠ {row["root_cause"]}</div>'
    return (
        f'<div class="node {ncls}">'
        f'<div class="node-head"><div><div class="node-name">{row["display_name"]}</div>'
        f'<div class="node-host">{row["hostname"]}</div>{badge}</div>'
        f'<span class="pill {pcls}">{plabel}</span></div>'
        f'<div class="node-gpu">{row["gpu_model"]} · {vram}GB</div>'
        f'<div class="node-job">▶ {row["current_job"]}</div>'
        f'<div class="node-user">👤 {row["researcher"]}</div>'
        f'<div class="bar"><div class="bar-fill" style="width:{util}%;background:{color};"></div></div>'
        f'<div class="node-metrics">'
        f'<div class="chip"><div class="k">Risk</div><div class="v" style="color:{color};">{row["risk_score"]}</div></div>'
        f'<div class="chip"><div class="k">Temp</div><div class="v">{row["temperature"]}°</div></div>'
        f'<div class="chip"><div class="k">GPU Load</div><div class="v">{util}%</div></div>'
        f'<div class="chip"><div class="k">VRAM</div><div class="v">{mem_pct}%</div></div>'
        f'</div>{cause}</div>'
    )


# ─── SIDEBAR ───────────────────────────────────
with st.sidebar:
    st.markdown("### 🛰 Live Hardware")
    st.caption("Auto-detects every real GPU on THIS machine and shows each as a live node. Remaining nodes stay simulated.")
    live_on = st.checkbox("Enable live hardware mode", value=True)
    set_live_mode(live_on)
    _lm = live_mode_info()
    if _lm["enabled"]:
        n = _lm.get("num_live", 0)
        if _lm["is_real_gpu"]:
            name = _lm.get("gpu_name") or (_lm.get("mode") or "").upper()
            st.success(f"● {n} real GPU node(s) live\n\n{name}")
        else:
            st.info(f"● 1 system-based live node\n\nno discrete GPU — using CPU/RAM (mode: {(_lm.get('mode') or 'system')})")
        st.caption(f"{5 - n} node(s) simulated.")
    else:
        st.caption("Simulation only — all 5 nodes synthetic.")

    st.divider()
    st.markdown("### ⚡ Demo Control Room")
    st.caption("Inject a live fault on any node and watch SensorAI + SchedulerAI react in real time.")
    node_sel = st.selectbox(
        "Target workstation",
        options=list(CLUSTER_NODES.keys()),
        format_func=lambda n: CLUSTER_NODES[n]["display_name"],
    )
    a, b = st.columns(2)
    if a.button("🔥 Thermal Spike", use_container_width=True):
        trigger_chaos(node_sel, "thermal_spike"); st.rerun()
    if b.button("⚡ Power Surge", use_container_width=True):
        trigger_chaos(node_sel, "power_surge"); st.rerun()
    c, d = st.columns(2)
    if c.button("🧠 Memory Leak", use_container_width=True):
        trigger_chaos(node_sel, "memory_leak"); st.rerun()
    if d.button("💤 Force Idle", use_container_width=True):
        trigger_chaos(node_sel, "idle_force"); st.rerun()
    if st.button("♻️ Clear All Faults", use_container_width=True):
        clear_all_chaos(); st.rerun()
    st.divider()
    paused = st.checkbox("⏸ Pause live refresh", value=False)
    refresh_rate = st.slider("Refresh interval (s)", 2, 10, 4)

# ─── LOAD LOGO ────────────────────────────────
logo_path = Path("assets/logo.png")
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
else:
    logo_base64 = ""  # Fallback

# ─── DATA REFRESH ─────────────────────────────
frag = getattr(st, "fragment", None) or getattr(st, "experimental_fragment")

@frag(run_every=(refresh_rate if not paused else None))
def live_view():
    metrics_df = generate_metrics()
    risk_df = predict_risk(metrics_df)
    data = metrics_df.merge(risk_df[["node_id", "risk_score", "risk_level", "root_cause"]], on="node_id")

    insert_metrics(metrics_df[["node_id", "temperature", "utilization", "memory_used", "power_draw", "timestamp"]].to_dict("records"))
    for _, r in risk_df.iterrows():
        insert_prediction(r["node_id"], r["risk_score"], r["risk_level"])

    # SchedulerAI — pull one job from the queue each refresh
    job_name, best_node, reason = assign_job(metrics_df, risk_df)
    if job_name:
        log_job(job_name, best_node, reason)
        cfg = CLUSTER_NODES.get(best_node, {})
        st.session_state["job_logs"].insert(0, f'<b>{job_name}</b> → {cfg.get("hostname", "Node " + str(best_node))} | {reason}')

    # Migration check
    for m in check_migration(metrics_df, risk_df):
        st.session_state["migration_logs"].insert(0, f'Node {m["node_id"]} ({CLUSTER_NODES[m["node_id"]]["hostname"]}) — Risk {m["risk_score"]}% — {m["action"]}')
        st.session_state["total_prevented_crashes"] += 1

    cost = get_cost_summary()

    # LoopProof: advance the learning loop one cycle (scores previous
    # outcomes, records new decisions, detects & resolves module conflicts)
    loop_proof.run_cycle(metrics_df, risk_df, get_idle_nodes(), best_node, get_node_jobs())

    # Real energy from measured power draw (live node reports real watts)
    real_power_kw = float(data["power_draw"].sum()) / 1000.0
    live_power_w = float(data[data["data_source"] == "live"]["power_draw"].sum())
    _bdt_per_usd = COST_PER_GPU_PER_HOUR_BDT / COST_PER_GPU_PER_HOUR_USD
    elec_usd_kwh = ELECTRICITY_PER_KWH_BDT / _bdt_per_usd
    real_cost_usd_hr = real_power_kw * elec_usd_kwh

    # Live-mode presentation values
    _lm = live_mode_info()
    live_badge = ("🛰 LIVE HW" if _lm["is_real_gpu"] else "🛰 LIVE · SYS") if _lm["enabled"] else ""
    live_label = "LIVE HW · 5 NODES" if (_lm["enabled"] and _lm["is_real_gpu"]) else "LIVE · 5 NODES"

    # ─── HEADER ──────────────────────────────
    now = datetime.now(DHAKA)
    st.markdown(f"""
<div class="top">
  <div class="brand">
    <img src="data:image/png;base64,{{logo_base64}}" class="logo-img" style="width:50px;height:50px;border-radius:12px;"/>
    <div><h1>TensorTitan</h1><p>see the cluster. Predict the failure. Save the cost.</p></div>
  </div>
  <div class="top-right">
    <div class="clock">{now.strftime('%H:%M:%S')}<span>{now.strftime('%A, %d %B %Y')}</span></div>
    <div class="live"><span class="ldot"></span>{live_label}</div>
  </div>
</div>
""".replace("{logo_base64}", logo_base64), unsafe_allow_html=True)

    # ─── KPI STRIP ───────────────────────────
    # Overload & live-workload notifications
    _overloaded = data[(data["risk_level"] == "Critical") | (data["utilization"] >= 96)]
    if len(_overloaded):
        _names = ", ".join(_overloaded["display_name"].tolist())
        st.markdown(f'<div class="topalert"><span class="rdot"></span>⚠ OVERLOAD — {_names} cannot accept more load (Critical / GPU maxed). SchedulerAI is rerouting workloads.</div>', unsafe_allow_html=True)
        if st.session_state.get("_ovl") != _names:
            st.toast(f"🚨 Overload: {_names}", icon="🚨")
            st.session_state["_ovl"] = _names
    else:
        st.session_state["_ovl"] = ""

    _ws = workload_status()
    if _ws.get("running"):
        _wcfg = CLUSTER_NODES.get(_ws.get("node"), {})
        st.markdown(f'<div class="topalert" style="background:rgba(45,212,191,.08);border-color:rgba(45,212,191,.4);border-left-color:#2DD4BF;color:#8ff0e4;"><span class="rdot" style="background:#2DD4BF;"></span>🔴 REAL WORKLOAD RUNNING — <b>{_ws.get("job")}</b> on {_wcfg.get("display_name","live node")} · {str(_ws.get("device") or "cpu").upper()} · {int(_ws.get("elapsed") or 0)}s elapsed</div>', unsafe_allow_html=True)

    avg_risk = risk_df["risk_score"].mean()
    health_pct = max(0, round(100 - avg_risk, 1))
    if health_pct > 70:
        h_accent, h_trend, h_sub = "#3FCF8E", "up", "Nominal"
    elif health_pct > 40:
        h_accent, h_trend, h_sub = "#F5B451", "neutral", "Attention"
    else:
        h_accent, h_trend, h_sub = "#F26D6D", "down", "Action needed"

    active_jobs = int((data["job_type"] != "Idle").sum())

    st.markdown('<div class="kpi-strip">' + "".join([
        kpi_card("🩺", h_accent, f"{health_pct}%", "Cluster Health", h_sub, h_trend),
        kpi_card("🚀", "#2DD4BF", f"{active_jobs}/5", "Active AI Jobs", f"{queue_length()} queued", "neutral"),
        kpi_card("🛡", "#7C6BF5", f'{st.session_state["total_prevented_crashes"]}', "Crashes Prevented", "auto-migrated", "up"),
        kpi_card("💰", "#F5B451", f"${real_cost_usd_hr:.2f}/hr", "Power Cost · real", f"{real_power_kw:.2f} kW draw", "neutral"),
        kpi_card("🌱", "#3FCF8E", f"{cost['co2_saved_kg']} kg", "CO₂ Prevented", "vs no mgmt", "up"),
    ]) + '</div>', unsafe_allow_html=True)

    # ─── LIVE NODE MONITOR ───────────────────────
    crit = int((data["risk_level"] == "Critical").sum())
    st.markdown(
        f'<div class="sec"><h3>📡 Live Cluster Monitor</h3>'
        f'<span class="count">5 workstations</span>'
        + (f'<span class="count" style="color:#F26D6D;border-color:rgba(242,109,109,.3);">{crit} critical</span>' if crit else '')
        + '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="nodes">' + "".join(node_card(row, live_badge) for _, row in data.iterrows()) + '</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # ─── TABS ───────────────────────────────
    VIEWS = ["🔬 Risk Analysis", "⚙️ Smart Scheduler", "💰 Cost & Energy", "🔁 Loop Proof"]
    view = st.radio("view", VIEWS, horizontal=True,
                     label_visibility="collapsed", key="active_view")

    # ── TAB 1 ──
    if view == VIEWS[0]:
        st.markdown(
            '<div class="desc"><b>SensorAI</b> fuses an <code>Isolation Forest</code> (anomaly detection) with a '
            '<code>Random Forest</code> (failure prediction) trained on GPU telemetry to produce a live risk score per node.</div>',
            unsafe_allow_html=True,
        )
        ca, cb = st.columns(2)
        with ca:
            order = data.sort_values("risk_score")
            rc = [LVL[l.lower()][3] for l in order["risk_level"]]
            f1 = go.Figure(go.Bar(
                x=order["risk_score"], y=order["display_name"], orientation="h",
                marker=dict(color=rc), text=[f"{s}%" for s in order["risk_score"]],
                textposition="outside", textfont=dict(color="#EAEDF4", size=12),
                hovertemplate="%{y}<br>Risk: %{x}%<extra></extra>",
            ))
            f1.update_xaxes(range=[0, 108])
            st.plotly_chart(brand_fig(f1, 300, "Failure Risk Score by Node"), use_container_width=True)
        with cb:
            tc = ["#F26D6D" if t > 87 else "#F5B451" if t > 80 else "#3FCF8E" for t in data["temperature"]]
            f2 = go.Figure(go.Bar(
                x=data["display_name"], y=data["temperature"], marker=dict(color=tc),
                text=[f"{t}°" for t in data["temperature"]], textposition="outside",
                textfont=dict(color="#EAEDF4", size=12),
                hovertemplate="%{x}<br>%{y}°C<extra></extra>",
            ))
            f2.add_hline(y=80, line_dash="dot", line_color="#F5B451", annotation_text="Warning 80°", annotation_font_color="#F5B451")
            f2.add_hline(y=87, line_dash="dot", line_color="#F26D6D", annotation_text="Critical 87°", annotation_font_color="#F26D6D")
            f2.update_yaxes(range=[30, 100])
            f2.update_xaxes(tickangle=-15)
            st.plotly_chart(brand_fig(f2, 300, "Thermal Safety Monitor"), use_container_width=True)

        st.markdown('<div class="card-h">🔍 Explainable AI — Root Cause Breakdown</div>', unsafe_allow_html=True)
        rows_html = "".join(
            f'<tr><td>{r["display_name"]}</td><td style="color:var(--muted);text-align:left;font-weight:400;font-family:Inter;">{r["current_job"]}</td>'
            f'<td style="color:{LVL[("idle" if r["job_type"]=="Idle" else r["risk_level"].lower())][3]};">{r["risk_level"]} · {r["risk_score"]}%</td>'
            f'<td style="color:var(--muted);text-align:left;font-weight:400;font-family:Inter;">{r["root_cause"]}</td></tr>'
            for _, r in data.iterrows()
        )
        st.markdown(
            '<table class="etable"><tr>'
            '<td style="color:var(--faint);font-weight:600;">WORKSTATION</td>'
            '<td style="color:var(--faint);font-weight:600;text-align:left;">ACTIVE JOB</td>'
            '<td style="color:var(--faint);font-weight:600;text-align:left;">RISK</td>'
            '<td style="color:var(--faint);font-weight:600;text-align:left;">ROOT CAUSE</td>'
            f'</tr>{rows_html}</table>',
            unsafe_allow_html=True,
        )

    # ── TAB 2 ──
    if view == VIEWS[1]:
        st.markdown(
            '<div class="desc"><b>SchedulerAI</b> intelligently assigns jobs to the healthiest GPU nodes and auto-migrates workloads when a node becomes critical.</div>',
            unsafe_allow_html=True,
        )
        with st.expander("ℹ️ How does the scoring algorithm work?"):
            st.markdown("""
**Node Scoring Formula:**
```
Score = (1 − Risk) × 0.5 + FreeVRAM × 0.3 + ThermalHeadroom × 0.2
```

**Weights explained:**
- **50%** — Health & Stability (inverse of risk score)
- **30%** — Available VRAM (memory capacity)
- **20%** — Thermal headroom (temperature safety margin)

The job is assigned to the node with the **highest score**. If a node turns Critical mid-job, the workload automatically migrates to the next healthiest node.
            """)

        mini_grid([
            ("Jobs in Queue", queue_length(), "#2DD4BF"),
            ("Auto-Migrations", len(st.session_state["migration_logs"]), "#F5B451"),
            ("Crashes Prevented", st.session_state["total_prevented_crashes"], "#3FCF8E"),
        ])
        cl, cr = st.columns(2)
        with cl:
            st.markdown('<div class="card-h">📋 Job Assignment Log</div>', unsafe_allow_html=True)
            if st.session_state["job_logs"]:
                st.markdown("".join(f'<div class="log">✅ {x}</div>' for x in reversed(st.session_state["job_logs"][:8])), unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Queue is processing — assignments will appear here.</div>', unsafe_allow_html=True)
        with cr:
            st.markdown('<div class="card-h">🚨 Auto-Migration Alerts</div>', unsafe_allow_html=True)
            if st.session_state["migration_logs"]:
                st.markdown("".join(f'<div class="alert">🔴 {x}</div>' for x in reversed(st.session_state["migration_logs"][:6])), unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty" style="color:#3FCF8E;">✅ All nodes within safe thresholds. No migrations needed.</div>', unsafe_allow_html=True)

        st.markdown('<div class="card-h" style="margin-top:20px;">➕ Assign a Job to a Specific GPU</div>', unsafe_allow_html=True)
        _lm2 = live_mode_info()
        _live_ids = list(CLUSTER_NODES)[: _lm2.get("num_live", 0)] if _lm2.get("enabled") else []
        # আসল/live নাম live data থেকে নাও, static config থেকে না
        _name_by_id = dict(zip(data["node_id"], data["display_name"]))
        def _fmt_target(n):
            if n == "auto":
                return "🤖 Auto — let AI pick the healthiest GPU"
            nm = _name_by_id.get(n, CLUSTER_NODES[n]["display_name"])
            return nm + (" · 🛰 LIVE" if n in _live_ids else "")
        with st.form("assign_job_form", clear_on_submit=True):
            fa, fb, fc, fd = st.columns([3, 2, 1, 1])
            job_input = fa.text_input("Job", placeholder="e.g. GPT-4 Bangla Finetune, YOLOv9 Training…", label_visibility="collapsed")
            target_choice = fb.selectbox("Target GPU", ["auto"] + list(CLUSTER_NODES.keys()), format_func=_fmt_target, label_visibility="collapsed")
            priority_input = fc.selectbox("Priority", [5, 4, 3, 2, 1], format_func=lambda x: f"P{x}", label_visibility="collapsed")
            submitted = fd.form_submit_button("⚡ Assign", use_container_width=True)
            if submitted:
                if not job_input.strip():
                    st.error("Please enter a job name.")
                else:
                    job = job_input.strip()
                    if target_choice == "auto":
                        _cand = data[data["risk_level"] != "Critical"]
                        target = int(_cand.sort_values(["utilization", "risk_score"]).iloc[0]["node_id"]) if len(_cand) else None
                    else:
                        target = int(target_choice)
                    if target is None:
                        st.warning("⏳ All nodes are Critical — job held in queue.")
                    else:
                        _trow = data[data["node_id"] == target].iloc[0]
                        if _trow["risk_level"] == "Critical" or _trow["utilization"] >= 96:
                            st.session_state["migration_logs"].insert(0, f'{CLUSTER_NODES[target]["hostname"]} rejected "{job}" — node overloaded.')
                            st.toast(f"🚨 {CLUSTER_NODES[target]['display_name']} is overloaded", icon="🚨")
                            st.error(f"❌ {CLUSTER_NODES[target]['display_name']} can't accept more load right now. Pick another GPU or use Auto.")
                        else:
                            assign_job_to_node(target, job, priority_input)
                            _is_live = target in _live_ids
                            if _is_live:
                                start_workload(job, target, priority_input)
                            _cfg = CLUSTER_NODES.get(target, {})
                            _tag = " · 🔴 REAL workload started" if _is_live else ""
                            log_job(job, target, "Manual" if target_choice != "auto" else "AI auto")
                            st.session_state["job_logs"].insert(0, f'<b>{job}</b> → {_cfg.get("hostname", "Node " + str(target))} | P{priority_input}{_tag}')
                            st.success(f"✅ {job} → {_name_by_id.get(target, 'Node ' + str(target))}{_tag}")
                            st.rerun()

        _ws_now = workload_status()
        _bc1, _bc2, _bc3 = st.columns(3)
        # ▶ START — প্রথম live GPU-তে আসল workload চালু করে
        if _bc1.button("▶ Start workload", use_container_width=True,
                       disabled=(_ws_now.get("running") or not _live_ids)):
            _lnode = _live_ids[0]
            _jobname = "Manual Live Benchmark"
            assign_job_to_node(_lnode, _jobname, 3)
            start_workload(_jobname, _lnode, 3)
            st.toast("▶ Live workload started."); st.rerun()
        # ⏹ STOP — workload থামায় + node-টাও clear করে যাতে দৃশ্যমানভাবে থামে
        if _bc2.button("⏹ Stop workload", use_container_width=True,
                       disabled=not _ws_now.get("running")):
            stop_workload()
            _sn = _ws_now.get("node")
            if _sn is not None:
                clear_node_job(_sn)
            st.toast("⏹ Live workload stopped."); st.rerun()
        # 🧹 CLEAR — সব assignment মুছে দেয়
        if _bc3.button("🧹 Clear all", use_container_width=True):
            clear_all_node_jobs(); stop_workload(); st.rerun()

    # ── TAB 3 ──
    if view == VIEWS[2]:
        idle_nodes = get_idle_nodes()
        idle_count = len(idle_nodes)
        active_count = 5 - idle_count
        mini_grid([
            ("Active Workstations", f"{active_count}/5", "#3FCF8E"),
            ("Idle Machines", idle_count, "#F5B451" if idle_count else "#3FCF8E"),
            ("Power Cost/hr · real", f"${real_cost_usd_hr:.2f}", "#2DD4BF"),
            ("Monthly Waste", f"${cost['monthly_waste']:.0f}" if cost["monthly_waste"] > 0 else "$0", "#F26D6D" if cost["monthly_waste"] > 0 else "#3FCF8E"),
        ])

        st.markdown(f"""
    <div class="banner">
      <div class="lbl">💰 Total Savings This Session ({session_mins} min)</div>
      <div class="big">${cost['total_savings']:.2f} USD</div>
      <div class="co2">🌱 {cost['co2_saved_kg']} kg CO₂ prevented</div>
      <div class="note">CostAI scans every 10 seconds. A GPU idle for 5+ minutes (below 5% utilization) is flagged and its workload is auto-reassigned from the queue.</div>
    </div>
    """, unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        cp, ce = st.columns(2)
        with cp:
            pie = go.Figure(go.Pie(
                labels=["Running AI Jobs", "Idle / Unallocated"],
                values=[max(active_count, 0.001), max(idle_count, 0.001)],
                hole=0.62, marker=dict(colors=["#3FCF8E", "#7C6BF5"], line=dict(color="#0A0C12", width=3)),
                textfont=dict(color="#EAEDF4", size=13), sort=False,
            ))
            pie.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(brand_fig(pie, 300, "Cluster Allocation"), use_container_width=True)
        with ce:
            st.markdown('<div class="card-h">⚡ Electricity & Carbon Impact</div>', unsafe_allow_html=True)
            total_kw = real_power_kw
            daily_kwh = total_kw * 24
            live_row = (f'<tr><td>🔴 Live measured (real HW)</td><td style="color:#2DD4BF;">{live_power_w:.0f} W</td></tr>' if live_power_w > 0 else '')
            st.markdown(f"""
        <table class="etable">
          <tr><td>Total Power Draw (real+sim)</td><td>{total_kw:.2f} kW</td></tr>
          {live_row}
          <tr><td>Electricity Cost / hr</td><td>${real_cost_usd_hr:.2f}</td></tr>
          <tr><td>Daily Energy Usage</td><td>{daily_kwh:.1f} kWh</td></tr>
          <tr><td>CO₂ (today est.)</td><td>{daily_kwh * CO2_PER_KWH_KG:.1f} kg</td></tr>
          <tr><td>CO₂ Prevented (idle mgmt)</td><td style="color:#3FCF8E;">{cost['co2_saved_kg']} kg</td></tr>
        </table>
        """, unsafe_allow_html=True)


    # ── LOOP PROOF PANEL ──
    if view == VIEWS[3]:
        st.markdown(
            '<div class="desc"><b>Loop Proof Panel</b> sits on top of SensorAI + SchedulerAI + CostAI. '
            'It records every module decision with its measured outcome, proves the loop learns via a rising '
            '<code>helpful-decision</code> curve, and resolves conflicts (e.g. CostAI wants to fill an idle GPU that '
            'SchedulerAI wants to keep free) using a clear <code>Safety &gt; Cost</code> rule. No model training — '
            'the loop adapts a real safety margin from its own past outcomes.</div>',
            unsafe_allow_html=True,
        )
        _lp = loop_proof.summary()
        _tr = _lp["trend"]
        mini_grid([
            ("Loop Cycles", _lp["cycles"], "#2DD4BF"),
            ("Helpful Decisions", f'{_lp["helpful_pct"]}%', "#3FCF8E"),
            ("Conflicts Resolved", _lp["conflicts_resolved"], "#F5B451"),
            ("Learning Trend", f'{"+" if _tr >= 0 else ""}{_tr}%', "#7C6BF5"),
        ])

        _cL, _cR = st.columns([3, 2])
        with _cL:
            st.markdown('<div class="card-h">📈 Learning Curve — share of helpful decisions per cycle</div>', unsafe_allow_html=True)
            _curve = loop_proof.learning_curve()
            if len(_curve) >= 2:
                _xs = [c["cycle"] for c in _curve]
                _ys = [c["helpful_pct"] for c in _curve]
                _lf = go.Figure(go.Scatter(
                    x=_xs, y=_ys, mode="lines+markers",
                    line=dict(color="#3FCF8E", width=3, shape="spline"),
                    marker=dict(size=7, color="#3FCF8E"),
                    fill="tozeroy", fillcolor="rgba(63,207,142,.12)",
                    hovertemplate="Cycle %{x}<br>Helpful: %{y}%<extra></extra>",
                    name=""  # Empty name to prevent "undefined" from showing
                ))
                _lf.update_yaxes(range=[0, 105], ticksuffix="%", title="Helpful Decisions (%)")
                _lf.update_xaxes(title="Cycle", dtick=1)
                _lf.update_layout(showlegend=False)  # Hide legend completely
                st.plotly_chart(brand_fig(_lf, 300, ""), use_container_width=True)
            else:
                st.markdown('<div class="empty">Collecting decisions… the curve appears after a few refresh cycles.</div>', unsafe_allow_html=True)

            if st.button("⚔️ Force a live conflict (demo)", use_container_width=True):
                loop_proof.force_conflict()
                st.toast("Conflict staged — watch it resolve on the next refresh.")
                st.rerun()

            st.markdown('<div class="card-h" style="margin-top:14px;">⚔️ Conflict Resolution Log</div>', unsafe_allow_html=True)
            _cf = loop_proof.conflict_log(6)
            if _cf:
                st.markdown("".join(
                    f'<div class="alert" style="border-left-color:#F5B451;color:#ffe0b0;background:rgba(245,180,81,.07);">'
                    f'⚔️ <b>Node {c["node_id"]}</b> (risk {c["risk"]}) — {c["modules"]} → '
                    f'<b>{c["winner"]}</b>: {c["action"]}<br><span style="color:#8B93A7;font-family:Inter;">{c["reason"]}</span></div>'
                    for c in _cf
                ), unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">No conflicts yet. Click “Force a live conflict” to demo the rule.</div>', unsafe_allow_html=True)

        with _cR:
            st.markdown('<div class="card-h">📋 Decision Record</div>', unsafe_allow_html=True)
            _oc = {"helpful": "#3FCF8E", "harmful": "#F26D6D", "neutral": "#8B93A7", "pending": "#5A6274"}
            _dec = loop_proof.recent_decisions(12)
            if _dec:
                st.markdown("".join(
                    f'<div class="log" style="border-left-color:{_oc.get(d["outcome"], "#8B93A7")};">'
                    f'<b>{d["module"]}</b> · {d["action"]} '
                    f'<span style="color:{_oc.get(d["outcome"], "#8B93A7")};font-weight:700;">[{d["outcome"].upper()}]</span></div>'
                    for d in _dec
                ), unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Decisions will appear here as the loop runs.</div>', unsafe_allow_html=True)


live_view()
