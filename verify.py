from cluster_config import CLUSTER_NODES
from data_simulator import generate_metrics
from sensor_ai import predict_risk, load_models
from scheduler_ai import add_job, assign_job, queue_length
from cost_ai import get_cost_summary
from database import init_db

init_db()
load_models()
df = generate_metrics()
risk = predict_risk(df)
cost = get_cost_summary()

print("=== SYSTEM VERIFICATION ===")
print(f"Nodes loaded: {len(CLUSTER_NODES)}")
print(f"Metrics generated: {len(df)} rows")
print(f"Risk columns: {list(risk.columns)}")

for _, r in risk.iterrows():
    node = CLUSTER_NODES[r["node_id"]]
    print(f"  {node['hostname']:32s} | {node['gpu_model']:20s} | Risk: {r['risk_score']:5.1f}% [{r['risk_level']}]")
    print(f"    Job: {node['current_job']}")
    print(f"    Cause: {r['root_cause']}")
    print()

print(f"Cost summary: {cost}")
print()
print("=== ALL SYSTEMS GO ===")
