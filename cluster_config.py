"""
cluster_config.py — DIU CSE AI Research Lab GPU Cluster Definition
Defines the 5 GPU workstations in the lab with their hardware specs and active workloads.
"""

# ─── GPU LAB NODE DEFINITIONS ────────────────────────────────────────────────
# These represent the 5 physical GPU workstations in DIU CSE AI Research Lab.

CLUSTER_NODES = {
    1: {
        "node_id": 1,
        "hostname": "gpu-lab-01",
        "display_name": "GPU Lab Station #1",
        "gpu_model": "NVIDIA RTX 4090",
        "gpu_vram_gb": 24,
        "gpu_tdp_watts": 450,
        "location": "CSE AI Lab — Rack A, Slot 1",
        "assigned_researcher": "Md. Arif Hossain (CSE, Batch-51)",
        "current_job": "LLaMA-3 8B Finetune — Bangla Language Model",
        "job_type": "LLM Training",
        "base_util": 87,
        "base_temp": 74,
        "base_memory_pct": 88,  # % of VRAM used
        "base_power": 390,
    },
    2: {
        "node_id": 2,
        "hostname": "gpu-lab-02",
        "display_name": "GPU Lab Station #2",
        "gpu_model": "NVIDIA RTX 3090",
        "gpu_vram_gb": 24,
        "gpu_tdp_watts": 350,
        "location": "CSE AI Lab — Rack A, Slot 2",
        "assigned_researcher": "Farhan Tanvir (CSE, Batch-53)",
        "current_job": "YOLOv9 Object Detection — Traffic Surveillance",
        "job_type": "CV Model Training",
        "base_util": 79,
        "base_temp": 69,
        "base_memory_pct": 65,
        "base_power": 290,
    },
    3: {
        "node_id": 3,
        "hostname": "gpu-lab-03",
        "display_name": "GPU Lab Station #3",
        "gpu_model": "NVIDIA RTX 4080",
        "gpu_vram_gb": 16,
        "gpu_tdp_watts": 320,
        "location": "CSE AI Lab — Rack B, Slot 1",
        "assigned_researcher": "Nusrat Jahan (CSE, Batch-52)",
        "current_job": "Stable Diffusion XL — Bengali Art Generation",
        "job_type": "Generative AI",
        "base_util": 91,
        "base_temp": 77,
        "base_memory_pct": 95,
        "base_power": 305,
    },
    4: {
        "node_id": 4,
        "hostname": "gpu-lab-04",
        "display_name": "GPU Lab Station #4",
        "gpu_model": "NVIDIA RTX 3080",
        "gpu_vram_gb": 12,
        "gpu_tdp_watts": 320,
        "location": "CSE AI Lab — Rack B, Slot 2",
        "assigned_researcher": "Tahsin Ahmed (CSE, Batch-54)",
        "current_job": "BERT-Large Finetune — Bangla Sentiment Analysis",
        "job_type": "NLP Training",
        "base_util": 72,
        "base_temp": 64,
        "base_memory_pct": 72,
        "base_power": 245,
    },
    5: {
        "node_id": 5,
        "hostname": "gpu-lab-05",
        "display_name": "GPU Lab Station #5",
        "gpu_model": "NVIDIA RTX 3070",
        "gpu_vram_gb": 8,
        "gpu_tdp_watts": 220,
        "location": "CSE AI Lab — Rack C, Slot 1",
        "assigned_researcher": "Available / Queue",
        "current_job": "Idle — Awaiting Job Assignment",
        "job_type": "Idle",
        "base_util": 4,
        "base_temp": 42,
        "base_memory_pct": 8,
        "base_power": 28,
    },
}

# ─── COST CONFIGURATION ───────────────────────────────────────────────────────
COST_PER_GPU_PER_HOUR_BDT = 280   # ~2.5 USD at current rate, in Taka for local relevance
COST_PER_GPU_PER_HOUR_USD = 2.50
ELECTRICITY_PER_KWH_BDT = 11.0   # Bangladesh electricity rate (BDT per kWh)
CO2_PER_KWH_KG = 0.59            # Bangladesh grid CO2 intensity (kg/kWh)
