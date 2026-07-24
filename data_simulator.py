"""
data_simulator.py — Tensor Titan
Generates realistic GPU telemetry for DIU CSE AI Research Lab cluster nodes.

Data sources, combined automatically:
  1. LIVE HARDWARE — real readings from THIS machine (via live_gpu_collector).
     Every real GPU detected is mapped to a node in order. On integrated/no-GPU
     machines, one "system-based" live node is shown.
  2. SIMULATION — remaining nodes get realistic synthetic telemetry.

Also supports:
  - Live Chaos Injection (thermal/idle/memory/power) for demos.
  - Job Assignment: assign a named job (with priority) to any node. The node's
    label updates and simulated nodes visibly ramp up. On a LIVE node, a REAL
    workload (see workload_runner.py) drives the actual telemetry spike.
"""
import numpy as np
import pandas as pd
from datetime import datetime
import time
import psutil
from cluster_config import CLUSTER_NODES

# ─── SIMULATION STATE ────────────────────────────────────────────
_sim_state = {
    nid: {
        "phase": np.random.uniform(0, 2 * np.pi),
        "anomaly_cooldown": 0,
    }
    for nid in CLUSTER_NODES
}

# ─── UTILIZATION HISTORY (for idle detection) ─────────────────────────
_utilization_history = {nid: [] for nid in CLUSTER_NODES}

# ─── CHAOS INJECTION (live demo controls) ───────────────────────────
_chaos_overrides = {}   # node_id → chaos_type

def trigger_chaos(node_id: int, chaos_type: str):
    """chaos_type: 'thermal_spike' | 'idle_force' | 'memory_leak' | 'power_surge' | 'reset'"""
    if chaos_type == "reset":
        _chaos_overrides.pop(node_id, None)
    else:
        _chaos_overrides[node_id] = chaos_type

def clear_all_chaos():
    _chaos_overrides.clear()

# ─── JOB ASSIGNMENT (scheduler / manual) ────────────────────────────
_node_jobs = {}   # node_id → {"job_name": str, "priority": int}

def assign_job_to_node(node_id: int, job_name: str, priority: int = 3):
    """Pin a named job to a node. Its card label updates immediately; simulated
    nodes ramp up their load. Live nodes show real telemetry from the workload."""
    _node_jobs[int(node_id)] = {"job_name": job_name, "priority": int(priority)}

def clear_node_job(node_id: int):
    _node_jobs.pop(int(node_id), None)

def clear_all_node_jobs():
    _node_jobs.clear()

def get_node_jobs() -> dict:
    return dict(_node_jobs)

# ─── LIVE HARDWARE MODE (real telemetry from THIS machine) ─────────────────
_live_enabled = False
_live_collector = None


def set_live_mode(enabled: bool, node_id: int = 1):
    """Enable/disable live hardware mode. Every real GPU on this PC becomes a
    live node automatically (node_id kept only for backwards compatibility)."""
    global _live_enabled, _live_collector
    _live_enabled = bool(enabled)
    if _live_enabled and _live_collector is None:
        try:
            from live_gpu_collector import LiveGPUCollector
            _live_collector = LiveGPUCollector(num_simulated_gpus=5)
        except Exception as e:  # pragma: no cover - depends on host libs
            print(f"[WARN] Live collector unavailable, staying in simulation: {e}")
            _live_collector = None
            _live_enabled = False


def _get_live_data():
    """
    Return (readings, is_real_gpu).
    - Real GPUs (NVIDIA/Intel/AMD): map every detected GPU to a node.
    - No real GPU (pure simulation): expose ONE system-based live node so a
      GPU-less laptop still shows its real CPU/RAM-driven telemetry.
    """
    if not _live_enabled or _live_collector is None:
        return [], False
    try:
        info = _live_collector.get_mode_info()
        is_real = bool(info.get("is_real_gpu", False))
        readings = _live_collector.collect_metrics() or []
        if is_real:
            return readings[: len(CLUSTER_NODES)], True
        return readings[:1], False
    except Exception as e:  # pragma: no cover
        print(f"[WARN] Live reading failed, using simulation this tick: {e}")
        return [], False


def live_mode_info() -> dict:
    """Report current live-mode status for the dashboard header/badges."""
    info = {"enabled": False, "is_real_gpu": False, "mode": None,
            "num_live": 0, "gpu_name": None}
    if not (_live_enabled and _live_collector is not None):
        return info
    try:
        mi = _live_collector.get_mode_info()
        readings, is_real = _get_live_data()
        info["enabled"] = True
        info["is_real_gpu"] = is_real
        info["mode"] = mi.get("mode")
        info["num_live"] = len(readings)
        detected = mi.get("detected_gpus") or []
        if detected:
            info["gpu_name"] = detected[0].get("name")
    except Exception:
        pass
    return info

# ─── CORE METRIC GENERATION ─────────────────────────────────────

def _get_system_factor() -> float:
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    return (cpu + mem) / 200.0

