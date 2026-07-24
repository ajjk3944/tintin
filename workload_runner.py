"""
workload_runner.py — Tensor Titan
Runs a REAL compute workload on THIS machine so that assigning a job actually
makes the hardware work (utilization / temperature genuinely climb).

- If an NVIDIA GPU + PyTorch (CUDA) is available -> real GPU matrix workload.
- Otherwise -> real heavy CPU workload (numpy BLAS matmul). This still spikes
  the CPU/RAM, which the system-based live node reflects.

Safe for demos & cloud: the workload auto-stops after `max_seconds`.
"""
import threading
import time

import numpy as np

try:
    import torch
    _HAS_CUDA = bool(torch.cuda.is_available())
except Exception:
    torch = None
    _HAS_CUDA = False

_lock = threading.Lock()
_stop_evt = threading.Event()
_thread = None
_state = {
    "running": False, "job": None, "node": None, "priority": None,
    "device": None, "started": None, "max_seconds": None,
}


def _cpu_loop(stop_evt, size=720):
    """Heavy real CPU work: continuous large matrix multiplications."""
    while not stop_evt.is_set():
        a = np.random.rand(size, size)
        b = np.random.rand(size, size)
        c = a @ b
        _ = float(c.sum())
        time.sleep(0.004)  # tiny yield so the UI thread stays responsive


def _gpu_loop(stop_evt, size=4096):
    """Real GPU work via CUDA tensor matmul."""
    dev = torch.device("cuda")
    while not stop_evt.is_set():
        a = torch.rand((size, size), device=dev)
        b = torch.rand((size, size), device=dev)
        c = a @ b
        torch.cuda.synchronize()
        _ = float(c.sum().item())
        time.sleep(0.002)


def _watchdog(stop_evt, max_seconds, started):
    while not stop_evt.is_set():
        if max_seconds and (time.time() - started) > max_seconds:
            stop_evt.set()
            break
        time.sleep(1)


def start_workload(job_name, node_id, priority=3, max_seconds=90):
    """Start a real workload on this machine. Replaces any running one."""
    global _thread, _stop_evt, _state
    stop_workload()
    _stop_evt = threading.Event()
    started = time.time()
    device = "gpu" if _HAS_CUDA else "cpu"
    target = _gpu_loop if _HAS_CUDA else _cpu_loop
    _thread = threading.Thread(target=target, args=(_stop_evt,), daemon=True)
    _thread.start()
    threading.Thread(target=_watchdog, args=(_stop_evt, max_seconds, started), daemon=True).start()
    with _lock:
        _state = {
            "running": True, "job": job_name, "node": int(node_id),
            "priority": priority, "device": device, "started": started,
            "max_seconds": max_seconds,
        }


def stop_workload():
    """Stop the running workload (if any)."""
    global _state
    _stop_evt.set()
    with _lock:
        _state = {
            "running": False, "job": None, "node": None, "priority": None,
            "device": None, "started": None, "max_seconds": None,
        }


def workload_status():
    """Return a snapshot of the current workload state (with elapsed seconds)."""
    with _lock:
        s = dict(_state)
    if s.get("running") and _stop_evt.is_set():
        s["running"] = False
    if s.get("running") and s.get("started"):
        s["elapsed"] = time.time() - s["started"]
    else:
        s["elapsed"] = 0
    return s


def has_gpu():
    return _HAS_CUDA
