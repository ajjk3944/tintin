# 🧠 Tensor Titan — One-Page Pitch & Architecture

**DIU CSE AI Innovation Hackathon 2026**

---

## 🎯 The Hook (say this first)
> **Tensor Titan is an AI autopilot for GPU clusters — it predicts hardware failures *before* they happen, auto-migrates jobs to safe nodes, and eliminates idle-power waste.**

Reactive dashboards tell you a GPU already died. We **predict and prevent**.

---

## 🔥 The Problem (Real-World Impact)
AI research labs lose huge amounts of money and time because:
- A GPU **overheats and crashes** mid-training → days of work + thousands of taka lost.
- GPUs sit **idle** while still drawing power → wasted electricity + carbon.
- There is **no early-warning system** and no automatic response.

At DIU's own AI lab rate: **1 GPU ≈ 280৳/hour**. One avoided crash or idle stretch pays for itself.

---

## ⚙️ The Solution — 4 cooperating AI services

```
            ┌─────────────────────────────────────────────────────┐
            │                  TENSOR TITAN                       │
            └─────────────────────────────────────────────────────┘

  [ GPU Nodes / This Machine ]
            │   real + simulated telemetry
            ▼
  ┌──────────────────────┐     temp / util / VRAM / power
  │ LiveGPUCollector     │────────────────────────────────┐
  │ (NVIDIA/Intel/AMD)   │                                 │
  └──────────────────────┘                                 ▼
            │                                     ┌──────────────────┐
            ▼                                     │  SQLite Database │
  ┌──────────────────────┐                        │  (time-series)   │
  │  SensorAI            │                        └──────────────────┘
  │  Isolation Forest +  │  risk score + root cause        │
  │  Random Forest       │────────────┐                    │
  └──────────────────────┘            ▼                    ▼
            │                 ┌──────────────────┐   ┌──────────────────┐
            │                 │  SchedulerAI     │   │  CostAI          │
            │                 │  score & place / │   │  idle detection, │
            │                 │  auto-migrate    │   │  cost + CO₂ calc │
            │                 └──────────────────┘   └──────────────────┘
            └────────────────────────┬───────────────────────┘
                                     ▼
                        ┌────────────────────────────┐
                        │  Streamlit Control Console │  (live dashboard)
                        └────────────────────────────┘
```

| Service | What it does | Tech |
|---|---|---|
| **LiveGPUCollector** | Reads real GPU/CPU/RAM telemetry; auto-detects NVIDIA / Intel / AMD, falls back to simulation | `GPUtil`, `pynvml`, `WMI`, `psutil` |
| **SensorAI** | Predicts failure risk per node + explains the root cause (XAI) | `Isolation Forest` + `Random Forest` (scikit-learn) |
| **SchedulerAI** | Scores nodes and places/migrates jobs to the healthiest one | Priority queue + weighted scoring |
| **CostAI** | Flags idle GPUs, computes running cost + CO₂ saved | Background scanner thread |
| **Console** | Real-time NOC-style dashboard + live fault-injection demo | Streamlit + Plotly |

**Scheduler formula:** `Score = (1 − Risk)×0.5 + FreeVRAM×0.3 + ThermalHeadroom×0.2`

---

## 📊 Impact Numbers (Scalability & Sustainability)
- **Crash prevention:** each auto-migration saves an entire training run (days of compute).
- **Cost:** idle GPUs flagged in 5 min → direct ৳ savings, shown live per session.
- **Carbon:** CO₂ prevented computed on Bangladesh grid intensity (**0.59 kg/kWh**).
- **Scale:** 5 lab nodes today → drop one agent per machine → 500+ GPUs, cloud or on-prem.

---

## 🆚 What's Real vs Simulated (be honest — it scores)
- ✅ **Real:** live hardware telemetry (Station #1 = this machine), the full ML pipeline, scheduler logic, cost/CO₂ engine, database, dashboard.
- 🧩 **Simulated:** the other 4 lab nodes (realistic synthetic data) and the ML training set — the *same* pipeline runs on both, so production only needs the collector pointed at real nodes.

---

## 🏆 Why We Win
- **Innovation:** predictive + auto-remediation, not just monitoring.
- **Technical depth:** 2 ML models, real-time pipeline, multi-vendor hardware layer.
- **Impact:** money + carbon saved, quantified live on Bangladesh rates.
- **Demo:** judges inject a live fault and watch the AI fix it in seconds.

> **Predict. Prevent. Save. — Tensor Titan.**