def _generate_node_metrics(node_id, system_factor, live_reading=None, assignment=None) -> dict:
    cfg = CLUSTER_NODES[node_id]
    state = _sim_state[node_id]
    t = time.time()

    wave = np.sin(t / 12 + state["phase"])
    noise = lambda std: np.random.normal(0, std)

    base_util = cfg["base_util"]
    base_temp = cfg["base_temp"]
    base_mem_pct = cfg["base_memory_pct"]
    base_power = cfg["base_power"]
    vram_gb = cfg["gpu_vram_gb"]
    tdp = cfg["gpu_tdp_watts"]

    utilization = np.clip(base_util + wave * 8 + system_factor * 5 + noise(3), 1, 99)
    temperature = np.clip(base_temp + (utilization - base_util) * 0.25 + noise(2), 35, 95)
    memory_used = np.clip((base_mem_pct / 100) * vram_gb + wave * 0.5 + noise(0.3), 0.1, vram_gb)
    power_draw = np.clip(base_power + (utilization - base_util) * 1.5 + noise(10), 15, tdp + 20)

    # Occasional organic anomaly (2% chance)
    if state["anomaly_cooldown"] <= 0:
        if np.random.random() < 0.02:
            kind = np.random.choice(["thermal", "idle"])
            if kind == "thermal":
                temperature = np.random.uniform(87, 93)
                utilization = np.random.uniform(88, 97)
                power_draw = np.random.uniform(tdp * 0.9, tdp * 1.05)
            else:
                utilization = np.random.uniform(1, 4)
                temperature = max(38, temperature - 20)
                power_draw = np.random.uniform(15, 40)
            state["anomaly_cooldown"] = 25
    else:
        state["anomaly_cooldown"] -= 1

    # ── LIVE HARDWARE OVERLAY (real readings from this machine) ──
    data_source = "sim"
    gpu_name = None
    if live_reading is not None:
        try:
            temperature = float(live_reading["temperature"])
            utilization = float(live_reading["utilization"])
            mem_total = float(live_reading.get("memory_total") or vram_gb)
            mem_used = float(live_reading.get("memory_used", 0.0))
            mem_pct = (mem_used / mem_total) if mem_total else 0.0
            memory_used = float(np.clip(mem_pct * vram_gb, 0.1, vram_gb))
            power_draw = float(live_reading["power_draw"])
            gpu_name = live_reading.get("gpu_name")
            data_source = "live"
        except Exception:
            data_source = "sim"

    chaos = _chaos_overrides.get(node_id)

    # ── ASSIGNED JOB (manual / scheduler) ──
    current_job = cfg["current_job"]
    job_type = cfg["job_type"]
    researcher = cfg["assigned_researcher"]
    if assignment is not None:
        current_job = assignment.get("job_name", current_job)
        job_type = f"Priority {assignment.get('priority', 3)}"
        researcher = "🔴 Assigned via SchedulerAI"
        # Simulated nodes visibly ramp up. Live nodes keep REAL telemetry (the
        # actual workload from workload_runner drives their spike).
        if data_source != "live" and not chaos:
            utilization = float(np.clip(np.random.normal(89, 3), 80, 97))
            temperature = float(np.clip(base_temp + 8 + noise(2), 55, 84))
            memory_used = float(np.clip(vram_gb * 0.62 + noise(0.4), 0.5, vram_gb))
            power_draw = float(np.clip(base_power + 45 + noise(10), 40, tdp + 10))

    # ── CHAOS override wins over everything ──
    if chaos == "thermal_spike":
        temperature = 93.5
        power_draw = min(tdp * 1.05, base_power * 1.2)
        utilization = 97.0
    elif chaos == "idle_force":
        utilization = 1.5
        power_draw = 22.0
        temperature = 41.0
    elif chaos == "memory_leak":
        memory_used = vram_gb * 0.97
        utilization = 89.0
    elif chaos == "power_surge":
        power_draw = tdp * 1.08
        temperature = 88.0

    return {
        "node_id": node_id,
        "hostname": cfg["hostname"],
        "display_name": cfg["display_name"],
        "gpu_model": gpu_name or cfg["gpu_model"],
        "gpu_vram_gb": vram_gb,
        "current_job": current_job,
        "job_type": job_type,
        "researcher": researcher,
        "location": cfg["location"],
        "temperature": round(float(temperature), 1),
        "utilization": round(float(utilization), 1),
        "memory_used": round(float(memory_used), 2),
        "power_draw": round(float(power_draw), 1),
        "timestamp": datetime.now().isoformat(),
        "chaos_active": chaos or "none",
        "data_source": data_source,
    }


def generate_metrics() -> pd.DataFrame:
    """
    Generate fresh metrics for all lab nodes. Real GPUs map to the first nodes;
    the rest are simulated. Assigned jobs override node labels/load.
    """
    system_factor = _get_system_factor()
    live_readings, _ = _get_live_data()
    num_live = min(len(live_readings), len(CLUSTER_NODES))

    rows = []
    for idx, node_id in enumerate(CLUSTER_NODES):
        lr = live_readings[idx] if idx < num_live else None
        assignment = _node_jobs.get(node_id)
        m = _generate_node_metrics(node_id, system_factor, live_reading=lr, assignment=assignment)
        rows.append(m)

        _utilization_history[node_id].append(m["utilization"])
        if len(_utilization_history[node_id]) > 15:
            _utilization_history[node_id].pop(0)

    return pd.DataFrame(rows)


def get_util_history() -> dict:
    return _utilization_history.copy()


def reset_history():
    global _utilization_history
    _utilization_history = {nid: [] for nid in CLUSTER_NODES}
    _chaos_overrides.clear()
    _node_jobs.clear()
