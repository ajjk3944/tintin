# 🎤 Tensor Titan — 2-Minute Live Demo Script

**Goal:** Make the judges *feel* the problem and *see* the AI solve it in real time.
**Team roles:** 1 Presenter (talks), 1 Driver (controls the dashboard). Rehearse **3 times**.

---

## ⏱ Timeline (target: 2 min 00 sec)

### 0:00 – 0:20 — The Hook (Presenter)
> "AI labs waste crores of taka on GPUs that either **crash mid-training** or sit **idle burning power**. There is no early warning. Our system, **Tensor Titan**, is an AI *autopilot* for GPU clusters — it predicts a failure **before** it happens and moves the job automatically."

*(Screen: the full dashboard is already open, clock ticking, 5 nodes green/live.)*

### 0:20 – 0:40 — Show It's Real (Driver + Presenter)
- Driver: point to **Station #1** — the `🛰 LIVE HW` badge.
> "This isn't fake data. **Station #1 is reading the real GPU/CPU telemetry of this very laptop** through our live collector. Watch — if I load this machine, the numbers move."
- Driver: (optional) open a heavy tab / run something → utilization ticks up.

### 0:40 – 1:10 — The "Wow" Moment: Predict + Prevent (Driver)
- Driver: open the **⚡ Demo Control Room** (sidebar) → select **Station #3** → click **🔥 Thermal Spike**.
> "Imagine a GPU overheating during a 3-day training run. Watch what our AI does — instantly."
- On screen (narrate as it happens):
  1. Station #3 card turns **red → CRITICAL**.
  2. **SensorAI** risk score jumps to ~80%+ with a root cause: *Thermal Spike (93°C)*.
  3. Go to **⚙️ Smart Scheduler** tab → an **Auto-Migration Alert** appears, **Crashes Prevented** counter goes up.
> "SensorAI caught it, explained *why*, and SchedulerAI **migrated the job to a healthy node** — no human, no crash, no lost training."

### 1:10 – 1:35 — The Money & Green Angle (Presenter + Driver)
- Driver: open **💰 Cost & Energy** tab.
> "It also watches for waste. An idle GPU is flagged in 5 minutes and its work is reassigned. This session alone we've saved **\$X** and prevented **X kg of CO₂** — on Bangladesh's grid rate."
- Driver: point to the savings banner + CO₂ number.

### 1:35 – 2:00 — Close: Scale + Vision (Presenter)
> "Today it runs on our lab's 5 workstations. Tomorrow, drop one lightweight agent on any machine — NVIDIA, Intel, AMD, or cloud — and it scales to 500 GPUs. **Predict. Prevent. Save. That's Tensor Titan.**"
- Driver: click **♻️ Clear All Faults** to reset to a clean green board.

---

## ✅ Pre-Demo Checklist (5 min before)
- [ ] `streamlit run dashboard.py` running, browser full-screen, zoom ~90%.
- [ ] Sidebar toggle **🛰 Live hardware mode** is ON (Station #1 shows LIVE HW badge).
- [ ] `♻️ Clear All Faults` clicked — board starts clean.
- [ ] Refresh interval set to ~4s (not too fast for narration).
- [ ] Internet on (so Google Fonts load and design looks premium).
- [ ] Backup: a screen-recording of a successful run, in case of live failure.

## 🗣 One-liners to repeat
- "**Reactive monitoring tells you it's dead. We predict it before it dies.**"
- "**Every red card you see, our AI turns green — automatically.**"
- "**Real hardware today, any hardware tomorrow.**"

## ⚠️ Honesty note (if a judge asks)
> "Station #1 is genuine live hardware. Stations #2–5 are a realistic simulation of the full lab cluster — the exact same AI pipeline runs on both, so in production you just point the collector at real nodes."
This honesty scores points under **Technical Complexity** and **Real-world Impact**; over-claiming loses them.
