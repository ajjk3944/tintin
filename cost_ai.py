import threading
import time
from data_simulator import get_util_history
from database import log_idle
from cluster_config import CLUSTER_NODES, COST_PER_GPU_PER_HOUR_USD, CO2_PER_KWH_KG

IDLE_THRESHOLD = 5.0
IDLE_MINUTES_REQUIRED = 5
SCAN_INTERVAL = 10
COST_PER_GPU_PER_HOUR = COST_PER_GPU_PER_HOUR_USD
NUM_NODES = len(CLUSTER_NODES)

_idle_nodes = set()
_idle_durations = {}
_running = False
_lock = threading.Lock()

def _scan_loop():
    global _idle_nodes, _idle_durations
    while _running:
        history = get_util_history()
        with _lock:
            for node_id, hist in history.items():
                if len(hist) >= IDLE_MINUTES_REQUIRED:
                    recent = hist[-IDLE_MINUTES_REQUIRED:]
                    avg_util = sum(recent) / len(recent)
                    if avg_util < IDLE_THRESHOLD:
                        _idle_nodes.add(node_id)
                        _idle_durations[node_id] = _idle_durations.get(node_id, 0) + SCAN_INTERVAL / 60
                        log_idle(node_id, _idle_durations[node_id])
                    else:
                        _idle_nodes.discard(node_id)
                        _idle_durations.pop(node_id, None)
        time.sleep(SCAN_INTERVAL)

def start_scanner():
    global _running, _idle_nodes, _idle_durations
    _running = True
    # Pre-seed node 5 as idle (configured as Idle in cluster_config)
    # 30 min already tracked so CO2/savings show from session start
    _idle_nodes.add(5)
    _idle_durations[5] = 30.0
    t = threading.Thread(target=_scan_loop, daemon=True)
    t.start()

def stop_scanner():
    global _running
    _running = False

def get_idle_nodes():
    with _lock:
        return list(_idle_nodes)

def get_cost_summary():
    with _lock:
        idle_count = len(_idle_nodes)
        active_count = NUM_NODES - idle_count
        hourly_cost = active_count * COST_PER_GPU_PER_HOUR
        idle_hourly_waste = idle_count * COST_PER_GPU_PER_HOUR
        monthly_waste = idle_hourly_waste * 24 * 30
        total_idle_minutes = sum(_idle_durations.values())
        savings = (total_idle_minutes / 60) * COST_PER_GPU_PER_HOUR
        # Each idle GPU saved: ~0.25 kW × time × CO2 intensity
        saved_kwh = (total_idle_minutes / 60) * 0.25
        co2_saved_kg = round(saved_kwh * CO2_PER_KWH_KG, 3)

    return {
        'active_gpus': active_count,
        'idle_gpus': idle_count,
        'hourly_cost': round(hourly_cost, 2),
        'idle_waste_hourly': round(idle_hourly_waste, 2),
        'monthly_waste': round(monthly_waste, 2),
        'total_savings': round(savings, 2),
        'co2_saved_kg': co2_saved_kg,
    }
