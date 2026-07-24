"""
data_simulator.py — Tensor Titan
Generates realistic GPU telemetry for DIU CSE AI Research Lab cluster nodes.

Two data sources, combined automatically:
  1. LIVE HARDWARE — real readings from THIS machine (via live_gpu_collector).
     EVERY real GPU detected on the PC is mapped to a node, in order
     (GPU 0 → Station #1, GPU 1 → Station #2, ...). On machines with an
     integrated/Intel/AMD GPU or none, one "system-based" live node is shown.
  2. SIMULATION — any remaining nodes are filled with realistic synthetic
     telemetry so the full 5-node cluster story is always complete.

Also supports Live Chaos Injection for hackathon demos.
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
    """
    Inject a live fault into a node for demo purposes.
    chaos_type: 'thermal_spike' | 'idle_force' | 'memory_leak' | 'power_surge' | 'reset'
    """
    if chaos_type == "reset":
        _chaos_overrides.pop(node_id, None)
    else:
        _chaos_overrides[node_id] = chaos_type

def clear_all_chaos():
    _chaos_overrides.clear()

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
        # simulation mode: only the first node reflects this machine's system load
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
    """Use real CPU/RAM load to influence simulation realism."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    return (cpu + mem) / 200.0   # 0.0 → 1.0

def _generate_node_metrics(node_id: int, system_factor: float, live_reading=None) -> dict:
    cfg = CLUSTER_NODES[node_id]
    state = _sim_state[node_id]
    t = time.time()

    wave = np.sin(t / 12 + state["phase"])
    noise = lambda std: np.random.normal(0, std)

    # ── Base values from node config ──
    base_util = cfg["base_util"]
    base_temp = cfg["base_temp"]
    base_mem_pct = cfg["base_memory_pct"]
    base_power = cfg["base_power"]
    vram_gb = cfg["gpu_vram_gb"]
    tdp = cfg["gpu_tdp_watts"]

    # ── Simulate realistic fluctuation ──
    utilization = np.clip(base_util + wave * 8 + system_factor * 5 + noise(3), 1, 99)
    temperature = np.clip(base_temp + (utilization - base_util) * 0.25 + noise(2), 35, 95)
    memory_used = np.clip((base_mem_pct / 100) * vram_gb + wave * 0.5 + noise(0.3), 0.1, vram_gb)
    power_draw = np.clip(base_power + (utilization - base_util) * 1.5 + noise(10), 15, tdp + 20)

    # ── Occasional organic anomaly (2% chance) ──
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
    if live_reading is not None:
        try:
            temperature = float(live_reading["temperature"])
            utilization = float(live_reading["utilization"])
            mem_total = float(live_reading.get("memory_total") or vram_gb)
            mem_used = float(live_reading.get("memory_used", 0.0))
            mem_pct = (mem_used / mem_total) if mem_total else 0.0
            memory_used = float(np.clip(mem_pct * vram_gb, 0.1, vram_gb))
            power_draw = float(live_reading["power_draw"])
            data_source = "live"
        except Exception:
            data_source = "sim"

    # ── Apply chaos override if set (wins over both sim and live) ──
    chaos = _chaos_overrides.get(node_id)
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

    # A live GPU that gets a chaos fault is a demo, not real anymore
    gpu_name = live_reading.get("gpu_name") if (live_reading and data_source == "live") else None

    return {
        "node_id": node_id,
        "hostname": cfg["hostname"],
        "display_name": cfg["display_name"],
        "gpu_model": gpu_name or cfg["gpu_model"],
        "gpu_vram_gb": vram_gb,
        "current_job": cfg["current_job"],
        "job_type": cfg["job_type"],
        "researcher": cfg["assigned_researcher"],
        "location": cfg["location"],
        # Hardware metrics
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
    Generate fresh metrics for all lab nodes.
    Real GPUs on this machine are mapped to the first nodes; the rest are
    filled with simulation. Returns a DataFrame the ML layer + dashboard use.
    """
    system_factor = _get_system_factor()
    live_readings, _ = _get_live_data()   # real telemetry from this machine
    num_live = min(len(live_readings), len(CLUSTER_NODES))

    rows = []
    for idx, node_id in enumerate(CLUSTER_NODES):
        lr = live_readings[idx] if idx < num_live else None
        m = _generate_node_metrics(node_id, system_factor, live_reading=lr)
        rows.append(m)

        # Update utilization history for idle detection
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
